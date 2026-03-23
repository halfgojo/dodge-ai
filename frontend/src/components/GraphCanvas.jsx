import React, { useRef, useEffect, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { X } from 'lucide-react';

const colors = {
  Customer: "#58a6ff",
  SalesOrder: "#bc8cff",
  Delivery: "#3fb950",
  Invoice: "#d29922",
  JournalEntry: "#fa4549",
  Product: "#2ea043"
};

export default function GraphCanvas({ graphData }) {
  const fgRef = useRef();
  const [selectedNode, setSelectedNode] = useState(null);
  const [dimensions, setDimensions] = useState({ width: window.innerWidth - 400, height: window.innerHeight });

  useEffect(() => {
    const handleResize = () => setDimensions({ width: window.innerWidth - 400, height: window.innerHeight });
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleNodeClick = useCallback(node => {
    setSelectedNode(node);
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 1000);
      fgRef.current.zoom(2.5, 2000);
    }
  }, []);

  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null);
    if (fgRef.current) {
      fgRef.current.zoomToFit(400);
    }
  }, []);

  const nodeColor = useCallback(node => {
    return selectedNode && node.id === selectedNode.id ? '#ffffff' : (colors[node.type] || '#8b949e');
  }, [selectedNode]);

  return (
    <div className="graph-pane" style={{ width: '100%', height: '100%' }}>
      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeLabel="label"
        nodeColor={nodeColor}
        nodeRelSize={6}
        linkColor={() => 'rgba(88, 166, 255, 0.2)'}
        linkWidth={1.5}
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={1}
        onNodeClick={handleNodeClick}
        onBackgroundClick={handleBackgroundClick}
        enableNodeDrag={true}
        d3VelocityDecay={0.6}
        cooldownTicks={100}
      />
      
      {selectedNode && (
        <div className="node-modal">
          <div className="modal-header">
            <h3>{selectedNode.type} Details</h3>
            <button className="close-btn" onClick={() => setSelectedNode(null)}><X size={18} /></button>
          </div>
          <div className="node-type-badge" style={{ backgroundColor: colors[selectedNode.type] || '#8b949e' }}>
            {selectedNode.label}
          </div>
          <div className="node-props">
            {Object.entries(selectedNode)
              .filter(([key]) => !['id', 'x', 'y', 'vx', 'vy', 'index', 'type', 'label'].includes(key))
              .map(([key, val]) => (
                <div className="node-prop" key={key}>
                  <div className="prop-key">{key}</div>
                  <div className="prop-val">{typeof val === 'object' ? JSON.stringify(val) : String(val)}</div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
