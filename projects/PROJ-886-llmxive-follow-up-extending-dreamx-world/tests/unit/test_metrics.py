"""
Unit tests for metric independence (User Story 2).

This test suite verifies that the metric calculation pipeline in 
`code/pipeline/evaluate.py` is strictly decoupled from the generative 
model internals (DiT backbone, attention maps, latent spaces).

It performs static analysis to ensure no forbidden imports exist.
"""
import ast
import os
import unittest
from pathlib import Path
from typing import Set, List

# Constants for forbidden imports (US4 constraints)
FORBIDDEN_IMPORTS = {
    "dit_attention",
    "latent_space",
    "models.dreamx_base",  # Ensure evaluate.py doesn't import the base model directly
    "models.dreamx_lite",  # Ensure evaluate.py doesn't import the lite model directly
    "torch.nn.modules.transformer", # Specific attention internals
}

# The file to analyze
EVALUATE_FILE_PATH = Path("code/pipeline/evaluate.py")
METRICS_FILE_PATH = Path("code/analysis/metrics_writer.py")


class TestMetricIndependence(unittest.TestCase):
    """Tests to ensure metric pipeline independence from model internals."""

    def _get_imports_from_file(self, file_path: Path) -> Set[str]:
        """
        Parses a Python file and extracts all imported module names.
        
        Args:
            file_path: Path to the Python file.
        
        Returns:
            A set of strings representing the top-level imported modules.
        """
        if not file_path.exists():
            self.fail(f"File not found for analysis: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            self.fail(f"Syntax error in {file_path}: {e}")

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Add the top-level module (e.g., 'numpy' from 'numpy as np')
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Add the top-level module (e.g., 'models' from 'from models.dreamx_lite import ...')
                    imports.add(node.module.split(".")[0])
        
        return imports

    def test_evaluate_py_no_model_imports(self):
        """
        Verify that code/pipeline/evaluate.py does not import model internals.
        
        This enforces the 'Blindness' constraint of User Story 4.
        """
        imports = self._get_imports_from_file(EVALUATE_FILE_PATH)
        
        # Check for direct forbidden strings first
        violations = FORBIDDEN_IMPORTS.intersection(imports)
        
        # Additionally check for specific forbidden patterns if they appear as sub-modules
        # e.g., if 'models' is imported, we must ensure 'dreamx_base' or 'dreamx_lite' 
        # are not imported from it.
        if "models" in imports:
            with open(EVALUATE_FILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            if "from models.dreamx_base" in content or "from models.dreamx_lite" in content:
                violations.add("models.dreamx_base")
                violations.add("models.dreamx_lite")

        self.assertEqual(
            len(violations), 
            0, 
            f"evaluate.py imports forbidden model internals: {violations}. "
            "The metric pipeline must be strictly decoupled from the generative model."
        )

    def test_evaluate_py_accepts_only_frames_and_extrinsics(self):
        """
        Verify that the main entry point in evaluate.py accepts only 
        numpy frames and 4x4 matrices as per US4.
        
        We check the AST for the `run_evaluation_pipeline` function signature.
        """
        if not EVALUATE_FILE_PATH.exists():
            self.skipTest("evaluate.py not found")

        with open(EVALUATE_FILE_PATH, "r", encoding="utf-8") as f:
            source_code = f.read()

        tree = ast.parse(source_code)
        
        found_main_func = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "run_evaluation_pipeline":
                found_main_func = True
                args = [arg.arg for arg in node.args.args]
                
                # We expect arguments like 'frames' and 'extrinsics' or similar generic names
                # We do NOT expect arguments like 'model', 'weights', 'attention_map'
                forbidden_args = {"model", "weights", "state_dict", "attention_map", "latent"}
                arg_violations = set(args).intersection(forbidden_args)
                
                self.assertEqual(
                    len(arg_violations),
                    0,
                    f"Function 'run_evaluation_pipeline' accepts forbidden arguments: {arg_violations}. "
                    "It should only accept frames and extrinsics."
                )
        
        self.assertTrue(
            found_main_func,
            "Could not find 'run_evaluation_pipeline' function in evaluate.py to verify signature."
        )

    def test_metrics_writer_no_model_imports(self):
        """
        Verify that code/analysis/metrics_writer.py does not import model internals.
        """
        imports = self._get_imports_from_file(METRICS_FILE_PATH)
        
        violations = FORBIDDEN_IMPORTS.intersection(imports)
        
        self.assertEqual(
            len(violations),
            0,
            f"metrics_writer.py imports forbidden model internals: {violations}."
        )


if __name__ == "__main__":
    unittest.main()