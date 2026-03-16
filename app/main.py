import os
import logging
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import google.generativeai as genai
import swisseph as swe

# Internal Imports
from .constants import SYMBOL, HOUSE_SYSTEMS_CODE2CN
from .schemas import ChartInput, GeoOut
from .core.geocoder import geocode_location, to_julday_utc
from .core.astrology import calc_chart, resolve_hsys
from .services.rag import get_retriever, _qdrant_vector_store
from .services.ai import gemini_interpretations, build_ai_advice_md, build_credits_md
from .utils.formatters import (
    build_four_kings, build_element_tables, build_houses_table,
    build_positions_table, build_aspects_table, 
    summarize_house_focus, summarize_major_aspects
)

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load Environment and Configure AI
load_dotenv()
GEMINI_ENABLED = False
if os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
    GEMINI_ENABLED = True

if os.getenv("SWEPH_PATH"):
    swe.set_ephe_path(os.getenv("SWEPH_PATH"))

# Initialize FastAPI
app = FastAPI(title="Astrology API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Frontend
try:
    if os.path.exists("frontend/dist"):
        app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
except Exception as e:
    logger.warning(f"Could not mount frontend/dist: {e}")

# Routes
@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/geocode", response_model=GeoOut)
def api_geocode(location: str = Query(..., description="地名或地址")):
    return geocode_location(location)

@app.get("/api/chart")
def api_chart(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    location: str,
    house_system: str = Query("整宮制", description="中文名稱或代碼，例如：整宮制 / W"),
    ai: int = Query(0, ge=0, le=1, description="是否產生AI解說內容 : 1=是, 0=否")
):
    geo = geocode_location(location)
    jd_ut = to_julday_utc(
        ChartInput(year=year, month=month, day=day, hour=hour, minute=minute, location=location),
        geo.tz,
    )
    HSYS = resolve_hsys(house_system)
    data = calc_chart(jd_ut, geo.lat, geo.lon, HSYS)

    interp = gemini_interpretations(data, GEMINI_ENABLED) if (GEMINI_ENABLED and ai == 1) else {}
    four_rows, chart_ruler = build_four_kings(data, interpretations=interp)
    detail_rows, summary_rows = build_element_tables(data, chart_ruler)
    houses_rows = build_houses_table(data)
    positions_rows = build_positions_table(data)
    aspects_rows = build_aspects_table(data)
    
    ai_advice_md = ""
    if GEMINI_ENABLED and ai == 1:
        house_sum = summarize_house_focus(data)
        aspect_sum = summarize_major_aspects(data)
        ai_advice_md = build_ai_advice_md(data, GEMINI_ENABLED, house_sum, aspect_sum)

    payload = {
        "geo": geo.dict(),
        "asc": data["asc"],
        "mc": data["mc"],
        "asc_sign": data["asc_sign"],
        "mc_sign": data["mc_sign"],
        "cusps": data["cusps"],
        "planet_lons": data["planet_lons"],
        "planet_signs": data["planet_signs"],
        "planet_houses": data["planet_houses"],
        "north_node": data["north_node"],
        "south_node": data["south_node"],
        "four_kings": four_rows,
        "chart_ruler": chart_ruler,
        "detail_rows": detail_rows,
        "summary_rows": summary_rows,
        "houses_rows": houses_rows,
        "positions_rows": positions_rows,
        "aspects_rows": aspects_rows,
        "symbols": SYMBOL,
        "house_system_cn": HOUSE_SYSTEMS_CODE2CN.get(HSYS, "整宮制"),
        "ai_advice_md": ai_advice_md,
        "rag_active": get_retriever(GEMINI_ENABLED) is not None,
    }
    payload["credits_md"] = build_credits_md(geo.tz)
    payload["ai_generated"] = bool(ai)
    return payload
