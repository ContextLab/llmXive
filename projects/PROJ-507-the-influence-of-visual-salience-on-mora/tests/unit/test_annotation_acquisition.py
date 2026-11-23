"""
Unit tests for the annotation acquisition script (code/02_acquire_annotations.py).

The test verifies that:
1. Template CSVs can be generated for a list of scenario IDs.
2. Validation succeeds when at least three annotation files exist and each
   scenario has at least three ratings in total.
"""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

# Helper to import the module with a numeric-leading filename.
def load_acquire_annotations_module():
    """
    Dynamically load the ``02_acquire_annotations.py`` module.
    Returns the loaded module object.
    """
    module_path = Path(__file__).resolve().parents[2] / "code" / "02_acquire_annotations.py"
    spec = importlib.util.spec_from_file_location("acquire_annotations", str(module_path))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None, f"Could not load spec for {module_path}"
    spec.loader.exec_module(module)
    return module

def test_generate_and_validate_annotations(tmp_path: Path):
    """
    End‑to‑end test for template generation and validation.

    Steps:
    1. Create a dummy ``candidates_filtered.csv`` containing a few scenario IDs.
    2. Generate empty annotation templates for three annotators.
    3. Fill each template with a ``rating`` column so that every scenario receives
       at least three ratings in total.
    4. Run the ``validate_annotations`` function and expect no exception.
    """
    # -------------------------------------------------
    # 1. Dummy candidates CSV
    # -------------------------------------------------
    candidates_csv = tmp_path / "candidates_filtered.csv"
    scenario_ids = ["S1", "S2", "S3"]
    pd.DataFrame({"scenario_id": scenario_ids}).to_csv(candidates_csv, index=False)

    # -------------------------------------------------
    # 2. Load the module and generate templates
    # -------------------------------------------------
    acquire_mod = load_acquire_annotations_module()
    annotator_ids = ["A1", "A2", "A3"]
    output_dir = tmp_path / "human_coding"

    # Generate empty templates (they contain only the scenario_id column)
    acquire_mod.generate_templates(
        input_csv=candidates_csv,
        annotator_ids=annotator_ids,
        output_dir=output_dir,
    )

    # -------------------------------------------------
    # 3. Populate each template with ratings
    # -------------------------------------------------
    for annotator_id in annotator_ids:
        template_path = output_dir / f"annotations_template_{annotator_id}.csv"
        # Load the empty template, add a rating column, and write back
        df = pd.read_csv(template_path, dtype=str)
        # Assign a simple rating (e.g., 1, 2, 3) cyclically
        df["rating"] = [str((i % 5) + 1) for i in range(len(df))]
        df.to_csv(template_path, index=False)

    # -------------------------------------------------
    # 4. Validate – should pass without raising
    # -------------------------------------------------
    # No exception means the validation succeeded.
    acquire_mod.validate_annotations(annotation_dir=output_dir)

def test_insufficient_annotators_error_is_raised(tmp_path: Path):
    """
    Ensure that ``InsufficientAnnotatorsError`` is raised when the
    validation requirements are not met.
    """
    # Create a dummy candidates CSV with a single scenario.
    candidates_csv = tmp_path / "candidates_filtered.csv"
    pd.DataFrame({"scenario_id": ["S1"]}).to_csv(candidates_csv, index=False)

    # Generate only two annotation files (less than the required three).
    acquire_mod = load_acquire_annotations_module()
    annotator_ids = ["A1", "A2"]  # Only two annotators
    output_dir = tmp_path / "human_coding_insufficient"
    acquire_mod.generate_templates(
        input_csv=candidates_csv,
        annotator_ids=annotator_ids,
        output_dir=output_dir,
    )

    # Populate the two files with a rating each (still insufficient).
    for annotator_id in annotator_ids:
        template_path = output_dir / f"annotations_template_{annotator_id}.csv"
        df = pd.read_csv(template_path, dtype=str)
        df["rating"] = ["3"]
        df.to_csv(template_path, index=False)

    # Validation should raise InsufficientAnnotatorsError.
    with pytest.raises(acquire_mod.InsufficientAnnotatorsError):
        acquire_mod.validate_annotations(annotation_dir=output_dir)