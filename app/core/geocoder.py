from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime
import swisseph as swe
from ..schemas import GeoOut, ChartInput

_geolocator = Nominatim(user_agent="astro_app")
_tzf = TimezoneFinder()

def geocode_location(q: str) -> GeoOut:
    loc = _geolocator.geocode(q)
    if not loc:
        raise ValueError("找不到地點")
    lat, lon = float(loc.latitude), float(loc.longitude)
    tzname = _tzf.timezone_at(lat=lat, lng=lon) or "UTC"
    return GeoOut(lat=lat, lon=lon, tz=tzname)

def to_julday_utc(inp: ChartInput, tzname: str) -> float:
    local = pytz.timezone(tzname)
    dt_local = local.localize(datetime(inp.year, inp.month, inp.day, inp.hour, inp.minute))
    dt_utc = dt_local.astimezone(pytz.utc)
    h = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, h)
