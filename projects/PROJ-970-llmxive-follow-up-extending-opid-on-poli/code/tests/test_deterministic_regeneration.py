"""
Test module for verifying deterministic regeneration of synthetic graphs.
Implements T015: verify_deterministic_regeneration task.

This task explicitly runs the generator for each tier with a fixed seed,
computes checksums, regenerates, recomputes checksums, and asserts equality
to satisfy FR-001 (Reproducibility) and Const I (Seed Initialization).
"""
import os
import sys
import hashlib
import json
from typing import Dict, Any, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import set_seed, get_seed, ensure_directories
from environment.graph_generator import GraphGenerator
from environment.state_graph import StateGraph


def serialize_graph(graph: StateGraph) -> str:
    """
    Serialize a StateGraph to a deterministic string representation.
    This ensures that the same graph structure always produces the same string.
    
    Args:
        graph: The StateGraph to serialize
        
    Returns:
        A deterministic string representation of the graph
    """
    # Sort nodes and edges to ensure deterministic ordering
    nodes_str = []
    for node_id in sorted(graph.nodes.keys()):
        node = graph.nodes[node_id]
        nodes_str.append(f"node:{node_id}:{node.tier}")
    
    edges_str = []
    # Sort edges by source, then target for determinism
    sorted_edges = sorted(graph.edges, key=lambda e: (e.source, e.target))
    for edge in sorted_edges:
        edges_str.append(f"edge:{edge.source}->{edge.target}:{edge.probability:.6f}:{edge.reward}")
    
    # Combine into a single string
    serialized = "\n".join(nodes_str + edges_str)
    return serialized


def compute_checksum(data: str) -> str:
    """
    Compute a SHA-256 checksum of the given data string.
    
    Args:
        data: The string to checksum
        
    Returns:
        Hexadecimal SHA-256 hash string
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def verify_tier_determinism(
    tier: int,
    seed: int = 42,
    max_retries: int = 100
) -> Tuple[bool, str, str, Dict[str, Any]]:
    """
    Verify that a graph generated for a specific tier and seed is deterministic.
    
    This function:
    1. Sets the seed
    2. Generates a graph
    3. Computes its checksum
    4. Regenerates with the same seed
    5. Recomputes the checksum
    6. Asserts equality
    
    Args:
        tier: The tier number (1, 2, or 3)
        seed: The random seed to use
        max_retries: Maximum retries for graph generation (passed to generator)
        
    Returns:
        Tuple of (success, message, checksum1, metadata)
    """
    # Ensure directories exist
    ensure_directories()
    
    # Set seed for reproducibility
    set_seed(seed)
    
    # Create generator
    generator = GraphGenerator()
    
    # Generate first graph
    graph1 = generator.generate(tier=tier, seed=seed)
    
    # Validate graph1
    if not graph1.is_valid():
        return False, f"First generated graph for tier {tier} is invalid", "", {}
    
    # Serialize and checksum
    serialized1 = serialize_graph(graph1)
    checksum1 = compute_checksum(serialized1)
    
    # Reset seed for regeneration
    set_seed(seed)
    
    # Generate second graph
    graph2 = generator.generate(tier=tier, seed=seed)
    
    # Validate graph2
    if not graph2.is_valid():
        return False, f"Second generated graph for tier {tier} is invalid", checksum1, {}
    
    # Serialize and checksum
    serialized2 = serialize_graph(graph2)
    checksum2 = compute_checksum(serialized2)
    
    # Check if checksums match
    if checksum1 != checksum2:
        return False, (
            f"Graphs for tier {tier} with seed {seed} are not deterministic. "
            f"Checksum1: {checksum1}, Checksum2: {checksum2}"
        ), checksum1, {}
    
    # Prepare metadata
    metadata = {
        "tier": tier,
        "seed": seed,
        "num_nodes": len(graph1.nodes),
        "num_edges": len(graph1.edges),
        "checksum": checksum1,
        "is_valid": graph1.is_valid()
    }
    
    return True, f"Tier {tier} with seed {seed} is deterministic", checksum1, metadata


def run_all_tier_verifications(
    seeds: List[int] = None,
    tiers: List[int] = None
) -> Dict[str, Any]:
    """
    Run deterministic regeneration verification for all tiers and specified seeds.
    
    Args:
        seeds: List of seeds to test (default: [42, 123, 456])
        tiers: List of tiers to test (default: [1, 2, 3])
        
    Returns:
        Dictionary containing verification results and metadata
    """
    if seeds is None:
        seeds = [42, 123, 456]
    if tiers is None:
        tiers = [1, 2, 3]
    
    results = {
        "verification_status": "passed",
        "details": [],
        "summary": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0
        }
    }
    
    for tier in tiers:
        for seed in seeds:
            success, message, checksum, metadata = verify_tier_determinism(
                tier=tier,
                seed=seed
            )
            
            test_result = {
                "tier": tier,
                "seed": seed,
                "success": success,
                "message": message,
                "checksum": checksum,
                "metadata": metadata
            }
            
            results["details"].append(test_result)
            results["summary"]["total_tests"] += 1
            
            if success:
                results["summary"]["passed"] += 1
            else:
                results["summary"]["failed"] += 1
                results["verification_status"] = "failed"
    
    return results


def main():
    """
    Main entry point for the deterministic regeneration verification.
    
    This script:
    1. Runs verification for all tiers (1, 2, 3) with multiple seeds
    2. Outputs results to data/processed/determinism_verification.json
    3. Prints a summary to stdout
    """
    print("Starting deterministic regeneration verification (T015)...")
    
    # Run verifications
    results = run_all_tier_verifications()
    
    # Ensure output directory exists
    ensure_directories()
    
    # Save results to JSON
    output_path = "data/processed/determinism_verification.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\nVerification Results:")
    print(f"  Total Tests: {results['summary']['total_tests']}")
    print(f"  Passed: {results['summary']['passed']}")
    print(f"  Failed: {results['summary']['failed']}")
    print(f"  Status: {results['verification_status'].upper()}")
    print(f"\nResults saved to: {output_path}")
    
    # Exit with appropriate code
    if results["verification_status"] == "failed":
        print("\nERROR: Deterministic regeneration verification FAILED!")
        sys.exit(1)
    else:
        print("\nSUCCESS: All tiers are deterministic with fixed seeds.")
        sys.exit(0)


if __name__ == "__main__":
    main()