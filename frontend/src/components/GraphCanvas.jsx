import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { X, Network } from 'lucide-react';

const TYPE_COLORS = {
  Customer:       "#3b82f6",
  SalesOrder:     "#8b5cf6",
  SalesOrderItem: "#a78bfa",
  Delivery:       "#22c55e",
  Invoice:        "#f59e0b",
  JournalEntry:   "#ef4444",
  Payment:        "#06b6d4",
  Product:        "#10b981",
};

export default function GraphCanvas({ graphData }) {
  const fgRef = useRef();
  const [selectedNode, setSelectedNode] = useState(null);
  const [dimensions, setDimensions] = useState({ width: window.innerWidth - 420, height: window.innerHeight });

  useEffect(() => {
    const handleResize = () => setDimensions({ width: window.innerWidth - 420, height: window.innerHeight });
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Zoom to fit once data loads
  useEffect(() => {
    if (graphData.nodes.length > 0 && fgRef.current) {
      setTimeout(() => fgRef.current.zoomToFit(400, 60), 500);
    }
  }, [graphData]);

  const handleNodeClick = useCallback(node => {
    setSelectedNode(node);
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 800);
      fgRef.current.zoom(3, 1000);
    }
  }, []);

  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const nodeCanvasObject = useCallback((node, ctx, globalScale) => {
    const isSelected = selectedNode && node.id === selectedNode.id;
    const color = TYPE_COLORS[node.type] || '#6b7280';
    const size = isSelected ? 7 : 5;
    
    // Glow effect for selected
    if (isSelected) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI);
      ctx.fillStyle = color + '40';
      ctx.fill();
    }

    // Node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = isSelected ? '#ffffff' : color + '80';
    ctx.lineWidth = isSelected ? 2 : 1;
    ctx.stroke();

    // Label (only at sufficient zoom)
    if (globalScale > 1.2) {
      const label = node.label || node.id;
      const fontSize = Math.max(10 / globalScale, 2);
      ctx.font = `${fontSize}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = isSelected ? '#ffffff' : '#8b949e';
      ctx.fillText(label, node.x, node.y + size + 2);
    }
  }, [selectedNode]);

  const nodeConnections = useMemo(() => {
    if (!selectedNode) return 0;
    return graphData.links.filter(l => {
      const src = typeof l.source === 'object' ? l.source.id : l.source;
      const tgt = typeof l.target === 'object' ? l.target.id : l.target;
      return src === selectedNode.id || tgt === selectedNode.id;
    }).length;
  }, [selectedNode, graphData.links]);

  const excludedKeys = new Set(['id', 'x', 'y', 'vx', 'vy', 'index', 'type', 'label', '__indexColor']);

  // Legend items from types present in data
  const legendItems = useMemo(() => {
    const types = new Set(graphData.nodes.map(n => n.type));
    return Object.entries(TYPE_COLORS).filter(([t]) => types.has(t));
  }, [graphData.nodes]);

  return (
    <div className="graph-pane">
      <div className="graph-header">
        <h1><Network size={20} /> <span>Mapping</span> / Order to Cash</h1>
      </div>

      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeCanvasObject={nodeCanvasObject}
        nodePointerAreaPaint={(node, color, ctx) => {
          ctx.beginPath();
          ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        linkColor={() => 'rgba(99, 102, 241, 0.12)'}
        linkWidth={1}
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
        linkDirectionalArrowColor={() => 'rgba(99, 102, 241, 0.3)'}
        onNodeClick={handleNodeClick}
        onBackgroundClick={handleBackgroundClick}
        enableNodeDrag={true}
        d3VelocityDecay={0.4}
        cooldownTicks={200}
        warmupTicks={100}
      />

      <div className="graph-legend">
        {legendItems.map(([type, color]) => (
          <div className="legend-item" key={type}>
            <div className="legend-dot" style={{ backgroundColor: color }} />
            {type}
          </div>
        ))}
      </div>
      
      {selectedNode && (
        <div className="node-modal">
          <div className="modal-header">
            <h3>{selectedNode.type}</h3>
            <button className="close-btn" onClick={() => setSelectedNode(null)}><X size={16} /></button>
          </div>
          <div className="node-type-badge" style={{ backgroundColor: TYPE_COLORS[selectedNode.type] || '#6b7280' }}>
            {selectedNode.label}
          </div>
          <div className="node-props">
            {Object.entries(selectedNode)
              .filter(([key]) => !excludedKeys.has(key))
              .map(([key, val]) => (
                <div className="node-prop" key={key}>
                  <div className="prop-key">{key}</div>
                  <div className="prop-val">{val === null || val === undefined ? '—' : typeof val === 'object' ? JSON.stringify(val) : String(val)}</div>
                </div>
              ))}
          </div>
          <div className="connections-badge">
            🔗 {nodeConnections} connection{nodeConnections !== 1 ? 's' : ''}
          </div>
        </div>
      )}
    </div>
  );
}
