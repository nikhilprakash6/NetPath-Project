import React, { useState } from 'react';
import './NetworkPathGraph.css';

const NetworkPathGraph = ({ hops }) => {
  const [hoveredNode, setHoveredNode] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const handleNodeHover = (event, hop) => {
    setHoveredNode(hop);
    setTooltipPosition({
      x: event.clientX + 10,
      y: event.clientY - 10
    });
  };

  const handleNodeLeave = () => {
    setHoveredNode(null);
  };

  if (!hops || hops.length === 0) {
    return (
      <div className="graph-container">
        <div className="no-data-message">
          No network path data available. Run a traceroute to see the graph.
        </div>
      </div>
    );
  }

  return (
    <div className="graph-container">
      <div className="graph-header">
        <h3>Network Path Visualization</h3>
        <div className="legend">
          <div className="legend-item">
            <div className="legend-color source"></div>
            <span>Source</span>
          </div>
          <div className="legend-item">
            <div className="legend-color intermediate"></div>
            <span>Intermediate</span>
          </div>
          <div className="legend-item">
            <div className="legend-color destination"></div>
            <span>Destination</span>
          </div>
        </div>
      </div>
      
      <div className="graph-content">
        <div className="path-container">
          {hops.map((hop, index) => (
            <React.Fragment key={hop.hop}>
              <div
                className={`path-node ${
                  index === 0 ? 'source' : 
                  index === hops.length - 1 ? 'destination' : 'intermediate'
                }`}
                onMouseEnter={(e) => handleNodeHover(e, hop)}
                onMouseLeave={handleNodeLeave}
              >
                <div className="node-content">
                  <div className="hop-number">Hop {hop.hop}</div>
                  <div className="ip-address">{hop.ip}</div>
                  {hop.hostname && hop.hostname !== 'Unknown' && (
                    <div className="hostname">{hop.hostname}</div>
                  )}
                </div>
              </div>
              
              {index < hops.length - 1 && (
                <div className="path-connection">
                  <div className="connection-line"></div>
                  <div className="connection-arrow"></div>
                  {hops[index + 1].rtt && hops[index + 1].rtt.length > 0 && (
                    <div className="rtt-label">
                      {hops[index + 1].rtt.reduce((a, b) => a + b, 0) / hops[index + 1].rtt.length}ms
                    </div>
                  )}
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Tooltip */}
      {hoveredNode && (
        <div 
          className="tooltip"
          style={{
            left: tooltipPosition.x,
            top: tooltipPosition.y
          }}
        >
          <div className="tooltip-header">
            <strong>Hop {hoveredNode.hop}</strong>
          </div>
          <div className="tooltip-content">
            <div className="tooltip-row">
              <span className="tooltip-label">IP Address:</span>
              <span className="tooltip-value">{hoveredNode.ip}</span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">Hostname:</span>
              <span className="tooltip-value">{hoveredNode.hostname || 'N/A'}</span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">Location:</span>
              <span className="tooltip-value">{hoveredNode.geo || 'N/A'}</span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">AS Info:</span>
              <span className="tooltip-value">{hoveredNode.as || 'N/A'}</span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">Avg RTT:</span>
              <span className="tooltip-value">
                {hoveredNode.rtt && hoveredNode.rtt.length > 0 
                  ? `${(hoveredNode.rtt.reduce((a, b) => a + b, 0) / hoveredNode.rtt.length).toFixed(2)}ms`
                  : 'N/A'
                }
              </span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">Packet Loss:</span>
              <span className="tooltip-value">{hoveredNode.loss}%</span>
            </div>
            <div className="tooltip-row">
              <span className="tooltip-label">RTT Values:</span>
              <span className="tooltip-value">
                {hoveredNode.rtt && hoveredNode.rtt.length > 0 
                  ? hoveredNode.rtt.map(rtt => `${rtt}ms`).join(', ')
                  : 'N/A'
                }
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NetworkPathGraph; 