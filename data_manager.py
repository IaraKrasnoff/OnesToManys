"""
Data Management Utilities for Orders API
Provides file-based export/import functionality
"""

import json
import sqlite3
from datetime import date
from typing import Optional
from database import OrderDatabase, Order, OrderItem

class DataManager:
    def __init__(self, db_path: str = "orders.db"):
        self.db = OrderDatabase(db_path)
        self.db_path = db_path
    
    def export_to_json_file(self, filename: Optional[str] = None):
        """Export all data to a JSON file"""
        if not filename:
            filename = f"orders_export_{date.today().isoformat()}.json"
        
        orders = self.db.get_all_orders()
        export_data = {
            "export_date": date.today().isoformat(),
            "total_orders": len(orders),
            "data": []
        }
        
        for order in orders:
            items = self.db.get_order_items_by_order(order.order_id or 0)
            order_data = {
                "order": order.dict(),
                "items": [item.dict() for item in items]
            }
            export_data["data"].append(order_data)
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"Data exported to {filename}")
        print(f"Exported {len(orders)} orders with {sum(len(od['items']) for od in export_data['data'])} items")
        return filename
    
    def import_from_json_file(self, filename: str):
        """Import data from a JSON file"""
        try:
            with open(filename, 'r') as f:
                import_data = json.load(f)
            
            if "data" not in import_data:
                raise ValueError("Invalid import format: missing 'data' field")
            
            imported_orders = 0
            imported_items = 0
            
            for order_data in import_data["data"]:
                if "order" not in order_data or "items" not in order_data:
                    print(f"Skipping invalid order data: {order_data}")
                    continue
                
                # Create order (without order_id to let it auto-generate)
                order_info = order_data["order"]
                new_order = Order(
                    customer_id=order_info["customer_id"],
                    order_date=order_info["order_date"],
                    total_amount=0.0  # Will be recalculated
                )
                created_order = self.db.create_order(new_order)
                imported_orders += 1
                
                # Create order items
                for item_info in order_data["items"]:
                    new_item = OrderItem(
                        order_id=created_order.order_id or 0,
                        product_id=item_info["product_id"],
                        quantity=item_info["quantity"],
                        unit_price=item_info["unit_price"]
                    )
                    self.db.create_order_item(new_item)
                    imported_items += 1
            
            print(f"Import completed successfully:")
            print(f"Imported {imported_orders} orders")
            print(f"Imported {imported_items} items")
            return {"imported_orders": imported_orders, "imported_items": imported_items}
        
        except FileNotFoundError:
            print(f"File not found: {filename}")
            return None
        except Exception as e:
            print(f"Import failed: {str(e)}")
            return None
    
    def export_to_sql_file(self, filename: Optional[str] = None):
        """Export all data to a SQL file"""
        if not filename:
            filename = f"orders_export_{date.today().isoformat()}.sql"
        
        orders = self.db.get_all_orders()
        
        with open(filename, 'w') as f:
            # Write header
            f.write("-- Orders and Order Items Export\n")
            f.write(f"-- Generated on {date.today().isoformat()}\n\n")
            
            # Write table creation statements
            f.write("CREATE TABLE IF NOT EXISTS orders (\n")
            f.write("    order_id INTEGER PRIMARY KEY AUTOINCREMENT,\n")
            f.write("    customer_id INTEGER NOT NULL,\n")
            f.write("    order_date DATE NOT NULL,\n")
            f.write("    total_amount DECIMAL(10, 2) DEFAULT 0.00\n")
            f.write(");\n\n")
            
            f.write("CREATE TABLE IF NOT EXISTS order_items (\n")
            f.write("    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,\n")
            f.write("    order_id INTEGER NOT NULL,\n")
            f.write("    product_id INTEGER NOT NULL,\n")
            f.write("    quantity INTEGER NOT NULL,\n")
            f.write("    unit_price DECIMAL(10, 2) NOT NULL,\n")
            f.write("    line_total DECIMAL(10, 2) NOT NULL,\n")
            f.write("    FOREIGN KEY (order_id) REFERENCES orders(order_id)\n")
            f.write(");\n\n")
            
            f.write("-- Data Inserts\n\n")
            
            total_items = 0
            for order in orders:
                # Order insert
                f.write(f"INSERT INTO orders (order_id, customer_id, order_date, total_amount) ")
                f.write(f"VALUES ({order.order_id}, {order.customer_id}, '{order.order_date}', {order.total_amount});\n")
                
                # Order items inserts
                items = self.db.get_order_items_by_order(order.order_id or 0)
                for item in items:
                    f.write(f"INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, line_total) ")
                    f.write(f"VALUES ({item.order_item_id}, {item.order_id}, {item.product_id}, {item.quantity}, {item.unit_price}, {item.line_total});\n")
                    total_items += 1
                
                f.write("\n")  # Empty line between orders
        
        print(f"SQL export completed: {filename}")
        print(f"Exported {len(orders)} orders with {total_items} items")
        return filename
    
    def backup_database(self, backup_filename: Optional[str] = None):
        """Create a complete backup of the SQLite database"""
        if not backup_filename:
            backup_filename = f"orders_backup_{date.today().isoformat()}.db"
        
        # Copy the database file
        import shutil
        shutil.copy2(self.db_path, backup_filename)
        
        print(f"Database backed up to: {backup_filename}")
        return backup_filename
    
    def get_database_info(self):
        """Get information about the current database"""
        orders = self.db.get_all_orders()
        all_items = self.db.get_all_order_items()
        
        if not orders:
            return {
                "status": "empty",
                "total_orders": 0,
                "total_items": 0,
                "database_file": self.db_path
            }
        
        return {
            "status": "active",
            "total_orders": len(orders),
            "total_items": len(all_items),
            "total_revenue": sum((order.total_amount or 0.0) for order in orders),
            "date_range": {
                "earliest": min(order.order_date for order in orders).isoformat(),
                "latest": max(order.order_date for order in orders).isoformat()
            },
            "database_file": self.db_path,
            "customer_count": len(set(order.customer_id for order in orders)),
            "product_count": len(set(item.product_id for item in all_items))
        }

def main():
    """Command line interface for data management"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_manager.py [export-json|export-sql|import-json|backup|info] [filename]")
        return
    
    command = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    dm = DataManager()
    
    if command == "export-json":
        dm.export_to_json_file(filename)
    elif command == "export-sql":
        dm.export_to_sql_file(filename)
    elif command == "import-json":
        if not filename:
            print("Filename required for import")
            return
        dm.import_from_json_file(filename)
    elif command == "backup":
        dm.backup_database(filename)
    elif command == "info":
        info = dm.get_database_info()
        print("\nDatabase Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    else:
        print("Unknown command. Available: export-json, export-sql, import-json, backup, info")

if __name__ == "__main__":
    main()
