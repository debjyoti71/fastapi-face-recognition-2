import logging
from ultralytics import YOLO
import numpy as np

logger = logging.getLogger(__name__)

# Load YOLO model once at module level
model = YOLO('models/yolo11n.pt')

def detect_phone(image: np.ndarray) -> bool:
    """
    Detect if a phone is present in the image using YOLO11n.
    Returns True if phone detected, False otherwise.
    """
    try:
        results = model(image, verbose=False)
        max_phone_confidence = 0.0
        detected_objects = []
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = model.names[class_id]
                    
                    if confidence > 0.3:  # Log all objects with decent confidence
                        detected_objects.append(f"{class_name}({confidence:.3f})")
                    
                    if class_id == 67:  # cell phone class in COCO
                        max_phone_confidence = max(max_phone_confidence, confidence)
        
        logger.info(f"Detected objects: {', '.join(detected_objects) if detected_objects else 'None'}")
        
        if max_phone_confidence > 0:
            if max_phone_confidence > 0.3:  # Lower threshold for phone detection
                logger.info(f"Phone detected with confidence: {max_phone_confidence:.3f}")
                return True
            else:
                logger.info(f"Phone detected but below threshold: {max_phone_confidence:.3f}")
        else:
            logger.info("No phone detected in image")
        
        return False
    except Exception as e:
        logger.error(f"Error in phone detection: {e}")
        return False