# Phase 2 GUI Testing Guide

This guide explains how to test the Phase 2 functionality using GUI-based REST API clients like Postman, Insomnia, or similar tools.

## Setup Instructions

### 1. Start the API Server
```bash
uvicorn main:app --reload
```
The server will be running at `http://localhost:8000`

### 2. Import the Collection

#### For Postman:
1. Open Postman
2. Click "Import" button
3. Select the file `postman_collection.json`
4. The collection "Orders API - Phase 2" will be imported

#### For Insomnia:
1. Open Insomnia
2. Go to Application → Preferences → Data → Import Data
3. Select `postman_collection.json`
4. Choose "Postman Collection" as format

#### For Thunder Client (VS Code):
1. Open VS Code
2. Install Thunder Client extension
3. Open Thunder Client
4. Click "Import" and select `postman_collection.json`

### 3. Environment Variables
Set up these variables in your client:
- `baseUrl`: `http://localhost:8000`
- `order_id`: `1` (will be updated as you create orders)
- `item_id`: `1` (will be updated as you create items)

## Phase 2 Testing Workflow

### Step 1: Basic Setup
1. **Get API Info** - Verify server is running
2. **Get All Orders** - See existing data
3. **Create Order** - Create a new order for testing

### Step 2: Enhanced Relationships Testing
1. **Add Item to Order** - Use the order ID from Step 1
2. **Get Order Items** - Verify the item was added
3. **Update Item in Order** - Modify the item through the order relationship
4. **Get Order Summary** - See the comprehensive order details
5. **Delete Item from Order** - Remove item through order relationship

### Step 3: Data Management Testing
1. **Export to JSON** - Download all data as JSON
2. **Export to SQL** - Get SQL INSERT statements
3. **Import from JSON** - Upload sample data
4. **Get Database Stats** - View analytics

### Step 4: Error Handling Testing
1. **Test Error - Invalid Order** - Try to get non-existent order
2. **Test Error - Add Item to Invalid Order** - Try to add item to non-existent order

## Key Phase 2 Features to Test

### 1. Enhanced One-to-Many Relationships
- **Nested CRUD operations**: `/orders/{id}/items`
- **Relationship integrity**: Items belong to specific orders
- **Automatic calculations**: Order totals update when items change

### 2. Data Export/Import
- **JSON Export**: Complete data structure with relationships
- **SQL Export**: Executable SQL statements
- **JSON Import**: Bulk data loading with validation

### 3. Advanced Analytics
- **Order Summary**: Detailed breakdown with product grouping
- **Database Stats**: Overview of all data with calculations
- **Product Analytics**: Quantity and revenue by product

## Testing Scenarios

### Scenario 1: Complete Order Lifecycle
1. Create a new order
2. Add multiple items with different products
3. Add duplicate products (different line items)
4. Get order summary to see product grouping
5. Update item quantities
6. View updated totals
7. Export the order data

### Scenario 2: Data Migration
1. Export current data to JSON
2. Create new orders and items
3. Export updated data
4. Import the original data to restore previous state

### Scenario 3: Error Handling
1. Try to access non-existent orders/items
2. Try to update items in wrong orders
3. Import invalid JSON structure
4. Verify appropriate error messages

## Expected Results

### Success Responses
- **200 OK**: Successful operations
- **Proper JSON structure**: All responses follow API schema
- **Calculated fields**: Totals, line amounts automatically computed
- **Referential integrity**: Items always linked to valid orders

### Error Responses
- **404 Not Found**: Non-existent resources
- **400 Bad Request**: Invalid data or structure
- **Descriptive error messages**: Clear explanation of what went wrong

## Advanced Testing

### Performance Testing
- Create orders with many items (50-100 items)
- Test bulk import with large JSON files
- Measure response times for summary endpoints

### Data Integrity Testing
- Delete orders and verify cascade deletion of items
- Update order items and verify total recalculation
- Import overlapping data and verify handling

### Relationship Testing
- Access items through both direct endpoints and order relationships
- Verify consistency between `/order-items/{id}` and `/orders/{id}/items`
- Test cross-order item operations (should fail)

## Troubleshooting

### Common Issues
1. **Server not responding**: Check if uvicorn is running on port 8000
2. **404 errors**: Verify order/item IDs exist (check with GET requests)
3. **Validation errors**: Ensure JSON structure matches API schema
4. **Import failures**: Check JSON format and data types

### Debug Tips
1. Use the **Get Database Stats** endpoint to understand current state
2. Check the **Interactive API docs** at `http://localhost:8000/docs`
3. Verify data with **Get All Orders** before complex operations
4. Use **Order Summary** to see complete relationship structure

This comprehensive testing approach will validate all Phase 2 functionality and prepare you for Phase 3 development!
