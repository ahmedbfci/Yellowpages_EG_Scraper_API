# Yellow Pages Scraper API

This project provides a **FastAPI-based backend** for scraping company details from Yellow Pages and caching the results in a **MongoDB database**. It includes features like periodic cleanup of expired cached results, error handling, and external API communication.

## Features

- **Scrape Company Details:** Extracts comprehensive details about companies from Yellow Pages, including location, ratings, reviews, and more.
- **Caching:** Uses MongoDB to store and retrieve cached responses to reduce scraping load.
- **Automatic Cleanup:** Periodically removes cached responses older than 24 hours.
- **Robust Error Handling:** Handles scraping failures and returns meaningful HTTP responses.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://www.docker.com/)
- Python 3.8+
- MongoDB (if not using Docker)

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-folder>
```


### 2.Set Environment Variables
Create a `.env` file in the root directory with the following content:

```env
MONGO_URI=mongodb://mongo:27017/
DB_NAME=your_database_name
```


### 3. Install Dependencies
To install the Python dependencies, run:

```
pip install -r requirements.txt
```

### 4. Run with Docker
Ensure Docker is running and start the services using docker-compose:

```
docker-compose up --build
```

This will start:

MongoDB: Available on port 27017
FastAPI application: Available on http://localhost:8000

### 5. Run Locally (Optional)
To run the application without Docker:

Start MongoDB on your local machine.
Run the FastAPI application

```
uvicorn main:app --reload
```

## Usage
## API Endpoints
### 1.Search Companies

```
GET /search/?keyword=<keyword>&size=<size>
```
### Parameters:
#### keyword (string): Search keyword (e.g., "restaurants").

#### size (integer): Number of results to fetch (30–100).
## Response: Returns a JSON object with the company details or a cached response if available.
Example:

```
curl "http://localhost:8000/search/?keyword=restaurants&size=50"
```
