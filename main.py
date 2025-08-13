from fastapi import FastAPI, HTTPException
from typing import List
from database import Order, OrderItem, OrderDatabase
from datetime import date

app = FastAPI(title="Orders API", description="A master-detail orders management API", version="1.0.0")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)