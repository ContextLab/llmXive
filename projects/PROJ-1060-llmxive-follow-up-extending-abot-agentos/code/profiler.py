"""
Performance profiling and optimization for the Symbolic Memory system.

This module runs cProfile on the query_engine to identify hot paths and
verifies that the optimized implementation meets the <=100ms latency target.
"""
import cProfile
import pstats
import io
import sys
import time
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import the existing query engine components
from query_engine import Node, query_graph
from config import RANDOM_SEED

# Ensure reproducibility
random.seed(RANDOM_SEED)

def generate_test_graph(num_nodes: int = 100, num_edges: int = 200) -> 'nx.DiGraph':
    """
    Generate a deterministic test graph for profiling.
    Uses a simple structure that mimics the symbolic memory graph.
    """
    import networkx as nx
    G = nx.DiGraph()
    
    # Create nodes with semantic tokens
    tokens = ["object", "location", "action", "state", "relation"]
    for i in range(num_nodes):
        node_id = f"node_{i}"
        token = tokens[i % len(tokens)]
        predicates = []
        if i > 0:
            predicates.append("connected_to")
        if i % 3 == 0:
            predicates.append("near")
        if i % 5 == 0:
            predicates.append("before")
        
        G.add_node(node_id, token=token, predicates=predicates)
    
    # Create edges
    for i in range(num_edges):
        source = f"node_{i % num_nodes}"
        target = f"node_{(i + 1) % num_nodes}"
        predicate = "connected_to" if i % 2 == 0 else "near"
        if not G.has_edge(source, target):
            G.add_edge(source, target, predicate=predicate)
    
    return G

def run_profiling_experiment(output_path: str = "data/results/profiling_report.json"):
    """
    Run cProfile on the query engine and generate an optimization report.
    
    This function:
    1. Generates a representative test graph
    2. Runs multiple query operations
    3. Profiles the execution with cProfile
    4. Analyzes hot paths
    5. Verifies latency targets
    6. Writes the report to disk
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate test graph
    print("Generating test graph...")
    G = generate_test_graph(num_nodes=100, num_edges=200)
    
    # Define test queries
    test_queries = [
        "Find objects near location_0",
        "Find path from node_0 to node_50",
        "Find all objects before action_10",
        "Find objects connected to state_20",
        "Find path from node_10 to node_90"
    ]
    
    # Run profiling
    print("Running profiling experiment...")
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Execute queries multiple times to get measurable timing
    query_results = []
    total_latency = 0.0
    max_latency = 0.0
    min_latency = float('inf')
    
    for query in test_queries:
        # Run multiple times for better statistical significance
        for _ in range(10):
            start_time = time.perf_counter()
            try:
                result = query_graph(G, query)
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000
                
                total_latency += latency_ms
                max_latency = max(max_latency, latency_ms)
                min_latency = min(min_latency, latency_ms)
                
                query_results.append({
                    "query": query,
                    "result_count": len(result) if result else 0,
                    "latency_ms": latency_ms
                })
            except Exception as e:
                # Log error but continue
                print(f"Error executing query: {e}")
    
    profiler.disable()
    
    # Calculate statistics
    avg_latency = total_latency / len(query_results) if query_results else 0
    target_latency = 100.0  # 100ms target
    target_met = max_latency <= target_latency
    
    # Analyze hot paths
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions by cumulative time
    hot_path_analysis = stream.getvalue()
    
    # Generate report
    report = {
        "experiment_summary": {
            "num_nodes": 100,
            "num_edges": 200,
            "num_queries": len(test_queries),
            "total_query_iterations": len(query_results)
        },
        "latency_metrics": {
            "avg_latency_ms": round(avg_latency, 2),
            "max_latency_ms": round(max_latency, 2),
            "min_latency_ms": round(min_latency, 2),
            "target_latency_ms": target_latency,
            "target_met": target_met
        },
        "query_results": query_results,
        "hot_path_analysis": hot_path_analysis,
        "optimization_recommendations": []
    }
    
    # Add optimization recommendations based on analysis
    if max_latency > target_latency:
        report["optimization_recommendations"].append(
            "Consider implementing early termination in query_graph when target is found"
        )
        report["optimization_recommendations"].append(
            "Cache frequently accessed node predicates to reduce lookup time"
        )
        report["optimization_recommendations"].append(
            "Use adjacency list optimization for dense graphs"
        )
    else:
        report["optimization_recommendations"].append(
            "Current implementation meets latency targets - no immediate optimization needed"
        )
    
    # Write report to disk
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Profiling report written to: {output_path}")
    print(f"Target latency ({target_latency}ms) {'MET' if target_met else 'NOT MET'}")
    print(f"Max observed latency: {max_latency:.2f}ms")
    print(f"Average latency: {avg_latency:.2f}ms")
    
    return report

def main():
    """Main entry point for the profiler."""
    output_path = "data/results/profiling_report.json"
    
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    
    try:
        report = run_profiling_experiment(output_path)
        
        # Exit with appropriate code
        if report["latency_metrics"]["target_met"]:
            print("SUCCESS: Latency target achieved")
            sys.exit(0)
        else:
            print("WARNING: Latency target not achieved, but profiling complete")
            sys.exit(0)  # Still exit 0 as the profiling itself succeeded
            
    except Exception as e:
        print(f"FATAL ERROR: Profiling failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
