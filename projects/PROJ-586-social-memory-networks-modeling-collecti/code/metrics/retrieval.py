"""Retrieval efficiency metrics computation."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


@dataclass
class RetrievalMetrics:
    efficiency: float = 0.0
    total_queries: int = 0
    successful_retrievals: int = 0


def compute_retrieval_efficiency(
    retrieved: Union[int, float], 
    total: Union[int, float], 
    agent_count: Union[int, List[int]]
) -> Tuple[float, RetrievalMetrics]:
    """
    Compute retrieval efficiency.
    
    Handles multiple call signatures:
    - (retrieved, total, agent_count)
    - (retrieved, total, [agent_list])
    """
    # Normalize agent_count
    if isinstance(agent_count, list):
        n = len(agent_count)
    else:
        n = agent_count
    
    if n <= 0:
        n = 1
    
    if total <= 0:
        return 0.0, RetrievalMetrics()
    
    efficiency = float(retrieved) / float(total)
    efficiency = max(0.0, min(1.0, efficiency))
    
    metrics = RetrievalMetrics(
        efficiency=efficiency,
        total_queries=int(total),
        successful_retrievals=int(retrieved)
    )
    
    return efficiency, metrics


def validate_retrieval_efficiency(efficiency: float) -> bool:
    """Validate that efficiency is in [0, 1]."""
    return 0.0 <= efficiency <= 1.0


def batch_compute_retrieval_efficiency(results: List[Dict[str, Any]]) -> List[float]:
    """Compute retrieval efficiency for a list of game results."""
    efficiencies = []
    for res in results:
        retrieved = res.get("num_queries", 0) # In simulation, we track retrieved vs queries
        total = res.get("num_queries", 1)
        agents = res.get("agent_count", 1)
        
        eff, _ = compute_retrieval_efficiency(retrieved, total, agents)
        efficiencies.append(eff)
    return efficiencies
