import cloudinary
import cloudinary.uploader
import logging
from app.core import config

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=config.CLOUD_NAME,
    api_key=config.API_KEY,
    api_secret=config.API_SECRET
)

EMBEDDINGS_PUBLIC_ID = "face_recognition/embeddings"  # folder + filename in Cloudinary


def upload_embeddings(file_path: str):
    """Upload local embeddings.json to Cloudinary"""
    try:
        logger.info(f"Uploading embeddings file: {file_path}")
        res = cloudinary.uploader.upload(
            file_path,
            public_id=EMBEDDINGS_PUBLIC_ID,
            resource_type="raw",
            overwrite=True,
            invalidate=True  # Force cache invalidation
        )
        logger.info(f"Successfully uploaded embeddings to Cloudinary: {res.get('public_id')}")
        return res
    except Exception as e:
        logger.error(f"Failed to upload embeddings to Cloudinary: {e}")
        raise


def download_embeddings(local_path: str):
    """Download embeddings.json from Cloudinary if exists"""
    import time
    cache_buster = int(time.time())
    url = f"https://res.cloudinary.com/{config.CLOUD_NAME}/raw/upload/{EMBEDDINGS_PUBLIC_ID}.json?cb={cache_buster}"
    import requests
    try:
        logger.info(f"Downloading embeddings from Cloudinary to: {local_path}")
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(r.content)
            logger.info(f"Successfully downloaded embeddings to: {local_path}")
            return True
        logger.warning(f"Embeddings not found on Cloudinary, status: {r.status_code}")
        return False
    except requests.RequestException as e:
        logger.error(f"Network error downloading embeddings: {e}")
        return False
    except IOError as e:
        logger.error(f"File error downloading embeddings: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading embeddings: {e}")
        return False
