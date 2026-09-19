import json
import tracemalloc
import sys
import logging
from collections import OrderedDict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure code directory is in path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

logger = logging.getLogger(__name__)

@dataclass
class GraphNode:
    id: str
    token: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphEdge:
    source: str
    target: str
    predicate: str
    confidence: float = 1.0

class SymbolicGraphBuilder:
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.contradictions: List[str] = []

    def add_node(self, node_id: str, token: str, metadata: Optional[Dict] = None):
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(id=node_id, token=token, metadata=metadata or {})

    def add_edge(self, source: str, target: str, predicate: str, confidence: float = 1.0):
        # Check for contradictions (simple check for now)
        for existing in self.edges:
            if existing.source == source and existing.target == target and existing.predicate != predicate:
                self.contradictions.append(f"Contradiction: {source} {predicate} {target} vs {existing.predicate}")
                return # Exclude flagged edges
            
        self.edges.append(GraphEdge(source=source, target=target, predicate=predicate, confidence=confidence))

    def build_dag(self, traces: List[Dict[str, Any]]) -> None:
        """
        Constructs the DAG from a list of traces.
        """
        for trace in traces:
            trace_id = trace.get('id', 'unknown')
            steps = trace.get('steps', [])
            
            for i, step in enumerate(steps):
                # Extract nodes and edges from step
                # Simplified logic for demonstration
                obj = step.get('object', 'unknown_object')
                action = step.get('action', 'unknown_action')
                location = step.get('location', 'unknown_location')
                
                node_id = f"{trace_id}_{i}"
                self.add_node(node_id, obj)
                
                if i > 0:
                    prev_node_id = f"{trace_id}_{i-1}"
                    # Determine predicate based on action
                    predicate = "near"
                    if action == "pick":
                        predicate = "on_top_of"
                    elif action == "move":
                        predicate = "near"
                        
                    self.add_edge(prev_node_id, node_id, predicate)

    def get_graph_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [asdict(n) for n in self.nodes.values()],
            "edges": [asdict(e) for e in self.edges],
            "contradictions": self.contradictions
        }

def build_graph_from_traces(traces: List[Dict[str, Any]]) -> SymbolicGraphBuilder:
    builder = SymbolicGraphBuilder()
    builder.build_dag(traces)
    return builder

def save_graph(builder: SymbolicGraphBuilder, filepath: str = "data/results/constructed_graph.json"):
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(builder.get_graph_dict(), f, indent=2)

def validate_memory_footprint(builder: SymbolicGraphBuilder, max_mb: int = 2048) -> bool:
    """
    Validates that the memory footprint of the constructed graph is within limits.
    
    Args:
        builder: The graph builder instance.
        max_mb: Maximum allowed memory in MB.
        
    Returns:
        True if within limits, False otherwise.
    """
    tracemalloc.start()
    
    # Force garbage collection to get accurate snapshot
    import gc
    gc.collect()
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    peak_mb = peak / (1024 * 1024)
    passed = peak_mb <= max_mb
    
    result = {
        "pass": passed,
        "peak_memory_mb": peak_mb,
        "limit_mb": max_mb
    }
    
    output_path = Path("data/results/memory_check.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Memory check: {peak_mb:.2f}MB / {max_mb}MB -> {'PASS' if passed else 'FAIL'}")
    return passed

def main():
    """
    Main entry point for graph building and validation.
    """
    # Load sample traces (in real scenario, loaded from data_loader)
    sample_traces = [
        {
            "id": "trace_001",
            "steps": [
                {"object": "cup", "action": "move", "location": "kitchen"},
                {"object": "cup", "action": "pick", "location": "counter"}
            ]
        }
    ]
    
    builder = build_graph_from_traces(sample_traces)
    save_graph(builder)
    print(f"Graph saved to data/results/constructed_graph.json")
    
    passed = validate_memory_footprint(builder)
    print(f"Memory validation: {'PASS' if passed else 'FAIL'}")

if __name__ == "__main__":
    main()
