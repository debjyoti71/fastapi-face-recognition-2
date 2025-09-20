import json
import requests
import logging
import tempfile
import os
import time
from app.services import cloud_storage
from app.core import config

# Check if using Cloudinary or local storage
USE_CLOUDINARY = os.getenv("USE_CLOUDINARY", "true").lower() == "true"
LOCAL_EMBEDDINGS_PATH = "data/embeddings.json"

logger = logging.getLogger(__name__)


def _load_embeddings_from_cloudinary(retry_count=3):
    """Load embeddings from Cloudinary or local file based on USE_CLOUDINARY flag"""
    if not USE_CLOUDINARY:
        # Load from local file
        try:
            if os.path.exists(LOCAL_EMBEDDINGS_PATH):
                with open(LOCAL_EMBEDDINGS_PATH, 'r') as f:
                    logger.info(f"Loading embeddings from local file: {LOCAL_EMBEDDINGS_PATH}")
                    return json.load(f)
            else:
                logger.info(f"Local embeddings file not found: {LOCAL_EMBEDDINGS_PATH}")
                return {}
        except Exception as e:
            logger.error(f"Error loading local embeddings: {e}")
            return {}
    
    # Load from Cloudinary (original code)
    cache_buster = int(time.time())
    url = f"https://res.cloudinary.com/{config.CLOUD_NAME}/raw/upload/face_recognition/embeddings.json?cb={cache_buster}"
    
    for attempt in range(retry_count):
        try:
            logger.info(f"Loading embeddings from Cloudinary (attempt {attempt + 1})")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logger.info("Successfully loaded embeddings")
                return response.json()
            
            if attempt < retry_count - 1:
                logger.info(f"Retrying in 2 seconds... (attempt {attempt + 1}/{retry_count})")
                time.sleep(2)
            else:
                logger.warning(f"No embeddings found after {retry_count} attempts, status: {response.status_code}")
                
        except requests.RequestException as e:
            if attempt < retry_count - 1:
                logger.warning(f"Request failed, retrying: {e}")
                time.sleep(2)
            else:
                logger.error(f"Failed to load embeddings after {retry_count} attempts: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in embeddings: {e}")
            break
    
    return {}


def _save_embeddings_to_cloudinary(data):
    """Save embeddings to Cloudinary or local file based on USE_CLOUDINARY flag"""
    if not USE_CLOUDINARY:
        # Save to local file
        try:
            os.makedirs(os.path.dirname(LOCAL_EMBEDDINGS_PATH), exist_ok=True)
            with open(LOCAL_EMBEDDINGS_PATH, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Successfully saved embeddings to local file: {LOCAL_EMBEDDINGS_PATH}")
            return
        except Exception as e:
            logger.error(f"Failed to save local embeddings: {e}")
            raise
    
    # Save to Cloudinary (original code)
    try:
        logger.info("Saving embeddings to Cloudinary")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        
        cloud_storage.upload_embeddings(temp_path)
        logger.info("Successfully saved embeddings")
    except Exception as e:
        logger.error(f"Failed to save embeddings: {e}")
        raise
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)


def get_all_events():
    """Get list of all events with user counts."""
    try:
        logger.info("Fetching all events")
        storage_data = _load_embeddings_from_cloudinary()
        
        events = [{
            "event_name": event_name,
            "user_count": len(users)
        } for event_name, users in storage_data.items()]
        
        logger.info(f"Found {len(events)} events")
        return {"events": events}
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return {"status": "error", "message": "Failed to fetch events"}


def delete_event(event_name: str):
    """Delete an event and all its data."""
    if not event_name or not event_name.strip():
        logger.warning("Delete event called with empty name")
        return {"status": "error", "message": "Event name is required"}
    
    try:
        logger.info(f"Deleting event: {event_name}")
        storage_data = _load_embeddings_from_cloudinary()
        
        if event_name not in storage_data:
            logger.warning(f"Event not found: {event_name}")
            return {"status": "error", "message": f"Event '{event_name}' not found"}
        
        user_count = len(storage_data[event_name])
        del storage_data[event_name]
        _save_embeddings_to_cloudinary(storage_data)
        
        logger.info(f"Successfully deleted event '{event_name}' with {user_count} users")
        return {"status": "success", "message": f"Event '{event_name}' deleted"}
    except Exception as e:
        logger.error(f"Error deleting event '{event_name}': {e}")
        return {"status": "error", "message": "Failed to delete event"}
    

def get_all_users(event_name: str):
    """Get all users for a given event."""
    try:
        logger.info(f"Fetching all users in event: {event_name}")
        storage_data = _load_embeddings_from_cloudinary()
        
        users = list(storage_data.get(event_name, {}).keys())
        
        logger.info(f"Found {len(users)} users in event '{event_name}'")
        return {"users": users}
    except Exception as e:
        logger.error(f"Error fetching users for event '{event_name}': {e}")
        return {"status": "error", "message": "Failed to fetch users"} 
    

def delete_user(event_name: str, user_id: str):
    """Delete a specific user from an event."""
    if not event_name or not event_name.strip() or not user_id or not user_id.strip():
        logger.warning("Delete user called with empty event name or user ID")
        return {"status": "error", "message": "Event name and user ID are required"}
    
    try:
        logger.info(f"Deleting user '{user_id}' from event: {event_name}")
        storage_data = _load_embeddings_from_cloudinary()
        
        if event_name not in storage_data or user_id not in storage_data[event_name]:
            logger.warning(f"User '{user_id}' not found in event '{event_name}'")
            return {"status": "error", "message": f"User '{user_id}' not found in event '{event_name}'"}
        
        del storage_data[event_name][user_id]

        # Optional: clean up empty event
        if not storage_data[event_name]:
            logger.info(f"Event '{event_name}' has no more users, deleting event")
            del storage_data[event_name]

        _save_embeddings_to_cloudinary(storage_data)
        
        logger.info(f"Successfully deleted user '{user_id}' from event '{event_name}'")
        return {"status": "success", "message": f"User '{user_id}' deleted from event '{event_name}'"}
    except Exception as e:
        logger.error(f"Error deleting user '{user_id}' from event '{event_name}': {e}")
        return {"status": "error", "message": f"Failed to delete user: {str(e)}"}  

