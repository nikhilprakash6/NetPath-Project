import React, { useState } from 'react';
import './App.css';
import NetworkPathGraph from './NetworkPathGraph';

function App() {
  const [destination, setDestination] = useState('');
  const [hops, setHops] = useState([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'graph'

  const traceRoute = async () => {
    setLoading(true);
    setHops([]);
    try {
      const response = await fetch(`/trace/${destination || '8.8.8.8'}`);
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      setHops(data);
    } catch (error) {
      console.error('Error fetching trace:', error);
      alert('Error running traceroute. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>NetPath Project</h1>
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          value={destination}
          onChange={(e) => setDestination(e.target.value)}
          placeholder="Enter destination (e.g., 8.8.8.8)"
          style={{ padding: '8px', marginRight: '10px', width: '200px' }}
          disabled={loading}
        />
        <button
          onClick={traceRoute}
          disabled={loading}
          style={{
            padding: '8px 16px',
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            marginRight: '10px',
          }}
        >
          {loading ? 'Tracing...' : 'Trace Route'}
        </button>
      </div>

      {hops.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div className="view-toggle-container">
            <button
              onClick={() => setViewMode('table')}
              className={`view-toggle-button ${viewMode === 'table' ? 'active' : ''}`}
            >
              Table View
            </button>
            <button
              onClick={() => setViewMode('graph')}
              className={`view-toggle-button ${viewMode === 'graph' ? 'active' : ''}`}
            >
              Graph View
            </button>
          </div>

          {viewMode === 'table' && (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f2f2f2' }}>
                  <th style={{ border: '1px solid #ddd', padding: '8px' }}>Hop</th>
                  <th style={{ border: '1px solid #ddd', padding: '8px' }}>IP</th>
                  <th style={{ border: '1px solid #ddd', padding: '8px' }}>Hostname</th>
                  <th style={{ border: '1px solid #ddd', padding: '8px' }}>RTTs (ms)</th>
                  <th style={{ border: '1px solid #ddd', padding: '8px' }}>Avg RTT (ms)</th>
                  <th style={{ border: '1px solid #ddd', padding: '8px' }}>Packet Loss</th>
                  <th style={{ border: '1px solid #ddd', padding: '8px' }}>Geo</th>
                  <th style={{ border: '1px solid #ddd', padding: '8px' }}>AS Info</th>
                </tr>
              </thead>
              <tbody>
                {hops.map(hop => (
                  <tr key={hop.hop}>
                    <td style={{ border: '1px solid #ddd', padding: '8px' }}>{hop.hop}</td>
                    <td style={{ border: '1px solid #ddd', padding: '8px' }}>{hop.ip}</td>
                    <td style={{ border: '1px solid #ddd', padding: '8px' }}>{hop.hostname}</td>
                    <td style={{ border: '1px solid #ddd', padding: '8px' }}>{hop.rtt.length ? hop.rtt.join(', ') : 'N/A'}</td>
                    <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                      {hop.rtt.length ? (hop.rtt.reduce((a, b) => a + b, 0) / hop.rtt.length).toFixed(2) : 'N/A'}
                    </td>
                    <td style={{ border: '1px solid #ddd', padding: '8px' }}>{hop.loss}%</td>
                    <td style={{ border: '1px solid #ddd', padding: '8px' }}>{hop.geo}</td>
                    <td style={{ border: '1px solid #ddd', padding: '8px' }}>{hop.as}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {viewMode === 'graph' && (
            <NetworkPathGraph hops={hops} />
          )}
        </div>
      )}
    </div>
  );
}

export default App;
