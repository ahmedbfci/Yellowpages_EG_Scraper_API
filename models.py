from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict


class CachedResponse(BaseModel):
    keyword: str
    size: int
    date: datetime
    results: List[Dict]
