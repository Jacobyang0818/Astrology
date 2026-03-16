import React from 'react';

const DataTable = ({ title, columns, data }) => {
  if (!data || data.length === 0) return null;

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', height: '100%' }}>
      <h3 style={{ marginBottom: '1rem', color: 'var(--text-bright)', fontSize: '1.25rem' }}>{title}</h3>
      <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-sm)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr>
              {columns.map((col, i) => (
                <th 
                  key={i} 
                  style={{ 
                    padding: '1rem', 
                    background: 'rgba(255, 255, 255, 0.05)', 
                    color: 'var(--text-muted)',
                    fontWeight: '600',
                    borderBottom: '2px solid var(--panel-border)',
                    whiteSpace: 'nowrap'
                  }}
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr 
                key={i} 
                style={{ 
                  borderBottom: '1px solid var(--panel-border)',
                  background: i % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.02)',
                  transition: 'background 0.2s',
                  cursor: 'default'
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)'}
                onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.02)'}
              >
                {columns.map((col, j) => (
                  <td 
                    key={j} 
                    style={{ 
                      padding: '1rem', 
                      color: 'var(--text-main)',
                      fontSize: '0.95rem'
                    }}
                  >
                    {row[col] || row[col.toLowerCase()] || '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataTable;
