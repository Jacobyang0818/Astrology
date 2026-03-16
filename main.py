import os
import math
import logging
from typing import Dict, List, Optional
from datetime import datetime

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# RAG related imports
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_qdrant import QdrantVectorStore
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from qdrant_client import QdrantClient

# -------------------- 可選：Gemini LLM --------------------
GEMINI_ENABLED = False
try:
    import google.generativeai as genai
    import os
    from dotenv import load_dotenv

    load_dotenv() # Load .env for both Gemini API key and Qdrant path
    if os.getenv("GEMINI_API_KEY"):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
        GEMINI_ENABLED = True
except ImportError:
    GEMINI_ENABLED = False

# --- Global RAG Retriever ---
_qdrant_vector_store = None

def get_retriever():
    global _qdrant_vector_store
    if _qdrant_vector_store is not None:
        return _qdrant_vector_store

    db_path = "./qdrant_db"
    if not os.path.exists(db_path):
        logger.info(f"Qdrant DB path not found: {db_path}. RAG will be skipped.")
        return None

    if not GEMINI_ENABLED:
        logger.info("Gemini API key not configured. RAG will be skipped.")
        return None

    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        client = QdrantClient(path=db_path)
        # Check if collection exists
        collections = client.get_collections().collections
        if "astrology_knowledge" not in [c.name for c in collections]:
            logger.warning(f"Qdrant collection 'astrology_knowledge' not found. RAG will be skipped.")
            return None

        _qdrant_vector_store = QdrantVectorStore(
            client=client,
            collection_name="astrology_knowledge",
            embedding=embeddings
        )
        logger.info("Qdrant RAG retriever initialized successfully.")
        return _qdrant_vector_store
    except Exception as e:
        logger.error(f"RAG Initialization failed: {e}", exc_info=True)
        return None

# 可選：Swiss Ephemeris 路徑（若有本地 ephe 檔）
if os.getenv("SWEPH_PATH"):
    swe.set_ephe_path(os.getenv("SWEPH_PATH"))

# -------------------- FastAPI --------------------
app = FastAPI(title="Astrology API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend build directory
# Note: In production, frontend/dist should contain the built React app
try:
    if os.path.exists("frontend/dist"):
        app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
except Exception as e:
    logger.warning(f"Could not mount frontend/dist: {e}")

# -------------------- 常數 --------------------
ZODIAC_CN = [
    "牡羊", "金牛", "雙子", "巨蟹", "獅子", "處女",
    "天秤", "天蠍", "射手", "魔羯", "水瓶", "雙魚"
]

def sign_opposite(sign: str) -> str:
    idx = ZODIAC_CN.index(sign)
    return ZODIAC_CN[(idx + 6) % 12]

ELEMENT_OF_SIGN = {
    "牡羊": "火", "金牛": "地", "雙子": "風", "巨蟹": "水",
    "獅子": "火", "處女": "地", "天秤": "風", "天蠍": "水",
    "射手": "火", "魔羯": "地", "水瓶": "風", "雙魚": "水",
}
RULER_OF_SIGN = {
    "牡羊": "火星", "金牛": "金星", "雙子": "水星", "巨蟹": "月亮",
    "獅子": "太陽", "處女": "水星", "天秤": "金星", "天蠍": "火星",
    "射手": "木星", "魔羯": "土星", "水瓶": "土星", "雙魚": "木星",
}
PLANET_KEY = {
    "太陽": swe.SUN, "月亮": swe.MOON, "水星": swe.MERCURY, "金星": swe.VENUS,
    "火星": swe.MARS, "木星": swe.JUPITER, "土星": swe.SATURN,
    "天王星": swe.URANUS, "海王星": swe.NEPTUNE, "冥王星": swe.PLUTO,
}
SYMBOL = {
    "上升": "ASC", "天頂": "MC", "太陽": "☉", "月亮": "☾", "水星": "☿", "金星": "♀",
    "火星": "♂", "木星": "♃", "土星": "♄", "天王星": "♅", "海王星": "♆", "冥王星": "♇",
    "北交點": "☊", "南交點": "☋"
}
SCORES = [15, 10, 16, 4, 13, 2, 6, 4, 5, 5, 6, 4, 4, 3, 1, 1, 1]
ITEM_ORDER = [
    "上升", "上升守護星(命主星)", "太陽", "太陽守護星", "月亮", "月亮守護星",
    "天頂", "天頂守護星", "水星", "金星", "火星", "木星", "土星",
    "南交點", "天王星", "海王星", "冥王星"
]
HOUSE_NAMES = [
    "命宮", "財帛宮", "兄弟宮", "田宅宮", "子女宮", "奴僕宮",
    "夫妻宮", "疾厄宮", "遷移宮", "官祿宮", "福德宮", "玄密宮"
]

# 宮位制度：中文 ↔ 代碼
HOUSE_SYSTEMS_CN2CODE: Dict[str, bytes] = {
    "整宮制": b"W",
    "等宮制": b"E",
    "普拉西杜斯": b"P",
    "柯赫": b"K",
    "坎帕納斯": b"C",
    "雷吉歐蒙塔納斯": b"R",
    "波菲利": b"O",
    "阿卡彼特": b"B",
}
HOUSE_SYSTEMS_CODE2CN: Dict[bytes, str] = {v: k for k, v in HOUSE_SYSTEMS_CN2CODE.items()}

HOUSE_MEANINGS = {
    1: "自我、外貌、天賦、給人的第一印象。",
    2: "正財、財務、資源獲得與運用方式。",
    3: "手足、親戚鄰居、基礎教育與學習能力。",
    4: "原生家庭、父親、不動產與晚年生活。",
    5: "小孩、子女、投機、創作、娛樂與休閒。",
    6: "工作、勞動、部屬、員工、身體健康。",
    7: "婚姻、配偶、合夥人、訴訟、公開的敵人。",
    8: "他人資源、配偶遺產、死亡、保險。",
    9: "法律、理想、長途旅行、高等教育。",
    10: "事業、母親、社會形象、名譽、權威。",
    11: "朋友、社團、希望、政黨、公益、理想。",
    12: "潛意識、犧牲、秘密、暗小人。",
}

# 傳統尊貴：入廟/旺/失勢/落陷
EXALTATION = {  # 擢升
    "太陽": "牡羊", "月亮": "金牛", "水星": "處女",
    "金星": "雙魚", "火星": "魔羯", "木星": "巨蟹", "土星": "天秤",
}
# 入廟：由 RULER_OF_SIGN 反推
DOMICILE: Dict[str, List[str]] = {}
for s, r in RULER_OF_SIGN.items():
    DOMICILE.setdefault(r, []).append(s)
DETRIMENT = {p: [sign_opposite(s) for s in signs] for p, signs in DOMICILE.items()}
FALL = {p: sign_opposite(s) for p, s in EXALTATION.items()}

# -------------------- Schemas --------------------
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

# -------------------- Helpers --------------------
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

def deg_to_sign(deg: float) -> str:
    idx = int(math.floor((deg % 360.0) / 30.0))
    return ZODIAC_CN[idx]



def wrap360(x: float) -> float:
    x = x % 360.0
    return x if x >= 0 else x + 360.0

def resolve_hsys(house_system: str) -> bytes:
    """接受中文名稱或單字母代碼。預設整宮制。"""
    if not house_system:
        return HOUSE_SYSTEMS_CN2CODE["整宮制"]
    s = house_system.strip()
    if s in HOUSE_SYSTEMS_CN2CODE:
        return HOUSE_SYSTEMS_CN2CODE[s]
    code = s.upper().encode("ascii")[:1]
    return code if code in HOUSE_SYSTEMS_CODE2CN else HOUSE_SYSTEMS_CN2CODE["整宮制"]

# -------------------- Chart Core --------------------
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

    # house_pos 相容包裝
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
        # 版本 A：house_pos(armc, geolat, hsys, xlon, xlat)
        try:
            hpos = swe.house_pos(armc, lat, HSYS, xlon, xlat)
        except TypeError:
            # 版本 A-簡化：house_pos(armc, geolat, hsys, xlon)
            try:
                hpos = swe.house_pos(armc, lat, HSYS, xlon)
            except TypeError:
                # 版本 B：house_pos(armc, geolat, eps, hsys, xlon, xlat, xdist)
                try:
                    eps = swe.calc_ut(jd_ut, swe.ECL_NUT)[0][0]
                except Exception:
                    eps = 23.4392911
                try:
                    hpos = swe.house_pos(armc, lat, eps, HSYS, xlon, xlat, xdist)
                except TypeError:
                    # 最後後備：以宮首區間決定
                    return house_by_cusps(xlon)
        # 轉為 1..12
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

# -------------------- 表格構建 --------------------
def build_four_kings(data: dict, interpretations: Optional[Dict[str, str]] = None):
    asc_sign = data["asc_sign"]
    chart_ruler = RULER_OF_SIGN[asc_sign]

    houses = data["planet_houses"].copy()
    houses["上升"] = 1
    houses["天頂"] = houses.get("天頂", 10)

    signs = data["planet_signs"].copy()
    signs["上升"] = asc_sign

    rows = []
    items = [
        ("太陽", "太陽"),
        ("月亮", "月亮"),
        ("上升", "上升"),
        (f"命主星({chart_ruler})", chart_ruler),
    ]
    for label, key in items:
        sign = signs[key] if key in signs else data.get("mc_sign")
        elem = ELEMENT_OF_SIGN[sign]
        house = houses.get(key)
        rows.append({
            "項目": label,
            "宮位": house,
            "屬性": elem,
            "說明": (interpretations or {}).get(label, "")
        })
    return rows, chart_ruler

def build_element_tables(data: dict, chart_ruler: str):
    signs = data["planet_signs"]
    mc_sign = data["mc_sign"]
    asc_sign = data["asc_sign"]

    def ruler_of(sign: str) -> str:
        return RULER_OF_SIGN[sign]

    sun_guardian = ruler_of(signs["太陽"])
    moon_guardian = ruler_of(signs["月亮"])
    mc_guardian = ruler_of(mc_sign)

    resolved_sign_of_item: Dict[str, str] = {
        "上升": asc_sign,
        "太陽": signs["太陽"],
        "月亮": signs["月亮"],
        "天頂": mc_sign,
        "水星": signs["水星"],
        "金星": signs["金星"],
        "火星": signs["火星"],
        "木星": signs["木星"],
        "土星": signs["土星"],
        "南交點": signs["南交點"],
        "天王星": signs["天王星"],
        "海王星": signs["海王星"],
        "冥王星": signs["冥王星"],
    }

    item_planet_identity = {
        "上升守護星(命主星)": chart_ruler,
        "太陽守護星": sun_guardian,
        "月亮守護星": moon_guardian,
        "天頂守護星": mc_guardian,
    }

    for label, planet_name in item_planet_identity.items():
        resolved_sign_of_item[label] = signs[planet_name]

    detail_rows = []
    element_totals = {"地": 0, "水": 0, "火": 0, "風": 0}

    for idx, label in enumerate(ITEM_ORDER):
        score = SCORES[idx]
        if label.endswith("守護星") or label == "上升守護星(命主星)":
            planet_or_point = item_planet_identity[label]
        else:
            planet_or_point = label
        sym = SYMBOL.get(planet_or_point, SYMBOL.get(label, ""))

        sign = resolved_sign_of_item[label]
        elem = ELEMENT_OF_SIGN[sign]

        detail_rows.append({
            "Item": label,
            "Symbol": sym,
            "Constellation": sign,
            "Element": elem,
            "Score": score,
        })
        element_totals[elem] += score

    total_sum = sum(element_totals.values())
    if total_sum != 100:
        raise ValueError(f"元素總分不是100，請檢查計算：{element_totals} 總和={total_sum}")

    summary_rows = [
        {"元素": "地", "簡介": "實際、感官、務實、責任", "總分": element_totals["地"]},
        {"元素": "水", "簡介": "情感、感覺、精神、同理、體諒、心靈", "總分": element_totals["水"]},
        {"元素": "火", "簡介": "直接、行動力、積極、急躁、坦率、粗魯、沒心機、直覺", "總分": element_totals["火"]},
        {"元素": "風", "簡介": "理性、公平、抽象思考、社交、文化涵養、知性交流", "總分": element_totals["風"]},
    ]

    return detail_rows, summary_rows

# ===== 修改：12宮表格 =====
def build_houses_table(data: dict):
    cusps = data["cusps"]
    planet_houses = data["planet_houses"]

    house_planets: Dict[int, List[str]] = {i: [] for i in range(1, 13)}
    include = [
        "太陽", "月亮", "金星", "木星", "水星", "土星", "火星",
        "天王星", "冥王星", "海王星", "天頂", "南交點", "北交點"
    ]
    for name in include:
        h = planet_houses.get(name)
        if h:
            house_planets[h].append(name)

    rows = []
    for i in range(1, 13):
        sign = deg_to_sign(cusps[i - 1])
        rows.append({
            "宮位": f"第{i}宮",
            "宮名": HOUSE_NAMES[i - 1],
            "宮位星座": sign,
            "宮中行星": "、".join(house_planets[i]) if house_planets[i] else "-",
            "宮位意涵": HOUSE_MEANINGS[i],
        })
    return rows

def gemini_interpretations(data: dict) -> Dict[str, str]:
    if not GEMINI_ENABLED:
        return {}
    model = genai.GenerativeModel("gemini-2.5-flash")
    # 動態計算命主星與其掌管宮位
    asc_sign = data["asc_sign"]
    chart_ruler = RULER_OF_SIGN[asc_sign]                   # 例：牡羊→火星
    pr_sign = data["planet_signs"].get(chart_ruler, "")     # 命主星所在星座
    pr_house = data["planet_houses"].get(chart_ruler, 0)    # 命主星所在宮位

    # 本命盤中由命主星掌管的宮（看各宮宮首星座的守護星）
    cusp_signs = [deg_to_sign(c) for c in data["cusps"]]
    houses_ruled = [i+1 for i, s in enumerate(cusp_signs) if RULER_OF_SIGN[s] == chart_ruler]
    ruled_str = "、".join(f"第{h}宮" for h in houses_ruled) if houses_ruled else "—"

    # 提示詞（50字內要點：所在星座、所在宮、掌管宮、核心影響）
    prompts = {
        "太陽": f"用繁體中文50字說明：太陽在{data['planet_signs']['太陽']}座，第{data['planet_houses']['太陽']}宮，性格與生命能量的核心表現與課題。",
        "月亮": f"用繁體中文50字說明：月亮在{data['planet_signs']['月亮']}座，第{data['planet_houses']['月亮']}宮，情緒需求與安全感來源的表現。",
        "上升": f"用繁體中文50字說明：上升在{data['asc_sign']}座，外在形象、互動風格與他人第一印象。",
        f"命主星({chart_ruler})": (
            f"用繁體中文50字說明：命主星{chart_ruler}在{pr_sign}座，第{pr_house}宮，掌管{ruled_str}；"
            f"交代其對人格傾向、行動路徑與生命方向的影響重點。"
        ),
    }

    out: Dict[str, str] = {}
    for k, p in prompts.items():
        try:
            r = model.generate_content(p)
            out[k] = r.text.strip()
        except Exception:
            out[k] = ""
    return out

def build_positions_table(data: dict):
    planet_lons = data["planet_lons"]
    planet_signs = data["planet_signs"]
    planet_houses = data["planet_houses"]
    asc_deg, mc_deg = data["asc"], data["mc"]
    asc_sign, mc_sign = data["asc_sign"], data["mc_sign"]

    # 計算每顆行星的「守護宮」：看每宮宮首星座的守護星
    cusp_signs = [deg_to_sign(c) for c in data["cusps"]]
    ruler_to_houses: Dict[str, List[int]] = {}
    for idx, s in enumerate(cusp_signs, start=1):
        r = RULER_OF_SIGN[s]
        ruler_to_houses.setdefault(r, []).append(idx)

    def pos_str(name: str, lon_deg: float, sign: str) -> str:
        sym = SYMBOL.get(name, "")
        dd, mm = deg_to_dms_in_sign(lon_deg)
        return f"{sym} {dd:02d}°{mm:02d}′{sign}"

    rows = []

    # 主要行星與點
    items = [
        ("上升", asc_deg, asc_sign, 1, []),  # 上升固定第1宮，無守護宮
        ("太陽", planet_lons["太陽"], planet_signs["太陽"], planet_houses["太陽"], ruler_to_houses.get("太陽", [])),
        ("月亮", planet_lons["月亮"], planet_signs["月亮"], planet_houses["月亮"], ruler_to_houses.get("月亮", [])),
        ("水星", planet_lons["水星"], planet_signs["水星"], planet_houses["水星"], ruler_to_houses.get("水星", [])),
        ("金星", planet_lons["金星"], planet_signs["金星"], planet_houses["金星"], ruler_to_houses.get("金星", [])),
        ("火星", planet_lons["火星"], planet_signs["火星"], planet_houses["火星"], ruler_to_houses.get("火星", [])),
        ("木星", planet_lons["木星"], planet_signs["木星"], planet_houses["木星"], ruler_to_houses.get("木星", [])),
        ("土星", planet_lons["土星"], planet_signs["土星"], planet_houses["土星"], ruler_to_houses.get("土星", [])),
        ("天王星", planet_lons["天王星"], planet_signs["天王星"], planet_houses["天王星"], []),
        ("海王星", planet_lons["海王星"], planet_signs["海王星"], planet_houses["海王星"], []),
        ("冥王星", planet_lons["冥王星"], planet_signs["冥王星"], planet_houses["冥王星"], []),
        ("北交點", data["north_node"], data["planet_signs"]["北交點"], data["planet_houses"]["北交點"], []),
        ("南交點", data["south_node"], data["planet_signs"]["南交點"], data["planet_houses"]["南交點"], []),
        ("天頂", mc_deg, mc_sign, planet_houses["天頂"], []),
    ]

    for name, lonv, sign, house, ruled in items:
        status = "-" if name in ("上升", "天頂") else essential_dignity(name, sign)
        rows.append({
            "行星": name,
            "位置": pos_str(name, lonv, sign),
            "落宮": house,
            "守護宮": "、".join(map(str, ruled)) if ruled else "-",
            "黃道狀態": status,
        })
    return rows

# ===== 相位表：組合 / 類型 / 偏離角度 =====
def build_aspects_table(data: dict):
    # 僅十顆行星，不含上升
    names = ["太陽","月亮","水星","金星","火星","木星","土星","天王星","海王星","冥王星"]
    lons = {k: v for k, v in data["planet_lons"].items() if k in names}

    # 相位定義與容差
    # 目標排序：合相 > 三合(120) > 六合(60) > 刑(90) > 對沖(180)
    aspects = [
        ("合相", 0.0,   8.0),
        ("三合", 120.0, 7.0),
        ("六合", 60.0,  4.0),
        ("刑",   90.0,  6.0),
        ("對沖", 180.0, 8.0),
    ]
    kind_priority = {"合相":0, "三合":1, "六合":2, "刑":3, "對沖":4}

    def sep(a, b):
        d = abs((a % 360.0) - (b % 360.0))
        return d if d <= 180.0 else 360.0 - d

    rows = []
    for i in range(len(names)):
        Ai = names[i]
        if Ai not in lons: continue
        for j in range(i+1, len(names)):  # 去重
            Bj = names[j]
            if Bj not in lons: continue
            s = sep(lons[Ai], lons[Bj])
            for kind, ang, orb in aspects:
                diff = abs(s - ang)
                if diff <= orb:
                    rows.append({
                        "組合": f"{Ai}-{Bj}",
                        "類型": kind,
                        "偏離角度": round(diff, 2),
                    })
                    break  # 一對只記錄最匹配的一個相位

    # 先依類型優先級，再依偏離角度由小到大
    rows.sort(key=lambda r: (kind_priority[r["類型"]], r["偏離角度"]))
    return rows

# ===== 提取重點（落宮 / 相位） =====
def _summarize_house_focus(data: dict) -> str:
    ph = data["planet_houses"]
    order = ["太陽","月亮","水星","金星","火星","木星","土星","天王星","海王星","冥王星"]
    parts = [f"{p}第{ph[p]}宮" for p in order if p in ph]
    return "、".join(parts)

def _summarize_major_aspects(data: dict, top_n: int = 8) -> str:
    rows = build_aspects_table(data)  # 你已實作，會依類型與偏離角排序
    def fmt(r): return f"{r['組合']} {r['類型']}（Δ{r['偏離角度']}°）"
    return "、".join(map(fmt, rows[:top_n])) if rows else "無明顯主要相位"

# ===== 產生 AI 命盤分析（Markdown） =====
def build_ai_advice_md(data: dict) -> str:
    if not GEMINI_ENABLED:
        return ""

    sun = f"{data['planet_signs']['太陽']}座 第{data['planet_houses']['太陽']}宮"
    moon = f"{data['planet_signs']['月亮']}座 第{data['planet_houses']['月亮']}宮"
    asc  = f"{data['asc_sign']}座"
    house_focus = _summarize_house_focus(data)
    major_aspects = _summarize_major_aspects(data)

    prompt = f"""
你是一位專業占星解讀者。請根據以下出生星盤重點，撰寫約 400–600 字的務實分析（避免宿命論）：
- 太陽：{sun}
- 月亮：{moon}
- 上升：{asc}
- 落宮重點：{house_focus}
- 主要相位：{major_aspects}

接著說明「行星落入各宮」對生活領域可能帶來的影響（請以條列方式簡述 4–7 點，對應上文的落宮）。
最後給出具體可行的建議 3–5 條，聚焦學習、工作、人際與情緒管理。
請使用 Markdown 呈現，包含小標題與條列清單。
""".strip()

    import traceback
    system_msg = "你是精通西洋占星的中文助理，提供務實且尊重自由意志的解讀。務必使用繁體中文。"
    
    # 嘗試使用 RAG
    vector_store = get_retriever()
    if vector_store:
        print("RAG Vector Store found. Attempting augmented generation...")
        try:
            # 1. 相似度檢索
            docs = vector_store.similarity_search(prompt, k=8)
            context_text = "\n\n".join([doc.page_content for doc in docs])
            
            # 2. 構建增強後的提示詞，強制使用 Gemini 2.5 Flash
            model_name = "gemini-2.5-flash"
            llm = genai.GenerativeModel(
                model_name,
                system_instruction=system_msg + f"\n\n請根據以下提供的占星學知識庫內容輔助分析：\n\n{context_text}"
            )
            
            print(f"Invoking {model_name} with RAG context...")
            r = llm.generate_content(prompt)
            print("RAG generation successful.")
            return (r.text or "").strip()
        except Exception as e:
            print(f"RAG Generation failed, falling back to basic Gemini: {e}")
            traceback.print_exc()
    else:
        print("RAG Retriever not available (skipped or failed to init).")

    # Fallback: 無 RAG，直接呼叫原始 Gemini SDK
    try:
        print("Falling back to basic Gemini SDK...")
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            system_instruction=system_msg
        )
        r = model.generate_content(prompt)
        return (r.text or "").strip()
    except Exception as e:
        print(f"Gemini API Error (fallback): {e}")
        traceback.print_exc()
        return ""

def build_credits_md(payload: dict) -> str:
    tz = payload["geo"]["tz"]
    return f"""
    ## 🙏 引用與致謝

- 星體計算：Swiss Ephemeris（`pyswisseph`）
- 地理座標：OpenStreetMap / Nominatim 地理編碼
- 時區查詢：`timezonefinder` → IANA 時區（目前：`{tz}`）
- 時間換算：`pytz`（本地時 → UTC → 儒略日）
- 星盤繪圖：`@astrodraw/astrochart` 以 SVG 呈現星盤
- AI 模型：Google Gemini 2.5 Flash（僅在提供 API 金鑰時啟用），輸出為 Markdown
- 領域知識來源：占星之門、黃銘老師占星資料
""".strip()


def deg_to_dms_in_sign(deg: float):
    d = wrap360(deg) % 30.0
    dd = int(d)
    mm = int(round((d - dd) * 60))
    if mm == 60:
        dd += 1
        mm = 0
    return dd, mm





def essential_dignity(planet: str, sign: str) -> str:
    if planet in ("天王星", "海王星", "冥王星"):
        return "（無傳統）"
    if sign in DOMICILE.get(planet, []):
        return "入廟"
    if EXALTATION.get(planet) == sign:
        return "擢升"
    if sign in DETRIMENT.get(planet, []):
        return "失勢"
    if FALL.get(planet) == sign:
        return "落陷"
    return "一般"
# -------------------- API --------------------
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
    ai: int = Query(0, ge=0, le=1, dscription="是否產生AI解說內容 : 1=是, 0=否")
):
    geo = geocode_location(location)
    jd_ut = to_julday_utc(
        ChartInput(year=year, month=month, day=day, hour=hour, minute=minute, location=location),
        geo.tz,
    )
    HSYS = resolve_hsys(house_system)
    data = calc_chart(jd_ut, geo.lat, geo.lon, HSYS)

    interp = gemini_interpretations(data) if (GEMINI_ENABLED and ai == 1) else {}
    four_rows, chart_ruler = build_four_kings(data, interpretations=interp)
    detail_rows, summary_rows = build_element_tables(data, chart_ruler)
    houses_rows = build_houses_table(data)
    positions_rows = build_positions_table(data)  # <— 新增
    aspects_rows = build_aspects_table(data)  # <— 新增
    ai_advice_md = build_ai_advice_md(data) if (GEMINI_ENABLED and ai == 1) else "" # 可能為空字串

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
        "positions_rows": positions_rows,  # <— 新增
        "aspects_rows": aspects_rows,  # <— 新增
        "symbols": SYMBOL,
        "house_system_cn": HOUSE_SYSTEMS_CODE2CN.get(HSYS, "整宮制"),
        "ai_advice_md": ai_advice_md,               # <— 新增
        "rag_active": _qdrant_vector_store is not None, # <— 新增 RAG 狀態
    }
    payload["credits_md"] = build_credits_md(payload)
    payload["ai_generated"] = bool(ai)  # ← 可供前端判斷
    return payload