"""
Unit tests for metric independence (User Story 2 - T019).

This test suite verifies that the evaluation pipeline and metric calculation
modules are strictly decoupled from the generative model internals (DiT backbone,
attention maps, latent spaces).

Constraint: The evaluation pipeline must ONLY accept numpy frames and 4x4 matrices.
It must NOT import or depend on model-specific classes like DreamXBase or DreamXLite.
"""

import ast
import os
import sys
import unittest
from pathlib import Path
from typing import Set, List

# Add the project root to the path to allow imports
# We assume this test runs from the project root or the test directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

sys.path.insert(0, str(PROJECT_ROOT))


class TestMetricIndependence(unittest.TestCase):
    """Tests to ensure metric modules do not import model internals."""

    # Forbidden imports that indicate coupling to the generative model
    FORBIDDEN_IMPORTS: Set[str] = {
        "models.dreamx_base",
        "models.dreamx_lite",
        "models.dreamx_world",  # Hypothetical full model name
        "dit_attention",
        "latent_space",
        "DreamXBase",
        "DreamXLite",
        "DiT",
        "transformer", # Specific to model architecture
    }

    # Modules that are allowed to be imported by the evaluation pipeline
    ALLOWED_MODULES: Set[str] = {
        "os", "sys", "json", "logging", "subprocess", "tempfile", "shutil",
        "numpy", "cv2", "sklearn", "scipy", "pandas",
        "pipeline.evaluate", "utils.io", "utils.config",
        "collections", "typing", "math", "itertools"
    }

    def _get_imports_from_file(self, file_path: Path) -> List[str]:
        """Parse a Python file and return a list of all imported module names."""
        if not file_path.exists():
            self.fail(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            self.fail(f"Syntax error in {file_path}: {e}")

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get the top-level module name (e.g., 'numpy' from 'numpy.linalg')
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get the top-level module name
                    imports.append(node.module.split(".")[0])
        return imports

    def _check_forbidden_imports(self, file_path: Path, forbidden: Set[str]) -> List[str]:
        """Check if a file contains any forbidden imports."""
        imports = self._get_imports_from_file(file_path)
        found_forbidden = []
        for imp in imports:
            # Check exact match or if the forbidden string is the module name
            if imp in forbidden:
                found_forbidden.append(imp)
        return found_forbidden

    def test_evaluate_py_no_model_imports(self):
        """
        Verify that code/pipeline/evaluate.py does not import model internals.
        This is the core requirement for User Story 4 (Integrity) and US2.
        """
        evaluate_path = CODE_DIR / "pipeline" / "evaluate.py"
        self.assertTrue(evaluate_path.exists(), f"evaluate.py not found at {evaluate_path}")

        found_forbidden = self._check_forbidden_imports(evaluate_path, self.FORBIDDEN_IMPORTS)

        if found_forbidden:
            self.fail(
                f"evaluate.py violates metric independence constraint. "
                f"Found forbidden imports: {found_forbidden}. "
                f"The evaluation pipeline must not depend on generative model internals."
            )

    def test_evaluate_py_function_signatures(self):
        """
        Verify that evaluate.py functions accept only generic types (numpy frames, 4x4 matrices)
        and not model-specific objects.
        """
        evaluate_path = CODE_DIR / "pipeline" / "evaluate.py"
        with open(evaluate_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        # Functions expected in evaluate.py based on T022-T025
        expected_functions = [
            "extract_trajectory_from_sfm",
            "calculate_procrustes_alignment",
            "calculate_metrics",
            "run_evaluation_pipeline"
        ]

        found_functions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in expected_functions:
                found_functions[node.name] = node

        # Check if all expected functions exist
        missing = set(expected_functions) - set(found_functions.keys())
        if missing:
            self.fail(f"Missing expected functions in evaluate.py: {missing}")

        # Check argument types (basic check: ensure no model class names in type hints)
        for func_name, node in found_functions.items():
            for arg in node.args.args + node.args.kwonlyargs:
                if arg.annotation:
                    # Simple check: if annotation is a Name or Attribute, check its string representation
                    annotation_str = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
                    for forbidden in self.FORBIDDEN_IMPORTS:
                        if forbidden in annotation_str:
                            self.fail(
                                f"Function {func_name} in evaluate.py uses model-specific type hint: "
                                f"'{annotation_str}'. Arguments must be generic (e.g., np.ndarray, List, Matrix)."
                            )

    def test_metrics_module_isolation(self):
        """
        Additional check: Ensure that any helper modules in the pipeline
        that calculate metrics also do not import model internals.
        """
        pipeline_dir = CODE_DIR / "pipeline"
        if not pipeline_dir.exists():
            return

        for py_file in pipeline_dir.glob("*.py"):
            if py_file.name == "static_analysis_check.py":
                continue # Skip the checker itself

            found_forbidden = self._check_forbidden_imports(py_file, self.FORBIDDEN_IMPORTS)
            if found_forbidden:
                self.fail(
                    f"Pipeline module {py_file.name} violates metric independence. "
                    f"Found forbidden imports: {found_forbidden}."
                )


if __name__ == "__main__":
    unittest.main()