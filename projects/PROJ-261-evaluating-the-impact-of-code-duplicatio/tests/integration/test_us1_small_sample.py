import csv
import shutil
import sys
from pathlib import Path
import pytest

# Import the pipeline orchestration entry‑point.
from code.main import run_pipeline

@pytest.fixture
def tiny_raw_dataset(tmp_path: Path) -> Path:
    """
    Create a tiny raw dataset consisting of ten real Python files taken from the
    repository itself.  The files are copied into a temporary directory that
    mimics the structure expected by the pipeline (``data/raw``).
    """
    source_files = list(Path(__file__).parents[4] / "code").rglob("*.py")[:10]
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    for src in source_files:
        dest = raw_dir / src.name
        shutil.copyfile(src, dest)

    return raw_dir

def test_pipeline_produces_outputs(tiny_raw_dataset: Path) -> None:
    """
    End‑to‑end integration test for US 1 on a tiny sample.

    The test invokes ``run_pipeline`` with the temporary raw directory and
    asserts that the two required CSV artefacts are created and contain at
    least one record each.
    """
    # Ensure a clean environment – remove any leftover artefacts from previous
    # runs.
    processed_dir = Path("data/processed")
    if processed_dir.exists():
        shutil.rmtree(processed_dir)

    # The pipeline may accept the raw directory either as a positional argument
    # or via a named ``input_path``/``raw_dir`` parameter.  We try both.
    try:
        # Preferred signature (positional)
        run_pipeline(tiny_raw_dataset)
    except TypeError:
        # Fallback – try common keyword names.
        try:
            run_pipeline(input_path=tiny_raw_dataset)
        except TypeError:
            run_pipeline(raw_dir=tiny_raw_dataset)

    # Verify that the expected CSV files exist.
    clone_csv = processed_dir / "clone_metrics.csv"
    perplexity_csv = processed_dir / "perplexity_scores.csv"

    assert clone_csv.is_file(), f"Clone‑density CSV not found at {clone_csv}"
    assert perplexity_csv.is_file(), f"Perplexity CSV not found at {perplexity_csv}"

    # Minimal sanity‑check: each file must contain a header row and at least one
    # data row.
    for csv_path in (clone_csv, perplexity_csv):
        with csv_path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            assert len(rows) >= 2, f"{csv_path} appears empty (only header?)"