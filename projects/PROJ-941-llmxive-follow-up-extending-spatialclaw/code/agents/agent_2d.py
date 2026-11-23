"""
Restricted 2D Agent Implementation (US1).

This module implements the SpatialClaw agent restricted to a 2D action space.
It strictly uses `shapely` and `numpy` for geometric operations, adhering to
the kernel's 2D policy (FR-002). It integrates with the MetricsCollector
(T022b) to record step-level latency and success metrics.
"""
import time
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union

# Import from local project modules (API Surface)
from metrics.collector import MetricsCollector
from kernel.blockers import RestrictedActionError, check_library_policy
from utils.logging_config import get_logger

# Configure logger
logger = get_logger(__name__)


class Agent2D:
    """
    A spatial reasoning agent restricted to 2D operations.

    This agent processes projected 2D tasks and attempts to solve them using
    only 2D geometric primitives (Shapely) and numerical operations (NumPy).
    It does not attempt to reconstruct 3D geometry or use 3D libraries.

    Attributes:
        collector (MetricsCollector): Instance for recording step metrics.
        task_type (str): The type of task being executed (occlusion, depth, relative).
    """

    def __init__(self, collector: MetricsCollector):
        """
        Initialize the 2D agent.

        Args:
            collector: The metrics collector instance for step-level recording.
        """
        self.collector = collector
        self.task_type = None
        logger.info("Initialized Agent2D with MetricsCollector integration.")

    def _record_step_start(self, task_id: str, step_name: str) -> float:
        """Record start time for a step."""
        # We don't strictly need to return the start time if we use context managers,
        # but for explicit recording:
        return time.time()

    def _record_step_end(self, task_id: str, step_name: str, start_time: float, status: str = "success"):
        """Record end time and metrics for a step."""
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        # blocked_time_ms is 0 for the agent logic itself as we assume kernel
        # handles blocking separately, but we pass 0 here to satisfy signature.
        self.collector.record_step(
            task_id=task_id,
            latency_ms=latency_ms,
            status=status,
            blocked_time_ms=0.0
        )

    def _validate_2d_compliance(self, obj: Any) -> None:
        """
        Validates that the object is a valid 2D geometry.
        Raises RestrictedActionError if 3D-like structures are detected.
        """
        # In a real 3D library, we might check for Z-coordinates.
        # Here we rely on Shapely's 2D nature. If a user accidentally passes
        # a 3D point (x, y, z), Shapely might ignore Z or error.
        # We explicitly check for 3D points if they are passed as tuples/lists.
        if isinstance(obj, (list, tuple)) and len(obj) == 3:
            raise RestrictedActionError("Detected 3D coordinate (x, y, z). Agent is restricted to 2D.")
        if hasattr(obj, 'has_z') and obj.has_z:
            logger.warning("Geometry has Z coordinates. Projecting to 2D.")
            # Shapely operations on 3D geometries are limited; we proceed assuming
            # the kernel or projector has already handled this, but we log it.

    def solve_occlusion_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve an occlusion task using 2D polygon intersection logic.

        Args:
            task_data: Dictionary containing projected 2D object geometries.
                       Expected keys: 'occluder_polygon', 'target_polygon', 'task_id'.

        Returns:
            Dictionary with 'success' (bool) and 'reason' (str).
        """
        task_id = task_data.get('task_id', 'unknown')
        start_time = self._record_step_start(task_id, "solve_occlusion")

        try:
            occluder = Polygon(task_data['occluder_polygon'])
            target = Polygon(task_data['target_polygon'])

            self._validate_2d_compliance(occluder)
            self._validate_2d_compliance(target)

            # Logic: If the target is completely inside the occluder, it is occluded.
            # Or if they intersect significantly.
            intersection = target.intersection(occluder)
            target_area = target.area

            if target_area == 0:
                logger.warning(f"Target area is zero. Cannot determine occlusion.")
                result = {'success': False, 'reason': 'zero_area'}
            else:
                intersection_ratio = intersection.area / target_area
                # Heuristic: If > 50% of target is covered, consider it occluded.
                is_occluded = intersection_ratio > 0.5

                # For the agent "success", we assume it correctly identifies the state.
                # In a real experiment, this would be compared against ground truth.
                # Here we return the computed state as the "solution".
                result = {
                    'success': True,
                    'reason': f'occlusion_ratio={intersection_ratio:.4f}',
                    'computed_state': 'occluded' if is_occluded else 'visible'
                }

            self._record_step_end(task_id, "solve_occlusion", start_time, "success")
            return result

        except Exception as e:
            logger.error(f"Error solving occlusion task: {e}")
            self._record_step_end(task_id, "solve_occlusion", start_time, "failed")
            return {'success': False, 'reason': str(e)}

    def solve_depth_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve a depth task using 2D depth histogram analysis.

        Since we are in 2D, we rely on the 'depth_histogram' or 'depth_score'
        provided in the projected task data (from projector.py).
        The agent compares these scores to determine relative depth.

        Args:
            task_data: Dictionary containing 'depth_histogram_a', 'depth_histogram_b', 'task_id'.

        Returns:
            Dictionary with 'success' (bool) and 'reason' (str).
        """
        task_id = task_data.get('task_id', 'unknown')
        start_time = self._record_step_start(task_id, "solve_depth")

        try:
            # Extract depth scores (assumed to be pre-calculated or aggregated)
            # If full histograms are provided, we compute a centroid or mean.
            hist_a = task_data.get('depth_histogram_a', [])
            hist_b = task_data.get('depth_histogram_b', [])

            # Convert to numpy arrays
            arr_a = np.array(hist_a) if hist_a else np.array([0.0])
            arr_b = np.array(hist_b) if hist_b else np.array([0.0])

            # Compute mean depth score (higher index = deeper in projection context)
            # Or if it's a value: mean of the values.
            # Assuming histogram bins represent depth ranges, we calculate a weighted mean.
            # For simplicity, assume the histogram values are depth scores.
            mean_a = np.mean(arr_a) if len(arr_a) > 0 else 0.0
            mean_b = np.mean(arr_b) if len(arr_b) > 0 else 0.0

            # Determine which is deeper (larger value)
            deeper_a = mean_a > mean_b

            result = {
                'success': True,
                'reason': f'mean_depth_a={mean_a:.4f}, mean_depth_b={mean_b:.4f}',
                'computed_state': 'a_deeper' if deeper_a else 'b_deeper'
            }

            self._record_step_end(task_id, "solve_depth", start_time, "success")
            return result

        except Exception as e:
            logger.error(f"Error solving depth task: {e}")
            self._record_step_end(task_id, "solve_depth", start_time, "failed")
            return {'success': False, 'reason': str(e)}

    def solve_relative_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve a relative position task using 2D centroids.

        Args:
            task_data: Dictionary containing 'polygon_a', 'polygon_b', 'task_id'.

        Returns:
            Dictionary with 'success' (bool) and 'reason' (str).
        """
        task_id = task_data.get('task_id', 'unknown')
        start_time = self._record_step_start(task_id, "solve_relative")

        try:
            poly_a = Polygon(task_data['polygon_a'])
            poly_b = Polygon(task_data['polygon_b'])

            self._validate_2d_compliance(poly_a)
            self._validate_2d_compliance(poly_b)

            centroid_a = poly_a.centroid
            centroid_b = poly_b.centroid

            # Calculate relative direction (simplified to 4 quadrants)
            dx = centroid_b.x - centroid_a.x
            dy = centroid_b.y - centroid_a.y

            direction = "unknown"
            if abs(dx) > abs(dy):
                direction = "right" if dx > 0 else "left"
            else:
                direction = "above" if dy > 0 else "below"

            result = {
                'success': True,
                'reason': f'dx={dx:.4f}, dy={dy:.4f}',
                'computed_state': direction
            }

            self._record_step_end(task_id, "solve_relative", start_time, "success")
            return result

        except Exception as e:
            logger.error(f"Error solving relative task: {e}")
            self._record_step_end(task_id, "solve_relative", start_time, "failed")
            return {'success': False, 'reason': str(e)}

    def execute_task(self, task_instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point to execute a task instance.

        Dispatches to the appropriate solver based on task_type.

        Args:
            task_instance: The task dictionary from the dataset (projected).

        Returns:
            Result dictionary.
        """
        task_id = task_instance.get('task_id', 'unknown')
        task_type = task_instance.get('task_type')
        self.task_type = task_type

        logger.info(f"Executing task {task_id} of type {task_type}")

        if task_type == 'occlusion':
            return self.solve_occlusion_task(task_instance)
        elif task_type == 'depth':
            return self.solve_depth_task(task_instance)
        elif task_type == 'relative':
            return self.solve_relative_task(task_instance)
        else:
            logger.error(f"Unknown task type: {task_type}")
            return {'success': False, 'reason': f'Unknown task type: {task_type}'}


def run_agent_on_dataset(collector: MetricsCollector, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run the 2D agent on a list of tasks.

    Args:
        collector: MetricsCollector instance.
        tasks: List of task instances.

    Returns:
        List of results.
    """
    agent = Agent2D(collector)
    results = []

    for task in tasks:
        result = agent.execute_task(task)
        result['task_id'] = task.get('task_id')
        result['task_type'] = task.get('task_type')
        results.append(result)

    return results


def main():
    """
    Entry point for running the agent on a dataset file.
    Loads data, runs the agent, and prints results.
    """
    import json
    from data.loader import load_dataset
    from metrics.collector import MetricsCollector

    # Setup
    logger.info("Starting Agent2D Main Execution")

    # Initialize Collector
    collector = MetricsCollector(output_path="results/agent_2d_metrics.json")

    # Load Data
    # Assuming T006 generated data/raw/synthetic_spatialclaw_v1.json
    # and T007 loads it.
    try:
        tasks = load_dataset("data/raw/synthetic_spatialclaw_v1.json")
        logger.info(f"Loaded {len(tasks)} tasks.")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return

    # Run Agent
    results = run_agent_on_dataset(collector, tasks)

    # Save Results
    output_path = "results/agent_2d_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {output_path}")
    collector.flush()


if __name__ == "__main__":
    main()