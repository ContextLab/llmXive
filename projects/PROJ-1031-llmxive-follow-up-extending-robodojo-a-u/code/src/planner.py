"""
Planner module implementing A* symbolic planning with memory constraints.
"""
import time
import heapq
import logging
import tracemalloc
import sys
import os
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field

# Add parent directory to path for imports if running as script
if "code" in sys.path[0]:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
elif os.path.basename(os.path.dirname(__file__)) == "src":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import PLANNING_TIMEOUT_S, RAM_LIMIT_GB
from src.state_mapper import SymbolicState, AffordanceGraph
from src.metrics_logger import MetricsLogger, ResourceLimitExceeded

logger = logging.getLogger(__name__)

@dataclass
class ActionSequence:
    """Represents a sequence of symbolic actions."""
    actions: List[str] = field(default_factory=list)
    sub_goals: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actions": self.actions,
            "sub_goals": self.sub_goals
        }

@dataclass
class AStarNode:
    """Node for A* search."""
    state_id: str
    g_cost: float = 0.0
    h_cost: float = 0.0
    parent: Optional['AStarNode'] = None
    action: Optional[str] = None

    @property
    def f_cost(self) -> float:
        return self.g_cost + self.h_cost

    def __lt__(self, other: 'AStarNode') -> bool:
        return self.f_cost < other.f_cost

class AffordanceViolationError(Exception):
    """Raised when an action violates object affordances."""
    pass

class ResourceLimitExceeded(Exception):
    """Raised when RAM usage exceeds the configured limit."""
    pass

class AStarPlanner:
    """A* planner for symbolic action sequences."""

    def __init__(self, affordance_graph: AffordanceGraph, timeout_s: float = PLANNING_TIMEOUT_S):
        self.graph = affordance_graph
        self.timeout_s = timeout_s
        self.metrics_logger: Optional[MetricsLogger] = None

    def set_metrics_logger(self, logger: MetricsLogger):
        self.metrics_logger = logger

    def _heuristic(self, state_id: str, goal_id: str) -> float:
        """Simple heuristic: 0 if goal, 1 otherwise (uninformed search fallback)."""
        if state_id == goal_id:
            return 0.0
        # Could use BFS distance or graph topology here
        return 1.0

    def _check_memory_limit(self):
        """Check if RAM usage exceeds the limit. Raises ResourceLimitExceeded if so."""
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            current_gb = current / (1024 ** 3)
            if current_gb > RAM_LIMIT_GB:
                logger.error(f"RAM limit exceeded: {current_gb:.2f} GB > {RAM_LIMIT_GB} GB")
                raise ResourceLimitExceeded(
                    f"RAM usage {current_gb:.2f} GB exceeds limit of {RAM_LIMIT_GB} GB"
                )

    def plan(self, start_state: SymbolicState, goal_state: SymbolicState) -> ActionSequence:
        """
        Generate an action sequence from start to goal using A*.
        Enforces 60s timeout and 6GB RAM limit.
        """
        start_time = time.time()
        tracemalloc.start()

        try:
            open_set: List[AStarNode] = []
            closed_set: Set[str] = set()
            g_scores: Dict[str, float] = {start_state.state_id: 0.0}
            came_from: Dict[str, AStarNode] = {}

            start_node = AStarNode(
                state_id=start_state.state_id,
                g_cost=0.0,
                h_cost=self._heuristic(start_state.state_id, goal_state.state_id)
            )
            heapq.heappush(open_set, start_node)

            while open_set:
                # Check timeout
                if time.time() - start_time > self.timeout_s:
                    raise TimeoutError(f"Planning timed out after {self.timeout_s}s")

                # Check memory
                self._check_memory_limit()

                current = heapq.heappop(open_set)

                if current.state_id == goal_state.state_id:
                    # Reconstruct path
                    actions = []
                    sub_goals = []
                    node = current
                    while node.parent is not None:
                        actions.append(node.action)
                        sub_goals.append({"state_id": node.state_id})
                        node = node.parent
                    actions.reverse()
                    sub_goals.reverse()
                    return ActionSequence(actions=actions, sub_goals=sub_goals)

                if current.state_id in closed_set:
                    continue

                closed_set.add(current.state_id)

                # Expand neighbors
                neighbors = self.graph.get_neighbors(current.state_id)
                for neighbor_id, edge_data in neighbors.items():
                    # Validate affordances
                    if edge_data.get("requires_affordance") and \
                       edge_data["requires_affordance"] not in start_state.affordances:
                        continue

                    tentative_g = current.g_cost + edge_data.get("cost", 1.0)

                    if neighbor_id not in g_scores or tentative_g < g_scores[neighbor_id]:
                        g_scores[neighbor_id] = tentative_g
                        h = self._heuristic(neighbor_id, goal_state.state_id)
                        neighbor_node = AStarNode(
                            state_id=neighbor_id,
                            g_cost=tentative_g,
                            h_cost=h,
                            parent=current,
                            action=edge_data.get("action")
                        )
                        heapq.heappush(open_set, neighbor_node)
                        came_from[neighbor_id] = neighbor_node

            raise RuntimeError("No path found")

        finally:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            elapsed = time.time() - start_time

            # Log metrics
            if self.metrics_logger:
                metrics = {
                    "planning_time_s": elapsed,
                    "peak_ram_mb": peak / (1024 ** 2),
                    "status": "success" if current.state_id == goal_state.state_id else "failed"
                }
                self.metrics_logger.log_task_metrics(metrics)

            logger.info(f"Planning completed in {elapsed:.2f}s (Peak RAM: {peak/(1024**2):.2f} MB)")
            if elapsed > self.timeout_s:
                logger.warning(f"Planning exceeded timeout: {elapsed:.2f}s > {self.timeout_s}s")

def create_planner(affordance_graph: AffordanceGraph) -> AStarPlanner:
    """Factory function to create a planner instance."""
    return AStarPlanner(affordance_graph)

def run_planning_pipeline(start_state: SymbolicState, goal_state: SymbolicState,
                          logger_instance: Optional[MetricsLogger] = None) -> ActionSequence:
    """
    Run the full planning pipeline with memory and time constraints.
    """
    planner = create_planner(start_state.connectivity)
    if logger_instance:
        planner.set_metrics_logger(logger_instance)

    try:
        return planner.plan(start_state, goal_state)
    except ResourceLimitExceeded as e:
        logger.error(f"Resource limit exceeded during planning: {e}")
        raise
    except TimeoutError as e:
        logger.error(f"Planning timeout: {e}")
        raise

if __name__ == "__main__":
    # Simple test to verify imports and structure
    logging.basicConfig(level=logging.INFO)
    from src.state_mapper import AffordanceGraph
    g = AffordanceGraph(nodes=["A", "B"], edges=[("A", "B", {"cost": 1.0, "action": "move"})])
    planner = create_planner(g)
    s1 = SymbolicState(state_id="A", predicates=[], affordances={}, connectivity=g, replan_support=True)
    s2 = SymbolicState(state_id="B", predicates=[], affordances={}, connectivity=g, replan_support=True)
    res = run_planning_pipeline(s1, s2)
    print(f"Plan: {res.actions}")