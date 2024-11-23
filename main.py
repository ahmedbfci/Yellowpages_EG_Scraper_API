import logging
from fastapi import FastAPI, HTTPException
from scraper import scrape_yellowpages
from database import get_cached_response, cache_response, delete_expired_responses, delete_cached_response
from datetime import datetime
import asyncio
from database import client

#uvicorn main:app --reload 

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    try:
        logger.info("Connecting to MongoDB...")
        # Simulate the connection
        print("Connected to MongoDB")
        asyncio.create_task(periodic_cleanup())
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to MongoDB")

async def periodic_cleanup():
    while True:
        try:
            logger.info("Running periodic cleanup...")
            await delete_expired_responses()
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        logger.info("Closing MongoDB client...")
        client.close()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/search/")
async def search_companies(keyword: str, size: int = 30):
    
    # Validate the size parameter
    if size < 30 or size > 100:
        logger.warning(f"Invalid size parameter: {size}. Must be between 30 and 100.")
        raise HTTPException(status_code=400, detail="Size must be between 30 and 100")

    # Check for cached results
    cached_results = await get_cached_response(keyword)
    if cached_results:
        logger.info(f"Cache hit for keyword: {keyword}")

        if cached_results.size >= size:
            cached_results.results = cached_results.results[:size]
            cached_results.size = size
            return cached_results
        else:
            logger.info(f"Cached results size ({cached_results.size}) smaller than requested size ({size}), scraping new data.")
            results = scrape_yellowpages(keyword, size)
            if not results:
                logger.warning(f"No results found for keyword: {keyword}")
                raise HTTPException(status_code=404, detail="No results found.")
            
            await delete_cached_response(keyword)
    else:
        logger.info(f"No cached results found for keyword: {keyword}")
        results = scrape_yellowpages(keyword, size)
        if not results:
            logger.warning(f"No results found for keyword: {keyword}")
            raise HTTPException(status_code=404, detail="No results found.")

    # Cache the new results
    logger.info(f"Caching new results for keyword: {keyword}")
    response = await cache_response(keyword, size, results)
    return response
