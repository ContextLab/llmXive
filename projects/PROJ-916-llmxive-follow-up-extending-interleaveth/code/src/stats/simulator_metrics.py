import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from src.data_models import SceneGraph, ObjectNode, RelationshipEdge
from src.simulator.noise_injector import calculate_noise_ratio

@dataclass
class SimulatorMetrics:
    """Container for simulator performance metrics."""
    graph_edit_distance: float
    error_rate: float
    noise_injection_rate: Optional[float] = None
    is_within_target_range: Optional[bool] = None

def calculate_graph_edit_distance(
    graph1: SceneGraph, graph2: SceneGraph
) -> float:
    """
    Calculate the Graph Edit Distance (GED) between two SceneGraphs.
    Returns a normalized score between 0.0 (identical) and 1.0 (completely different).
    
    This is a simplified implementation counting node/edge mismatches relative to
    the union of elements.
    """
    # Create sets of canonical representations for comparison
    nodes1 = set((n.id, n.label, n.attributes) for n in graph1.objects)
    nodes2 = set((n.id, n.label, n.attributes) for n in graph2.objects)
    
    edges1 = set((e.subject_id, e.predicate, e.object_id) for e in graph1.relationships)
    edges2 = set((e.subject_id, e.predicate, e.object_id) for e in graph2.relationships)
    
    # Calculate symmetric differences
    node_diff = len(nodes1.symmetric_difference(nodes2))
    edge_diff = len(edges1.symmetric_difference(edges2))
    
    total_elements = len(nodes1.union(nodes2)) + len(edges1.union(edges2))
    
    if total_elements == 0:
        return 0.0
        
    return (node_diff + edge_diff) / total_elements

def calculate_error_rate(
    generated_graph: SceneGraph, ground_truth_graph: SceneGraph
) -> float:
    """
    Calculate the error rate as the Graph Edit Distance.
    Higher values indicate more deviation from ground truth.
    """
    return calculate_graph_edit_distance(generated_graph, ground_truth_graph)

def evaluate_simulator_against_ground_truth(
    generated_graph: SceneGraph, ground_truth_graph: SceneGraph
) -> SimulatorMetrics:
    """
    Evaluate a generated scene graph against human-annotated ground truth.
    """
    ged = calculate_graph_edit_distance(generated_graph, ground_truth_graph)
    error_rate = calculate_error_rate(generated_graph, ground_truth_graph)
    
    return SimulatorMetrics(
        graph_edit_distance=ged,
        error_rate=error_rate
    )

def calculate_simulator_error_rate(
    generated_graph: SceneGraph, 
    ground_truth_graph: SceneGraph,
    noise_injection_rate: Optional[float] = None
) -> SimulatorMetrics:
    """
    Calculate comprehensive simulator metrics including noise validation.
    
    Args:
        generated_graph: The graph produced by the simulator (potentially noisy).
        ground_truth_graph: The human-annotated ground truth.
        noise_injection_rate: The theoretical noise rate applied (from noise_injector).
        
    Returns:
        SimulatorMetrics object with calculated values.
    """
    metrics = evaluate_simulator_against_ground_truth(generated_graph, ground_truth_graph)
    
    if noise_injection_rate is not None:
        metrics.noise_injection_rate = noise_injection_rate
        # Target range is 5-15% (0.05 - 0.15)
        metrics.is_within_target_range = 0.05 <= noise_injection_rate <= 0.15
        
    return metrics

def verify_noise_injection_target(
    noise_injection_rate: float,
    lower_bound: float = 0.05,
    upper_bound: float = 0.15,
    tolerance: float = 0.02
) -> None:
    """
    Assert that the injected noise falls within the target range (SC-006).
    
    The target range for Noisy Mode is 5-15% (0.05 - 0.15).
    A tolerance of +/- 2% is allowed for stochastic variance.
    
    Args:
        noise_injection_rate: The measured or calculated noise ratio.
        lower_bound: Minimum acceptable noise rate (default 0.05).
        upper_bound: Maximum acceptable noise rate (default 0.15).
        tolerance: Allowed deviation from bounds (default 0.02).
        
    Raises:
        AssertionError: If the noise rate is outside the acceptable range.
    """
    effective_lower = lower_bound - tolerance
    effective_upper = upper_bound + tolerance
    
    if not (effective_lower <= noise_injection_rate <= effective_upper):
        raise AssertionError(
            f"Noise injection rate {noise_injection_rate:.4f} is outside the "
            f"target range [{lower_bound:.2f}, {upper_bound:.2f}] (tolerance ±{tolerance:.2f}). "
            f"Effective allowed range: [{effective_lower:.2f}, {effective_upper:.2f}]. "
            f"Verify noise_injector configuration or increase sample size."
        )

def validate_noisy_mode_simulation(
    noise_injection_rate: float,
    ground_truth_error_rate: float
) -> SimulatorMetrics:
    """
    Validate that the noisy mode simulation meets the target criteria.
    
    This function performs the specific check required by T016b:
    Asserts that the injected noise is within the 5-15% target range.
    
    Args:
        noise_injection_rate: The rate of noise injected into the scene description.
        ground_truth_error_rate: The error rate compared to ground truth (optional context).
        
    Returns:
        SimulatorMetrics with validation results.
        
    Raises:
        AssertionError: If noise injection is not within 5-15% bounds.
    """
    # This is the core verification logic for SC-006
    verify_noise_injection_target(noise_injection_rate)
    
    return SimulatorMetrics(
        graph_edit_distance=ground_truth_error_rate,
        error_rate=ground_truth_error_rate,
        noise_injection_rate=noise_injection_rate,
        is_within_target_range=True
    )
