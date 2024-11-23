import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from typing import Optional
from models import CachedResponse
from fastapi import HTTPException
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Access the variables
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MONGO_URI = "mongodb+srv://ahmedomarkaf:cn0sLOKuHHO3MwGT@cluster0.z3crq.mongodb.net/"
# DB_NAME = "mydatabase"

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
responses_collection = db.responses

#########################################################################
#########################################################################
#########################################################################
#########################################################################

async def delete_expired_responses():
    try:
        expiration_date = datetime.now() - timedelta(days=1)
        result = await responses_collection.delete_many({
            "date": {"$lt": expiration_date}
        })
        logger.info(f"Deleted {result.deleted_count} expired responses.")
    except Exception as e:
        logger.error(f"Error while deleting expired responses: {e}")

#########################################################################
#########################################################################
#########################################################################
#########################################################################

async def get_cached_response(keyword: str) -> Optional[CachedResponse]:
    try:
        today = datetime.now()
        cached_result = await responses_collection.find_one({
            "keyword": keyword
        })

        if cached_result:
            cache_timestamp = cached_result.get("date")
            if cache_timestamp:
                cache_age = today - cache_timestamp
                if cache_age < timedelta(days=1):
                    logger.info(f"Cache hit for keyword: {keyword}")
                    return CachedResponse(**cached_result)
        
        logger.info(f"No valid cache found for keyword: {keyword}")
        return None
    except Exception as e:
        logger.error(f"Error while fetching cached response for {keyword}: {e}")
        return None

#########################################################################
#########################################################################
#########################################################################
#########################################################################

async def delete_cached_response(keyword: str):
    try:
        result = await responses_collection.delete_one({"keyword": keyword})
        if result.deleted_count == 0:
            logger.warning(f"Cached response for keyword {keyword} not found for deletion.")
            raise HTTPException(status_code=404, detail="Cached response not found.")
        logger.info(f"Successfully deleted cached response for keyword: {keyword}")
    except Exception as e:
        logger.error(f"Error while deleting cached response for {keyword}: {e}")

#########################################################################
#########################################################################
#########################################################################
#########################################################################

async def cache_response(keyword: str, size: int, results: list):
    try:
        today = datetime.now()
        cached_response = CachedResponse(
            keyword=keyword,
            size=len(results),
            date=today,
            results=results
        )
        await responses_collection.insert_one(cached_response.dict())
        logger.info(f"Cached new response for keyword: {keyword}")
        return cached_response
    except Exception as e:
        logger.error(f"Error while caching response for {keyword}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cache response")
