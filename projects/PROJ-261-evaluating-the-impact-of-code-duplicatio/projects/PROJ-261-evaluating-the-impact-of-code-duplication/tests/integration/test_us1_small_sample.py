"""Integration test for US1 pipeline on a small sample.

The test creates a temporary directory with 10 simple Python files,
invokes the pipeline entry point defined in ``code/main.py`` (expected
to be a function ``run_pipeline(sample_dir: str, output_dir: str)``),
and checks that the expected CSV output files are created and contain
at least one row per input file.

The test is deliberately written to **fail** until the pipeline is
fully implemented, satisfying the requirement that tests be authored
before implementation.
"""

import csv
import pathlib
import importlib.util

import pytest


def _create_sample_python_files(base_dir: pathlib.Path, count: int = 10) -> None:
    """Create ``count`` trivial Python files in *base_dir*.

    Each file contains a tiny function that will be identical across
    files, providing a deterministic clone pattern for the future
    clone‑density detector.
    """
    for i in range(count):
        file_path = base_dir / f"sample_{i}.py"
        file_path.write_text(
            "def duplicated_function():\n"
            "    return 42\n"
        )


def _load_pipeline_module() -> object:
    """Dynamically load ``code/main.py`` as a module.

    This avoids import‑path issues caused by the project’s nested
    directory structure (the ``code`` directory is not a package).
    """
    project_root = pathlib.Path(__file__).resolve().parents[4]
    main_path = project_root / "code" / "main.py"
    spec = importlib.util.spec_from_file_location("pipeline_main", main_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import pipeline from {main_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.integration
def test_pipeline_small_sample(tmp_path: pathlib.Path) -> None:
    """Run the US1 pipeline on a 10‑file sample and verify CSV outputs."""
    # Set up sample input files
    sample_dir = tmp_path / "samples"
    sample_dir.mkdir()
    _create_sample_python_files(sample_dir, count=10)

    # Set up output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Load and execute the pipeline
    pipeline = _load_pipeline_module()
    if not hasattr(pipeline, "run_pipeline"):
        pytest.fail("Pipeline module does not define 'run_pipeline' function.")
    pipeline.run_pipeline(str(sample_dir), str(output_dir))

    # Expected output files
    clone_csv = output_dir / "clone_metrics.csv"
    perplexity_csv = output_dir / "perplexity_scores.csv"

    # Verify that the CSV files were created
    assert clone_csv.is_file(), f"Expected clone metrics CSV at {clone_csv}"
    assert perplexity_csv.is_file(), f"Expected perplexity CSV at {perplexity_csv}"

    # Verify that each CSV contains at least a header plus one row per input file
    for csv_path in (clone_csv, perplexity_csv):
        with csv_path.open(newline="") as f:
            rows = list(csv.reader(f))
            # Header + at least 10 data rows
            assert len(rows) >= 11, f"{csv_path.name} should have ≥11 rows (header + 10 samples)"