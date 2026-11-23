import json
import os
import tempfile
import pytest
from pathlib import Path

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from failure_logger import (
    FailureReason,
    load_existing_failure_log,
    record_failure,
    compile_failure_summary,
    write_failure_report
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_record_failure_structure(temp_dir):
    log_path = temp_dir / "test_log.json"
    entries = []
    
    record_failure(entries, "10.1038/s123", FailureReason.MODEL_SUBSTITUTION, "Test details")
    
    assert len(entries) == 1
    entry = entries[0]
    assert entry["paper_doi"] == "10.1038/s123"
    assert entry["failure_mode"] == FailureReason.MODEL_SUBSTITUTION
    assert entry["details"] == "Test details"
    assert "timestamp" in entry

def test_compile_failure_summary_from_mock_data(temp_dir):
    # Create a mock repro_results.json
    repro_path = temp_dir / "repro_results.json"
    mock_results = [
        {
            "doi": "10.1038/mock1",
            "flags": ["model_substitution", "missing_seed"],
            "mae": 0.5,
            "r2": 0.8
        },
        {
            "doi": "10.1038/mock2",
            "flags": ["covariate_missing"],
            "mae": None,
            "r2": None
        },
        {
            "doi": "10.1038/mock3",
            "flags": [],
            "mae": 0.1,
            "r2": 0.9
        }
    ]
    
    with open(repro_path, 'w') as f:
        json.dump(mock_results, f)
    
    # Patch the function to use our temp path
    import failure_logger
    original_compile = failure_logger.compile_failure_summary
    
    def mock_compile(path=str(repro_path)):
        return compile_failure_summary(path)
    
    failure_logger.compile_failure_summary = mock_compile
    
    try:
        log_entries = compile_failure_summary(str(repro_path))
        
        # Should have 2 failures (mock1 and mock2)
        assert len(log_entries) == 2
        
        # Check specific modes
        doi_modes = {e["paper_doi"]: e["failure_mode"] for e in log_entries}
        assert doi_modes["10.1038/mock1"] == FailureReason.MODEL_SUBSTITUTION
        assert doi_modes["10.1038/mock2"] == FailureReason.COVARIATE_MISSING
    finally:
        failure_logger.compile_failure_summary = original_compile

def test_write_failure_report(temp_dir):
    entries = [
        {"paper_doi": "10.1038/test", "failure_mode": "other", "details": "test", "timestamp": "2023-01-01"}
    ]
    output_path = temp_dir / "output.json"
    
    write_failure_report(entries, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    
    assert len(loaded) == 1
    assert loaded[0]["paper_doi"] == "10.1038/test"
    assert loaded[0]["failure_mode"] == "other"

def test_load_existing_failure_log(temp_dir):
    log_path = temp_dir / "existing.json"
    existing_data = [{"paper_doi": "10.1038/existing", "failure_mode": "test"}]
    
    with open(log_path, 'w') as f:
        json.dump(existing_data, f)
    
    loaded = load_existing_failure_log(str(log_path))
    assert len(loaded) == 1
    assert loaded[0]["paper_doi"] == "10.1038/existing"

def test_load_nonexistent_failure_log(temp_dir):
    log_path = temp_dir / "nonexistent.json"
    loaded = load_existing_failure_log(str(log_path))
    assert loaded == []