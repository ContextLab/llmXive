import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import networkx as nx
import spacy
from config import ensure_directories

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_nlp = None

def get_nlp() -> spacy.language.Language:
    """Lazily load the spaCy model."""
    global _nlp
    if _nlp is None:
        logger.info("Loading spaCy model 'en_core_web_sm'...")
        _nlp = spacy.load("en_core_web_sm")
    return _nlp

def parse_trajectory(trajectory: Dict[str, Any], cutoff_depth: float) -> List[Dict[str, Any]]:
    """
    Extract the first int(len(spans) * cutoff_depth) spans from a trajectory.
    """
    spans = trajectory.get("spans", [])
    if not spans:
        return []
    
    count = int(len(spans) * cutoff_depth)
    # Ensure we take at least 1 if spans exist and count is 0 due to float math,
    # unless cutoff_depth is effectively 0.
    if count == 0 and len(spans) > 0 and cutoff_depth > 0:
        count = 1
    
    return spans[:count]

def detect_citations(text: str, nlp: spacy.language.Language) -> List[str]:
    """
    Detect citation patterns in text (e.g., [1], (Author, Year), or standard bibliographic refs).
    Returns a list of citation strings found.
    """
    citations = []
    # Simple regex-like matching via spaCy patterns or basic string search for [x]
    # Using a basic pattern for [1], [12] etc.
    import re
    pattern = r'\[\d+\]'
    matches = re.findall(pattern, text)
    citations.extend(matches)
    
    # Check for (Author, Year) pattern
    pattern_author = r'\([A-Za-z]+,\s*\d{4}\)'
    matches_author = re.findall(pattern_author, text)
    citations.extend(matches_author)
    
    return list(set(citations))

def build_co_reference_graph(spans: List[Dict[str, Any]], nlp: spacy.language.Language) -> nx.DiGraph:
    """
    Build a graph based on co-reference and citation overlaps between spans.
    Nodes are spans (identified by index).
    Edges exist if spans share a citation or if a co-reference chain links them.
    """
    G = nx.DiGraph()
    
    # Add nodes
    for i, span in enumerate(spans):
        G.add_node(i, text=span.get("text", ""), citations=set())
    
    # Pre-process citations for each span
    span_citations: List[Set[str]] = []
    for span in spans:
        text = span.get("text", "")
        cites = set(detect_citations(text, nlp))
        span_citations.append(cites)
        # Update node attribute
        if i in G.nodes:
            G.nodes[i]["citations"] = cites
    
    # Build edges based on citation overlap
    # This is a simplified co-reference/citation logic:
    # If span A cites X and span B cites X, there is an edge.
    # We direct from earlier to later span.
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            # Check citation overlap
            if span_citations[i] & span_citations[j]:
                G.add_edge(i, j, type="citation_overlap")
            
            # Simple co-reference heuristic:
            # If span j mentions "this", "that", "it" and span i has a noun phrase that matches context?
            # For now, we stick to citation overlap as the primary signal per spec "co-reference/citation logic"
            # without heavy neuralcoref.
            
    return G

def build_dag(trajectory: Dict[str, Any], cutoff_depth: float) -> nx.DiGraph:
    """
    Construct a DiGraph from a trajectory, filtering spans by cutoff_depth
    and building edges based on co-reference/citation logic.
    Excludes ground-truth labels.
    """
    nlp = get_nlp()
    filtered_spans = parse_trajectory(trajectory, cutoff_depth)
    
    if not filtered_spans:
        G = nx.DiGraph()
        return G
    
    G = build_co_reference_graph(filtered_spans, nlp)
    return G

def load_trajectories_from_directory(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all JSON trajectory files from a directory.
    """
    trajectories = []
    if not data_dir.exists():
        logger.warning(f"Directory {data_dir} does not exist.")
        return trajectories
    
    for file_path in data_dir.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Handle if file is a list of trajectories or a single one
                if isinstance(data, list):
                    trajectories.extend(data)
                else:
                    trajectories.append(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
    
    return trajectories

def save_graph(G: nx.DiGraph, trajectory_id: str, output_dir: Path) -> Path:
    """
    Save a networkx DiGraph to a JSON file in the specified output directory.
    The graph is converted to a serializable dictionary format.
    """
    ensure_directories()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert graph to serializable format
    # Nodes: list of dicts with index and attributes
    # Edges: list of (u, v, attributes)
    nodes = []
    for node, data in G.nodes(data=True):
        # Ensure citations (set) is converted to list
        node_data = dict(data)
        if "citations" in node_data:
            node_data["citations"] = list(node_data["citations"])
        nodes.append({"id": node, **node_data})
    
    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({"source": u, "target": v, **data})
    
    graph_dict = {
        "trajectory_id": trajectory_id,
        "nodes": nodes,
        "edges": edges,
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges()
    }
    
    # Sanitize filename
    safe_id = trajectory_id.replace("/", "_").replace("\\", "_")
    filename = f"{safe_id}.json"
    output_path = output_dir / filename
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph_dict, f, indent=2)
    
    logger.info(f"Saved graph for {trajectory_id} to {output_path}")
    return output_path

def main():
    """
    Main entry point to build and save graphs for all trajectories in data/raw.
    """
    from config import cutoff_depth
    
    raw_dir = Path("data/raw")
    output_dir = Path("data/processed/graphs")
    
    ensure_directories()
    
    logger.info(f"Loading trajectories from {raw_dir}...")
    trajectories = load_trajectories_from_directory(raw_dir)
    
    if not trajectories:
        logger.warning("No trajectories found. Exiting.")
        return
    
    logger.info(f"Found {len(trajectories)} trajectories. Building graphs...")
    
    for traj in trajectories:
        traj_id = traj.get("id", "unknown")
        try:
            G = build_dag(traj, cutoff_depth)
            save_graph(G, traj_id, output_dir)
        except Exception as e:
            logger.error(f"Failed to build graph for {traj_id}: {e}")

if __name__ == "__main__":
    main()
