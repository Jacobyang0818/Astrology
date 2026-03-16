<p align="center">
  <img src="./logo.png" alt="Astrology Gemini Compass" width="500">
</p>

# Astrology Gemini Compass (占星雙子羅盤)

[English](./README.md) | [中文](./README.zh-tw.md)

Astrology Gemini Compass 是一個專業級的星盤計算與 RAG 增強型 AI 分析平台。它結合了高精度的天文計算與先進的檢索增強生成（RAG）系統，提供具有學理依據的專業占星指引。

---

## ✨ 核心貢獻

### 1. 高精度星盤視覺化
本專案實現了高度客製化的**星盤渲染功能**，能夠精確呈現行星位置、宮位邊界及相位表。我們將 **Swiss Ephemeris** 的原始數據轉化為直觀的 SVG 視覺體驗，讓占星師與愛好者一目了然。

### 2. RAG 增強型 AI 分析 (核心創新)
不同於一般的 AI 聊天機器人，本系統採用 **RAG (Retrieval-Augmented Generation)** 技術，讓 AI 在回答前先「翻閱」專業占星文獻。
- **本地知識庫**：使用 **Qdrant** 向量資料庫儲存專業占星指南的知識碎片。
- **專業度提升**：透過檢索特定情境的占星學理，AI (Gemini 2.5 Flash) 提供的建議比通用型 LLM 更精確、完整且具學術深度。

---

## 🚀 功能簡介
- **精確的天象計算**：使用 `pyswisseph` 獲取高精度的行星與宮位數據。
- **自動地理編碼**：自動將出生地解析為經緯度與對應時區（自動處理日光節約時間）。
- **RAG 架構**：整合 LangChain、Qdrant 與 Gemini，實現「有憑有據」的命盤解析。
- **現代化介面**：基於 React 的響應式前端，提供流暢的操作體驗。

---

## 🛠️ 技術棧
- **後端**: FastAPI (Python 3.12, 使用 UV 管理環境)
- **前端**: React (Vite)
- **向量資料庫**: Qdrant (Local Mode)
- **AI 模型**: Google Gemini 2.5 Flash + Gemini Embedding 001
- **開發框架**: LangChain + Langchain-Qdrant

---

## ⚙️ 本地開發環境設置

### 1. 前置需求
請確保您的系統已安裝 `uv` (Python 管理工具) 與 `npm` (Node.js)。

### 2. 安裝與依賴設定
```bash
# 安裝後端依賴
uv sync

# 安裝前端依賴
cd frontend
npm install
```

### 3. 建立知識庫 (RAG 核心步驟)
您需要下載以下占星指南檔案並放置於 `docs/` 資料夾中：
- [占星指南 第一部分](https://drive.google.com/file/d/151KLdRjCkaCwW4eTppCitg8vcQFU_vfd/view?usp=drive_link)
- [占星指南 第二部分](https://drive.google.com/file/d/1nSwX_pPxoOLFOeVsR_Q8XFU_vfd/view?usp=drive_link)

下載完成後，執行索引腳本：
```bash
uv run build_rag.py
```

### 4. 環境變數設定
在專案根目錄建立 `.env` 檔案：
```env
GEMINI_API_KEY=您的_API_金鑰
```

### 5. 啟動程式
**啟動後端:**
```bash
uv run uvicorn main:app --reload
```
**啟動前端:**
```bash
cd frontend
npm run dev
```

---

## 🚀 Docker 部署

### 建立映像 (Image)
```bash
docker build -t astrology-gemini-compass:latest .
```

### 執行容器
```bash
docker run -d \
  -p 8000:8000 \
  -e GEMINI_API_KEY=您的API金鑰 \
  astrology-gemini-compass:latest
```

---

## 🙏 引用與致謝
- **天體計算**: Swiss Ephemeris (`pyswisseph`)
- **地理編碼**: OpenStreetMap / Nominatim
- **RAG 知識來源**: 專業占星文獻（黃銘老師占星資料、占星之門）
- **星盤繪製**: `@astrodraw/astrochart`
- **啟發來源**: 專業西洋占星學理與計算模式。
