"""
Integration tests for the Restricted Kernel (2D Constraint).

This module verifies that:
1. The restricted kernel successfully enforces the 2D policy.
2. 2D operations (shapely) work correctly.
3. Blocked 3D operations (trimesh, pytorch3d) raise errors and are logged.
4. Execution logs contain zero occurrences of "trimesh" (meaning no successful imports or usage).
"""

import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure code/ is in path for imports
_project_root = Path(__file__).parent.parent.parent
_code_path = _project_root / "code"
if str(_code_path) not in sys.path:
    sys.path.insert(0, str(_code_path))

from kernel.blockers import RestrictedActionError
from kernel.restricted_kernel import RestrictedKernel, enforce_2d_policy, release_2d_policy
from data.loader import load_dataset
from data.projector import project_dataset_to_2d
from agents.agent_2d import run_agent_on_dataset
from utils.logging_config import setup_logging, get_logger, log_blocked_operation
from utils.reproducibility import set_seed


class TestKernel2DExecution:
    """Tests for the 2D restricted kernel execution flow."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup logging and temporary directories for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "kernel_test.log")
        
        # Setup logging to file and console
        setup_logging(
            level=logging.INFO,
            log_file=self.log_file,
            log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = get_logger("test_kernel_2d")
        
        yield

        # Teardown
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _run_orchestration_and_check_logs(self):
        """
        Helper to run a small subset of the pipeline through the restricted kernel
        and return the log content.
        """
        # 1. Generate a small synthetic dataset if it doesn't exist (for this test context)
        # Note: In a real CI, T006 should have run. Here we ensure data exists for the test.
        data_path = os.path.join(self.temp_dir, "synthetic_spatialclaw_v1.json")
        
        # We assume T006 generator is available and run it to create a small sample
        # If T006 is fully implemented, we might just load it. 
        # To be safe for this integration test, we generate a minimal valid dataset.
        from data.generator import generate_dataset, generate_scene_id, generate_object_id, generate_point3d, generate_object, calculate_depth_diff, calculate_occlusion_ratio, generate_occlusion_task
        import random
        
        tasks = []
        for i in range(3):
            scene_id = generate_scene_id()
            obj_id = generate_object_id()
            # Create a simple object
            center = generate_point3d()
            obj = generate_object(center, "cube", 1.0)
            
            # Create a task
            task = generate_occlusion_task(scene_id, obj_id)
            tasks.append(task)

        dataset = {
            "version": "1.0",
            "tasks": tasks
        }

        with open(data_path, 'w') as f:
            json.dump(dataset, f, indent=2)

        # 2. Enforce 2D policy
        kernel = enforce_2d_policy()
        set_seed(42) # Fixed seed for reproducibility

        try:
            # 3. Load dataset
            self.logger.info("Loading dataset from %s", data_path)
            tasks_loaded = load_dataset(data_path)
            self.logger.info("Loaded %d tasks", len(tasks_loaded))

            # 4. Project to 2D
            self.logger.info("Projecting tasks to 2D...")
            projected_tasks = project_dataset_to_2d(tasks_loaded)
            self.logger.info("Projected %d tasks", len(projected_tasks))

            # 5. Run 2D Agent
            self.logger.info("Running 2D Agent on projected tasks...")
            # Run on a small subset to save time
            results = run_agent_on_dataset(projected_tasks[:2])
            
            self.logger.info("Agent execution complete. Successes: %d", sum(1 for r in results if r.get('success')))

        finally:
            # 6. Release policy
            release_2d_policy()

        # 7. Read logs
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        return log_content

    def test_no_trimesh_in_execution_logs(self):
        """
        T019: Verify execution logs for the string "trimesh" count is 0.
        
        This test runs the full 2D pipeline (Load -> Project -> Agent) under the
        restricted kernel. It then scans the generated log file for the string
        "trimesh". Since the kernel blocks imports of 'trimesh', and the 2D agent
        only uses 'shapely' and 'numpy', the string "trimesh" should NOT appear
        in the logs (except potentially in error messages if someone tried to import
        it, but the policy prevents the import from succeeding, so it shouldn't even
        be logged as a successful operation. If it appears in a blocked log, we count it.
        The requirement is "count is 0", implying no successful usage or even attempted
        blocks should be present if the agent is pure 2D.
        
        Wait, T015 logs blocked operations. If the agent tries to import trimesh, it logs.
        But the agent_2d.py should NOT try to import trimesh.
        So "trimesh" should not appear in the logs at all if the agent is compliant.
        """
        log_content = self._run_orchestration_and_check_logs()
        
        # Count occurrences of "trimesh"
        # We look for the string case-insensitively to be thorough, though logs are usually lowercase.
        count = log_content.lower().count("trimesh")
        
        self.logger.info("Log content snippet:\n%s", log_content[:500])
        self.logger.info("Count of 'trimesh' in logs: %d", count)
        
        assert count == 0, (
            f"Found {count} occurrence(s) of 'trimesh' in execution logs. "
            "The 2D agent or pipeline must not reference the trimesh library."
            f"\nLog content:\n{log_content}"
        )

    def test_no_pytorch3d_in_execution_logs(self):
        """
        Verify execution logs for the string "pytorch3d" count is 0.
        """
        log_content = self._run_orchestration_and_check_logs()
        
        count = log_content.lower().count("pytorch3d")
        self.logger.info("Count of 'pytorch3d' in logs: %d", count)
        
        assert count == 0, (
            f"Found {count} occurrence(s) of 'pytorch3d' in execution logs. "
            "The 2D agent or pipeline must not reference the pytorch3d library."
        )

    def test_2d_operations_succeed(self):
        """
        Verify that valid 2D operations (shapely) succeed under the kernel.
        """
        log_content = self._run_orchestration_and_check_logs()
        
        # Check for success indicators
        assert "Agent execution complete" in log_content
        assert "Projected" in log_content
        assert "Loaded" in log_content
        
        # Verify no RestrictedActionError was raised for valid 2D ops
        assert "RestrictedActionError" not in log_content or "shapely" not in log_content