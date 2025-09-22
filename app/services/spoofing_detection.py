import logging
from ultralytics import YOLO
import numpy as np
import cv2

logger = logging.getLogger(__name__)

# Load YOLO model once at module level
model = YOLO('app/models/yolov8n.pt')

def detect_spoofing(image: np.ndarray) -> bool:
    """
    Detect if spoofing attempt (phone screen showing person) is present in the image.
    Returns True if spoofing detected, False otherwise.
    """
    try:
        # Run YOLO detection
        results = model(image, conf=0.3, verbose=False)
        
        # Get person detections
        persons = []
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0])
                    if cls == 0:  # person class
                        conf = float(box.conf[0])
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        persons.append((x1, y1, x2, y2, conf))
        
        if not persons:
            return False
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        for x1, y1, x2, y2, conf in persons:
            # Person area analysis
            person_area = (x2-x1) * (y2-y1)
            
            # Extract person region
            person_roi = gray[y1:y2, x1:x2]
            if person_roi.size == 0:
                continue
            
            # Analyze brightness characteristics
            brightness_std = np.std(person_roi)
            avg_brightness = np.mean(person_roi)
            
            # Spoofing detection thresholds
            too_uniform = brightness_std < 60          # phone screens more uniform
            too_bright = avg_brightness > 160         # phone screen brightness
            too_small = person_area < 180000          # small area indicates phone

            logger.info(f"Person area: {person_area:.0f}, Brightness std: {brightness_std:.1f}, Avg brightness: {avg_brightness:.1f}")
            
            # Spoofing conditions
            # if too_uniform or too_bright or too_small:
            if too_uniform or too_bright:
                logger.warning("SPOOFING DETECTED - Phone screen characteristics!")
                return True
        
        return False
    except Exception as e:
        logger.error(f"Spoofing detection error: {e}")
        return False

