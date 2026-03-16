import { useState, useCallback } from 'react';
import axios from 'axios';
import { Loader2, AlertCircle } from 'lucide-react';
import InputForm from './components/InputForm';
import DataTable from './components/DataTable';
import AIAdvice, { CreditsInfo } from './components/AIAdvice';
import CustomAstroChart from './components/CustomAstroChart';

function App() {
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chartData, setChartData] = useState(null);

  const fetchChart = useCallback(async (formData, useAI) => {
    // If we already have chart data and just want AI, use the specialized aiLoading state
    if (useAI && chartData) {
      setAiLoading(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const { year, month, day, hour, minute, location, house_system } = formData;
      const response = await axios.get('/api/chart', {
        params: {
          year, month, day, hour, minute, location, house_system, ai: useAI ? 1 : 0
        }
      });
      setChartData(response.data);
    } catch (err) {
      console.error(err);
      setError('獲取星盤資料失敗，請確認地點與時間格式。');
    } finally {
      setLoading(false);
      setAiLoading(false);
    }
  }, [chartData]);

  const handleCalculate = (data) => fetchChart(data, false);
  const handleGenerateAI = (data) => fetchChart(data, true);

  return (
    <div className="app-container" style={{ position: 'relative' }}>
      
      {/* Full screen AI loading overlay */}
      {aiLoading && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)',
          display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
          zIndex: 9999, color: 'var(--accent-gold)'
        }}>
          <Loader2 size={64} className="animate-spin" style={{ animation: 'slowSpin 1.5s linear infinite' }} />
          <h2 style={{ marginTop: '1rem', color: 'var(--accent-gold)', textShadow: '0 0 10px rgba(249, 212, 35, 0.5)' }}>
            Gemini AI 星盤解讀生成中...
          </h2>
          <p style={{ color: 'var(--text-main)' }}>這通常需要大約 5 ~ 10 秒鐘</p>
        </div>
      )}

      <header style={{ textAlign: 'center', marginBottom: '1rem', marginTop: '1rem' }}>
        <h1 style={{ 
          background: 'linear-gradient(to right, var(--accent-cyan), var(--accent-gold))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          fontSize: '3rem',
          letterSpacing: '2px',
          textShadow: '0 0 20px rgba(0,229,255,0.2)'
        }}>Astrology Gemini Compass</h1>
        <p style={{ color: 'var(--text-muted)' }}>專業星盤計算與 AI 命盤解讀</p>
      </header>

      <InputForm 
        onCalculate={handleCalculate} 
        onGenerateAI={handleGenerateAI} 
        isLoading={loading || aiLoading} 
      />

      {error && (
        <div className="glass-panel" style={{ padding: '1.5rem', border: '1px solid var(--status-bad)', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--status-bad)' }}>
          <AlertCircle size={24} /> {error}
        </div>
      )}

      {loading && !chartData && (
         <div style={{ display: 'flex', justifyContent: 'center', margin: '4rem 0' }}>
            <Loader2 size={48} className="animate-spin" style={{ animation: 'slowSpin 1.5s linear infinite', color: 'var(--accent-cyan)' }} />
         </div>
      )}

      {chartData && (
        <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          <div className="grid-cols-2">
            {/* Left: Chart SVG */}
            <CustomAstroChart chartData={chartData} />

            {/* Right: Quick Stats */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
               <div className="glass-panel" style={{ padding: '1.5rem' }}>
                  <h3 style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>座標資訊</h3>
                  <div style={{ fontSize: '1.1rem', color: 'var(--text-bright)' }}>
                     緯度 {chartData.geo.lat.toFixed(4)}° / 經度 {chartData.geo.lon.toFixed(4)}°<br/>
                     <span style={{ fontSize: '0.9rem', color: 'var(--accent-cyan)' }}>時區 {chartData.geo.tz}</span>
                  </div>
               </div>
               <DataTable title="四大天王表" columns={["項目", "宮位", "屬性", "說明"]} data={chartData.four_kings} />
               <DataTable title="元素總表" columns={["元素", "簡介", "總分"]} data={chartData.summary_rows} />
            </div>
          </div>

          <DataTable title="元素明細" columns={["Item", "Symbol", "Constellation", "Element", "Score"]} data={chartData.detail_rows} />
          
          <div className="grid-cols-2">
            <DataTable title="宮位狀態" columns={["宮位", "宮名", "宮位星座", "宮中行星"]} data={chartData.houses_rows} />
            <DataTable 
              title="行星狀況" 
              columns={["行星", "位置", "落宮", "守護宮", "黃道狀態"]} 
              data={chartData.positions_rows.map(row => ({
                ...row,
                "行星": `${chartData.symbols[row["行星"]] || ''} ${row["行星"]}`
              }))} 
            />
          </div>

          <DataTable title="相位表" columns={["組合", "類型", "偏離角度"]} data={chartData.aspects_rows} />
          
          {chartData.ai_generated && (
             chartData.ai_advice_md ? 
               <AIAdvice markdown={chartData.ai_advice_md} />
             :
               <div className="glass-panel" style={{ padding: '2rem', border: '1px solid var(--accent-gold)' }}>
                 <h2 style={{ color: 'var(--accent-gold)', marginBottom: '1rem' }}>AI 命盤建議產生失敗</h2>
                 <p style={{ color: 'var(--text-main)' }}>
                   無法取得 Gemini 的解析。請確認後端是否正確載入 <code>GEMINI_API_KEY</code> 環境變數，或是網路連線是否正常。
                 </p>
               </div>
          )}

          <CreditsInfo markdown={chartData.credits_md} />

        </div>
      )}
    </div>
  );
}

export default App;
