from app.services import cloud_storage
import os
import json
import logging

logger = logging.getLogger(__name__)

DATA_FILE = "data/embeddings.json"
os.makedirs("data", exist_ok=True)

def load_data():
    """Load embeddings data from local file, downloading from Cloudinary first"""
    try:
        logger.info("Loading embeddings data")
        # Try downloading latest from Cloudinary first
        download_success = cloud_storage.download_embeddings(DATA_FILE)
        
        if download_success:
            logger.info("Using fresh data from Cloudinary")
        else:
            logger.info("Using local data file")

        if not os.path.exists(DATA_FILE):
            logger.info("No embeddings file found, returning empty data")
            return {}
            
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            logger.info(f"Successfully loaded {len(data)} events")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in embeddings file: {e}")
        return {}
    except IOError as e:
        logger.error(f"Error reading embeddings file: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading data: {e}")
        return {}

def save_data(data):
    """Save embeddings data to local file and upload to Cloudinary"""
    try:
        logger.info(f"Saving embeddings data with {len(data)} events")
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
        logger.info("Successfully saved data to local file")
        
        # Upload to Cloudinary
        cloud_storage.upload_embeddings(DATA_FILE)
        logger.info("Successfully uploaded data to Cloudinary")
    except IOError as e:
        logger.error(f"Error writing embeddings file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error saving embeddings data: {e}")
        raise
