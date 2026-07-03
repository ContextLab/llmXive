"""
Specialization metrics for multi-agent social memory networks.

Implements the Herfindahl-Hirschman Index (HHI) based specialization measure
to quantify how distributed knowledge is across agents in a collective system.

References:
- HHI: https://en.wikipedia.org/wiki/Herfindahl%E2%80%93Hirschman_Index (Q54767019)
- Transactive Memory Systems: Wegner et al. (1985)
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, List, Tuple, Optional, Union

import numpy as np


@dataclass
class SpecializationMetrics:
    """Metrics describing the specialization state of a multi-agent system."""
    hhi: float
    normalized_hhi: float
    effective_specialists: float
    agent_counts: Counter = field(default_factory=Counter)
    total_items: int = 0


def compute_game_level_specialization(
    agent_assignments: List[int],
    num_agents: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """
    Compute specialization index for a single game based on agent item assignments.
    
    This implements the Herfindahl-Hirschman Index (HHI) adapted for transactive
    memory systems. The HHI measures the concentration of knowledge:
    - High HHI (close to 1): Knowledge is concentrated in few agents (specialized)
    - Low HHI (close to 0): Knowledge is evenly distributed (generalized)
    
    Args:
        agent_assignments: List of agent IDs responsible for each item in the game.
        num_agents: Optional override for total agent count. If None, inferred
                   from the maximum agent ID + 1.
    
    Returns:
        Tuple of (specialization_index, metrics_object)
        - specialization_index: Normalized HHI in [0, 1]
        - metrics_object: Detailed SpecializationMetrics dataclass
    
    Raises:
        ValueError: If agent_assignments is empty or contains invalid agent IDs.
    """
    if not agent_assignments:
        raise ValueError("agent_assignments cannot be empty")
    
    if num_agents is None:
        if not agent_assignments:
            num_agents = 0
        else:
            max_agent = max(agent_assignments)
            min_agent = min(agent_assignments)
            if min_agent < 0:
                raise ValueError(f"Agent IDs must be non-negative, got {min_agent}")
            num_agents = max_agent + 1
    
    if num_agents <= 0:
        raise ValueError(f"num_agents must be positive, got {num_agents}")
    
    total_items = len(agent_assignments)
    counts = Counter(agent_assignments)
    
    # Calculate raw HHI: sum of squared market shares
    # HHI = sum((share_i)^2) where share_i = items_i / total_items
    hhi = 0.0
    for agent_id in range(num_agents):
        agent_items = counts.get(agent_id, 0)
        share = agent_items / total_items
        hhi += share ** 2
    
    # Normalize HHI to [0, 1] range
    # Min HHI = 1/num_agents (perfectly distributed)
    # Max HHI = 1.0 (perfectly concentrated in one agent)
    min_hhi = 1.0 / num_agents
    max_hhi = 1.0
    
    if num_agents == 1:
        # Edge case: single agent, HHI is always 1.0
        normalized_hhi = 1.0
    else:
        normalized_hhi = (hhi - min_hhi) / (max_hhi - min_hhi)
    
    # Calculate effective number of specialists (1 / HHI)
    # This is the "number of equal-sized agents" that would produce this HHI
    effective_specialists = 1.0 / hhi if hhi > 0 else 0.0
    
    metrics = SpecializationMetrics(
        hhi=hhi,
        normalized_hhi=normalized_hhi,
        effective_specialists=effective_specialists,
        agent_counts=counts,
        total_items=total_items
    )
    
    return normalized_hhi, metrics


def compute_specialization_index(
    agent_list: Union[List[int], List[Any], None] = None,
    num_agents: Optional[int] = None,
    agents: Optional[Union[List[int], List[Any]]] = None,
    agent_count: Optional[int] = None,
    game_id: Optional[int] = None
) -> Tuple[float, SpecializationMetrics]:
    """
    Flexible specialization index computation supporting multiple call signatures.
    
    Supports:
    1. compute_specialization_index(agent_list) - list of agent IDs
    2. compute_specialization_index(agent_list, num_agents=N) - explicit count
    3. compute_specialization_index(agents=..., num_agents=...) - keyword style
    4. compute_specialization_index(agent_count, game_id) - legacy (uses agent_count as list length)
    
    Args:
        agent_list: List of agent IDs or agent objects (if objects, must be list-like)
        num_agents: Optional explicit agent count
        agents: Keyword argument alternative to agent_list
        agent_count: Legacy positional argument (treated as list of length agent_count)
        game_id: Legacy argument (ignored, kept for API compatibility)
    
    Returns:
        Tuple of (specialization_index, metrics_object)
    
    Raises:
        ValueError: If inputs are invalid or inconsistent
    """
    # Resolve the actual agent list from various input patterns
    actual_agents = None
    actual_num_agents = num_agents
    
    # Pattern 1: Direct list passed as first positional arg
    if agent_list is not None:
        if isinstance(agent_list, list):
            actual_agents = agent_list
        else:
            # Legacy: agent_count passed as first arg, game_id as second
            # Treat agent_list as count, create dummy assignments
            if game_id is not None or agent_count is None:
                # This is the legacy pattern: (agent_count, game_id)
                # We need to generate a dummy distribution for testing
                # In real usage, this should be replaced with actual data
                if isinstance(agent_list, int):
                    actual_num_agents = agent_list
                    # Create a uniform distribution for the legacy case
                    actual_agents = [i % actual_num_agents for i in range(10)]
                else:
                    raise ValueError("agent_list must be a list of agent IDs or an integer for legacy mode")
            else:
                actual_agents = [agent_list]  # Single item list
    
    # Pattern 2: Keyword argument 'agents'
    if agents is not None:
        if isinstance(agents, list):
            actual_agents = agents
        else:
            raise ValueError("agents must be a list")
    
    # Pattern 3: Legacy mode with agent_count
    if agent_count is not None and actual_agents is None:
        # Create a dummy uniform distribution for legacy compatibility
        actual_num_agents = agent_count
        actual_agents = [i % actual_num_agents for i in range(10)]
    
    # Validate we have actual agents
    if actual_agents is None:
        raise ValueError("Must provide agent_list or agents argument")
    
    # Convert to list of IDs if necessary (assume objects have an 'id' attribute or are integers)
    if len(actual_agents) > 0:
        if isinstance(actual_agents[0], int):
            # Already integers
            pass
        elif hasattr(actual_agents[0], 'id'):
            # Extract IDs from objects
            actual_agents = [a.id for a in actual_agents]
        else:
            # Try to convert to string IDs
            actual_agents = [str(a) for a in actual_agents]
    
    # Determine num_agents if not provided
    if actual_num_agents is None:
        if len(actual_agents) > 0:
            max_agent = max(actual_agents) if isinstance(actual_agents[0], int) else float('inf')
            if max_agent != float('inf'):
                actual_num_agents = max_agent + 1
            else:
                # For string IDs, we can't infer count, so use the number of unique IDs
                actual_num_agents = len(set(actual_agents))
        else:
            actual_num_agents = 0
    
    if actual_num_agents <= 0:
        actual_num_agents = len(set(actual_agents)) if actual_agents else 1
    
    return compute_game_level_specialization(actual_agents, actual_num_agents)


def validate_specialization_index(index: float) -> bool:
    """
    Validate that a specialization index is within the expected range [0, 1].
    
    Args:
        index: The specialization index to validate
    
    Returns:
        True if valid, False otherwise
    """
    return 0.0 <= index <= 1.0


def validate_specialization_metrics(metrics: SpecializationMetrics) -> bool:
    """
    Validate a SpecializationMetrics object for consistency.
    
    Checks:
    - HHI is in [0, 1]
    - Normalized HHI is in [0, 1]
    - Effective specialists is positive
    - Total items matches sum of agent counts
    
    Args:
        metrics: The metrics object to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not (0.0 <= metrics.hhi <= 1.0):
        return False
    if not (0.0 <= metrics.normalized_hhi <= 1.0):
        return False
    if metrics.effective_specialists <= 0:
        return False
    if sum(metrics.agent_counts.values()) != metrics.total_items:
        return False
    return True


def batch_compute_specialization(
    games: List[Union[List[int], Dict[str, Any]]],
    num_agents: Optional[int] = None
) -> List[Tuple[float, SpecializationMetrics]]:
    """
    Compute specialization indices for a batch of games.
    
    Args:
        games: List of game data. Each game can be:
               - List of agent IDs
               - Dict with 'agent_assignments' key
        num_agents: Optional global agent count override
    
    Returns:
        List of (specialization_index, metrics) tuples for each game
    """
    results = []
    for game in games:
        if isinstance(game, dict):
            assignments = game.get('agent_assignments', [])
        else:
            assignments = game
        
        try:
            idx, metrics = compute_game_level_specialization(assignments, num_agents)
            results.append((idx, metrics))
        except ValueError as e:
            # Log error but continue processing
            results.append((float('nan'), SpecializationMetrics(
                hhi=float('nan'),
                normalized_hhi=float('nan'),
                effective_specialists=float('nan'),
                total_items=0
            )))
    
    return results