import math
from typing import Dict, List, Optional
from ..constants import (
    ZODIAC_CN, ELEMENT_OF_SIGN, RULER_OF_SIGN,
    SYMBOL, SCORES, ITEM_ORDER, HOUSE_NAMES,
    HOUSE_MEANINGS, essential_dignity, wrap360
)
from ..core.astrology import deg_to_sign

def deg_to_dms_in_sign(deg: float):
    d = wrap360(deg) % 30.0
    dd = int(d)
    mm = int(round((d - dd) * 60))
    if mm == 60:
        dd += 1
        mm = 0
    return dd, mm

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

    summary_rows = [
        {"元素": "地", "簡介": "實際、感官、務實、責任", "總分": element_totals["地"]},
        {"元素": "水", "簡介": "情感、感覺、精神、同理、體諒、心靈", "總分": element_totals["水"]},
        {"元素": "火", "簡介": "直接、行動力、積極、急躁、坦率、粗魯、沒心機、直覺", "總分": element_totals["火"]},
        {"元素": "風", "簡介": "理性、公平、抽象思考、社交、文化涵養、知性交流", "總分": element_totals["風"]},
    ]

    return detail_rows, summary_rows

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

def build_positions_table(data: dict):
    planet_lons = data["planet_lons"]
    planet_signs = data["planet_signs"]
    planet_houses = data["planet_houses"]
    asc_deg, mc_deg = data["asc"], data["mc"]
    asc_sign, mc_sign = data["asc_sign"], data["mc_sign"]

    cusp_signs = [deg_to_sign(c) for c in data["cusps"]]
    ruler_to_houses: Dict[str, List[int]] = {}
    for idx, s in enumerate(cusp_signs, start=1):
        r = RULER_OF_SIGN[s]
        ruler_to_houses.setdefault(r, []).append(idx)

    def pos_str(p_name: str, lon_deg: float, sign: str) -> str:
        sym = SYMBOL.get(p_name, "")
        dd, mm = deg_to_dms_in_sign(lon_deg)
        return f"{sym} {dd:02d}°{mm:02d}′{sign}"

    rows = []
    items = [
        ("上升", asc_deg, asc_sign, 1, []),
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

def build_aspects_table(data: dict):
    names = ["太陽","月亮","水星","金星","火星","木星","土星","天王星","海王星","冥王星"]
    lons = {k: v for k, v in data["planet_lons"].items() if k in names}

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
        for j in range(i+1, len(names)):
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
                    break

    rows.sort(key=lambda r: (kind_priority[r["類型"]], r["偏離角度"]))
    return rows

def summarize_house_focus(data: dict) -> str:
    ph = data["planet_houses"]
    order = ["太陽","月亮","水星","金星","火星","木星","土星","天王星","海王星","冥王星"]
    parts = [f"{p}第{ph[p]}宮" for p in order if p in ph]
    return "、".join(parts)

def summarize_major_aspects(data: dict, top_n: int = 8) -> str:
    rows = build_aspects_table(data)
    def fmt(r): return f"{r['組合']} {r['類型']}（Δ{r['偏離角度']}°）"
    return "、".join(map(fmt, rows[:top_n])) if rows else "無明顯主要相位"
