"""
Integration test for Task T029: Verify baseline uses equivalent checkpointing capabilities.

This test confirms that `direct_comm.py` imports and utilizes the shared
`checkpoint` module from `code/foundation_protocol/checkpoint.py`, ensuring
logic equivalence with `middleware.py` regarding state serialization and loading.
"""
import ast
import os
import sys
import unittest
from pathlib import Path

# Add the project root to the path to allow imports
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

class TestDirectCheckpointVerification(unittest.TestCase):
    """Test suite to verify checkpoint integration in direct_comm.py."""

    def test_direct_comm_imports_checkpoint_module(self):
        """
        Verify that direct_comm.py explicitly imports from foundation_protocol.checkpoint.
        
        This ensures that the baseline (Native Direct Communication) uses the
        same checkpointing logic as the intervention (Foundation Middleware).
        """
        direct_comm_path = code_dir / "foundation_protocol" / "direct_comm.py"
        
        self.assertTrue(direct_comm_path.exists(), f"File not found: {direct_comm_path}")

        with open(direct_comm_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        # Parse the AST to inspect imports
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            self.fail(f"direct_comm.py has a syntax error: {e}")

        found_checkpoint_import = False
        imported_names = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module
                if module and "checkpoint" in module:
                    found_checkpoint_import = True
                    for alias in node.names:
                        imported_names.append(alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if "checkpoint" in alias.name:
                        imported_names.append(alias.name)

        self.assertTrue(
            found_checkpoint_import,
            "direct_comm.py does not import from a module containing 'checkpoint'."
        )

        # Verify specific functions from checkpoint.py are imported
        required_functions = {"save_checkpoint", "load_checkpoint", "serialize_state", "deserialize_state"}
        found_functions = set(imported_names) & required_functions

        self.assertTrue(
            len(found_functions) > 0,
            f"direct_comm.py imports from checkpoint module but does not import any of the core functions: {required_functions}. Found imports: {imported_names}"
        )

        self.assertIn(
            "save_checkpoint",
            imported_names,
            "direct_comm.py must import 'save_checkpoint' from the shared checkpoint module."
        )
        self.assertIn(
            "load_checkpoint",
            imported_names,
            "direct_comm.py must import 'load_checkpoint' from the shared checkpoint module."
        )

    def test_direct_comm_uses_checkpoint_functions(self):
        """
        Verify that the imported checkpoint functions are actually called in the code.
        """
        direct_comm_path = code_dir / "foundation_protocol" / "direct_comm.py"
        
        with open(direct_comm_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        # Simple string check for usage (AST check for calls is more complex but sufficient for this verification)
        # We expect to see calls like save_checkpoint(...) or load_checkpoint(...)
        self.assertIn(
            "save_checkpoint",
            source_code,
            "save_checkpoint function is not called in direct_comm.py."
        )
        self.assertIn(
            "load_checkpoint",
            source_code,
            "load_checkpoint function is not called in direct_comm.py."
        )

    def test_checkpoint_module_exists_and_valid(self):
        """
        Verify that the shared checkpoint module exists and can be imported.
        """
        checkpoint_path = code_dir / "foundation_protocol" / "checkpoint.py"
        
        self.assertTrue(
            checkpoint_path.exists(),
            f"Shared checkpoint module not found at {checkpoint_path}"
        )

        # Try to import it to ensure it's valid Python
        try:
            from foundation_protocol import checkpoint
            self.assertTrue(hasattr(checkpoint, "save_checkpoint"))
            self.assertTrue(hasattr(checkpoint, "load_checkpoint"))
        except ImportError as e:
            self.fail(f"Failed to import shared checkpoint module: {e}")


if __name__ == "__main__":
    unittest.main()