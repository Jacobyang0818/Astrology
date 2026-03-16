import swisseph as swe
from typing import Dict, List

ZODIAC_CN = [
    "牡羊", "金牛", "雙子", "巨蟹", "獅子", "處女",
    "天秤", "天蠍", "射手", "魔羯", "水瓶", "雙魚"
]

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

EXALTATION = {  # 擢升
    "太陽": "牡羊", "月亮": "金牛", "水星": "處女",
    "金星": "雙魚", "火星": "魔羯", "木星": "巨蟹", "土星": "天秤",
}

def sign_opposite(sign: str) -> str:
    idx = ZODIAC_CN.index(sign)
    return ZODIAC_CN[(idx + 6) % 12]

def wrap360(x: float) -> float:
    x = x % 360.0
    return x if x >= 0 else x + 360.0

def deg_to_sign(deg: float) -> str:
    import math
    idx = int(math.floor((deg % 360.0) / 30.0))
    return ZODIAC_CN[idx]

# 入廟：由 RULER_OF_SIGN 反推
DOMICILE: Dict[str, List[str]] = {}
for s, r in RULER_OF_SIGN.items():
    DOMICILE.setdefault(r, []).append(s)

DETRIMENT = {p: [sign_opposite(s) for s in signs] for p, signs in DOMICILE.items()}
FALL = {p: sign_opposite(s) for p, s in EXALTATION.items()}

# -------------------- Traditional Dignities Helper --------------------
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
