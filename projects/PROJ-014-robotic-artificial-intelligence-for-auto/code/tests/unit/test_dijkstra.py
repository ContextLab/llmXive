import numpy as np
import pytest
import sys
import os
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.environment.baselines import DijkstraPlanner, DijkstraConfig

class TestDijkstraPlanner:
    def test_simple_grid_path(self):
        """Test path finding on a simple open grid."""
        # 5x5 grid, all free
        grid = np.zeros((5, 5), dtype=int)
        planner = DijkstraPlanner()
        
        start = (0, 0)
        goal = (4, 4)
        
        path = planner.plan(grid, start, goal)
        
        assert path is not None, "Path should exist on open grid"
        assert path[0] == start, "Path should start at start"
        assert path[-1] == goal, "Path should end at goal"
        # Check connectivity
        for i in range(len(path) - 1):
            r1, c1 = path[i]
            r2, c2 = path[i+1]
            dist = abs(r1 - r2) + abs(c1 - c2)
            # Allow diagonal (dist=1 in Chebyshev, but Euclidean logic in planner)
            # In 8-connectivity, max delta is 1
            assert max(abs(r1 - r2), abs(c1 - c2)) == 1, "Path must be connected"

    def test_obstacle_avoidance(self):
        """Test path finding with an obstacle in the middle."""
        grid = np.zeros((5, 5), dtype=int)
        # Block the direct diagonal path
        grid[2, 2] = 1
        
        planner = DijkstraPlanner()
        start = (0, 0)
        goal = (4, 4)
        
        path = planner.plan(grid, start, goal)
        
        assert path is not None, "Path should exist around obstacle"
        assert (2, 2) not in path, "Path should not go through obstacle"

    def test_no_path(self):
        """Test when no path exists (blocked goal)."""
        grid = np.zeros((5, 5), dtype=int)
        grid[4, 4] = 1 # Goal is blocked
        
        planner = DijkstraPlanner()
        start = (0, 0)
        goal = (4, 4)
        
        path = planner.plan(grid, start, goal)
        assert path is None, "Path should be None if goal is blocked"

    def test_start_blocked(self):
        """Test when start is blocked."""
        grid = np.zeros((5, 5), dtype=int)
        grid[0, 0] = 1 # Start is blocked
        
        planner = DijkstraPlanner()
        start = (0, 0)
        goal = (4, 4)
        
        path = planner.plan(grid, start, goal)
        assert path is None, "Path should be None if start is blocked"

    def test_out_of_bounds(self):
        """Test handling of out of bounds coordinates."""
        grid = np.zeros((5, 5), dtype=int)
        planner = DijkstraPlanner()
        
        # Start out of bounds
        path = planner.plan(grid, (-1, 0), (4, 4))
        assert path is None
        
        # Goal out of bounds
        path = planner.plan(grid, (0, 0), (10, 10))
        assert path is None

    def test_diagonal_movement(self):
        """Test that diagonal movement is allowed by default."""
        grid = np.zeros((3, 3), dtype=int)
        planner = DijkstraPlanner(config=DijkstraConfig(diagonal_movement=True))
        
        start = (0, 0)
        goal = (2, 2)
        
        path = planner.plan(grid, start, goal)
        assert path is not None
        # With diagonal, shortest path is 3 steps (0,0)->(1,1)->(2,2)
        # Length should be 3 (start, mid, goal)
        assert len(path) == 3

    def test_no_diagonal_movement(self):
        """Test that diagonal movement can be disabled."""
        grid = np.zeros((3, 3), dtype=int)
        planner = DijkstraPlanner(config=DijkstraConfig(diagonal_movement=False))
        
        start = (0, 0)
        goal = (2, 2)
        
        path = planner.plan(grid, start, goal)
        assert path is not None
        # Without diagonal, shortest path is 5 steps (Manhattan distance 4 + 1 start)
        # (0,0)->(0,1)->(0,2)->(1,2)->(2,2) or similar
        assert len(path) == 5

    def test_factory_function(self):
        """Test the factory function."""
        planner = DijkstraPlanner()
        assert isinstance(planner, DijkstraPlanner)
        
        planner_custom = DijkstraPlanner(config=DijkstraConfig(grid_resolution=1.0))
        assert planner_custom.config.grid_resolution == 1.0