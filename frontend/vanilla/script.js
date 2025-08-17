// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Global state
let currentOrderId = null;
let currentItemId = null;
let isEditMode = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    const orderDateInput = document.getElementById('orderDate');
    if (orderDateInput) {
        orderDateInput.value = today;
    }

    // Load initial data
    loadDashboardStats();
    loadOrders();
    loadItems();

    // Setup form event listeners
    setupFormListeners();
});

// Tab Management
function showTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(tab => tab.classList.remove('active'));

    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => button.classList.remove('active'));

    // Show selected tab content
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Add active class to clicked button
    event.target.classList.add('active');

    // Load data based on selected tab
    switch(tabName) {
        case 'orders':
            loadOrders();
            break;
        case 'items':
            loadItems();
            break;
        case 'analytics':
            refreshAnalytics();
            break;
    }
}

// API Helper Functions
async function apiCall(endpoint, options = {}) {
    showLoading(true);
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message, 'error');
        throw error;
    } finally {
        showLoading(false);
    }
}

// Dashboard Statistics
async function loadDashboardStats() {
    try {
        const stats = await apiCall('/stats');
        
        document.getElementById('totalOrders').textContent = stats.total_orders;
        document.getElementById('totalRevenue').textContent = `$${stats.total_revenue.toFixed(2)}`;
        document.getElementById('totalCustomers').textContent = stats.unique_customers;
    } catch (error) {
        console.error('Failed to load dashboard stats:', error);
    }
}

// Orders Management
async function loadOrders() {
    try {
        const orders = await apiCall('/orders/');
        const tbody = document.getElementById('ordersTableBody');
        
        tbody.innerHTML = orders.map(order => `
            <tr>
                <td>#${order.order_id}</td>
                <td>${order.customer_id}</td>
                <td>${formatDate(order.order_date)}</td>
                <td>$${order.total_amount.toFixed(2)}</td>
                <td class="action-buttons">
                    <button class="btn btn-sm btn-primary" onclick="viewOrder(${order.order_id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-sm btn-warning" onclick="editOrder(${order.order_id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteOrder(${order.order_id})">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load orders:', error);
    }
}

async function viewOrder(orderId) {
    try {
        const order = await apiCall(`/orders/${orderId}/`);
        const summary = await apiCall(`/orders/${orderId}/summary/`);
        
        // Populate order form with view data
        document.getElementById('customerId').value = order.customer_id;
        document.getElementById('orderDate').value = order.order_date;
        
        // Show order items
        await loadOrderItems(orderId);
        
        // Update modal title and show
        document.getElementById('orderModalTitle').textContent = `Order #${orderId} Details`;
        document.getElementById('orderItemsSection').style.display = 'block';
        
        // Disable form for view-only
        const form = document.getElementById('orderForm');
        const inputs = form.querySelectorAll('input');
        inputs.forEach(input => input.disabled = true);
        
        currentOrderId = orderId;
        isEditMode = false;
        document.getElementById('orderModal').style.display = 'block';
    } catch (error) {
        console.error('Failed to view order:', error);
    }
}

async function editOrder(orderId) {
    try {
        const order = await apiCall(`/orders/${orderId}/`);
        
        // Populate form
        document.getElementById('customerId').value = order.customer_id;
        document.getElementById('orderDate').value = order.order_date;
        
        // Load order items
        await loadOrderItems(orderId);
        
        // Update modal title
        document.getElementById('orderModalTitle').textContent = `Edit Order #${orderId}`;
        document.getElementById('orderItemsSection').style.display = 'block';
        
        // Enable form for editing
        const form = document.getElementById('orderForm');
        const inputs = form.querySelectorAll('input');
        inputs.forEach(input => input.disabled = false);
        
        currentOrderId = orderId;
        isEditMode = true;
        document.getElementById('orderModal').style.display = 'block';
    } catch (error) {
        console.error('Failed to edit order:', error);
    }
}

async function deleteOrder(orderId) {
    if (confirm(`Are you sure you want to delete Order #${orderId}? This action cannot be undone.`)) {
        try {
            await apiCall(`/orders/${orderId}/`, { method: 'DELETE' });
            showToast('Order deleted successfully!');
            loadOrders();
            loadDashboardStats();
        } catch (error) {
            console.error('Failed to delete order:', error);
        }
    }
}

async function loadOrderItems(orderId) {
    try {
        const items = await apiCall(`/orders/${orderId}/items/`);
        const container = document.getElementById('orderItemsList');
        
        if (items.length === 0) {
            container.innerHTML = '<div class="order-item">No items in this order</div>';
            return;
        }
        
        container.innerHTML = items.map(item => `
            <div class="order-item">
                <div class="item-info">
                    <strong>Product #${item.product_id}</strong> - 
                    Qty: ${item.quantity} × $${item.unit_price.toFixed(2)} = 
                    <strong>$${item.line_total.toFixed(2)}</strong>
                </div>
                <div class="item-actions">
                    <button class="btn btn-sm btn-warning" onclick="editOrderItem(${orderId}, ${item.order_item_id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteOrderItem(${orderId}, ${item.order_item_id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load order items:', error);
    }
}

// Order Items Management
async function loadItems() {
    try {
        const items = await apiCall('/order-items/');
        const tbody = document.getElementById('itemsTableBody');
        
        tbody.innerHTML = items.map(item => `
            <tr>
                <td>#${item.order_item_id}</td>
                <td>#${item.order_id}</td>
                <td>#${item.product_id}</td>
                <td>${item.quantity}</td>
                <td>$${item.unit_price.toFixed(2)}</td>
                <td>$${item.line_total.toFixed(2)}</td>
                <td class="action-buttons">
                    <button class="btn btn-sm btn-warning" onclick="editItem(${item.order_item_id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteItem(${item.order_item_id})">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load items:', error);
    }
}

async function editItem(itemId) {
    try {
        const item = await apiCall(`/order-items/${itemId}`);
        
        // Populate form
        document.getElementById('itemOrderId').value = item.order_id;
        document.getElementById('productId').value = item.product_id;
        document.getElementById('quantity').value = item.quantity;
        document.getElementById('unitPrice').value = item.unit_price;
        
        // Update modal title
        document.getElementById('itemModalTitle').textContent = `Edit Item #${itemId}`;
        
        currentItemId = itemId;
        isEditMode = true;
        document.getElementById('itemModal').style.display = 'block';
    } catch (error) {
        console.error('Failed to edit item:', error);
    }
}

async function deleteItem(itemId) {
    if (confirm(`Are you sure you want to delete Item #${itemId}?`)) {
        try {
            await apiCall(`/order-items/${itemId}`, { method: 'DELETE' });
            showToast('Item deleted successfully!');
            loadItems();
            loadDashboardStats();
        } catch (error) {
            console.error('Failed to delete item:', error);
        }
    }
}

async function deleteOrderItem(orderId, itemId) {
    if (confirm('Are you sure you want to delete this item?')) {
        try {
            await apiCall(`/orders/${orderId}/items/${itemId}/`, { method: 'DELETE' });
            showToast('Item deleted successfully!');
            loadOrderItems(orderId);
            loadOrders();
            loadDashboardStats();
        } catch (error) {
            console.error('Failed to delete order item:', error);
        }
    }
}

async function editOrderItem(orderId, itemId) {
    try {
        const item = await apiCall(`/order-items/${itemId}`);
        
        // Populate add item form
        document.getElementById('newProductId').value = item.product_id;
        document.getElementById('newQuantity').value = item.quantity;
        document.getElementById('newUnitPrice').value = item.unit_price;
        
        currentOrderId = orderId;
        currentItemId = itemId;
        document.getElementById('addItemToOrderModal').style.display = 'block';
    } catch (error) {
        console.error('Failed to edit order item:', error);
    }
}

// Analytics
async function refreshAnalytics() {
    try {
        const stats = await apiCall('/stats');
        
        // Update product statistics
        const productStatsContainer = document.getElementById('productStats');
        productStatsContainer.innerHTML = Object.entries(stats.product_stats)
            .sort(([,a], [,b]) => b.revenue - a.revenue)
            .slice(0, 10) // Show top 10 products
            .map(([productId, data]) => `
                <div class="stat-row">
                    <div>
                        <div class="stat-product">Product #${productId}</div>
                        <div class="stat-details">Qty: ${data.quantity}</div>
                    </div>
                    <div class="stat-value">$${data.revenue.toFixed(2)}</div>
                </div>
            `).join('');
        
        // Update date range
        const dateRangeContainer = document.getElementById('dateRange');
        dateRangeContainer.innerHTML = `
            <p><strong>Earliest Order:</strong> ${formatDate(stats.date_range.earliest_order)}</p>
            <p><strong>Latest Order:</strong> ${formatDate(stats.date_range.latest_order)}</p>
            <p><strong>Date Span:</strong> ${calculateDateSpan(stats.date_range.earliest_order, stats.date_range.latest_order)} days</p>
        `;
        
        // Update customer analysis
        const customerAnalysisContainer = document.getElementById('customerAnalysis');
        customerAnalysisContainer.innerHTML = `
            <div class="customer-grid">
                ${stats.customer_ids.slice(0, 20).map(customerId => `
                    <div class="customer-card">
                        <strong>Customer #${customerId}</strong>
                    </div>
                `).join('')}
                ${stats.customer_ids.length > 20 ? `
                    <div class="customer-card" style="border-left-color: #6c757d;">
                        <strong>+${stats.customer_ids.length - 20} more</strong>
                    </div>
                ` : ''}
            </div>
        `;
        
    } catch (error) {
        console.error('Failed to refresh analytics:', error);
    }
}

// Data Management
async function exportData(format) {
    try {
        const data = await apiCall(`/export/orders/${format}`);
        
        let content, filename, mimeType;
        
        if (format === 'json') {
            content = JSON.stringify(data, null, 2);
            filename = `orders_export_${new Date().toISOString().split('T')[0]}.json`;
            mimeType = 'application/json';
        } else if (format === 'sql') {
            content = data.sql_content;
            filename = `orders_export_${new Date().toISOString().split('T')[0]}.sql`;
            mimeType = 'text/sql';
        }
        
        // Create and trigger download
        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast(`${format.toUpperCase()} export completed successfully!`);
    } catch (error) {
        console.error('Failed to export data:', error);
    }
}

async function importData() {
    const fileInput = document.getElementById('importFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('Please select a file to import', 'error');
        return;
    }
    
    try {
        const content = await file.text();
        const data = JSON.parse(content);
        
        const result = await apiCall('/import/orders/json', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        showToast(`Import completed! Orders: ${result.imported_orders}, Items: ${result.imported_items}`);
        
        // Refresh data
        loadOrders();
        loadItems();
        loadDashboardStats();
        
        // Clear file input
        fileInput.value = '';
    } catch (error) {
        console.error('Failed to import data:', error);
        showToast('Failed to import data. Please check the file format.', 'error');
    }
}

// Form Event Listeners
function setupFormListeners() {
    // Order form
    document.getElementById('orderForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            customer_id: parseInt(document.getElementById('customerId').value),
            order_date: document.getElementById('orderDate').value
        };
        
        try {
            if (isEditMode && currentOrderId) {
                await apiCall(`/orders/${currentOrderId}/`, {
                    method: 'PUT',
                    body: JSON.stringify(formData)
                });
                showToast('Order updated successfully!');
            } else {
                await apiCall('/orders/', {
                    method: 'POST',
                    body: JSON.stringify(formData)
                });
                showToast('Order created successfully!');
            }
            
            closeOrderModal();
            loadOrders();
            loadDashboardStats();
        } catch (error) {
            console.error('Failed to save order:', error);
        }
    });
    
    // Item form
    document.getElementById('itemForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            order_id: parseInt(document.getElementById('itemOrderId').value),
            product_id: parseInt(document.getElementById('productId').value),
            quantity: parseInt(document.getElementById('quantity').value),
            unit_price: parseFloat(document.getElementById('unitPrice').value)
        };
        
        try {
            if (isEditMode && currentItemId) {
                await apiCall(`/order-items/${currentItemId}`, {
                    method: 'PUT',
                    body: JSON.stringify(formData)
                });
                showToast('Item updated successfully!');
            } else {
                await apiCall('/order-items/', {
                    method: 'POST',
                    body: JSON.stringify(formData)
                });
                showToast('Item created successfully!');
            }
            
            closeItemModal();
            loadItems();
            loadDashboardStats();
        } catch (error) {
            console.error('Failed to save item:', error);
        }
    });
    
    // Add item to order form
    document.getElementById('addItemToOrderForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            product_id: parseInt(document.getElementById('newProductId').value),
            quantity: parseInt(document.getElementById('newQuantity').value),
            unit_price: parseFloat(document.getElementById('newUnitPrice').value)
        };
        
        try {
            if (currentItemId) {
                // Update existing item
                await apiCall(`/orders/${currentOrderId}/items/${currentItemId}/`, {
                    method: 'PUT',
                    body: JSON.stringify(formData)
                });
                showToast('Item updated successfully!');
            } else {
                // Add new item
                await apiCall(`/orders/${currentOrderId}/items/`, {
                    method: 'POST',
                    body: JSON.stringify(formData)
                });
                showToast('Item added successfully!');
            }
            
            closeAddItemToOrderModal();
            loadOrderItems(currentOrderId);
            loadOrders();
            loadDashboardStats();
        } catch (error) {
            console.error('Failed to save order item:', error);
        }
    });
}

// Modal Management
function showCreateOrderModal() {
    document.getElementById('orderModalTitle').textContent = 'Create New Order';
    document.getElementById('orderItemsSection').style.display = 'none';
    
    // Reset form
    document.getElementById('orderForm').reset();
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('orderDate').value = today;
    
    // Enable all inputs
    const inputs = document.getElementById('orderForm').querySelectorAll('input');
    inputs.forEach(input => input.disabled = false);
    
    currentOrderId = null;
    isEditMode = false;
    document.getElementById('orderModal').style.display = 'block';
}

function closeOrderModal() {
    document.getElementById('orderModal').style.display = 'none';
    document.getElementById('orderForm').reset();
    currentOrderId = null;
    isEditMode = false;
}

function showCreateItemModal() {
    document.getElementById('itemModalTitle').textContent = 'Create New Item';
    document.getElementById('itemForm').reset();
    currentItemId = null;
    isEditMode = false;
    document.getElementById('itemModal').style.display = 'block';
}

function closeItemModal() {
    document.getElementById('itemModal').style.display = 'none';
    document.getElementById('itemForm').reset();
    currentItemId = null;
    isEditMode = false;
}

function showAddItemToOrderModal() {
    document.getElementById('addItemToOrderForm').reset();
    currentItemId = null;
    document.getElementById('addItemToOrderModal').style.display = 'block';
}

function closeAddItemToOrderModal() {
    document.getElementById('addItemToOrderModal').style.display = 'none';
    document.getElementById('addItemToOrderForm').reset();
    currentItemId = null;
}

// Utility Functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function calculateDateSpan(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    spinner.style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    toastMessage.textContent = message;
    toast.className = `toast ${type}`;
    toast.style.display = 'block';
    
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    const orderModal = document.getElementById('orderModal');
    const itemModal = document.getElementById('itemModal');
    const addItemModal = document.getElementById('addItemToOrderModal');
    
    if (event.target === orderModal) {
        closeOrderModal();
    }
    if (event.target === itemModal) {
        closeItemModal();
    }
    if (event.target === addItemModal) {
        closeAddItemToOrderModal();
    }
});

// Handle escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeOrderModal();
        closeItemModal();
        closeAddItemToOrderModal();
    }
});
