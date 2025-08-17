"""
Sample data generator for the Orders API
Run this script to populate your database with test data
"""

from database import OrderDatabase, Order, OrderItem
from datetime import date

def populate_sample_data():
    """Populate the database with sample orders and order items"""
    db = OrderDatabase()
    
    print("Creating sample orders...")
    
    # Create sample orders (3 orders)
    orders_data = [
        Order(customer_id=101, order_date=date(2025, 8, 15), total_amount=0.0),
        Order(customer_id=102, order_date=date(2025, 8, 16), total_amount=0.0),
        Order(customer_id=103, order_date=date(2025, 8, 17), total_amount=0.0),
    ]
    
    created_orders = []
    for order in orders_data:
        created_order = db.create_order(order)
        created_orders.append(created_order)
        print(f"Created order {created_order.order_id} for customer {created_order.customer_id}")
    
    print("\nCreating sample order items...")
    
    # Create sample order items (3 items per order = 9 total items)
    order_items_data = [
        # Order 1 items (3 items)
        OrderItem(order_id=created_orders[0].order_id, product_id=501, quantity=2, unit_price=15.99),
        OrderItem(order_id=created_orders[0].order_id, product_id=502, quantity=1, unit_price=25.50),
        OrderItem(order_id=created_orders[0].order_id, product_id=503, quantity=3, unit_price=9.33),
        
        # Order 2 items (3 items)
        OrderItem(order_id=created_orders[1].order_id, product_id=504, quantity=1, unit_price=49.99),
        OrderItem(order_id=created_orders[1].order_id, product_id=505, quantity=2, unit_price=22.75),
        OrderItem(order_id=created_orders[1].order_id, product_id=506, quantity=4, unit_price=11.75),
        
        # Order 3 items (3 items)
        OrderItem(order_id=created_orders[2].order_id, product_id=507, quantity=1, unit_price=35.00),
        OrderItem(order_id=created_orders[2].order_id, product_id=508, quantity=3, unit_price=12.50),
        OrderItem(order_id=created_orders[2].order_id, product_id=509, quantity=2, unit_price=12.38),
    ]
    
    for item in order_items_data:
        created_item = db.create_order_item(item)
        print(f"Created order item {created_item.order_item_id}: "
              f"Product {created_item.product_id} (qty: {created_item.quantity}, "
              f"price: ${created_item.unit_price}, total: ${created_item.line_total})")
    
    print("\nSample data created successfully!")
    print("\nSummary:")
    
    # Display final order totals
    for order in created_orders:
        updated_order = db.get_order(order.order_id)
        if updated_order:
            items = db.get_order_items_by_order(order.order_id)
            print(f"Order {updated_order.order_id}: Customer {updated_order.customer_id}, "
                  f"Total: ${updated_order.total_amount:.2f}, Items: {len(items)}")

if __name__ == "__main__":
    populate_sample_data()
