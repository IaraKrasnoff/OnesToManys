# ====================================================================
# API TESTING SUITE - PHASE 1 TESTS
# These tests verify that all basic CRUD operations work correctly
# ====================================================================

# Import pytest - Python's testing framework
import pytest
# Import OS utilities for file operations (like deleting test databases)
import os
# Import FastAPI's test client for making HTTP requests to our API
from fastapi.testclient import TestClient
# Import our main FastAPI application
from main import app
# Import our database classes
from database import OrderDatabase
# Import date handling
from datetime import date

# Create a test client that can make requests to our API
# This simulates a web browser or frontend application making requests
client = TestClient(app)

@pytest.fixture
def test_db():
    """
    Create a test database that gets cleaned up after each test
    A fixture is a special function that runs before each test to set up test data
    The 'yield' keyword means: run everything before it for setup, 
    then run the test, then run everything after it for cleanup
    """
    test_db_path = "test_orders.db"          # Use a separate database file for testing
    db = OrderDatabase(test_db_path)         # Create a new database instance
    yield db                                 # Provide the database to the test
    # Cleanup code runs after the test finishes
    if os.path.exists(test_db_path):
        os.remove(test_db_path)              # Delete the test database file

# ====================================================================
# BASIC ENDPOINT TESTS
# ====================================================================

def test_root_endpoint():
    """
    Test the welcome/root endpoint (GET /)
    Purpose: Verify that the API server is running and responds correctly
    What it tests: Basic server functionality and welcome message
    """
    # Make a GET request to the root URL
    response = client.get("/")
    
    # Check that the response was successful (HTTP 200 = OK)
    assert response.status_code == 200
    
    # Check that the response contains the expected welcome message
    assert "Welcome to the Orders API!" in response.json()["message"]

# ====================================================================
# ORDER CRUD TESTS (Create, Read, Update, Delete)
# ====================================================================

def test_create_order():
    """
    Test creating a new order (POST /orders/)
    Purpose: Verify that we can successfully create new orders
    What it tests: Order creation, data validation, database insertion
    """
    # Define test data for a new order
    order_data = {
        "customer_id": 101,           # Which customer is placing this order
        "order_date": "2025-08-12",   # When the order was placed
        "total_amount": 0.0           # Initial total (will be calculated later)
    }
    
    # Send a POST request to create the order
    response = client.post("/orders/", json=order_data)
    
    # Verify that the order was created successfully (HTTP 200 = OK)
    assert response.status_code == 200
    
    # Get the created order data from the response
    created_order = response.json()
    
    # Verify that the order data was saved correctly
    assert created_order["customer_id"] == 101
    assert created_order["order_date"] == "2025-08-12"
    assert "order_id" in created_order  # Make sure an ID was assigned

def test_get_order():
    """
    Test retrieving a specific order (GET /orders/{id}/)
    Purpose: Verify that we can fetch individual orders by their ID
    What it tests: Order retrieval, database queries, data serialization
    """
    # Step 1: Create an order to test with
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
    """Test creating a new order item using order-specific endpoint"""
    # First create an order
    order_data = {
        "customer_id": 501,
        "order_date": "2025-08-12",
        "total_amount": 0.0
    }
    
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["order_id"]
    
    # Then create an order item using the order-specific endpoint
    order_item_data = {
        "product_id": 1001,
        "quantity": 2,
        "unit_price": 10.50
    }
    
    response = client.post(f"/orders/{order_id}/items", json=order_item_data)
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
    
    # Create multiple order items using order-specific endpoints
    items = [
        {
            "product_id": 2001,
            "quantity": 1,
            "unit_price": 25.00
        },
        {
            "product_id": 2002,
            "quantity": 3,
            "unit_price": 15.00
        }
    ]
    
    for item in items:
        client.post(f"/orders/{order_id}/items", json=item)
    
    # Get all items for the order
    response = client.get(f"/orders/{order_id}/items")
    assert response.status_code == 200
    
    order_items = response.json()
    assert len(order_items) == 2

def test_update_order_item():
    """Test updating an existing order item using order-specific endpoint"""
    # Create order and order item
    order_data = {
        "customer_id": 701,
        "order_date": "2025-08-12",
        "total_amount": 0.0
    }
    
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["order_id"]
    
    order_item_data = {
        "product_id": 3001,
        "quantity": 1,
        "unit_price": 30.00
    }
    
    item_response = client.post(f"/orders/{order_id}/items", json=order_item_data)
    item_id = item_response.json()["order_item_id"]
    
    # Update the order item using order-specific endpoint
    updated_data = {
        "product_id": 3002,
        "quantity": 2,
        "unit_price": 35.00
    }
    
    response = client.put(f"/orders/{order_id}/items/{item_id}/", json=updated_data)
    assert response.status_code == 200
    
    updated_item = response.json()
    assert updated_item["product_id"] == 3002
    assert updated_item["quantity"] == 2
    assert updated_item["line_total"] == 70.0

def test_delete_order_item():
    """Test deleting an order item using order-specific endpoint"""
    # Create order and order item
    order_data = {
        "customer_id": 801,
        "order_date": "2025-08-12",
        "total_amount": 0.0
    }
    
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["order_id"]
    
    order_item_data = {
        "product_id": 4001,
        "quantity": 1,
        "unit_price": 40.00
    }
    
    item_response = client.post(f"/orders/{order_id}/items", json=order_item_data)
    item_id = item_response.json()["order_item_id"]
    
    # Delete the order item using order-specific endpoint
    response = client.delete(f"/orders/{order_id}/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Order item deleted successfully"
    
    # Verify it's gone - check that the order has no items
    get_response = client.get(f"/orders/{order_id}/items")
    assert get_response.status_code == 200
    assert len(get_response.json()) == 0

def test_get_all_order_items():
    """Test the new /order-items/ endpoint that gets all items from all orders"""
    # Create a couple of orders with items
    order_data_1 = {
        "customer_id": 901,
        "order_date": "2025-08-12",
        "total_amount": 0.0
    }
    
    order_data_2 = {
        "customer_id": 902,
        "order_date": "2025-08-12",
        "total_amount": 0.0
    }
    
    order_response_1 = client.post("/orders/", json=order_data_1)
    order_id_1 = order_response_1.json()["order_id"]
    
    order_response_2 = client.post("/orders/", json=order_data_2)
    order_id_2 = order_response_2.json()["order_id"]
    
    # Add items to both orders
    item_1 = {
        "product_id": 9001,
        "quantity": 1,
        "unit_price": 10.00
    }
    
    item_2 = {
        "product_id": 9002,
        "quantity": 2,
        "unit_price": 20.00
    }
    
    client.post(f"/orders/{order_id_1}/items", json=item_1)
    client.post(f"/orders/{order_id_2}/items", json=item_2)
    
    # Test the new /order-items/ endpoint
    response = client.get("/order-items/")
    assert response.status_code == 200
    
    all_items = response.json()
    # Should have at least the 2 items we just created (plus any existing ones)
    assert len(all_items) >= 2
    
    # Verify the items are in the response
    order_ids = [item["order_id"] for item in all_items]
    assert order_id_1 in order_ids
    assert order_id_2 in order_ids

def test_order_not_found():
    """Test handling of non-existent order"""
    response = client.get("/orders/99999")
    assert response.status_code == 404
    assert "Order not found" in response.json()["detail"]

def test_order_item_with_invalid_order():
    """Test creating order item with non-existent order using order-specific endpoint"""
    order_item_data = {
        "product_id": 5001,
        "quantity": 1,
        "unit_price": 50.00
    }
    
    response = client.post("/orders/99999/items", json=order_item_data)
    assert response.status_code == 404
    assert "Order not found" in response.json()["detail"]

def test_create_order_with_items():
    """Test creating an order with items in a single atomic transaction"""
    order_data = {
        "customer_id": 1001,
        "order_date": "2025-08-12",
        "items": [
            {
                "product_id": 5001,
                "quantity": 2,
                "unit_price": 15.99
            },
            {
                "product_id": 5002,
                "quantity": 1,
                "unit_price": 29.99
            }
        ]
    }
    
    response = client.post("/orders/with-items/", json=order_data)
    assert response.status_code == 200
    
    created_order = response.json()
    assert created_order["customer_id"] == 1001
    assert created_order["order_date"] == "2025-08-12"
    assert created_order["total_amount"] == 61.97  # (2 * 15.99) + (1 * 29.99)
    assert "order_id" in created_order
    
    # Verify items were created
    order_id = created_order["order_id"]
    items_response = client.get(f"/orders/{order_id}/items/")
    assert items_response.status_code == 200
    
    items = items_response.json()
    assert len(items) == 2
    
    # Check first item
    item1 = next(item for item in items if item["product_id"] == 5001)
    assert item1["quantity"] == 2
    assert item1["unit_price"] == 15.99
    assert item1["line_total"] == 31.98
    
    # Check second item
    item2 = next(item for item in items if item["product_id"] == 5002)
    assert item2["quantity"] == 1
    assert item2["unit_price"] == 29.99
    assert item2["line_total"] == 29.99

def test_create_order_with_no_items():
    """Test creating an order with empty items list"""
    order_data = {
        "customer_id": 1002,
        "order_date": "2025-08-12",
        "items": []
    }
    
    response = client.post("/orders/with-items/", json=order_data)
    assert response.status_code == 200
    
    created_order = response.json()
    assert created_order["customer_id"] == 1002
    assert created_order["total_amount"] == 0.0

if __name__ == "__main__":
    pytest.main(["-v", __file__])
