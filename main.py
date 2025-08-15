from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from database import Order, OrderItem, OrderDatabase
from datetime import date
import json
import os

class OrderItemRequest(BaseModel):
    """Simplified request model for creating order items"""
    product_id: int
    quantity: int
    unit_price: float

app = FastAPI(title="Orders API", description="A master-detail orders management API", version="2.0.0")
db = OrderDatabase()

@app.get("/")
def read_root():
    """Welcome endpoint"""
    return {"message": "Welcome to the Orders API!", "endpoints": {
        "orders": "/orders/",
        "order_items": "/order-items/",
        "docs": "/docs"
    }}

# Order endpoints
@app.post("/orders/", response_model=Order)
def create_order(order: Order):
    """Create a new order"""
    try:
        return db.create_order(order)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create order: {str(e)}")

@app.get("/orders/", response_model=List[Order])
def get_all_orders():
    """Get all orders"""
    return db.get_all_orders()

@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    """Get a specific order by ID"""
    order = db.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: int, order: Order):
    """Update an existing order"""
    updated_order = db.update_order(order_id, order)
    if updated_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return updated_order

@app.delete("/orders/{order_id}")
def delete_order(order_id: int):
    """Delete an order (cascades to order items)"""
    if not db.delete_order(order_id):
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}

# Order Item endpoints
@app.post("/order-items/", response_model=OrderItem)
def create_order_item(order_item: OrderItem):
    """Create a new order item"""
    try:
        # Verify the order exists
        if not db.get_order(order_item.order_id):
            raise HTTPException(status_code=404, detail="Order not found")
        return db.create_order_item(order_item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create order item: {str(e)}")

@app.get("/order-items/", response_model=List[OrderItem])
def get_all_order_items():
    """Get all order items"""
    return db.get_all_order_items()

@app.get("/order-items/{order_item_id}", response_model=OrderItem)
def get_order_item(order_item_id: int):
    """Get a specific order item by ID"""
    order_item = db.get_order_item(order_item_id)
    if order_item is None:
        raise HTTPException(status_code=404, detail="Order item not found")
    return order_item

@app.get("/orders/{order_id}/items", response_model=List[OrderItem])
def get_order_items_by_order(order_id: int):
    """Get all order items for a specific order"""
    # Verify the order exists
    if not db.get_order(order_id):
        raise HTTPException(status_code=404, detail="Order not found")
    return db.get_order_items_by_order(order_id)

@app.put("/order-items/{order_item_id}", response_model=OrderItem)
def update_order_item(order_item_id: int, order_item: OrderItem):
    """Update an existing order item"""
    updated_order_item = db.update_order_item(order_item_id, order_item)
    if updated_order_item is None:
        raise HTTPException(status_code=404, detail="Order item not found")
    return updated_order_item

@app.delete("/order-items/{order_item_id}")
def delete_order_item(order_item_id: int):
    """Delete an order item"""
    if not db.delete_order_item(order_item_id):
        raise HTTPException(status_code=404, detail="Order item not found")
    return {"message": "Order item deleted successfully"}

# Enhanced Master-Detail Relationship Endpoints (Phase 2)
@app.post("/orders/{order_id}/items", response_model=OrderItem)
def add_item_to_order(order_id: int, item_request: OrderItemRequest):
    """Add a new item to a specific order (enhanced relationship endpoint)"""
    try:
        # Verify the order exists
        if not db.get_order(order_id):
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Create OrderItem from simplified request
        order_item = OrderItem(
            order_id=order_id,
            product_id=item_request.product_id,
            quantity=item_request.quantity,
            unit_price=item_request.unit_price
        )
        return db.create_order_item(order_item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add item to order: {str(e)}")

@app.put("/orders/{order_id}/items/{order_item_id}", response_model=OrderItem)
def update_order_item_in_order(order_id: int, order_item_id: int, item_request: OrderItemRequest):
    """Update a specific item within a specific order"""
    # Verify the order exists
    if not db.get_order(order_id):
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Verify the item exists and belongs to the order
    existing_item = db.get_order_item(order_item_id)
    if not existing_item or existing_item.order_id != order_id:
        raise HTTPException(status_code=404, detail="Order item not found in this order")
    
    # Create OrderItem from simplified request
    order_item = OrderItem(
        order_id=order_id,
        product_id=item_request.product_id,
        quantity=item_request.quantity,
        unit_price=item_request.unit_price
    )
    updated_item = db.update_order_item(order_item_id, order_item)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Failed to update order item")
    return updated_item

@app.delete("/orders/{order_id}/items/{order_item_id}")
def delete_item_from_order(order_id: int, order_item_id: int):
    """Delete a specific item from a specific order"""
    # Verify the order exists
    if not db.get_order(order_id):
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Verify the item exists and belongs to the order
    existing_item = db.get_order_item(order_item_id)
    if not existing_item or existing_item.order_id != order_id:
        raise HTTPException(status_code=404, detail="Order item not found in this order")
    
    if not db.delete_order_item(order_item_id):
        raise HTTPException(status_code=404, detail="Failed to delete order item")
    return {"message": "Order item deleted successfully"}

@app.get("/orders/{order_id}/summary")
def get_order_summary(order_id: int):
    """Get a complete order summary with items and calculations"""
    order = db.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    items = db.get_order_items_by_order(order_id)
    
    summary = {
        "order": order.model_dump(),
        "items": [item.model_dump() for item in items],
        "summary": {
            "total_items": len(items),
            "total_quantity": sum(item.quantity for item in items),
            "total_amount": order.total_amount,
            "item_count_by_product": {}
        }
    }
    
    # Group items by product
    for item in items:
        product_id = str(item.product_id)
        if product_id in summary["summary"]["item_count_by_product"]:
            summary["summary"]["item_count_by_product"][product_id]["quantity"] += item.quantity
            summary["summary"]["item_count_by_product"][product_id]["total"] += item.line_total
        else:
            summary["summary"]["item_count_by_product"][product_id] = {
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total": item.line_total
            }
    
    return summary

# Data Export/Import Endpoints (Phase 2)
@app.get("/export/orders/json")
def export_orders_json():
    """Export all orders and their items to JSON format"""
    orders = db.get_all_orders()
    export_data = []
    
    for order in orders:
        items = db.get_order_items_by_order(order.order_id or 0)
        order_data = {
            "order": order.model_dump(),
            "items": [item.model_dump() for item in items]
        }
        export_data.append(order_data)
    
    return {
        "export_date": date.today().isoformat(),
        "total_orders": len(export_data),
        "data": export_data
    }

@app.get("/export/orders/sql")
def export_orders_sql():
    """Export all orders and their items as SQL INSERT statements"""
    orders = db.get_all_orders()
    sql_statements = []
    
    # Add table creation statements
    sql_statements.extend([
        "-- Orders and Order Items Export",
        "-- Generated on " + date.today().isoformat(),
        "",
        "CREATE TABLE IF NOT EXISTS orders (",
        "    order_id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    customer_id INTEGER NOT NULL,",
        "    order_date DATE NOT NULL,",
        "    total_amount DECIMAL(10, 2) DEFAULT 0.00",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS order_items (",
        "    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    order_id INTEGER NOT NULL,",
        "    product_id INTEGER NOT NULL,",
        "    quantity INTEGER NOT NULL,",
        "    unit_price DECIMAL(10, 2) NOT NULL,",
        "    line_total DECIMAL(10, 2) NOT NULL,",
        "    FOREIGN KEY (order_id) REFERENCES orders(order_id)",
        ");",
        "",
        "-- Data Inserts",
        ""
    ])
    
    for order in orders:
        # Order insert
        sql_statements.append(
            f"INSERT INTO orders (order_id, customer_id, order_date, total_amount) "
            f"VALUES ({order.order_id}, {order.customer_id}, '{order.order_date}', {order.total_amount});"
        )
        
        # Order items inserts
        items = db.get_order_items_by_order(order.order_id or 0)
        for item in items:
            sql_statements.append(
                f"INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, line_total) "
                f"VALUES ({item.order_item_id}, {item.order_id}, {item.product_id}, {item.quantity}, {item.unit_price}, {item.line_total});"
            )
        
        sql_statements.append("")  # Empty line between orders
    
    return {
        "export_date": date.today().isoformat(),
        "sql_statements": sql_statements,
        "sql_content": "\n".join(sql_statements)
    }

@app.post("/import/orders/json")
def import_orders_json(import_data: dict):
    """Import orders and their items from JSON format"""
    try:
        if "data" not in import_data:
            raise HTTPException(status_code=400, detail="Invalid import format: missing 'data' field")
        
        imported_orders = 0
        imported_items = 0
        
        for order_data in import_data["data"]:
            if "order" not in order_data or "items" not in order_data:
                continue
            
            # Create order (without order_id to let it auto-generate)
            order_info = order_data["order"]
            new_order = Order(
                customer_id=order_info["customer_id"],
                order_date=order_info["order_date"],
                total_amount=0.0  # Will be recalculated
            )
            created_order = db.create_order(new_order)
            imported_orders += 1
            
            # Create order items
            # Create order items
            for item_info in order_data["items"]:
                new_item = OrderItem(
                    order_id=created_order.order_id or 0,
                    product_id=item_info["product_id"],
                    quantity=item_info["quantity"],
                    unit_price=item_info["unit_price"]
                )
                db.create_order_item(new_item)
                imported_items += 1
        
        return {
            "message": "Import completed successfully",
            "imported_orders": imported_orders,
            "imported_items": imported_items
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

@app.get("/stats")
def get_database_stats():
    """Get database statistics and summary information"""
    orders = db.get_all_orders()
    all_items = db.get_all_order_items()
    
    if not orders:
        return {
            "total_orders": 0,
            "total_items": 0,
            "total_revenue": 0.0,
            "average_order_value": 0.0,
            "customers": [],
            "products": []
        }
    
    # Calculate statistics
    total_revenue = sum((order.total_amount or 0.0) for order in orders)
    customer_ids = list(set(order.customer_id for order in orders))
    product_ids = list(set(item.product_id for item in all_items))
    
    # Product statistics
    product_stats = {}
    for item in all_items:
        product_key = str(item.product_id)
        if product_key not in product_stats:
            product_stats[product_key] = {"quantity": 0, "revenue": 0.0}
        product_stats[product_key]["quantity"] += item.quantity
        product_stats[product_key]["revenue"] += item.line_total or 0.0
    
    return {
        "total_orders": len(orders),
        "total_items": len(all_items),
        "total_revenue": total_revenue,
        "average_order_value": total_revenue / len(orders) if orders else 0.0,
        "unique_customers": len(customer_ids),
        "unique_products": len(product_ids),
        "customer_ids": sorted(customer_ids),
        "product_stats": product_stats,
        "date_range": {
            "earliest_order": min(order.order_date for order in orders).isoformat(),
            "latest_order": max(order.order_date for order in orders).isoformat()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)