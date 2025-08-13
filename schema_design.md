# Schema Design for Orders API

This document outlines the database schema design for the Orders API project, showing both the current implementation and potential enhancements.

## Current Implementation (Phase 1)

### Orders Table (Master)
```sql
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) DEFAULT 0.00
);
```

### Order Items Table (Detail)
```sql
CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    line_total DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);















```


## Enhanced Schema Design (Future Enhancement)

Based on the requirements provided, here's an enhanced schema that could be implemented in future phases:

### Orders Table (Enhanced)
```sql
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2),
    status TEXT CHECK (status IN ('pending', 'processing', 'shipped', 'delivered')) DEFAULT 'pending',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

### Order Items Table (Enhanced)
```sql
CREATE TABLE order_items (
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(10,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

### Supporting Tables (For Enhanced Version)
```sql
-- Customers table to support the foreign key relationship
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table to support the foreign key relationship
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    description TEXT,
    unit_price DECIMAL(10,2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Key Design Differences

### Current vs Enhanced Implementation

| Feature | Current | Enhanced |
|---------|---------|----------|
| **Order Items PK** | Single auto-increment ID | Composite key (order_id, product_id) |
| **Status Tracking** | Not implemented | Order status with constraints |
| **Timestamps** | Simple DATE | TIMESTAMP with auto-generation |
| **Foreign Keys** | Orders → Order Items only | Full referential integrity |
| **Line Totals** | Calculated in application | Could use generated columns |
| **Cascade Deletes** | Handled in application code | Database-level CASCADE |

## Current Schema Benefits

1. **Simplicity**: Easy to understand and implement
2. **Flexibility**: Allows multiple entries of same product per order
3. **Auto-increment IDs**: Simpler primary key management
4. **Application Control**: Total calculations handled in Python

## Enhanced Schema Benefits

1. **Data Integrity**: Full referential integrity with customers/products
2. **Business Rules**: Status constraints ensure valid order states
3. **Composite Keys**: Prevents duplicate product entries per order
4. **Database-level Logic**: Calculations and constraints at DB level
5. **Audit Trail**: Timestamps for tracking record creation

## Master-Detail Relationship

Both schemas maintain the core one-to-many relationship:
- One **Order** can have many **Order Items**
- Each **Order Item** belongs to exactly one **Order**
- Foreign key `order_id` links the tables

## Implementation Notes

### Current Schema (SQLite)
- Uses INTEGER PRIMARY KEY for auto-increment
- Simple DATE type for order_date
- Manual calculation of totals in Python
- Basic foreign key constraint

### Enhanced Schema Considerations
- Composite primary key requires careful handling in ORMs
- CHECK constraints for status validation
- Generated columns for automatic line_total calculation
- ON DELETE CASCADE for automatic cleanup

## Migration Path

To move from current to enhanced schema:
1. Add status column with default 'pending'
2. Change order_date to TIMESTAMP
3. Create customers and products tables
4. Add foreign key constraints
5. Modify order_items to use composite primary key
6. Add generated column for line_total

## Conclusion

The current schema effectively demonstrates the master-detail relationship for Phase 1 requirements. The enhanced schema shows how the design could evolve to support more complex business requirements while maintaining the core relational structure.
