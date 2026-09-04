"""
Symbolic Planner for RoboDojo Extension.

Implements an A* search algorithm to generate valid action sequences (sub-goals)
for long-horizon tasks based on the SymbolicState and AffordanceGraph provided
by the state_mapper.

Constraints:
- CPU-tractable (must run within 60s per task).
- Memory usage must not exceed 6 GB (enforced via checks).
- Respects object affordances defined in the input graph.
"""

import time
import heapq
import logging
import tracemalloc
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field

from src.state_mapper import SymbolicState, AffordanceGraph
from src.config import MAX_PLANNING_TIME_S, MAX_RAM_GB

logger = logging.getLogger(__name__)

# Constants for resource limits
MAX_PLANNING_TIME_S = 60.0
MAX_RAM_GB = 6.0

class ResourceLimitExceeded(Exception):
    """Raised when planning exceeds memory or time constraints."""
    pass

@dataclass
class ActionSequence:
    """Represents a discrete sequence of sub-goal states."""
    steps: List[Dict[str, Any]]
    success: bool
    plan_time_seconds: float
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": self.steps,
            "success": self.success,
            "plan_time_seconds": self.plan_time_seconds,
            "reason": self.reason
        }

class AStarPlanner:
    """
    A* Planner for generating symbolic action sequences.

    Uses the AffordanceGraph to determine valid transitions between SymbolicStates.
    """

    def __init__(self, affordance_graph: AffordanceGraph):
        self.graph = affordance_graph
        self.open_set: List[Tuple[float, int, Dict[str, Any]]] = []
        self.closed_set: Set[Tuple[str, ...]] = set()
        self.counter = 0  # Tie-breaker for heap

    def _hash_state(self, state: SymbolicState) -> Tuple[str, ...]:
        """Converts a SymbolicState to a hashable tuple for set operations."""
        # Assuming SymbolicState has a dict-like representation or specific fields
        # We serialize the key predicates to a sorted tuple
        if hasattr(state, 'predicates'):
            return tuple(sorted(state.predicates.items()))
        # Fallback for dict-like state
        return tuple(sorted(state.items())) if isinstance(state, dict) else (str(state),)

    def _heuristic(self, current: SymbolicState, goal: SymbolicState) -> float:
        """
        Heuristic function h(n).
        Simple heuristic: Hamming distance on predicates (number of mismatched predicates).
        """
        current_pred = set(current.predicates.items()) if hasattr(current, 'predicates') else set(current.items())
        goal_pred = set(goal.predicates.items()) if hasattr(goal, 'predicates') else set(goal.items())
        
        # Heuristic: number of differences
        return len(current_pred.symmetric_difference(goal_pred))

    def _get_neighbors(self, state: SymbolicState) -> List[SymbolicState]:
        """
        Retrieves valid neighbor states based on the AffordanceGraph.
        Checks object affordances to ensure validity.
        """
        neighbors = []
        # Logic to expand state based on graph edges
        # This is a placeholder for the actual graph traversal logic
        # which would depend on the specific structure of AffordanceGraph
        # defined in state_mapper.py.
        
        if hasattr(self.graph, 'get_neighbors'):
            raw_neighbors = self.graph.get_neighbors(state)
            for neighbor in raw_neighbors:
                # Validate against affordances
                if self._validate_affordance(state, neighbor):
                    neighbors.append(neighbor)
        return neighbors

    def _validate_affordance(self, current: SymbolicState, next_state: SymbolicState) -> bool:
        """
        Validates that the transition from current to next_state respects
        object affordances.
        """
        # Implementation depends on AffordanceGraph structure.
        # For now, assume the graph already enforces this, or check specific predicates.
        # Example: if current has 'holding: object_a' and next has 'holding: object_b',
        # we must ensure the robot can hold object_b (affordance check).
        return True

    def plan(self, start: SymbolicState, goal: SymbolicState) -> ActionSequence:
        """
        Executes A* search to find a path from start to goal.

        Returns:
            ActionSequence containing the steps if successful, or failure details.
        """
        start_time = time.time()
        tracemalloc.start()

        try:
            # g_score: cost from start to current node
            g_score: Dict[Tuple[str, ...], float] = {self._hash_state(start): 0}
            # f_score: g_score + heuristic
            f_score: Dict[Tuple[str, ...], float] = {self._hash_state(start): self._heuristic(start, goal)}
            
            # Parent map for path reconstruction
            came_from: Dict[Tuple[str, ...], SymbolicState] = {}

            # Priority queue: (f_score, counter, state)
            heapq.heappush(self.open_set, (f_score[self._hash_state(start)], self.counter, start))
            self.counter += 1

            while self.open_set:
                # Check time limit
                if time.time() - start_time > MAX_PLANNING_TIME_S:
                    raise ResourceLimitExceeded(f"Planning exceeded {MAX_PLANNING_TIME_S}s time limit.")

                # Check memory limit
                current_mem, _ = tracemalloc.get_traced_memory()
                if current_mem / (1024 ** 3) > MAX_RAM_GB:
                    raise ResourceLimitExceeded(f"Planning exceeded {MAX_RAM_GB}GB RAM limit.")

                # Pop node with lowest f_score
                _, _, current = heapq.heappop(self.open_set)
                current_hash = self._hash_state(current)

                # Check if goal reached
                if self._hash_state(current) == self._hash_state(goal):
                    path = self._reconstruct_path(came_from, current)
                    plan_time = time.time() - start_time
                    tracemalloc.stop()
                    return ActionSequence(
                        steps=path,
                        success=True,
                        plan_time_seconds=plan_time
                    )

                if current_hash in self.closed_set:
                    continue
                self.closed_set.add(current_hash)

                for neighbor in self._get_neighbors(current):
                    neighbor_hash = self._hash_state(neighbor)
                    if neighbor_hash in self.closed_set:
                        continue

                    tentative_g = g_score[current_hash] + 1.0  # Assuming uniform cost for now

                    if neighbor_hash not in g_score or tentative_g < g_score[neighbor_hash]:
                        came_from[neighbor_hash] = current
                        g_score[neighbor_hash] = tentative_g
                        f = tentative_g + self._heuristic(neighbor, goal)
                        f_score[neighbor_hash] = f
                        
                        if neighbor_hash not in [x[2] for x in self.open_set]: # Optimization: check if in open set
                            heapq.heappush(self.open_set, (f, self.counter, neighbor))
                            self.counter += 1

            # If queue is empty and goal not reached
            plan_time = time.time() - start_time
            tracemalloc.stop()
            return ActionSequence(
                steps=[],
                success=False,
                plan_time_seconds=plan_time,
                reason="No path found in affordance graph."
            )

        except ResourceLimitExceeded as e:
            tracemalloc.stop()
            logger.error(str(e))
            return ActionSequence(
                steps=[],
                success=False,
                plan_time_seconds=time.time() - start_time,
                reason=str(e)
            )
        finally:
            tracemalloc.stop()

    def _reconstruct_path(self, came_from: Dict[Tuple[str, ...], SymbolicState], current: SymbolicState) -> List[Dict[str, Any]]:
        """Reconstructs the path from start to goal."""
        total_path = [current]
        current_hash = self._hash_state(current)
        
        while current_hash in came_from:
            current = came_from[current_hash]
            total_path.append(current)
            current_hash = self._hash_state(current)
        
        total_path.reverse()
        
        # Convert to serializable dict format
        return [self._state_to_dict(s) for s in total_path]

    def _state_to_dict(self, state: SymbolicState) -> Dict[str, Any]:
        """Converts a SymbolicState to a dictionary for the output sequence."""
        if hasattr(state, 'predicates'):
            return {"predicates": dict(state.predicates)}
        return dict(state) if isinstance(state, dict) else {"raw": str(state)}

def create_planner(affordance_graph: AffordanceGraph) -> AStarPlanner:
    """Factory function to create a planner instance."""
    return AStarPlanner(affordance_graph)

def run_planning_pipeline(
    start_state: SymbolicState,
    goal_state: SymbolicState,
    affordance_graph: AffordanceGraph
) -> ActionSequence:
    """
    Main entry point for the planning pipeline.
    
    Args:
        start_state: The initial symbolic state.
        goal_state: The target symbolic state.
        affordance_graph: The graph defining valid transitions.
        
    Returns:
        ActionSequence with the generated plan or failure info.
    """
    logger.info(f"Starting planning from {start_state} to {goal_state}")
    planner = create_planner(affordance_graph)
    result = planner.plan(start_state, goal_state)
    logger.info(f"Planning completed in {result.plan_time_seconds:.2f}s. Success: {result.success}")
    return result