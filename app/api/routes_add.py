from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from app.services import face_service_insightface as face_service
import numpy as np
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/")
async def add_user(event_name: str = Form(...), username: str = Form(...), file: UploadFile = File(...)):
    """
    Add a new user with a face image to a specific event.
    """
    logger.info(f"POST /addUser endpoint accessed for event: {event_name}, user: {username}")
    
    if not event_name:
        logger.warning("Add user request with empty event name")
        return JSONResponse({"status": "error", "message": "No event was provided"})

    try:
        logger.info(f"Processing image upload for user: {username}")
        # Load image and convert to numpy array
        image = np.array(Image.open(io.BytesIO(file.file.read())))
        logger.info(f"Image loaded successfully, shape: {image.shape}")

        # Extract face embedding using DeepFace
        embedding = face_service.extract_face_embedding(image)
        if embedding is None:
            logger.warning(f"No face detected in uploaded image for user: {username}")
            return JSONResponse({"status": "error", "message": "No face detected in image"})
        
        logger.info(f"Face encoding generated successfully for user: {username}")

        # Add user
        result = face_service.add_user_face(event_name, username, embedding)
        logger.info(f"Add user result: {result.get('status')} for {username}")
        return JSONResponse(result)

    except Exception as e:
        logger.error(f"Error adding user {username} to event {event_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
