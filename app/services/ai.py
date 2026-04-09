import os
import traceback
import google.generativeai as genai
from typing import Dict, Optional
from ..constants import RULER_OF_SIGN
from ..core.astrology import deg_to_sign
from .rag import get_retriever

def gemini_interpretations(data: dict, gemini_enabled: bool) -> Dict[str, str]:
    if not gemini_enabled:
        return {}
        
    model = genai.GenerativeModel("gemini-2.5-flash")
    asc_sign = data["asc_sign"]
    chart_ruler = RULER_OF_SIGN[asc_sign]
    pr_sign = data["planet_signs"].get(chart_ruler, "")
    pr_house = data["planet_houses"].get(chart_ruler, 0)

    cusp_signs = [deg_to_sign(c) for c in data["cusps"]]
    houses_ruled = [i+1 for i, s in enumerate(cusp_signs) if RULER_OF_SIGN[s] == chart_ruler]
    ruled_str = "、".join(f"第{h}宮" for h in houses_ruled) if houses_ruled else "—"

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

def build_ai_advice_md(data: dict, gemini_enabled: bool, house_summary: str, aspect_summary: str) -> str:
    if not gemini_enabled:
        return ""

    sun = f"{data['planet_signs']['太陽']}座 第{data['planet_houses']['太陽']}宮"
    moon = f"{data['planet_signs']['月亮']}座 第{data['planet_houses']['月亮']}宮"
    asc  = f"{data['asc_sign']}座"

    prompt = f"""
你是一位專業占星解讀者。請根據以下出生星盤重點，撰寫約 400–600 字的務實分析（避免宿命論）：
- 太陽：{sun}
- 月亮：{moon}
- 上升：{asc}
- 落宮重點：{house_summary}
- 主要相位：{aspect_summary}

接著說明「行星落入各宮」對生活領域可能帶來的影響（請以條列方式簡述 4–7 點，對應上文的落宮）。
最後給出具體可行的建議 3–5 條，聚焦學習、工作、人際與情緒管理。
請使用 Markdown 呈現，包含小標題與條列清單。
""".strip()

    system_msg = "你是精通西洋占星的中文助理，提供務實且尊重自由意志的解讀。務必使用繁體中文。"
    
    retriever = get_retriever(gemini_enabled)
    if retriever:
        try:
            docs = retriever.invoke(prompt)
            context_text = "\n\n".join([doc.page_content for doc in docs])
            
            model_name = "gemini-2.5-flash"
            llm = genai.GenerativeModel(
                model_name,
                system_instruction=system_msg + f"\n\n請根據以下提供的占星學知識庫內容輔助分析：\n\n{context_text}"
            )
            r = llm.generate_content(prompt)
            return (r.text or "").strip()
        except Exception as e:
            print(f"RAG Generation failed: {e}")
            traceback.print_exc()

    try:
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_msg)
        r = model.generate_content(prompt)
        return (r.text or "").strip()
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return ""

def build_credits_md(tz: str) -> str:
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
