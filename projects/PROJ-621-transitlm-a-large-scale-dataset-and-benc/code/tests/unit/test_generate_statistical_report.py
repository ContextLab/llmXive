import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Dict, Any

from src.analysis.generate_statistical_report import generate_report, StatisticalReport

@pytest.fixture
def sample_validation_data() -> List[Dict[str, Any]]:
    """Sample data for fine-tuned model (high validity)."""
    return [
        {"id": "1", "valid": True, "score": 0.95},
        {"id": "2", "valid": True, "score": 0.92},
        {"id": "3", "valid": False, "score": 0.40},
        {"id": "4", "valid": True, "score": 0.88},
        {"id": "5", "valid": True, "score": 0.91},
    ]

@pytest.fixture
def sample_baseline_data() -> List[Dict[str, Any]]:
    """Sample data for zero-shot baseline (lower validity, some discordant)."""
    # We need discordant pairs for McNemar's test to work.
    # FT: [T, T, F, T, T]
    # BS: [T, F, F, T, F] -> Discordant at indices 1 (FT=T, BS=F) and 4 (FT=T, BS=F)
    # So b=2, c=0.
    return [
        {"id": "1", "valid": True, "score": 0.80},
        {"id": "2", "valid": False, "score": 0.30},
        {"id": "3", "valid": False, "score": 0.25},
        {"id": "4", "valid": True, "score": 0.75},
        {"id": "5", "valid": False, "score": 0.20},
    ]

def test_generate_report_creates_file(
    sample_validation_data: List[Dict[str, Any]],
    sample_baseline_data: List[Dict[str, Any]]
):
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Write input files
        ft_file = tmp_path / "validation_scores.json"
        bs_file = tmp_path / "baseline_validation_scores.json"
        out_file = tmp_path / "statistical_report.md"
        
        with open(ft_file, 'w') as f:
            json.dump(sample_validation_data, f)
        
        with open(bs_file, 'w') as f:
            json.dump(sample_baseline_data, f)
        
        # Run generation
        report = generate_report(ft_file, bs_file, out_file)
        
        # Assertions
        assert out_file.exists(), "Output markdown file was not created"
        assert report.total_samples == 5
        assert report.mcnemar_p_value < 1.0 # Should be a valid probability
        assert report.is_significant == False # With b=2, c=0, p-value might not be < 0.05 with N=5
        
        # Check file content
        content = out_file.read_text()
        assert "Statistical Analysis Report" in content
        assert "McNemar" in content
        assert "Significant" in content or "Not Significant" in content

def test_generate_report_handles_mismatched_samples(
    sample_validation_data: List[Dict[str, Any]]
):
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        ft_file = tmp_path / "validation_scores.json"
        bs_file = tmp_path / "baseline_validation_scores.json"
        out_file = tmp_path / "statistical_report.md"
        
        with open(ft_file, 'w') as f:
            json.dump(sample_validation_data, f)
        
        # Baseline has different length
        with open(bs_file, 'w') as f:
            json.dump(sample_validation_data[:3], f)
        
        with pytest.raises(ValueError, match="Sample count mismatch"):
            generate_report(ft_file, bs_file, out_file)

def test_generate_report_missing_file(sample_validation_data: List[Dict[str, Any]]):
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        ft_file = tmp_path / "validation_scores.json"
        bs_file = tmp_path / "nonexistent.json"
        out_file = tmp_path / "statistical_report.md"
        
        with open(ft_file, 'w') as f:
            json.dump(sample_validation_data, f)
        
        with pytest.raises(FileNotFoundError):
            generate_report(ft_file, bs_file, out_file)
