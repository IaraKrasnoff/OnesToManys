# Import FastAPI - the main web framework for building APIs
from fastapi import FastAPI, HTTPException
# Import CORS middleware - allows frontend websites to talk to our API
from fastapi.middleware.cors import CORSMiddleware
# Import typing helpers for better code documentation
from typing import List, Dict, Any
# Import Pydantic for data validation (ensures data is in correct format)
from pydantic import BaseModel
# Import our custom database classes and models
from database import Order, OrderItem, OrderDatabase
# Import date handling for working with dates
from datetime import date, datetime
# Import JSON for data serialization (converting Python objects to JSON)
import json
# Import OS utilities for file operations
import os

# Define a simplified data model for creating order items
# This tells FastAPI what fields are required and their types
class OrderItemRequest(BaseModel):
    """Simplified request model for creating order items"""
    product_id: int      # Which product is being ordered (must be an integer)
    quantity: int        # How many of this product (must be an integer)
    unit_price: float    # Price per item (must be a decimal number)

# Define a data model for creating orders with items in a single transaction
class OrderWithItemsRequest(BaseModel):
    """Request model for creating orders with items atomically"""
    customer_id: int           # Which customer is placing this order
    order_date: str           # When the order was placed (YYYY-MM-DD format)
    items: List[OrderItemRequest] = []  # List of items to add to the order (optional)

# Create the main FastAPI application instance
# This is like creating a new web server that can handle HTTP requests
app = FastAPI(title="Iara's Orders API", description="A master-detail orders management API", version="2.0.0")

# Add CORS middleware to solve browser security restrictions
# CORS = Cross-Origin Resource Sharing - allows websites to make API calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow requests from any website (in production, be more specific)
    allow_credentials=True,     # Allow cookies and authentication headers
    allow_methods=["*"],        # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],        # Allow all HTTP headers
)

# Create a database connection instance
# This object handles all database operations (create, read, update, delete)
db = OrderDatabase()

# Define the root endpoint - this is what users see when they visit the main URL
@app.get("/")
def read_root():
    """Welcome endpoint - provides basic API information"""
    # Return a JSON response with welcome message and available endpoints
    return {"message": "Welcome to the Orders API!", "endpoints": {
        "orders": "/orders/",                         # Endpoint for managing orders
        "orders_with_items": "/orders/with-items/",   # Endpoint for creating orders with items atomically
        "all_order_items": "/order-items/",           # Endpoint for getting all order items
        "order_items": "/orders/{order_id}/items",    # Endpoint for managing items of specific order
        "docs": "/docs"                               # Endpoint for API documentation
    }}

# ORDERS ENDPOINTS - These handle all operations related to orders

# POST endpoint for creating new orders
# The response_model tells FastAPI what format the response should have
@app.post("/orders/", response_model=Order)
def create_order(order: Order):
    """Create a new order in the database"""
    try:
        # Try to create the order using our database class
        return db.create_order(order)
    except Exception as e:
        # If something goes wrong, return a proper HTTP error response
        raise HTTPException(status_code=400, detail=f"Failed to create order: {str(e)}")

# POST endpoint for creating new orders WITH items in a single transaction
# This is more efficient and ensures data consistency
@app.post("/orders/with-items/", response_model=Order)
def create_order_with_items(order_request: OrderWithItemsRequest):
    """Create a new order with items in a single atomic transaction"""
    try:
        # Parse the date string to a date object
        order_date = datetime.strptime(order_request.order_date, "%Y-%m-%d").date()
        
        # Create the basic order first
        order_data = Order(
            customer_id=order_request.customer_id,
            order_date=order_date,
            total_amount=0.0  # Will be calculated from items
        )
        
        # Create the order in the database
        created_order = db.create_order(order_data)
        
        # If items were provided, add them to the order
        if order_request.items and created_order.order_id is not None:
            total_amount = 0.0
            
            for item_request in order_request.items:
                # Calculate line total
                line_total = item_request.quantity * item_request.unit_price
                
                # Create each item
                item_data = OrderItem(
                    order_id=created_order.order_id,
                    product_id=item_request.product_id,
                    quantity=item_request.quantity,
                    unit_price=item_request.unit_price,
                    line_total=line_total
                )
                
                # Add item to database
                db.create_order_item(item_data)
                total_amount += line_total
            
            # Update the order with the calculated total
            created_order.total_amount = total_amount
            updated_order = db.update_order(created_order.order_id, created_order)
            return updated_order if updated_order else created_order
        
        return created_order
        
    except Exception as e:
        # If something goes wrong, return a proper HTTP error response
        raise HTTPException(status_code=400, detail=f"Failed to create order with items: {str(e)}")

# GET endpoint for retrieving all orders
# Returns a list of Order objects
@app.get("/orders/", response_model=List[Order])
def get_all_orders():
    """Get all orders from the database"""
    # Call the database method to fetch all orders
    return db.get_all_orders()

# GET endpoint for retrieving a specific order by its ID
# The {order_id} in the URL is a path parameter - it gets passed to the function
@app.get("/orders/{order_id}/", response_model=Order)
def get_order(order_id: int):
    """Get a specific order by its ID number"""
    # Try to find the order in the database
    order = db.get_order(order_id)
    # If no order is found, return a 404 (Not Found) error
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    # If found, return the order data
    return order

# PUT endpoint for updating an existing order
# PUT is used for updating existing resources
@app.put("/orders/{order_id}/", response_model=Order)
def update_order(order_id: int, order: Order):
    """Update an existing order with new information"""
    # Try to update the order in the database
    updated_order = db.update_order(order_id, order)
    # If the order doesn't exist, return a 404 error
    if updated_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    # If successful, return the updated order data
    return updated_order

# DELETE endpoint for removing an order
# This will also delete all associated order items (cascade delete)
@app.delete("/orders/{order_id}/")
def delete_order(order_id: int):
    """Delete an order and all its associated items"""
    # Try to delete the order from the database
    if not db.delete_order(order_id):
        # If the order doesn't exist, return a 404 error
        raise HTTPException(status_code=404, detail="Order not found")
    # If successful, return a confirmation message
    return {"message": "Order deleted successfully"}

# ORDER ITEM ENDPOINTS - These handle operations on individual items within orders

# GET endpoint to retrieve all items that belong to a specific order
# This demonstrates the "One-to-Many" relationship (one order has many items)
@app.get("/orders/{order_id}/items/", response_model=List[OrderItem])
def get_order_items_by_order(order_id: int):
    """Get all order items for a specific order"""
    # First, verify that the parent order actually exists
    if not db.get_order(order_id):
        raise HTTPException(status_code=404, detail="Order not found")
    # If the order exists, get all its items
    return db.get_order_items_by_order(order_id)

# GET endpoint to retrieve ALL order items across all orders
# This provides a standalone endpoint for accessing order items directly
@app.get("/order-items/", response_model=List[OrderItem])
def get_all_order_items():
    """Get all order items from all orders in the database"""
    # This is useful for getting a comprehensive view of all items
    return db.get_all_order_items()

# ENHANCED MASTER-DETAIL RELATIONSHIP ENDPOINTS (Phase 2 Features)
# These endpoints understand the relationship between orders and items

# POST endpoint to add a new item directly to a specific order
# This is more convenient than creating an item and then linking it to an order
@app.post("/orders/{order_id}/items/", response_model=OrderItem)
def add_item_to_order(order_id: int, item_request: OrderItemRequest):
    """Add a new item to a specific order (enhanced relationship endpoint)"""
    try:
        # Verify that the parent order exists before adding items to it
        if not db.get_order(order_id):
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Create a full OrderItem object from the simplified request
        # The order_id is automatically set from the URL parameter
        order_item = OrderItem(
            order_id=order_id,                    # Link this item to the specified order
            product_id=item_request.product_id,   # What product is being ordered
            quantity=item_request.quantity,       # How many units
            unit_price=item_request.unit_price    # Price per unit
        )
        # Save the new item to the database
        return db.create_order_item(order_item)
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) without modification
        raise
    except Exception as e:
        # Convert any other errors to a 400 Bad Request response
        raise HTTPException(status_code=400, detail=f"Failed to add item to order: {str(e)}")

# PUT endpoint to update an item within the context of a specific order
# This ensures the item actually belongs to the order being modified
@app.put("/orders/{order_id}/items/{order_item_id}/", response_model=OrderItem)
def update_order_item_in_order(order_id: int, order_item_id: int, item_request: OrderItemRequest):
    """Update a specific item within a specific order (maintains relationship context)"""
    # Verify that the parent order exists
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
    
    # Format all revenue values to 2 decimal places
    for product_key in product_stats:
        product_stats[product_key]["revenue"] = round(product_stats[product_key]["revenue"], 2)
    
    return {
        "total_orders": len(orders),
        "total_items": len(all_items),
        "total_revenue": round(total_revenue, 2),
        "average_order_value": round(total_revenue / len(orders), 2) if orders else 0.0,
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