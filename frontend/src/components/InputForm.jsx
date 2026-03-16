import { useState, useEffect } from 'react';
import { Calendar, Clock, MapPin } from 'lucide-react';

const InputForm = ({ onCalculate, onGenerateAI, isLoading }) => {
  const [formData, setFormData] = useState({
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    day: new Date().getDate(),
    hour: 12,
    minute: 0,
    house_system: '整宮制',
    location: '台北'
  });

  const [daysInMonth, setDaysInMonth] = useState(31);

  useEffect(() => {
    // Calculate days in month
    const d = new Date(formData.year, formData.month, 0).getDate();
    setDaysInMonth(d);
    if (formData.day > d) {
      setFormData(prev => ({ ...prev, day: d }));
    }
  }, [formData.year, formData.month]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleCalc = () => onCalculate(formData);
  const handleAI = () => onGenerateAI(formData);

  const years = Array.from({length: 150}, (_, i) => new Date().getFullYear() - i + 50).reverse();
  const months = Array.from({length: 12}, (_, i) => i + 1);
  const days = Array.from({length: daysInMonth}, (_, i) => i + 1);
  const hours = Array.from({length: 24}, (_, i) => i);
  const minutes = Array.from({length: 60}, (_, i) => i);
  const houseSystems = ['整宮制', '等宮制', '普拉西杜斯', '柯赫', '坎帕納斯', '雷吉歐蒙塔納斯', '波菲利', '阿卡彼特'];

  return (
    <div className="glass-panel" style={{ padding: '2rem' }}>
      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#ffffff' }}>
        <Calendar size={24} color="var(--accent-cyan)" /> 星盤參數設定
      </h2>
      
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        
        {/* Date Row */}
        <div style={{ display: 'flex', gap: '0.5rem', flex: '1 1 auto', alignItems: 'center' }}>
          <select name="year" value={formData.year} onChange={handleChange} className="input-field">
            {years.map(y => <option key={y} value={y}>{y}年</option>)}
          </select>
          <select name="month" value={formData.month} onChange={handleChange} className="input-field">
            {months.map(m => <option key={m} value={m}>{m}月</option>)}
          </select>
          <select name="day" value={formData.day} onChange={handleChange} className="input-field">
            {days.map(d => <option key={d} value={d}>{d}日</option>)}
          </select>
        </div>

        {/* Time Row */}
        <div style={{ display: 'flex', gap: '0.5rem', flex: '1 1 auto', alignItems: 'center' }}>
          <Clock size={20} color="var(--text-muted)" />
          <select name="hour" value={formData.hour} onChange={handleChange} className="input-field">
            {hours.map(h => <option key={h} value={h}>{String(h).padStart(2, '0')}</option>)}
          </select>
          <span>:</span>
          <select name="minute" value={formData.minute} onChange={handleChange} className="input-field">
            {minutes.map(m => <option key={m} value={m}>{String(m).padStart(2, '0')}</option>)}
          </select>
        </div>

        {/* Location & Houses */}
        <div style={{ display: 'flex', gap: '0.5rem', flex: '2 1 auto', alignItems: 'center' }}>
           <MapPin size={20} color="var(--text-muted)" />
           <input 
             type="text" 
             name="location" 
             value={formData.location} 
             onChange={handleChange} 
             placeholder="出生地 (如: 台北)"
             className="input-field"
             style={{ flex: 1 }}
           />
           <select name="house_system" value={formData.house_system} onChange={handleChange} className="input-field">
             {houseSystems.map(h => <option key={h} value={h}>{h}</option>)}
           </select>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
        <button 
          onClick={handleCalc} 
          disabled={isLoading}
          className="btn-primary"
        >
          {isLoading ? '計算中...' : '計算星盤'}
        </button>
        <button 
          onClick={handleAI} 
          disabled={isLoading}
          className="btn-ai"
        >
          {isLoading ? '生成中...' : '產生 AI 命盤建議'}
        </button>
      </div>

      <style>{`
        .input-field {
          background: rgba(0,0,0,0.3);
          border: 1px solid var(--panel-border);
          color: var(--text-main);
          padding: 0.6rem 1rem;
          border-radius: var(--radius-sm);
          font-family: 'Inter', sans-serif;
          font-size: 1rem;
          outline: none;
          transition: all 0.2s ease;
        }
        .input-field:focus {
          border-color: var(--accent-cyan);
          box-shadow: 0 0 0 2px var(--accent-cyan-glow);
        }
        option { 
          background: var(--bg-deep); 
          color: white; 
        }
        
        .btn-primary, .btn-ai {
          padding: 0.8rem 1.5rem;
          border: none;
          border-radius: var(--radius-sm);
          font-family: 'Outfit', sans-serif;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .btn-primary {
          background: linear-gradient(135deg, var(--accent-cyan), #0099cc);
          color: #000;
          box-shadow: 0 4px 15px var(--accent-cyan-glow);
        }
        .btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(0, 229, 255, 0.4);
        }
        .btn-ai {
          background: linear-gradient(135deg, var(--accent-gold), #cc8800);
          color: #000;
          box-shadow: 0 4px 15px var(--accent-gold-glow);
        }
        .btn-ai:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(249, 212, 35, 0.4);
        }
        button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none !important;
        }
      `}</style>
    </div>
  );
};

export default InputForm;
