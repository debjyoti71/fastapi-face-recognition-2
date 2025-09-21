from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from app.services import face_service_insightface as face_service
from app.services.spoofing_detection import detect_spoofing
import numpy as np
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/")
async def verify_user(event_name: str = Form(...), file: UploadFile = File(...)):
    """
    Verify if a given face image belongs to a registered user in the event.
    """
    logger.info(f"POST /verify endpoint accessed for event: {event_name}")
    
    if not event_name:
        logger.warning("Verify request with empty event name")
        return JSONResponse({"verified": False, "username": None, "info": "No event was provided"})

    try:
        logger.info(f"Processing verification image for event: {event_name}")
        # Load image and convert to numpy array
        image = np.array(Image.open(io.BytesIO(file.file.read())))
        logger.info(f"Verification image loaded successfully, shape: {image.shape}")

        # Detect phone in image
        logger.info(f"Phone detecting")
        spoofing_detect = detect_spoofing(image)
        
        # Extract face embedding using DeepFace
        embedding = face_service.extract_face_embedding(image)
        if embedding is None:
            logger.warning(f"No face detected in verification image for event: {event_name}")
            return JSONResponse({"verified": False, "username": None, "message": "No face detected in image"})
        
        logger.info(f"Face encoding generated for verification in event: {event_name}")

        # Call face_service
        result = face_service.verify_face(event_name, embedding)
        
        # Convert result format for compatibility
        response = {
            "flag": result.get('flag', False),
            "username": result.get('username'),
            "message": result.get('message', ''),
            "user_in_system": result.get('user_in_system', False),
            "confidence": float(result.get('confidence', 0)),
            "face_detected": result.get('face_detected', False),
            "spoofing_detect": spoofing_detect
        }
        
        logger.info(f"Verification result: {response} \n for event: {event_name}")
        return JSONResponse(response)

    except Exception as e:
        logger.error(f"Error verifying face in event {event_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
