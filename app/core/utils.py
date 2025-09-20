import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

def log_execution_time(func):
    """Decorator to log function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Starting execution of {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed {func.__name__} after {execution_time:.2f} seconds: {e}")
            raise
    
    return wrapper

def validate_image_format(filename: str) -> bool:
    """Validate if file has supported image format"""
    supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    file_ext = filename.lower().split('.')[-1]
    is_valid = f'.{file_ext}' in supported_formats
    
    if is_valid:
        logger.info(f"Valid image format detected: {file_ext}")
    else:
        logger.warning(f"Unsupported image format: {file_ext}")
    
    return is_valid