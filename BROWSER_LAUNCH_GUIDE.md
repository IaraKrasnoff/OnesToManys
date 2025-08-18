# OnesToManys - Browser Launch Guide

## Prerequisites
Make sure you have both servers running:

### 1. Start the FastAPI Backend Server
```bash
# In the project root directory
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
**Backend will be available at:** http://localhost:8000

### 2. Start the Frontend HTTP Server
```bash
# In the project root directory
cd frontend && python -m http.server 3000
```
**Frontend will be available at:** http://localhost:3000

## Access URLs in Google Chrome

### Frontend Applications:
- **React Application**: http://localhost:3000/react/
- **Vanilla JS Application**: http://localhost:3000/vanilla/

### API & Documentation:
- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000
- **API Health Check**: http://localhost:8000/

## What You'll See:

### React Application Features:
- Modern, responsive interface
- Complete CRUD operations for Orders and Order Items
- Real-time data updates
- Master-detail relationship management
- Order summary with calculations

### Vanilla JavaScript Application Features:
- Clean, tabbed interface
- Full CRUD functionality
- Analytics dashboard
- Data management tools
- Export/Import capabilities

### FastAPI Documentation:
- Interactive API testing interface
- Complete endpoint documentation
- Try-it-out functionality for all endpoints

## Troubleshooting:

### If React App Shows Blank:
1. Check browser console for JavaScript errors (F12 → Console)
2. Verify the FastAPI server is running on port 8000
3. Make sure you're accessing via `http://localhost:3000/react/` (not `file://`)

### If API Calls Fail:
1. Ensure FastAPI server is running: `curl http://localhost:8000/orders/`
2. Check CORS configuration (should be already configured)
3. Verify database has data: `http://localhost:8000/orders/`

## Quick Test Sequence:
1. Open http://localhost:8000/docs - Should show FastAPI documentation
2. Open http://localhost:3000/react/ - Should show React application
3. Open http://localhost:3000/vanilla/ - Should show Vanilla JS application
4. Test API in browser: http://localhost:8000/orders/ - Should return JSON data

## Enjoy exploring your OnesToManys project!
