"""
Graph Builder Module for Symbolic Memory System.

Constructs a Directed Acyclic Graph (DAG) from ALFWorld traces,
handling tokenization, predicate detection, and memory validation.
"""
import json
import tracemalloc
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

from config import MAX_TRACES
from tokenizer import SymbolicTokenizer, discretize_trace


@dataclass
class GraphNode:
    """Represents a node in the symbolic graph."""
    id: str
    token: str
    predicates: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "token": self.token,
            "predicates": self.predicates,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphNode":
        return cls(
            id=data["id"],
            token=data["token"],
            predicates=data.get("predicates", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class GraphEdge:
    """Represents an edge in the symbolic graph."""
    source: str
    target: str
    predicate: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "predicate": self.predicate,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphEdge":
        return cls(
            source=data["source"],
            target=data["target"],
            predicate=data["predicate"],
            metadata=data.get("metadata", {})
        )


class SymbolicGraphBuilder:
    """
    Builds a symbolic graph from discretized task traces.
    Implements memory footprint validation to ensure scalability.
    """
    
    def __init__(self, max_memory_gb: float = 2.0):
        self.max_memory_gb = max_memory_gb
        self.max_memory_bytes = int(max_memory_gb * 1024 ** 3)
        self.graph = nx.DiGraph()
        self.tokenizer = SymbolicTokenizer()
        self._trace_count = 0
        self._validation_errors: List[Dict[str, Any]] = []

    def _estimate_graph_memory(self) -> int:
        """
        Estimate the memory footprint of the current graph.
        Uses a heuristic based on node/edge counts and average object size.
        """
        # Heuristic: 1KB per node + 500 bytes per edge + base overhead
        # This is a conservative estimate to ensure we stay under 2GB
        base_overhead = 10 * 1024  # 10KB
        node_size = 1024  # 1KB per node
        edge_size = 500   # 500 bytes per edge
        
        estimated = base_overhead + \
                   (self.graph.number_of_nodes() * node_size) + \
                   (self.graph.number_of_edges() * edge_size)
        return estimated

    def _validate_memory_footprint(self) -> bool:
        """
        Validate that the current graph memory footprint is within limits.
        Returns True if within limits, False otherwise.
        """
        current_memory = self._estimate_graph_memory()
        is_valid = current_memory <= self.max_memory_bytes
        
        if not is_valid:
            error = {
                "type": "memory_limit_exceeded",
                "current_mb": current_memory / (1024 ** 2),
                "limit_mb": self.max_memory_bytes / (1024 ** 2),
                "node_count": self.graph.number_of_nodes(),
                "edge_count": self.graph.number_of_edges(),
                "trace_count": self._trace_count
            }
            self._validation_errors.append(error)
        
        return is_valid

    def _detect_inconsistencies(self, source: str, target: str, 
                              predicate: str, trace_context: Dict) -> bool:
        """
        Detect logical inconsistencies in spatial/temporal predicates.
        Returns True if an inconsistency is detected.
        """
        # Check for contradictory spatial relations
        if predicate in ["on_top_of", "under", "left_of", "right_of"]:
            # If we already have the reverse relation, it's a contradiction
            reverse_predicate_map = {
                "on_top_of": "under",
                "under": "on_top_of",
                "left_of": "right_of",
                "right_of": "left_of"
            }
            
            if predicate in reverse_predicate_map:
                reverse_pred = reverse_predicate_map[predicate]
                if self.graph.has_edge(target, source) and \
                   self.graph[target][source].get("predicate") == reverse_pred:
                    return True
        
        # Check for cycles (DAG should have no cycles)
        if self.graph.has_edge(source, target):
            # Check if adding this edge would create a cycle
            try:
                # Temporarily add edge and check for cycles
                self.graph.add_edge(source, target)
                has_cycle = not nx.is_directed_acyclic_graph(self.graph)
                self.graph.remove_edge(source, target)
                return has_cycle
            except Exception:
                return True
        
        return False

    def add_node(self, node_id: str, token: str, 
                predicates: Optional[List[str]] = None,
                metadata: Optional[Dict] = None) -> GraphNode:
        """Add a node to the graph with validation."""
        if node_id not in self.graph:
            node = GraphNode(
                id=node_id,
                token=token,
                predicates=predicates or [],
                metadata=metadata or {}
            )
            self.graph.add_node(node_id, **node.to_dict())
            self._validate_memory_footprint()
        return self._get_node(node_id)

    def _get_node(self, node_id: str) -> GraphNode:
        """Retrieve a node from the graph."""
        data = self.graph.nodes[node_id]
        return GraphNode(
            id=data["id"],
            token=data["token"],
            predicates=data.get("predicates", []),
            metadata=data.get("metadata", {})
        )

    def add_edge(self, source: str, target: str, predicate: str,
               metadata: Optional[Dict] = None, trace_context: Optional[Dict] = None) -> Optional[GraphEdge]:
        """Add an edge to the graph with consistency checking."""
        # Check for inconsistencies
        if trace_context and self._detect_inconsistencies(
            source, target, predicate, trace_context
        ):
            # Flag and exclude inconsistent edges
            self._validation_errors.append({
                "type": "inconsistency_detected",
                "source": source,
                "target": target,
                "predicate": predicate,
                "trace_context": trace_context.get("trace_id", "unknown")
            })
            return None
        
        if not self.graph.has_edge(source, target):
            edge = GraphEdge(
                source=source,
                target=target,
                predicate=predicate,
                metadata=metadata or {}
            )
            self.graph.add_edge(source, target, **edge.to_dict())
            self._validate_memory_footprint()
        
        return GraphEdge(
            source=source,
            target=target,
            predicate=predicate,
            metadata=metadata or {}
        )

    def build_from_trace(self, trace: Dict[str, Any]) -> None:
        """Build graph from a single trace."""
        self._trace_count += 1
        
        # Discretize the trace
        tokens = discretize_trace(trace)
        
        # Create nodes and edges based on tokenized trace
        prev_token = None
        for i, token in enumerate(tokens):
            node_id = f"trace_{self._trace_count}_step_{i}"
            
            # Add node
            self.add_node(
                node_id=node_id,
                token=token,
                metadata={"trace_id": trace.get("id", "unknown"), "step": i}
            )
            
            # Add edge from previous step
            if prev_token is not None:
                prev_node_id = f"trace_{self._trace_count}_step_{i-1}"
                self.add_edge(
                    source=prev_node_id,
                    target=node_id,
                    predicate="before",
                    trace_context={"trace_id": trace.get("id", "unknown")}
                )
            
            prev_token = token

    def build_from_traces(self, traces: List[Dict[str, Any]]) -> None:
        """Build graph from multiple traces."""
        for trace in traces[:MAX_TRACES]:
            self.build_from_trace(trace)

    def get_validation_report(self) -> Dict[str, Any]:
        """Generate a validation report including memory usage."""
        current_memory = self._estimate_graph_memory()
        return {
            "memory_mb": current_memory / (1024 ** 2),
            "memory_limit_mb": self.max_memory_bytes / (1024 ** 2),
            "within_limit": current_memory <= self.max_memory_bytes,
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "trace_count": self._trace_count,
            "validation_errors": self._validation_errors,
            "error_count": len(self._validation_errors)
        }


def build_graph_from_traces(traces: List[Dict[str, Any]], 
                           max_memory_gb: float = 2.0) -> Tuple[nx.DiGraph, Dict[str, Any]]:
    """
    Main entry point for building a symbolic graph from traces.
    
    Args:
        traces: List of trace dictionaries
        max_memory_gb: Maximum allowed memory footprint in GB
        
    Returns:
        Tuple of (networkx.DiGraph, validation_report)
    """
    builder = SymbolicGraphBuilder(max_memory_gb=max_memory_gb)
    builder.build_from_traces(traces)
    report = builder.get_validation_report()
    return builder.graph, report


def save_graph(graph: nx.DiGraph, output_path: str, 
              validation_report: Optional[Dict[str, Any]] = None) -> None:
    """
    Save the graph to a JSON file.
    
    Args:
        graph: networkx.DiGraph to save
        output_path: Path to output file
        validation_report: Optional validation report to include
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert graph to serializable format
    graph_data = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "is_dag": nx.is_directed_acyclic_graph(graph)
        }
    }
    
    for node_id, data in graph.nodes(data=True):
        graph_data["nodes"].append({
            "id": node_id,
            **data
        })
    
    for source, target, data in graph.edges(data=True):
        graph_data["edges"].append({
            "source": source,
            "target": target,
            **data
        })
    
    if validation_report:
        graph_data["validation"] = validation_report
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)


def main():
    """Main function to demonstrate graph building with memory validation."""
    import sys
    from data_loader import load_traces_as_list
    
    # Load traces
    try:
        traces = load_traces_as_list(max_traces=500)
    except Exception as e:
        print(f"Error loading traces: {e}")
        sys.exit(1)
    
    print(f"Loaded {len(traces)} traces")
    
    # Build graph with memory validation
    graph, report = build_graph_from_traces(traces, max_memory_gb=2.0)
    
    # Save results
    output_path = "data/results/symbolic_graph.json"
    save_graph(graph, output_path, report)
    
    print(f"Graph saved to {output_path}")
    print(f"Memory usage: {report['memory_mb']:.2f} MB (limit: {report['memory_limit_mb']:.2f} MB)")
    print(f"Nodes: {report['node_count']}, Edges: {report['edge_count']}")
    print(f"Validation errors: {report['error_count']}")
    
    if not report['within_limit']:
        print("WARNING: Memory limit exceeded!")
        sys.exit(1)


if __name__ == "__main__":
    main()
