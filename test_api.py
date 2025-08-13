import pytest
import os
from fastapi.testclient import TestClient
from main import app
from database import OrderDatabase
from datetime import date

client = TestClient(app)

@pytest.fixture
def test_db():
    """Create a test database that gets cleaned up after each test"""
    test_db_path = "test_orders.db"
    db = OrderDatabase(test_db_path)
    yield db
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

def test_root_endpoint():
    """Test the welcome endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to the Orders API!" in response.json()["message"]

def test_create_order():
    """Test creating a new order"""
    order_data = {
        "customer_id": 101,
        "order_date": "2025-08-12",
        "total_amount": 0.0
    }
    
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 200
    
    created_order = response.json()
    assert created_order["customer_id"] == 101
    assert created_order["order_date"] == "2025-08-12"
    assert "order_id" in created_order

def test_get_order():
    """Test retrieving a specific order"""
    # First create an order
    order_data = {
        "customer_id": 102,
        "order_date": "2025-08-12",
        "total_amount": 50.0
    }
    
    create_response = client.post("/orders/", json=order_data)
    order_id = create_response.json()["order_id"]
    
    # Then retrieve it
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    
    order = response.json()
    assert order["customer_id"] == 102
    assert order["order_id"] == order_id

def test_get_all_orders():
    """Test retrieving all orders"""
    # Create a couple of orders first
    orders = [
        {
            "customer_id": 201,
            "order_date": "2025-08-12",
            "total_amount": 25.0
        },
        {
            "customer_id": 202,
            "order_date": "2025-08-12",
            "total_amount": 75.0
        }
    ]
    
    for order in orders:
        client.post("/orders/", json=order)
    
    response = client.get("/orders/")
    assert response.status_code == 200
    
    all_orders = response.json()
    assert len(all_orders) >= 2

def test_update_order():
    """Test updating an existing order"""
    # Create an order
    order_data = {
        "customer_id": 301,
        "order_date": "2025-08-12",
        "total_amount": 100.0
    }
    
    create_response = client.post("/orders/", json=order_data)
    order_id = create_response.json()["order_id"]
    
    # Update the order
    updated_data = {
        "customer_id": 302,
        "order_date": "2025-08-13",
        "total_amount": 150.0
    }
    
    response = client.put(f"/orders/{order_id}", json=updated_data)
    assert response.status_code == 200
    
    updated_order = response.json()
    assert updated_order["customer_id"] == 302
    assert updated_order["total_amount"] == 150.0

def test_delete_order():
    """Test deleting an order"""
    # Create an order
    order_data = {
        "customer_id": 401,
        "order_date": "2025-08-12",
        "total_amount": 200.0
    }
    
    create_response = client.post("/orders/", json=order_data)
    order_id = create_response.json()["order_id"]
    
    # Delete the order
    response = client.delete(f"/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Order deleted successfully"
    
    # Verify it's gone
    get_response = client.get(f"/orders/{order_id}")
    assert get_response.status_code == 404

def test_create_order_item():
    """Test creating a new order item"""
    # First create an order
    order_data = {
        "customer_id": 501,
        "order_date": "2025-08-12",
        "total_amount": 0.0
    }
    
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["order_id"]
    
    # Then create an order item
    order_item_data = {
        "order_id": order_id,
        "product_id": 1001,
        "quantity": 2,
        "unit_price": 10.50
    }
    
    response = client.post("/order-items/", json=order_item_data)
    assert response.status_code == 200
    
    created_item = response.json()
    assert created_item["order_id"] == order_id
    assert created_item["product_id"] == 1001
    assert created_item["quantity"] == 2
    assert created_item["unit_price"] == 10.50
    assert created_item["line_total"] == 21.0  # 2 * 10.50
    assert "order_item_id" in created_item

def test_get_order_items_by_order():
    """Test retrieving all order items for a specific order"""
    # First create an order
    order_data = {
        "customer_id": 601,
        "order_date": "2025-08-12",
        "total_amount": 0.0
    }
    
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["order_id"]
    
    # Create multiple order items
    items = [
        {
            "order_id": order_id,
            "product_id": 2001,
            "quantity": 1,
            "unit_price": 25.00
        },
        {
            "order_id": order_id,
            "product_id": 2002,
            "quantity": 3,
            "unit_price": 15.00
        }
    ]
    
    for item in items:
        client.post("/order-items/", json=item)
    
    # Get all items for the order
    response = client.get(f"/orders/{order_id}/items")
    assert response.status_code == 200
    
    order_items = response.json()
    assert len(order_items) == 2

def test_update_order_item():
    """Test updating an existing order item"""
    # Create order and order item
    order_data = {
        "customer_id": 701,
        "order_date": "2025-08-12",
        "total_amount": 0.0
    }
    
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["order_id"]
    
    order_item_data = {
        "order_id": order_id,
        "product_id": 3001,
        "quantity": 1,
        "unit_price": 30.00
    }
    
    item_response = client.post("/order-items/", json=order_item_data)
    item_id = item_response.json()["order_item_id"]
    
    # Update the order item
    updated_data = {
        "order_id": order_id,
        "product_id": 3002,
        "quantity": 2,
        "unit_price": 35.00
    }
    
    response = client.put(f"/order-items/{item_id}", json=updated_data)
    assert response.status_code == 200
    
    updated_item = response.json()
    assert updated_item["product_id"] == 3002
    assert updated_item["quantity"] == 2
    assert updated_item["line_total"] == 70.0

def test_delete_order_item():
    """Test deleting an order item"""
    # Create order and order item
    order_data = {
        "customer_id": 801,
        "order_date": "2025-08-12",
        "total_amount": 0.0
    }
    
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["order_id"]
    
    order_item_data = {
        "order_id": order_id,
        "product_id": 4001,
        "quantity": 1,
        "unit_price": 40.00
    }
    
    item_response = client.post("/order-items/", json=order_item_data)
    item_id = item_response.json()["order_item_id"]
    
    # Delete the order item
    response = client.delete(f"/order-items/{item_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Order item deleted successfully"
    
    # Verify it's gone
    get_response = client.get(f"/order-items/{item_id}")
    assert get_response.status_code == 404

def test_order_not_found():
    """Test handling of non-existent order"""
    response = client.get("/orders/99999")
    assert response.status_code == 404
    assert "Order not found" in response.json()["detail"]

def test_order_item_with_invalid_order():
    """Test creating order item with non-existent order"""
    order_item_data = {
        "order_id": 99999,
        "product_id": 5001,
        "quantity": 1,
        "unit_price": 50.00
    }
    
    response = client.post("/order-items/", json=order_item_data)
    assert response.status_code == 404
    assert "Order not found" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main(["-v", __file__])
