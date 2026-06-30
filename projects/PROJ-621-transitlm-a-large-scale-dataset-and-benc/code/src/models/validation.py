"""
Graph-traversal oracle for validating route sequences against a ground-truth GTFS graph.

This module provides functions to validate whether a generated sequence of stations
represents a valid path in the transit network, checking for:
- Infinite loops (revisiting stations)
- Hallucinated stations (stations not in the graph)
- Connectivity validity (consecutive stations must be directly connected)
- Exact match scoring against ground truth
"""
import logging
from typing import List, Optional, Tuple, Dict, Any, Set
from src.contracts.models import GTFSGraph, RouteSequence, ValidationResult, ValidationStatus
from src.lib.config import get_logger

def check_infinite_loop(sequence: List[str]) -> Tuple[bool, str]:
    """
    Check if a station sequence contains an infinite loop (revisits any station).
    
    Args:
        sequence: List of station IDs in the order visited.
        
    Returns:
        Tuple of (is_valid, error_message).
        is_valid=True if no loops detected.
    """
    seen: Set[str] = set()
    for i, station in enumerate(sequence):
        if station in seen:
            return False, f"Infinite loop detected: station '{station}' revisited at position {i}"
        seen.add(station)
    return True, ""

def check_hallucinated_station(sequence: List[str], graph: GTFSGraph) -> Tuple[bool, str]:
    """
    Check if any station in the sequence does not exist in the graph.
    
    Args:
        sequence: List of station IDs.
        graph: The ground-truth GTFSGraph.
        
    Returns:
        Tuple of (is_valid, error_message).
        is_valid=True if all stations exist in the graph.
    """
    valid_stations = set(graph.stations.keys())
    for i, station in enumerate(sequence):
        if station not in valid_stations:
            return False, f"Hallucinated station detected: '{station}' at position {i} is not in the graph"
    return True, ""

def check_connectivity(sequence: List[str], graph: GTFSGraph) -> Tuple[bool, str]:
    """
    Verify that every consecutive pair of stations in the sequence is connected.
    
    Args:
        sequence: List of station IDs.
        graph: The ground-truth GTFSGraph.
        
    Returns:
        Tuple of (is_valid, error_message).
        is_valid=True if all consecutive pairs are connected.
    """
    if len(sequence) < 2:
        return True, ""
    
    # Build adjacency set for O(1) lookups
    # The graph stores edges as (from_station, to_station) in graph.edges
    adjacency: Dict[str, Set[str]] = {}
    for edge in graph.edges:
        src = edge.from_station
        dst = edge.to_station
        if src not in adjacency:
            adjacency[src] = set()
        adjacency[src].add(dst)
        # Transit is typically bidirectional for validation purposes unless specified
        if dst not in adjacency:
            adjacency[dst] = set()
        adjacency[dst].add(src)
    
    for i in range(len(sequence) - 1):
        current = sequence[i]
        next_station = sequence[i + 1]
        if current not in adjacency or next_station not in adjacency[current]:
            return False, f"Connectivity violation: '{current}' and '{next_station}' are not directly connected"
    
    return True, ""

def calculate_exact_match_score(predicted: List[str], ground_truth: List[str]) -> float:
    """
    Calculate the Exact Match score between predicted and ground truth sequences.
    
    Exact Match is 1.0 if the sequences are identical, 0.0 otherwise.
    
    Args:
        predicted: Predicted station sequence.
        ground_truth: Ground truth station sequence.
        
    Returns:
        Float score (0.0 or 1.0).
    """
    if len(predicted) != len(ground_truth):
        return 0.0
    
    for p, g in zip(predicted, ground_truth):
        if p != g:
            return 0.0
    return 1.0

def validate_route_sequence(
    sequence: RouteSequence,
    graph: GTFSGraph,
    ground_truth: Optional[List[str]] = None
) -> ValidationResult:
    """
    Validate a route sequence against the ground-truth graph.
    
    This function performs a comprehensive validation:
    1. Checks for infinite loops
    2. Checks for hallucinated stations
    3. Checks connectivity between consecutive stations
    4. Calculates Exact Match score if ground truth is provided
    
    Args:
        sequence: The RouteSequence to validate.
        graph: The ground-truth GTFSGraph.
        ground_truth: Optional ground truth station sequence for scoring.
        
    Returns:
        ValidationResult with status, scores, and error details.
    """
    logger = get_logger(__name__)
    station_list = sequence.stations
    
    errors: List[str] = []
    is_valid = True
    
    # Check 1: Infinite loop
    loop_valid, loop_error = check_infinite_loop(station_list)
    if not loop_valid:
        is_valid = False
        errors.append(loop_error)
        logger.warning(f"Loop validation failed for sequence {sequence.id}: {loop_error}")
    
    # Check 2: Hallucinated stations
    station_valid, station_error = check_hallucinated_station(station_list, graph)
    if not station_valid:
        is_valid = False
        errors.append(station_error)
        logger.warning(f"Station validation failed for sequence {sequence.id}: {station_error}")
    
    # Check 3: Connectivity
    connect_valid, connect_error = check_connectivity(station_list, graph)
    if not connect_valid:
        is_valid = False
        errors.append(connect_error)
        logger.warning(f"Connectivity validation failed for sequence {sequence.id}: {connect_error}")
    
    # Calculate scores
    exact_match = 0.0
    if ground_truth is not None:
        exact_match = calculate_exact_match_score(station_list, ground_truth)
    
    # Determine final status
    status = ValidationStatus.VALID if is_valid else ValidationStatus.INVALID
    
    result = ValidationResult(
        sequence_id=sequence.id,
        status=status,
        is_valid=is_valid,
        exact_match_score=exact_match,
        connectivity_valid=is_valid and len(errors) == 0,
        errors=errors,
        validation_details={
            "loop_check": loop_valid,
            "station_check": station_valid,
            "connectivity_check": connect_valid,
            "sequence_length": len(station_list),
            "ground_truth_length": len(ground_truth) if ground_truth else 0
        }
    )
    
    logger.info(f"Validation complete for {sequence.id}: status={status}, exact_match={exact_match:.4f}")
    return result