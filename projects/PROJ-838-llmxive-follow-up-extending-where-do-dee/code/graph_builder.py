import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import networkx as nx
import spacy
from spacy.matcher import Matcher

from config import ensure_directories

# Load spaCy model once globally to avoid reloading overhead
_nlp = spacy.load("en_core_web_sm")
_matcher = Matcher(_nlp.vocab)

def _add_citation_rules(matcher: Matcher) -> None:
    """
    Add rules to the Matcher to detect citation patterns.
    Pattern: [Token "cite" or "refer"] followed by [Token "to"] followed by [Token "previous" or "step"]
    This is a heuristic for detecting co-reference/citation in research agent trajectories.
    """
    pattern_cite = [
        {"LOWER": {"IN": ["cite", "refer", "reference"]}},
        {"LOWER": "to"},
        {"LOWER": {"IN": ["the", "this", "that", "previous", "earlier", "earlier", "step", "turn"]}},
    ]
    matcher.add("CITATION_PATTERN", [pattern_cite])

def parse_trajectory(trajectory: Dict[str, Any], cutoff_depth: float = 0.5) -> List[Dict[str, Any]]:
    """
    Extract the first int(len(spans) * cutoff_depth) spans from a trajectory.
    
    Args:
        trajectory: A dictionary containing a 'spans' key with a list of span dictionaries.
        cutoff_depth: A float between 0.0 and 1.0 indicating the fraction of spans to keep.
    
    Returns:
        A list of span dictionaries representing the early trajectory.
    """
    spans = trajectory.get("spans", [])
    if not spans:
        return []
    
    count = int(len(spans) * cutoff_depth)
    # If count is 0 but spans exist (e.g., very short trajectory), take at least one if available?
    # Per task T016: handle trajectories shorter than cutoff by using all spans.
    # If len(spans) * cutoff_depth < 1, int() returns 0. We should use all spans in that case.
    if count == 0 and len(spans) > 0:
        return spans
    
    return spans[:count]

def detect_citations(spans: List[Dict[str, Any]], nlp: spacy.language.Language, matcher: Matcher) -> List[Tuple[int, int]]:
    """
    Detect co-reference and citation edges between spans.
    
    Args:
        spans: List of span dictionaries, each with at least a 'text' key.
        nlp: Loaded spaCy nlp object.
        matcher: Initialized Matcher object.
    
    Returns:
        A list of tuples (source_idx, target_idx) representing edges in the DAG.
        source_idx is the span that cites, target_idx is the span being cited.
    """
    edges = []
    
    for i, span_data in enumerate(spans):
        text = span_data.get("text", "")
        if not text:
            continue
        
        doc = nlp(text)
        matches = matcher(doc)
        
        # If a citation pattern is found in this span, it likely cites previous spans
        if matches:
            # Heuristic: A span citing something usually refers to a previous span (index < i)
            # We create edges from current span i to all previous spans j < i
            # This is a conservative heuristic for DAG construction without ground truth
            for j in range(i):
                edges.append((i, j))
    
    return edges

def build_dag(spans: List[Dict[str, Any]], nlp: Optional[spacy.language.Language] = None, matcher: Optional[Matcher] = None) -> nx.DiGraph:
    """
    Construct a Directed Acyclic Graph (DAG) from spans based on co-reference/citation.
    
    Args:
        spans: List of span dictionaries.
        nlp: Optional pre-loaded spaCy nlp object.
        matcher: Optional pre-initialized Matcher object.
    
    Returns:
        A networkx.DiGraph representing the trajectory DAG.
    """
    if nlp is None:
        nlp = _nlp
    if matcher is None:
        matcher = _matcher
        _add_citation_rules(matcher)
    
    G = nx.DiGraph()
    
    if not spans:
        return G
    
    # Add nodes
    for idx, span_data in enumerate(spans):
        span_id = span_data.get("id", idx)
        G.add_node(span_id, text=span_data.get("text", ""), metadata=span_data)
    
    # Detect edges
    edges = detect_citations(spans, nlp, matcher)
    G.add_edges_from(edges)
    
    return G

def load_trajectories_from_directory(directory: Path) -> List[Dict[str, Any]]:
    """
    Load all JSON files from a directory containing trajectory data.
    
    Args:
        directory: Path to the directory containing JSON files.
    
    Returns:
        A list of trajectory dictionaries.
    """
    trajectories = []
    for json_file in directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # Handle both single trajectory and list of trajectories
                if isinstance(data, list):
                    trajectories.extend(data)
                else:
                    trajectories.append(data)
            except json.JSONDecodeError:
                continue
    return trajectories

def save_graph(graph: nx.DiGraph, trajectory_id: str, output_dir: Path) -> Path:
    """
    Save a DiGraph to a JSON file in the specified output directory.
    
    The graph is serialized to a JSON-compatible dictionary format.
    Node attributes and edge data are preserved.
    
    Args:
        graph: The networkx.DiGraph to save.
        trajectory_id: Unique identifier for the trajectory (used in filename).
        output_dir: Directory where the JSON file will be saved.
    
    Returns:
        Path to the saved JSON file.
    """
    ensure_directories()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert graph to serializable format
    data = nx.node_link_data(graph)
    
    # Add trajectory metadata
    output_data = {
        "trajectory_id": trajectory_id,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "graph": data
    }
    
    output_path = output_dir / f"{trajectory_id}_graph.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    return output_path

def main():
    """
    Main entry point for building and saving graphs from TELBench trajectories.
    Processes all trajectories in data/raw and saves intermediate DAGs to data/processed/graphs/.
    """
    from config import dataset_url
    import os
    
    # Define paths
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed/graphs")
    
    if not raw_dir.exists():
        print(f"Error: Raw data directory {raw_dir} does not exist.")
        print("Please run downloader.py first to fetch TELBench data.")
        return
    
    # Load trajectories
    trajectories = load_trajectories_from_directory(raw_dir)
    print(f"Loaded {len(trajectories)} trajectories.")
    
    if not trajectories:
        print("No trajectories found to process.")
        return
    
    # Process each trajectory
    for traj in trajectories:
        traj_id = traj.get("id", "unknown")
        
        # Parse early spans
        spans = parse_trajectory(traj, cutoff_depth=0.5)
        
        if not spans:
            print(f"Skipping {traj_id}: No spans found.")
            continue
        
        # Build DAG
        graph = build_dag(spans)
        
        # Save graph
        output_path = save_graph(graph, traj_id, processed_dir)
        print(f"Saved graph for {traj_id} to {output_path} ({graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges)")
    
    print(f"Graph generation complete. Output directory: {processed_dir}")

if __name__ == "__main__":
    main()
