import React from 'react';
import { marked } from 'marked';
import { Sparkles, Info } from 'lucide-react';

const AIAdvice = ({ markdown }) => {
  if (!markdown) return null;

  const htmlContent = marked(markdown);

  return (
    <div 
      className="glass-panel animate-fade-in" 
      style={{ 
        padding: '2rem',
        border: '1px solid var(--accent-gold-glow)',
        boxShadow: '0 0 30px rgba(249, 212, 35, 0.1) inset'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <Sparkles size={28} color="var(--accent-gold)" />
        <h2 style={{ color: 'var(--accent-gold)', margin: 0 }}>AI 命盤分析建議</h2>
      </div>
      
      <div 
        className="ai-markdown"
        dangerouslySetInnerHTML={{ __html: htmlContent }} 
      />

      <style>{`
        .ai-markdown {
          color: var(--text-main);
          font-size: 1.05rem;
          line-height: 1.8;
        }
        .ai-markdown h3 {
          color: var(--accent-cyan);
          margin-top: 1.5rem;
          margin-bottom: 0.75rem;
          font-size: 1.25rem;
        }
        .ai-markdown ul {
          padding-left: 1.5rem;
          margin-bottom: 1.5rem;
        }
        .ai-markdown li {
          margin-bottom: 0.5rem;
        }
        .ai-markdown p {
          margin-bottom: 1rem;
        }
        .ai-markdown strong {
          color: var(--text-bright);
        }
      `}</style>
    </div>
  );
};

export const CreditsInfo = ({ markdown }) => {
  if (!markdown) return null;
  const htmlContent = marked(markdown);
  
  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginTop: '1rem', borderLeft: '4px solid var(--accent-blue)' }}>
       <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
        <Info size={20} color="var(--accent-blue)" />
        <h3 style={{ color: 'var(--text-main)', margin: 0, fontSize: '1.1rem' }}>系統與天文資訊</h3>
      </div>
      <div 
        className="credits-markdown"
        dangerouslySetInnerHTML={{ __html: htmlContent }} 
      />
      <style>{`
        .credits-markdown {
          color: var(--text-muted);
          font-size: 0.9rem;
          line-height: 1.6;
          text-align: left;
        }
        .credits-markdown ul {
          padding-left: 1.25rem;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }
        .credits-markdown li {
          margin-bottom: 0.25rem;
        }
        .credits-markdown p {
          margin: 0;
        }
        .credits-markdown code {
          background: rgba(0, 0, 0, 0.3);
          padding: 0.1rem 0.4rem;
          border-radius: 4px;
          color: var(--accent-cyan);
          font-family: monospace;
        }
        .credits-markdown a {
             color: var(--accent-blue);
             text-decoration: none;
        }
        .credits-markdown a:hover {
             text-decoration: underline;
        }
        .credits-markdown h2 {
             display: none; /* Hide the markdown title to use our custom header */
        }
      `}</style>
    </div>
  );
};

export default AIAdvice;
