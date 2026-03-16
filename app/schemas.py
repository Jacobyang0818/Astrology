from pydantic import BaseModel
from typing import Dict, List, Optional

class ChartInput(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    location: str

class GeoOut(BaseModel):
    lat: float
    lon: float
    tz: str
