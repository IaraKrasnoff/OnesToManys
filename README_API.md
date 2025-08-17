# Orders API - Phase 1 Implementation

A FastAPI-based REST API implementing a master-detail relationship between Orders and Order Items, following the OnesToManys project requirements.

## Project Structure

```
OnesToManys/
├── main.py              # FastAPI application with all endpoints
├── database.py          # Database models and operations (SQLite)
├── test_api.py         # Comprehensive test suite
├── sample_data.py      # Script to populate database with test data
├── requirements.txt    # Python dependencies
├── Order.sql          # Original schema file
├── Order_items.sql    # Original data examples
└── README_API.md      # This file
```

## Master-Detail Relationship

- **Master**: Orders (order_id, customer_id, order_date, total_amount)
- **Detail**: Order Items (order_item_id, order_id, product_id, quantity, unit_price, line_total)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

### 3. View Interactive Documentation

Visit `http://localhost:8000/docs` for FastAPI's automatic interactive API documentation.

### 4. Populate Sample Data (Optional)

```bash
python sample_data.py
```

## API Endpoints

### Orders (Master Table)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders/` | Get all orders |
| GET | `/orders/{order_id}` | Get specific order |
| POST | `/orders/` | Create new order |
| PUT | `/orders/{order_id}` | Update existing order |
| DELETE | `/orders/{order_id}` | Delete order (cascades to items) |


## curl Testing Commands

### Testing Orders (Master Table)

#### 1. Welcome Endpoint
```bash
curl http://localhost:8000/
```

#### 2. Create a New Order
```bash
curl -X POST "http://localhost:8000/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 101,
    "order_date": "2025-08-12",
    "total_amount": 0.0
  }'
```

#### 3. Get All Orders
```bash
curl http://localhost:8000/orders/
```

#### 4. Get Specific Order
```bash
curl http://localhost:8000/orders/1
```

#### 5. Update an Order
```bash
curl -X PUT "http://localhost:8000/orders/1" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 102,
    "order_date": "2025-08-13",
    "total_amount": 75.50
  }'
```

#### 6. Delete an Order
```bash
curl -X DELETE http://localhost:8000/orders/1
```

### Testing Order Items (Detail Table)

#### 1. Create an Order Item
```bash
curl -X POST "http://localhost:8000/order-items/" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "product_id": 501,
    "quantity": 2,
    "unit_price": 10.50
  }'
```

#### 2. Get All Order Items
```bash
curl http://localhost:8000/order-items/
```

#### 3. Get Specific Order Item
```bash
curl http://localhost:8000/order-items/1
```

#### 4. Get All Items for a Specific Order
```bash
curl http://localhost:8000/orders/1/items
```

#### 5. Update an Order Item
```bash
curl -X PUT "http://localhost:8000/order-items/1" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "product_id": 502,
    "quantity": 3,
    "unit_price": 15.75
  }'
```

#### 6. Delete an Order Item
```bash
curl -X DELETE http://localhost:8000/order-items/1
```

## Complete Workflow Example

Here's a complete workflow demonstrating the master-detail relationship:

```bash
# 1. Create an order
ORDER_RESPONSE=$(curl -s -X POST "http://localhost:8000/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 201,
    "order_date": "2025-08-12",
    "total_amount": 0.0
  }')

echo "Created order: $ORDER_RESPONSE"

# Extract order_id (assuming jq is available)
ORDER_ID=$(echo $ORDER_RESPONSE | jq -r '.order_id')

# 2. Add order items to the order
curl -X POST "http://localhost:8000/order-items/" \
  -H "Content-Type: application/json" \
  -d "{
    \"order_id\": $ORDER_ID,
    \"product_id\": 601,
    \"quantity\": 2,
    \"unit_price\": 25.00
  }"

curl -X POST "http://localhost:8000/order-items/" \
  -H "Content-Type: application/json" \
  -d "{
    \"order_id\": $ORDER_ID,
    \"product_id\": 602,
    \"quantity\": 1,
    \"unit_price\": 45.99
  }"

# 3. Get the order with updated total
curl http://localhost:8000/orders/$ORDER_ID

# 4. Get all items for this order
curl http://localhost:8000/orders/$ORDER_ID/items
```

## Running Tests

Run the comprehensive test suite:

```bash
pytest test_api.py -v
```

## Key Features Implemented

### Phase 1 Requirements ✅

- [x] **Database Schema**: SQLite database with Orders and OrderItems tables
- [x] **Master Table CRUD**: Complete CRUD operations for Orders
- [x] **Detail Table CRUD**: Complete CRUD operations for OrderItems
- [x] **Foreign Key Relationships**: OrderItems reference Orders via order_id
- [x] **Automatic Calculations**: Order totals automatically calculated from line items
- [x] **REST API**: Full REST endpoints for both tables
- [x] **curl Testing**: All endpoints testable with curl commands
- [x] **Error Handling**: Proper HTTP status codes and error messages
- [x] **Data Validation**: Pydantic models ensure data integrity

### Additional Features

- **Cascade Deletes**: Deleting an order automatically deletes its items
- **Automatic Totals**: Order totals automatically update when items are added/modified/deleted
- **Interactive Documentation**: FastAPI auto-generates API docs at `/docs`
- **Comprehensive Tests**: Full test suite covering all endpoints and edge cases
- **Sample Data**: Script to populate database with realistic test data

## Database Schema

The SQLite database automatically creates these tables:

```sql
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) DEFAULT 0.00
);

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

## Next Steps (Phase 2)

- Add authentication and authorization
- Implement pagination for large datasets
- Add more advanced querying capabilities
- Set up logging and monitoring
- Deploy to a cloud platform

## Technology Stack

- **Framework**: FastAPI
- **Database**: SQLite
- **Validation**: Pydantic
- **Testing**: pytest + httpx
- **Server**: Uvicorn

This implementation provides a solid foundation for Phase 2 and Phase 3 of the OnesToManys project!
