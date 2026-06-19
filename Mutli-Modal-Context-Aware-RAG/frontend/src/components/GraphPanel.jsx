import { useMemo, useState, useCallback, useEffect } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Heading1, FileText, Table2, Image as ImageIcon } from 'lucide-react'
import axios from 'axios'
import NodeDetails from './NodeDetails.jsx'
import './GraphPanel.css'

const TYPE_ICON = {
  heading: Heading1,
  paragraph: FileText,
  table: Table2,
  figure: ImageIcon,
}

function layoutNodes(nodes, edges) {
  const childrenMap = {}
  edges.forEach((e) => {
    childrenMap[e.source] = childrenMap[e.source] || []
    childrenMap[e.source].push(e.target)
  })

  // If no heading, treat all nodes as roots
  let roots = nodes.filter((n) => n.type === 'heading')
  if (roots.length === 0) {
      roots = nodes.slice(0, 5) // Fallback to avoid infinite loop
  }

  const levelOf = {}
  const queue = roots.map((r) => ({ id: r.id, level: 0 }))
  const visited = new Set()

  while (queue.length) {
    const { id, level } = queue.shift()
    if (visited.has(id)) continue
    visited.add(id)
    levelOf[id] = level
    ;(childrenMap[id] || []).forEach((c) => queue.push({ id: c, level: level + 1 }))
  }

  const columns = {}
  nodes.forEach((n) => {
    const level = levelOf[n.id] ?? Math.floor(Math.random() * 3) // random if unconnected
    columns[level] = columns[level] || []
    columns[level].push(n)
  })

  const positioned = {}
  Object.entries(columns).forEach(([level, group]) => {
    group.forEach((n, i) => {
      positioned[n.id] = {
        x: Number(level) * 230 + 40,
        y: i * 110 + 30,
      }
    })
  })

  return positioned
}

function GraphNode({ data }) {
  const Icon = TYPE_ICON[data.nodeType] || FileText
  return (
    <div className={`graph-node graph-node-${data.status}`}>
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <Icon size={13} className="graph-node-icon" />
      <span className="graph-node-label">{data.label}</span>
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  )
}

const nodeTypes = { docNode: GraphNode }

export default function GraphPanel({ highlightedNodes = [], isMainView = false }) {
  const [selectedNodeId, setSelectedNodeId] = useState(null)
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })

  const fetchGraph = useCallback(async () => {
    try {
      const res = await axios.get('/api/graph')
      setGraphData(res.data)
    } catch (err) {
      console.error("Failed to fetch graph data", err)
    }
  }, [])

  useEffect(() => {
    fetchGraph()
    window.addEventListener('graph-updated', fetchGraph)
    return () => window.removeEventListener('graph-updated', fetchGraph)
  }, [fetchGraph])

  const positions = useMemo(
    () => layoutNodes(graphData.nodes, graphData.edges),
    [graphData]
  )

  const flowNodes = useMemo(() => {
    return graphData.nodes.map((n) => {
      let status = 'normal'
      if (selectedNodeId === n.id) status = 'selected'
      else if (highlightedNodes.includes(n.id)) status = 'used'

      return {
        id: n.id,
        type: 'docNode',
        position: positions[n.id] || { x: Math.random() * 500, y: Math.random() * 500 },
        data: { label: n.label, nodeType: n.type, status },
      }
    })
  }, [positions, highlightedNodes, selectedNodeId, graphData.nodes])

  const flowEdges = useMemo(() => {
    return graphData.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      animated: e.kind === 'semantic',
      style: {
        stroke: e.kind === 'semantic' ? 'var(--accent-2)' : 'var(--border)',
        strokeWidth: e.kind === 'semantic' ? 1.4 : 1.2,
        strokeDasharray: e.kind === 'semantic' ? '4 3' : undefined,
      },
    }))
  }, [graphData.edges])

  const handleNodeClick = useCallback((_, node) => {
    setSelectedNodeId(node.id)
  }, [])

  useEffect(() => {
    if (highlightedNodes.length) setSelectedNodeId(null)
  }, [highlightedNodes])

  const selectedNode = graphData.nodes.find((n) => n.id === selectedNodeId)
  const connections = selectedNode
    ? graphData.edges.filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
    : []

  return (
    <section className={`graph-panel ${isMainView ? 'is-main-view' : ''}`}>
      <div className="graph-panel-header">
        <span className="graph-panel-title">Graph Explorer</span>
        <div className="graph-legend-inline">
          <span><i style={{ background: 'var(--node-blue)' }} /> normal</span>
          <span><i style={{ background: 'var(--node-green)' }} /> used</span>
          <span><i style={{ background: 'var(--node-yellow)' }} /> selected</span>
        </div>
      </div>

      <div className="graph-canvas">
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          nodeTypes={nodeTypes}
          onNodeClick={handleNodeClick}
          onPaneClick={() => setSelectedNodeId(null)}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background color="rgba(0, 0, 0, 0.08)" gap={18} size={1.2} />
          <Controls showInteractive={false} />
          <MiniMap
            pannable
            zoomable
            style={{ background: 'var(--surface)' }}
            maskColor="rgba(250, 240, 230, 0.6)"
            nodeColor={() => 'var(--node-blue)'}
          />
        </ReactFlow>
      </div>

      {selectedNode && (
        <NodeDetails
          node={selectedNode}
          connections={connections}
          onClose={() => setSelectedNodeId(null)}
        />
      )}
    </section>
  )
}
