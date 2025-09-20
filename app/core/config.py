import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()  # load variables from .env
logger.info("Environment variables loaded from .env file")

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
API_KEY = os.getenv("CLOUDINARY_API_KEY")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

if not all([CLOUD_NAME, API_KEY, API_SECRET]):
    logger.error("Missing required Cloudinary environment variables")
else:
    logger.info("Cloudinary configuration loaded successfully")
