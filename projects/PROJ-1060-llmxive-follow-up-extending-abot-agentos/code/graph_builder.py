import json
import tracemalloc
import sys
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import networkx as nx

from config import MAX_TRACES, GRANULARITY, PREDICATE_SET, RANDOM_SEED
from tokenizer import SymbolicTokenizer, discretize_trace
from data_loader import load_traces_as_list
from validator import load_ground_truth, calculate_reconstruction_error

@dataclass
class GraphNode:
    id: str
    token: str
    trace_id: str
    step_idx: int

@dataclass
class GraphEdge:
    source: str
    target: str
    predicate: str
    confidence: float = 1.0

class SymbolicGraphBuilder:
    def __init__(self, tokenizer: SymbolicTokenizer):
        self.tokenizer = tokenizer
        self.graph = nx.DiGraph()
        self.inconsistencies: List[Dict[str, Any]] = []
        self.missing_matches: List[Dict[str, Any]] = []

    def build_from_trace(self, trace: Dict[str, Any]) -> None:
        trace_id = trace.get("id", "unknown")
        observations = trace.get("observations", [])
        
        prev_node_id = None
        
        for step_idx, obs in enumerate(observations):
            raw_obs = obs.get("observation", "")
            token = self.tokenizer.discretize(raw_obs)
            
            if token == "unknown_object":
                self.missing_matches.append({
                    "trace_id": trace_id,
                    "step": step_idx,
                    "raw": raw_obs
                })
            
            node_id = f"{trace_id}_step_{step_idx}"
            node = GraphNode(
                id=node_id,
                token=token,
                trace_id=trace_id,
                step_idx=step_idx
            )
            
            self.graph.add_node(node_id, token=token, trace_id=trace_id, step_idx=step_idx)
            
            if prev_node_id is not None:
                edge = GraphEdge(
                    source=prev_node_id,
                    target=node_id,
                    predicate="before",
                    confidence=1.0
                )
                self.graph.add_edge(prev_node_id, node_id, predicate="before", confidence=1.0)
                
                if self._is_inconsistent(prev_node_id, node_id):
                    self.graph.remove_edge(prev_node_id, node_id)
                    self.inconsistencies.append({
                        "source": prev_node_id,
                        "target": node_id,
                        "reason": "contradictory_spatial_info"
                    })
            
            prev_node_id = node_id

    def _is_inconsistent(self, source_id: str, target_id: str) -> bool:
        source_attrs = self.graph.nodes[source_id]
        target_attrs = self.graph.nodes[target_id]
        
        if GRANULARITY == "coarse":
            return False
        
        source_token = source_attrs.get("token", "")
        target_token = target_attrs.get("token", "")
        
        if source_token == target_token and "spatial" in PREDICATE_SET:
            return False
        
        return False

    def add_spatial_edges(self, traces: List[Dict[str, Any]]) -> None:
        for trace in traces:
            trace_id = trace.get("id", "unknown")
            observations = trace.get("observations", [])
            
            for i, obs in enumerate(observations):
                for j, other_obs in enumerate(observations):
                    if i >= j:
                        continue
                    
                    token_i = self.tokenizer.discretize(obs.get("observation", ""))
                    token_j = self.tokenizer.discretize(other_obs.get("observation", ""))
                    
                    if token_i == "unknown_object" or token_j == "unknown_object":
                        continue
                    
                    if GRANULARITY == "fine" and "spatial" in PREDICATE_SET:
                        node_i = f"{trace_id}_step_{i}"
                        node_j = f"{trace_id}_step_{j}"
                        
                        if self.graph.has_edge(node_i, node_j):
                            continue
                            
                        self.graph.add_edge(node_i, node_j, predicate="near", confidence=0.8)

    def get_graph(self) -> nx.DiGraph:
        return self.graph

    def get_inconsistencies(self) -> List[Dict[str, Any]]:
        return self.inconsistencies

    def get_missing_matches(self) -> List[Dict[str, Any]]:
        return self.missing_matches

def build_graph_from_traces(traces: List[Dict[str, Any]]) -> Tuple[nx.DiGraph, SymbolicGraphBuilder]:
    tokenizer = SymbolicTokenizer()
    builder = SymbolicGraphBuilder(tokenizer)
    
    for trace in traces:
        builder.build_from_trace(trace)
    
    builder.add_spatial_edges(traces)
    
    return builder.get_graph(), builder

def save_graph(graph: nx.DiGraph, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    data = nx.node_link_data(graph)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def validate_memory_footprint(graph: nx.DiGraph, max_mb: int = 2048) -> bool:
    tracemalloc.start()
    _ = json.dumps(nx.node_link_data(graph))
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    peak_mb = peak / (1024 * 1024)
    return peak_mb <= max_mb

def main() -> None:
    print("Building symbolic graphs from ALFWorld traces...")
    
    traces = load_traces_as_list(split="train", max_traces=MAX_TRACES)
    
    if not traces:
        print("No traces loaded. Exiting.")
        return
    
    graph, builder = build_graph_from_traces(traces)
    
    output_path = "data/processed/symbolic_graph.json"
    save_graph(graph, output_path)
    print(f"Graph saved to {output_path}")
    
    if not validate_memory_footprint(graph):
        print("WARNING: Memory footprint exceeded 2GB limit.")
    
    inconsistencies = builder.get_inconsistencies()
    missing = builder.get_missing_matches()
    
    warnings_log = Path("data/results/validation_warnings.log")
    warnings_log.parent.mkdir(parents=True, exist_ok=True)
    
    with open(warnings_log, "w", encoding="utf-8") as f:
        f.write(f"Total inconsistencies: {len(inconsistencies)}\n")
        f.write(f"Total missing matches: {len(missing)}\n")
        for inc in inconsistencies:
            f.write(f"INCONSISTENCY: {inc}\n")
        for miss in missing:
            f.write(f"MISSING: {miss}\n")
    
    print(f"Validation warnings written to {warnings_log}")
    print(f"Reconstruction error calculation starting...")
    
    gt_path = "data/schemas/ground_truth_mapping.json"
    if Path(gt_path).exists():
        error_rate = calculate_reconstruction_error(graph, gt_path)
        result_path = "data/results/reconstruction_error.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump({"error_rate": error_rate, "trace_count": len(traces)}, f, indent=2)
        print(f"Reconstruction error saved to {result_path}")
    else:
        print(f"Ground truth schema not found at {gt_path}. Skipping error calculation.")

if __name__ == "__main__":
    main()