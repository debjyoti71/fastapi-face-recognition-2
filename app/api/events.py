from fastapi import APIRouter
import logging
from app.services import event_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/events")
def get_events():
    """Get all events with user counts"""
    logger.info("GET /events endpoint accessed")
    result = event_service.get_all_events()
    logger.info(f"Returning {len(result.get('events', []))} events")
    return result


@router.delete("/events/{event_name}")
def delete_event(event_name: str):
    """Delete an event and all its data"""
    logger.info(f"DELETE /events/{event_name} endpoint accessed")
    result = event_service.delete_event(event_name)
    logger.info(f"Delete event result: {result.get('status')}")
    return result


@router.get("/debug/cloudinary-data")
def get_cloudinary_data():
    """Debug endpoint to check actual Cloudinary data"""
    logger.info("DEBUG: Fetching raw Cloudinary data")
    from app.services.event_service import _load_embeddings_from_cloudinary
    data = _load_embeddings_from_cloudinary()
    # logger.info(f"DEBUG: Raw data from Cloudinary: {data}")
    return {"raw_data": data}

@router.get("/all_user")
def get_all_users(event_name: str):
    """Get all users across all events"""
    logger.info("GET /all_user endpoint accessed")
    result = event_service.get_all_users(event_name)
    logger.info(f"Returning {len(result.get('users', []))} users")
    return result

@router.get("/delete_user")
def delete_user(event_name: str, user_id: str):
    """Delete a specific user from an event"""
    logger.info(f"DELETE /delete_user endpoint accessed for user_id: {user_id} in event: {event_name}")
    result = event_service.delete_user(event_name, user_id)
    logger.info(f"Delete user result: {result.get('status')}")
    return result