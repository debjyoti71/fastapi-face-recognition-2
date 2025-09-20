import numpy as np
import json
import requests
import logging
import tempfile
import os
import time
from app.services import cloud_storage
from app.core import config

logger = logging.getLogger(__name__)

# Threshold for face verification similarity (60% confidence)
THRESHOLD = 0.4


def _load_embeddings_from_cloudinary(retry_count=3):
    """Load embeddings directly from Cloudinary with retry mechanism"""
    import time
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
    """Save embeddings directly to Cloudinary"""
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


def add_user_face(event_name: str, username: str, embedding: list):
    """
    Add a new user embedding to the specified event.
    """
    if not event_name or not event_name.strip():
        logger.warning("Add user called with empty event name")
        return {"status": "error", "message": "Event name is required"}
    
    if not username or not username.strip():
        logger.warning("Add user called with empty username")
        return {"status": "error", "message": "Username is required"}
    
    if not embedding or not isinstance(embedding, list):
        logger.warning("Add user called with invalid embedding")
        return {"status": "error", "message": "Valid embedding is required"}

    try:
        logger.info(f"Adding user '{username}' to event '{event_name}'")
        storage_data = _load_embeddings_from_cloudinary()

        if event_name not in storage_data:
            storage_data[event_name] = {}
            logger.info(f"Created new event: {event_name}")

        if username not in storage_data[event_name]:
            storage_data[event_name][username] = []
            logger.info(f"Created new user: {username}")

        storage_data[event_name][username].append(embedding)
        
        # Debug logging
        logger.info(f"Data structure before saving: {list(storage_data.keys())}")
        logger.info(f"Event '{event_name}' has users: {list(storage_data[event_name].keys())}")
        
        _save_embeddings_to_cloudinary(storage_data)

        embedding_count = len(storage_data[event_name][username])
        logger.info(f"Successfully added user '{username}' to '{event_name}' (total embeddings: {embedding_count})")
        return {
            "status": "success", 
            "message": f"User '{username}' successfully added to event '{event_name}'",
            "embedding_count": embedding_count
        }
    except Exception as e:
        logger.error(f"Error adding user '{username}' to event '{event_name}': {e}")
        return {"status": "error", "message": "Failed to add user to event"}


def verify_face(event_name: str, embedding: list):
    """
    Verify a face embedding against a specific event.
    """
    if not event_name or not event_name.strip():
        logger.warning("Verify face called with empty event name")
        return {
            "flag": False, 
            "username": None, 
            "message": "Event name is required",
            "user_in_system": False,
            "face_detected": False
        }
    
    if not embedding or not isinstance(embedding, list):
        logger.warning("Verify face called with invalid embedding")
        return {
            "flag": False, 
            "username": None, 
            "message": "Valid embedding is required",
            "user_in_system": False,
            "face_detected": False
        }

    try:
        logger.info(f"Verifying face against event '{event_name}'")
        storage_data = _load_embeddings_from_cloudinary()
        event_users = storage_data.get(event_name, {})

        if not event_users:
            logger.info(f"Event '{event_name}' not found or has no users")
            return {
                "flag": False, 
                "username": None, 
                "message": f"Event '{event_name}' not found or has no registered users",
                "user_in_system": False,
                "face_detected": True
            }

        logger.info(f"Checking against {len(event_users)} users in event '{event_name}'")
        
        best_match = None
        best_distance = float('inf')
        best_username = None
        
        for username, embeddings in event_users.items():
            for i, saved_emb in enumerate(embeddings):
                try:
                    dist = np.linalg.norm(np.array(saved_emb) - np.array(embedding))
                    
                    # Track best match
                    if dist < best_distance:
                        best_distance = dist
                        best_username = username
                        best_match = round((1 - dist) * 100, 2)
                    
                    if dist < THRESHOLD:
                        logger.info(f"Match found: user '{username}' in event '{event_name}' (distance: {dist:.4f}, confidence: {round((1 - dist) * 100, 2)}%)")
                        return {
                            "flag": True, 
                            "username": username, 
                            "message": f"Face verified successfully for user '{username}' in event '{event_name}'",
                            "confidence": round((1 - dist) * 100, 2),
                            "user_in_system": True,
                            "face_detected": True
                        }
                except Exception as e:
                    logger.warning(f"Error comparing embedding {i} for user '{username}': {e}")
                    continue

        # Log most similar face even if not verified
        if best_username:
            logger.info(f"Most similar face: '{best_username}' with {best_match}% confidence (distance: {best_distance:.4f}) - Below threshold")
            return {
                "flag": False, 
                "username": None, 
                "message": "Face detected but confidence too low for verification",
                "user_in_system": False,
                "face_detected": True
            }
        
        logger.info(f"No match found in event '{event_name}'")
        return {
            "flag": False, 
            "username": None, 
            "message": f"No matching face found in event '{event_name}'",
            "user_in_system": False,
            "face_detected": True
        }
    except Exception as e:
        logger.error(f"Error verifying face in event '{event_name}': {e}")
        return {
            "flag": False, 
            "username": None, 
            "message": "Face verification failed due to system error",
            "user_in_system": False,
            "face_detected": False
        }
