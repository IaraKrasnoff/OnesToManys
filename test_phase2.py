"""
Enhanced test suite for Phase 2 functionality
Tests the new relationship endpoints and data management features
"""

import pytest
import json
import os
from fastapi.testclient import TestClient
from main import app
from database import OrderDatabase
from datetime import date

client = TestClient(app)

@pytest.fixture
def test_db():
    """Create a test database that gets cleaned up after each test"""
    test_db_path = "test_orders_phase2.db"
    db = OrderDatabase(test_db_path)
    yield db
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

def test_enhanced_relationship_endpoints():
    """Test the enhanced master-detail relationship endpoints"""
    # Create an order first
    order_data = {
        "customer_id": 1001,
        "order_date": "2025-08-14",
        "total_amount": 0.0
    }
    
    order_response = client.post("/orders/", json=order_data)
    assert order_response.status_code == 200
    order_id = order_response.json()["order_id"]
    
    # Test adding item to specific order via relationship endpoint
    item_data = {
        "product_id": 2001,
        "quantity": 3,
        "unit_price": 15.99
    }
    
    response = client.post(f"/orders/{order_id}/items", json=item_data)
    assert response.status_code == 200
    created_item = response.json()
    assert created_item["order_id"] == order_id
    assert created_item["product_id"] == 2001
    assert created_item["line_total"] == 47.97  # 3 * 15.99

def test_order_summary_endpoint():
    """Test the comprehensive order summary endpoint"""
    # Create order with multiple items
    order_data = {
        "customer_id": 2001,
        "order_date": "2025-08-14",
        "total_amount": 0.0
    }
    
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["order_id"]
    
    # Add multiple items
    items = [
        {"product_id": 101, "quantity": 2, "unit_price": 10.00},
        {"product_id": 102, "quantity": 1, "unit_price": 25.50},
        {"product_id": 101, "quantity": 3, "unit_price": 10.00}  # Same product, different line
    ]
    
    for item in items:
        client.post(f"/orders/{order_id}/items", json=item)
    
    # Get order summary
    response = client.get(f"/orders/{order_id}/summary")
    assert response.status_code == 200
    
    summary = response.json()
    assert "order" in summary
    assert "items" in summary
    assert "summary" in summary
    
    # Check summary calculations
    assert summary["summary"]["total_items"] == 3
    assert summary["summary"]["total_quantity"] == 6  # 2 + 1 + 3
    
    # Check product grouping
    product_stats = summary["summary"]["item_count_by_product"]
    assert "101" in product_stats
    assert "102" in product_stats
    assert product_stats["101"]["quantity"] == 5  # 2 + 3
    assert product_stats["102"]["quantity"] == 1

def test_nested_order_item_operations():
    """Test updating and deleting items within specific orders"""
    # Create order and item
    order_data = {"customer_id": 3001, "order_date": "2025-08-14", "total_amount": 0.0}
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["order_id"]
    
    item_data = {"product_id": 301, "quantity": 2, "unit_price": 12.50}
    item_response = client.post(f"/orders/{order_id}/items", json=item_data)
    item_id = item_response.json()["order_item_id"]
    
    # Test updating item within order context
    updated_item_data = {"product_id": 302, "quantity": 4, "unit_price": 8.75}
    update_response = client.put(f"/orders/{order_id}/items/{item_id}", json=updated_item_data)
    assert update_response.status_code == 200
    
    updated_item = update_response.json()
    assert updated_item["product_id"] == 302
    assert updated_item["quantity"] == 4
    assert updated_item["line_total"] == 35.0
    
    # Test deleting item within order context
    delete_response = client.delete(f"/orders/{order_id}/items/{item_id}")
    assert delete_response.status_code == 200
    
    # Verify item is gone
    get_response = client.get(f"/order-items/{item_id}")
    assert get_response.status_code == 404

def test_json_export_endpoint():
    """Test JSON data export functionality"""
    # Create some test data
    order_data = {"customer_id": 4001, "order_date": "2025-08-14", "total_amount": 0.0}
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["order_id"]
    
    item_data = {"product_id": 401, "quantity": 2, "unit_price": 20.00}
    client.post(f"/orders/{order_id}/items", json=item_data)
    
    # Test export
    response = client.get("/export/orders/json")
    assert response.status_code == 200
    
    export_data = response.json()
    assert "export_date" in export_data
    assert "total_orders" in export_data
    assert "data" in export_data
    assert export_data["total_orders"] >= 1
    
    # Check data structure
    first_order = export_data["data"][0]
    assert "order" in first_order
    assert "items" in first_order

def test_sql_export_endpoint():
    """Test SQL data export functionality"""
    response = client.get("/export/orders/sql")
    assert response.status_code == 200
    
    export_data = response.json()
    assert "export_date" in export_data
    assert "sql_statements" in export_data
    assert "sql_content" in export_data
    
    # Check that SQL content contains expected elements
    sql_content = export_data["sql_content"]
    assert "CREATE TABLE" in sql_content
    assert "INSERT INTO orders" in sql_content

def test_json_import_endpoint():
    """Test JSON data import functionality"""
    # Prepare import data
    import_data = {
        "data": [
            {
                "order": {
                    "customer_id": 5001,
                    "order_date": "2025-08-14",
                    "total_amount": 45.99
                },
                "items": [
                    {
                        "product_id": 501,
                        "quantity": 2,
                        "unit_price": 22.99
                    }
                ]
            }
        ]
    }
    
    response = client.post("/import/orders/json", json=import_data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["imported_orders"] == 1
    assert result["imported_items"] == 1
    
    # Verify the data was actually imported
    orders_response = client.get("/orders/")
    orders = orders_response.json()
    
    # Find our imported order
    imported_order = None
    for order in orders:
        if order["customer_id"] == 5001:
            imported_order = order
            break
    
    assert imported_order is not None
    
    # Check that items were imported
    items_response = client.get(f"/orders/{imported_order['order_id']}/items")
    items = items_response.json()
    assert len(items) == 1
    assert items[0]["product_id"] == 501

def test_database_stats_endpoint():
    """Test the database statistics endpoint"""
    # Create some test data
    order_data1 = {"customer_id": 6001, "order_date": "2025-08-14", "total_amount": 0.0}
    order_data2 = {"customer_id": 6002, "order_date": "2025-08-15", "total_amount": 0.0}
    
    order1 = client.post("/orders/", json=order_data1).json()
    order2 = client.post("/orders/", json=order_data2).json()
    
    # Add items
    client.post(f"/orders/{order1['order_id']}/items", json={"product_id": 601, "quantity": 2, "unit_price": 15.00})
    client.post(f"/orders/{order2['order_id']}/items", json={"product_id": 602, "quantity": 1, "unit_price": 25.00})
    
    # Get stats
    response = client.get("/stats")
    assert response.status_code == 200
    
    stats = response.json()
    assert "total_orders" in stats
    assert "total_items" in stats
    assert "total_revenue" in stats
    assert "unique_customers" in stats
    assert "unique_products" in stats
    assert "product_stats" in stats
    assert "date_range" in stats
    
    # Check some values
    assert stats["total_orders"] >= 2
    assert stats["unique_customers"] >= 2
    assert "601" in stats["product_stats"]
    assert "602" in stats["product_stats"]

def test_error_handling_relationship_endpoints():
    """Test error handling for relationship endpoints"""
    # Test adding item to non-existent order
    item_data = {"product_id": 999, "quantity": 1, "unit_price": 10.00}
    response = client.post("/orders/99999/items", json=item_data)
    assert response.status_code == 404
    assert "Order not found" in response.json()["detail"]
    
    # Test updating item in wrong order
    order_data = {"customer_id": 7001, "order_date": "2025-08-14", "total_amount": 0.0}
    order1 = client.post("/orders/", json=order_data).json()
    order2 = client.post("/orders/", json=order_data).json()
    
    item_response = client.post(f"/orders/{order1['order_id']}/items", json=item_data)
    item_id = item_response.json()["order_item_id"]
    
    # Try to update the item through the wrong order
    update_response = client.put(f"/orders/{order2['order_id']}/items/{item_id}", json=item_data)
    assert update_response.status_code == 404
    assert "Order item not found in this order" in update_response.json()["detail"]

def test_invalid_import_data():
    """Test import with invalid data structures"""
    # Test with missing data field
    invalid_data = {"invalid": "structure"}
    response = client.post("/import/orders/json", json=invalid_data)
    assert response.status_code == 400
    assert "missing 'data' field" in response.json()["detail"]
    
    # Test with malformed order data
    invalid_data = {
        "data": [
            {"invalid": "order_structure"}
        ]
    }
    response = client.post("/import/orders/json", json=invalid_data)
    assert response.status_code == 200  # Should complete but skip invalid entries
    result = response.json()
    assert result["imported_orders"] == 0

if __name__ == "__main__":
    pytest.main(["-v", __file__])
