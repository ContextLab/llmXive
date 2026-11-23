import pytest
import csv
from pathlib import Path
import tempfile

from code.config import set_mode
from code.data.annotator import run_ci_mode, run_research_mode

def test_ci_mode_independence():
    """Verify CI mode scores are random and decoupled from metrics."""
    set_mode("CI")
    image_ids = [f"img_{i:04d}" for i in range(10)]
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        output_path = Path(f.name)
    
    scores = run_ci_mode(image_ids, output_path)
    
    # Check scores are random 1-5
    for s in scores:
        assert 1 <= s["score"] <= 5
        assert s["mode"] == "CI"
    
    output_path.unlink()

def test_research_mode_validation():
    """Verify Research mode requires input file and sample size."""
    set_mode("RESEARCH")
    
    # Create a mock CSV with < 50 rows
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "score", "rater_id"])
        writer.writeheader()
        for i in range(10):
            writer.writerow({"image_id": f"img_{i}", "score": "3.0", "rater_id": "r1"})
        input_path = Path(f.name)
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        output_path = Path(f.name)
    
    with pytest.raises(ValueError, match="Sample size < 50"):
        run_research_mode(input_path, output_path)
    
    input_path.unlink()
    output_path.unlink()