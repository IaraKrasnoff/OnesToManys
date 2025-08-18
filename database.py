# Import sqlite3 - Python's built-in database library for SQLite databases
import sqlite3
# Import typing helpers for better code documentation and type checking
from typing import Optional, List
# Import Pydantic for data models with automatic validation
from pydantic import BaseModel
# Import OS utilities for file system operations
import os
# Import date and datetime for handling date/time data
from datetime import date, datetime

# Define the Order data model
# This represents a single order in our system
class Order(BaseModel):
    """
    Data model for an Order - the "Master" in our Master-Detail relationship
    An order is placed by a customer and can contain multiple items
    """
    order_id: Optional[int] = None      # Primary key (auto-generated), optional for new orders
    customer_id: int                    # Which customer placed this order (required)
    order_date: date                    # When the order was placed (required)
    total_amount: Optional[float] = 0.0 # Total price of all items (calculated automatically)

# Define the OrderItem data model  
# This represents a single item within an order
class OrderItem(BaseModel):
    """
    Data model for an OrderItem - the "Detail" in our Master-Detail relationship
    Each order item belongs to exactly one order and represents one product in that order
    """
    order_item_id: Optional[int] = None  # Primary key (auto-generated), optional for new items
    order_id: int                        # Foreign key - which order this item belongs to (required)
    product_id: int                      # Which product is being ordered (required)
    quantity: int                        # How many units of this product (required)
    unit_price: float                    # Price per unit (required)
    line_total: Optional[float] = None   # Total for this line item (calculated: quantity × unit_price)

# Database class that handles all data operations
# This is like a "data access layer" that sits between our API and the database
class OrderDatabase:
    """
    Database class that manages all order and order item operations
    Uses SQLite as the database engine (lightweight, file-based database)
    """
    
    def __init__(self, db_path: str = "orders.db"):
        """
        Initialize the database connection and create tables if needed
        Args:
            db_path: Path to the SQLite database file (defaults to 'orders.db')
        """
        self.db_path = db_path  # Store the database file path
        self.init_db()          # Create database tables if they don't exist
    
    def init_db(self):
        """Create the orders and order_items tables if they don't exist"""
        # Use 'with' statement to ensure database connection is properly closed
        with sqlite3.connect(self.db_path) as conn:
            
            # Create the Orders table (Master table)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Auto-incrementing primary key
                    customer_id INTEGER NOT NULL,                -- Customer who placed the order
                    order_date DATE NOT NULL,                    -- When the order was placed
                    total_amount DECIMAL(10, 2) DEFAULT 0.00     -- Total value (up to 10 digits, 2 decimal places)
                )
            """)
            
            # Create the Order Items table (Detail table)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Auto-incrementing primary key
                    order_id INTEGER NOT NULL,                        -- Foreign key to orders table
                    product_id INTEGER NOT NULL,                      -- Which product is being ordered
                    quantity INTEGER NOT NULL,                        -- How many units
                    unit_price DECIMAL(10, 2) NOT NULL,              -- Price per unit
                    line_total DECIMAL(10, 2) NOT NULL,              -- Total for this line (quantity × unit_price)
                    FOREIGN KEY (order_id) REFERENCES orders(order_id)  -- Enforces relationship integrity
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
