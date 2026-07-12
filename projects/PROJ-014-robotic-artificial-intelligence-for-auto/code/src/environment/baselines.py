import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import math
import heapq
import logging

logger = logging.getLogger(__name__)


@dataclass
class PurePursuitConfig:
    """Configuration for Pure Pursuit controller."""
    look_ahead_distance: float = 2.0
    wheel_base: float = 2.5
    max_steer_angle: float = math.radians(45)
    speed: float = 10.0  # m/s
    k_p: float = 0.3  # Proportional gain for steering


@dataclass
class DijkstraConfig:
    """Configuration for Dijkstra path planner."""
    resolution: float = 1.0  # meters per cell
    cost_penalty: float = 1.0
    diagonal_movement: bool = True


class PurePursuitController:
    """Pure Pursuit path following controller."""

    def __init__(self, config: PurePursuitConfig):
        self.config = config
        self.current_pos = np.array([0.0, 0.0])
        self.current_heading = 0.0
        logger.info(f"PurePursuitController initialized with look_ahead={config.look_ahead_distance}")

    def update_pose(self, x: float, y: float, yaw: float):
        """Update current robot pose."""
        self.current_pos = np.array([x, y])
        self.current_heading = yaw

    def compute_steering(self, path: List[Tuple[float, float]]) -> float:
        """
        Compute steering angle to follow path.
        Returns steering angle in radians.
        """
        if not path or len(path) < 2:
            return 0.0

        # Find closest point on path
        closest_idx = 0
        min_dist = float('inf')
        for i, (px, py) in enumerate(path):
            dist = np.linalg.norm(np.array([px, py]) - self.current_pos)
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        # Find look-ahead point
        target_idx = closest_idx
        for i in range(closest_idx, len(path)):
            dist = np.linalg.norm(np.array(path[i]) - self.current_pos)
            if dist >= self.config.look_ahead_distance:
                target_idx = i
                break
        else:
            target_idx = len(path) - 1

        tx, ty = path[target_idx]
        alpha = math.atan2(ty - self.current_pos[1], tx - self.current_pos[0])
        beta = alpha - self.current_heading

        # Pure pursuit steering formula
        steering = 2.0 * self.config.wheel_base * math.sin(beta) / self.config.look_ahead_distance
        steering = np.clip(steering, -self.config.max_steer_angle, self.config.max_steer_angle)

        return float(steering)


class DijkstraPlanner:
    """Dijkstra shortest path planner on grid."""

    def __init__(self, config: DijkstraConfig):
        self.config = config
        self.log = logging.getLogger(__name__)

    def plan(self, start: Tuple[float, float], goal: Tuple[float, float], 
             occupancy_grid: np.ndarray, origin: Tuple[float, float] = (0.0, 0.0)) -> List[Tuple[float, float]]:
        """
        Plan shortest path from start to goal on occupancy grid.
        
        Args:
            start: (x, y) start position in world coordinates
            goal: (x, y) goal position in world coordinates
            occupancy_grid: 2D binary array (0=free, 1=obstacle)
            origin: (x, y) of grid origin in world coordinates
        
        Returns:
            List of (x, y) waypoints from start to goal
        """
        # Convert world coords to grid indices
        ox, oy = origin
        res = self.config.resolution
        
        start_idx = (int((start[1] - oy) / res), int((start[0] - ox) / res))
        goal_idx = (int((goal[1] - oy) / res), int((goal[0] - ox) / res))
        
        rows, cols = occupancy_grid.shape
        
        # Validate bounds
        if not (0 <= start_idx[0] < rows and 0 <= start_idx[1] < cols):
            self.log.warning(f"Start {start} out of grid bounds, clamping")
            start_idx = (max(0, min(rows-1, start_idx[0])), max(0, min(cols-1, start_idx[1])))
        if not (0 <= goal_idx[0] < rows and 0 <= goal_idx[1] < cols):
            self.log.warning(f"Goal {goal} out of grid bounds, clamping")
            goal_idx = (max(0, min(rows-1, goal_idx[0])), max(0, min(cols-1, goal_idx[1])))
        
        # Check if start or goal is in obstacle
        if occupancy_grid[start_idx] == 1:
            self.log.warning(f"Start position is obstacle, cannot plan")
            return [start]
        if occupancy_grid[goal_idx] == 1:
            self.log.warning(f"Goal position is obstacle, cannot plan")
            return [start]

        # Dijkstra's algorithm
        # Priority queue: (cost, row, col, path)
        pq = [(0.0, start_idx[0], start_idx[1], [start])]
        visited = set()
        
        # Directions: N, NE, E, SE, S, SW, W, NW (if diagonal)
        directions = [
            (-1, 0), (0, 1), (1, 0), (0, -1)
        ]
        if self.config.diagonal_movement:
            directions += [
                (-1, -1), (-1, 1), (1, -1), (1, 1)
            ]
        
        while pq:
            cost, r, c, path = heapq.heappop(pq)
            
            if (r, c) in visited:
                continue
            visited.add((r, c))
            
            # Check if goal reached
            if (r, c) == goal_idx:
                return path
            
            # Explore neighbors
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                
                if not (0 <= nr < rows and 0 <= nc < cols):
                    continue
                if (nr, nc) in visited:
                    continue
                if occupancy_grid[nr, nc] == 1:
                    continue
                
                # Calculate movement cost
                if dr == 0 or dc == 0:
                    step_cost = res
                else:
                    step_cost = res * math.sqrt(2)
                
                new_cost = cost + step_cost * self.config.cost_penalty
                
                # Convert grid back to world coordinates
                nx = nc * res + ox
                ny = nr * res + oy
                new_path = path + [(nx, ny)]
                
                heapq.heappush(pq, (new_cost, nr, nc, new_path))
        
        # No path found
        self.log.warning(f"No path found from {start} to {goal}")
        return [start]


class StochasticPolicy:
    """
    Stochastic (Random) policy for baseline comparison.
    Selects actions uniformly at random from the action space.
    """

    def __init__(self, action_space_dim: int = 2):
        """
        Initialize stochastic policy.
        
        Args:
            action_space_dim: Dimension of action space (e.g., 2 for [steering, throttle])
        """
        self.action_space_dim = action_space_dim
        self.name = "StochasticPolicy"
        logger.info(f"StochasticPolicy initialized with action_dim={action_space_dim}")

    def select_action(self, observation: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Select a random action.
        
        Args:
            observation: Current state observation (ignored for random policy)
        
        Returns:
            Random action vector
        """
        # Uniform random action in range [-1, 1] for each dimension
        # This simulates a completely random controller
        action = np.random.uniform(-1.0, 1.0, size=self.action_space_dim)
        return action

    def predict(self, observation: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict action and log probability.
        
        Args:
            observation: Current state observation
        
        Returns:
            Tuple of (action, log_prob)
        """
        action = self.select_action(observation)
        # For uniform distribution on [-1, 1]^d, log_prob = -d * log(2)
        log_prob = -self.action_space_dim * np.log(2.0)
        return action, np.array(log_prob)


def create_pure_pursuit_controller(config: Optional[PurePursuitConfig] = None) -> PurePursuitController:
    """Factory function for Pure Pursuit controller."""
    if config is None:
        config = PurePursuitConfig()
    return PurePursuitController(config)


def create_dijkstra_planner(config: Optional[DijkstraConfig] = None) -> DijkstraPlanner:
    """Factory function for Dijkstra planner."""
    if config is None:
        config = DijkstraConfig()
    return DijkstraPlanner(config)


def create_stochastic_policy(action_space_dim: int = 2) -> StochasticPolicy:
    """Factory function for Stochastic policy."""
    return StochasticPolicy(action_space_dim)