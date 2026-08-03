"""
Unit tests for code/data/projector.py ensuring FR-002 compliance.

Specifically asserts that no 3D libraries (trimesh, pytorch3d, open3d)
are imported or called during the projection process.
"""
import sys
import builtins
import unittest
from unittest.mock import patch, MagicMock
from types import ModuleType

# Ensure we are testing the actual projector module
sys.path.insert(0, 'code')

class TestProjectorNo3DLibraries(unittest.TestCase):
    """
    Test suite to verify that the projector module does not import or use 3D libraries.
    """

    def setUp(self):
        # Clear any previously loaded projector module to ensure a fresh import
        if 'data.projector' in sys.modules:
            del sys.modules['data.projector']
        # Also clear any blocked libraries just in case
        for blocked in ['trimesh', 'pytorch3d', 'open3d']:
            if blocked in sys.modules:
                del sys.modules[blocked]

    def _block_import(self, name, *args, **kwargs):
        """Mock import function that raises an error for blocked libraries."""
        blocked_libs = {'trimesh', 'pytorch3d', 'open3d'}
        if name in blocked_libs or any(b in name for b in blocked_libs):
            raise ImportError(f"FR-002 Violation: Import of 3D library '{name}' is forbidden in projector.")
        return self._original_import(name, *args, **kwargs)

    def test_no_blocked_imports_on_module_load(self):
        """
        Assert that importing `data.projector` does not trigger the import of 
        any blocked 3D libraries.
        """
        # Patch builtins.__import__ to intercept and block 3D libraries
        self._original_import = builtins.__import__
        
        with patch('builtins.__import__', side_effect=self._block_import):
            # Attempt to import the projector module
            # If the module itself tries to import trimesh/pytorch3d, this will raise ImportError
            try:
                import data.projector
            except ImportError as e:
                if "FR-002 Violation" in str(e):
                    self.fail(f"Projector module violates FR-002: {e}")
                # Re-raise if it's a different import error (e.g., missing allowed dependency)
                raise

    def test_project_task_to_2d_no_blocked_calls(self):
        """
        Assert that calling project_task_to_2d does not invoke any blocked 3D libraries.
        """
        # We need to mock the import inside the function scope if it's lazy-loaded,
        # but primarily we check that the function doesn't trigger the block.
        
        # Prepare a minimal mock task instance based on the generator schema
        mock_task = {
            "task_id": "test-001",
            "scene_id": "scene-001",
            "task_type": "occlusion",
            "ground_truth_3d_params": {
                "depth": 1.5,
                "occlusion_ratio": 0.2
            }
        }

        # Patch builtins.__import__ to block 3D libs during execution
        self._original_import = builtins.__import__
        
        with patch('builtins.__import__', side_effect=self._block_import):
            # Import the function after patching to ensure no side effects from module load
            from data.projector import project_task_to_2d
            
            try:
                result = project_task_to_2d(mock_task)
                # If we get here without ImportError, the block was respected
                self.assertIsInstance(result, dict)
            except ImportError as e:
                if "FR-002 Violation" in str(e):
                    self.fail(f"project_task_to_2d violates FR-002: {e}")
                raise

    def test_project_dataset_to_2d_no_blocked_calls(self):
        """
        Assert that calling project_dataset_to_2d does not invoke any blocked 3D libraries.
        """
        mock_dataset = [
            {
                "task_id": "test-002",
                "scene_id": "scene-002",
                "task_type": "depth",
                "ground_truth_3d_params": {"depth": 2.0}
            }
        ]

        self._original_import = builtins.__import__
        
        with patch('builtins.__import__', side_effect=self._block_import):
            from data.projector import project_dataset_to_2d
            
            try:
                result = project_dataset_to_2d(mock_dataset)
                self.assertIsInstance(result, list)
            except ImportError as e:
                if "FR-002 Violation" in str(e):
                    self.fail(f"project_dataset_to_2d violates FR-002: {e}")
                raise

if __name__ == '__main__':
    unittest.main()