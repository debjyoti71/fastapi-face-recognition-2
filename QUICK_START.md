# Quick Start Guide

## Fixed Issues
✅ Added missing `__init__.py` files for all packages
✅ Updated requirements.txt with compatible version ranges
✅ Installed all required dependencies including InsightFace
✅ Created test interface (index.html)
✅ Created startup script (start_server.bat)

## How to Run

### 1. Start the Server
```bash
# Option 1: Use the batch script (Windows)
start_server.bat

# Option 2: Manual command
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Access the Application
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Test Interface**: Open `index.html` in your browser

### 3. Test the API
1. Open `index.html` in your browser
2. Set an event name (e.g., "test_event")
3. Add users with face images
4. Verify faces against registered users

## API Endpoints
- `POST /addUser/` - Add user with face image
- `POST /verify/` - Verify face against event users
- `GET /api/events` - Get all events
- `GET /api/all_user?event_name=X` - Get users in event
- `DELETE /api/events/{event_name}` - Delete event

## Environment Variables
Make sure your `.env` file contains:
```
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## Dependencies Installed
- FastAPI, Uvicorn, Python-multipart
- Pillow, NumPy, OpenCV-Python
- InsightFace, ONNX Runtime
- Cloudinary, Requests, Python-dotenv

The application is now ready to use!