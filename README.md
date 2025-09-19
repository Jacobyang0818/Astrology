# Astrology Chart Web App

這是一個以 **FastAPI** + **Swiss Ephemeris (pyswisseph)** 開發的星盤計算與展示服務。  
前端採用 **AstroChart.js** 繪製星盤，並呈現行星位置、宮位狀態、相位表等資訊。  
若有提供 Gemini API 金鑰，還能生成 **AI 命盤分析建議**（Markdown 格式）。

---

## ✨功能簡介
- 輸入出生年月日時分與地點，自動透過 Nominatim 解析經緯度與時區。
- 使用 Swiss Ephemeris 計算行星、宮位、上升、天頂等關鍵點。
- 前端星盤繪製（含相位、行星度數、宮位）。
- 表格輸出：四大天王表、元素總表、宮位狀態、行星位置、相位表。
- （可選）Google Gemini AI：提供 400–600 字性格與建議分析，並輸出 Markdown。

---

## ⚙️使用方式

### 1. 安裝需求
```bash
uv sync
```

（會根據 `pyproject.toml` 自動安裝所需套件。）

### 2. 啟動伺服器
```bash
uv run uvicorn main:app --reload
```

預設會在 <http://127.0.0.1:8000> 提供前端介面。

### 3. 操作步驟
1. 在首頁表單輸入 **年/月/日/時/分** 與 **出生地**。  
2. 點擊「計算」後，頁面會顯示：
   - 星盤圖（含相位）
   - 四大天王表
   - 元素總表與明細
   - 宮位狀態
   - 行星位置
   - 相位表
   - （若啟用 AI）AI 命盤分析建議  
3. 表格內容可直接閱讀，AI 分析與致謝則以 Markdown 呈現。

---

## 🤖啟用 Gemini AI
1. 在專案根目錄建立 `.env` 檔案。  
2. 加入以下內容（請替換成你自己的 API Key）：  
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
3. 重新啟動伺服器。  
4. 此時 `/api/chart` 的回傳資料會多出 `ai_advice_md` 欄位，前端會顯示「AI命盤分析建議」。

---

## 🙏引用與致謝
- 星體計算：Swiss Ephemeris（`pyswisseph`）
- 地理座標：OpenStreetMap / Nominatim
- 時區查詢：`timezonefinder` → IANA 時區
- 時間換算：`pytz`（本地時間 → UTC → 儒略日）
- 星盤繪圖：`@astrodraw/astrochart`（SVG 呈現）
- AI 模型：Google Gemini 1.5 Flash（僅在提供 API 金鑰時啟用，輸出 Markdown 格式）
- 參考專案：[AllanYiin's Project](https://github.com/AllanYiin/VibeChallenge49/tree/master)
- 領域知識來源：占星之門、黃銘老師占星資料
