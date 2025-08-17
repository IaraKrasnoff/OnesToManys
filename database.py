import sqlite3
from typing import Optional, List
from pydantic import BaseModel
import os
from datetime import date, datetime

class Order(BaseModel):
    order_id: Optional[int] = None
    customer_id: int
    order_date: date
    total_amount: Optional[float] = 0.0

class OrderItem(BaseModel):
    order_item_id: Optional[int] = None
    order_id: int
    product_id: int
    quantity: int
    unit_price: float
    line_total: Optional[float] = None

class OrderDatabase:
    def __init__(self, db_path: str = "orders.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Create the orders and order_items tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            # Create Orders table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    order_date DATE NOT NULL,
                    total_amount DECIMAL(10, 2) DEFAULT 0.00
                )
            """)
            
            # Create OrderItems table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    line_total DECIMAL(10, 2) NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id)
                )
            """)
            conn.commit()
    
    # Order CRUD operations
    def create_order(self, order: Order) -> Order:
        """Add a new order to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO orders (customer_id, order_date, total_amount)
                VALUES (?, ?, ?)
            """, (order.customer_id, order.order_date, order.total_amount))
            order.order_id = cursor.lastrowid
            conn.commit()
        return order
    
    def get_order(self, order_id: int) -> Optional[Order]:
        """Get an order by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            row = cursor.fetchone()
            if row:
                return Order(**dict(row))
        return None
    
    def get_all_orders(self) -> List[Order]:
        """Get all orders from the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM orders ORDER BY order_id")
            rows = cursor.fetchall()
            return [Order(**dict(row)) for row in rows]
    
    def update_order(self, order_id: int, order: Order) -> Optional[Order]:
        """Update an existing order"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE orders 
                SET customer_id = ?, order_date = ?, total_amount = ?
                WHERE order_id = ?
            """, (order.customer_id, order.order_date, order.total_amount, order_id))
            
            if conn.total_changes == 0:
                return None
            
            conn.commit()
            order.order_id = order_id
            return order
    
    def delete_order(self, order_id: int) -> bool:
        """Delete an order by ID (cascades to order items)"""
        with sqlite3.connect(self.db_path) as conn:
            # First delete all related order items
            conn.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
            # Then delete the order
            conn.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
            deleted = conn.total_changes > 0
            conn.commit()
            return deleted
    
    # OrderItem CRUD operations
    def create_order_item(self, order_item: OrderItem) -> OrderItem:
        """Add a new order item to the database"""
        # Calculate line total if not provided
        if order_item.line_total is None:
            order_item.line_total = round(order_item.quantity * order_item.unit_price, 2)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?)
            """, (order_item.order_id, order_item.product_id, order_item.quantity, 
                  order_item.unit_price, order_item.line_total))
            order_item.order_item_id = cursor.lastrowid
            conn.commit()
            
            # Update the total amount in the orders table
            self._update_order_total(order_item.order_id)
        
        return order_item
    
    def get_order_item(self, order_item_id: int) -> Optional[OrderItem]:
        """Get an order item by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM order_items WHERE order_item_id = ?", (order_item_id,))
            row = cursor.fetchone()
            if row:
                return OrderItem(**dict(row))
        return None
    
    def get_all_order_items(self) -> List[OrderItem]:
        """Get all order items from the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM order_items ORDER BY order_item_id")
            rows = cursor.fetchall()
            return [OrderItem(**dict(row)) for row in rows]
    
    def get_order_items_by_order(self, order_id: int) -> List[OrderItem]:
        """Get all order items for a specific order"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY order_item_id", (order_id,))
            rows = cursor.fetchall()
            return [OrderItem(**dict(row)) for row in rows]
    
    def update_order_item(self, order_item_id: int, order_item: OrderItem) -> Optional[OrderItem]:
        """Update an existing order item"""
        # Calculate line total if not provided
        if order_item.line_total is None:
            order_item.line_total = round(order_item.quantity * order_item.unit_price, 2)
            
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE order_items 
                SET order_id = ?, product_id = ?, quantity = ?, unit_price = ?, line_total = ?
                WHERE order_item_id = ?
            """, (order_item.order_id, order_item.product_id, order_item.quantity, 
                  order_item.unit_price, order_item.line_total, order_item_id))
            
            if conn.total_changes == 0:
                return None
            
            conn.commit()
            order_item.order_item_id = order_item_id
            
            # Update the total amount in the orders table
            self._update_order_total(order_item.order_id)
            
            return order_item
    
    def delete_order_item(self, order_item_id: int) -> bool:
        """Delete an order item by ID"""
        # First get the order_id for updating totals
        order_item = self.get_order_item(order_item_id)
        if not order_item:
            return False
            
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM order_items WHERE order_item_id = ?", (order_item_id,))
            deleted = conn.total_changes > 0
            conn.commit()
            
            if deleted:
                # Update the total amount in the orders table
                self._update_order_total(order_item.order_id)
            
            return deleted
    
    def _update_order_total(self, order_id: int):
        """Private method to update the total amount for an order"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COALESCE(SUM(line_total), 0.0) as total 
                FROM order_items 
                WHERE order_id = ?
            """, (order_id,))
            total = cursor.fetchone()[0]
            
            # Round to 2 decimal places for currency precision
            total = round(total, 2)
            
            conn.execute("""
                UPDATE orders 
                SET total_amount = ?
                WHERE order_id = ?
            """, (total, order_id))
            conn.commit()
