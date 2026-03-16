import math
import swisseph as swe
from typing import Dict, List, Optional
from ..constants import (
    ZODIAC_CN, PLANET_KEY, HOUSE_SYSTEMS_CN2CODE, 
    HOUSE_SYSTEMS_CODE2CN, deg_to_sign, wrap360
)

def resolve_hsys(house_system: str) -> bytes:
    """接受中文名稱或單字母代碼。預設整宮制。"""
    if not house_system:
        return HOUSE_SYSTEMS_CN2CODE["整宮制"]
    s = house_system.strip()
    if s in HOUSE_SYSTEMS_CN2CODE:
        return HOUSE_SYSTEMS_CN2CODE[s]
    code = s.upper().encode("ascii")[:1]
    return code if code in HOUSE_SYSTEMS_CODE2CN else HOUSE_SYSTEMS_CN2CODE["整宮制"]

def calc_chart(jd_ut: float, lat: float, lon: float, HSYS: bytes):
    # 宮首與關鍵點
    cusps, ascmc = swe.houses(jd_ut, lat, lon, HSYS)
    asc_deg, mc_deg, armc = ascmc[0], ascmc[1], ascmc[2]

    # 行星經緯與距離
    planet_lons: Dict[str, float] = {}
    planet_lats: Dict[str, float] = {}
    planet_dists: Dict[str, float] = {}
    for name, pid in PLANET_KEY.items():
        xx, _ = swe.calc_ut(jd_ut, pid)  # xx[0]=lon, xx[1]=lat, xx[2]=dist
        planet_lons[name] = wrap360(xx[0])
        planet_lats[name] = xx[1]
        planet_dists[name] = xx[2] if len(xx) > 2 else 1.0

    # 交點
    north_node = wrap360(swe.calc_ut(jd_ut, swe.MEAN_NODE)[0][0])
    south_node = wrap360(north_node + 180.0)

    def house_by_cusps(xlon: float) -> int:
        x = wrap360(xlon)
        for i in range(12):
            s = wrap360(cusps[i])
            e = wrap360(cusps[(i + 1) % 12])
            if e <= s:
                e += 360.0
            xx = x if x >= s else x + 360.0
            if s <= xx < e:
                return i + 1
        return 12

    def house_pos_compat(xlon: float, xlat: float = 0.0, xdist: float = 1.0) -> int:
        try:
            hpos = swe.house_pos(armc, lat, HSYS, xlon, xlat)
        except TypeError:
            try:
                hpos = swe.house_pos(armc, lat, HSYS, xlon)
            except TypeError:
                try:
                    eps = swe.calc_ut(jd_ut, swe.ECL_NUT)[0][0]
                except Exception:
                    eps = 23.4392911
                try:
                    hpos = swe.house_pos(armc, lat, eps, HSYS, xlon, xlat, xdist)
                except TypeError:
                    return house_by_cusps(xlon)
        return ((int(math.floor(hpos)) % 12) + 1)

    # 各點宮位
    planet_houses: Dict[str, int] = {}
    for pname in planet_lons:
        planet_houses[pname] = house_pos_compat(planet_lons[pname], planet_lats[pname], planet_dists[pname])
    planet_houses["北交點"] = house_pos_compat(north_node)
    planet_houses["南交點"] = house_pos_compat(south_node)
    planet_houses["天頂"] = house_pos_compat(mc_deg)

    # 星座
    planet_signs = {p: deg_to_sign(planet_lons[p]) for p in planet_lons}
    planet_signs["北交點"] = deg_to_sign(north_node)
    planet_signs["南交點"] = deg_to_sign(south_node)
    asc_sign = deg_to_sign(asc_deg)
    mc_sign = deg_to_sign(mc_deg)

    return {
        "asc": asc_deg,
        "mc": mc_deg,
        "asc_sign": asc_sign,
        "mc_sign": mc_sign,
        "cusps": [wrap360(c) for c in cusps],
        "planet_lons": planet_lons,
        "planet_signs": planet_signs,
        "planet_houses": planet_houses,
        "north_node": north_node,
        "south_node": south_node,
    }
