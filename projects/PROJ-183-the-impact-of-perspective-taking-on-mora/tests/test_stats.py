import json
import pytest
from pathlib import Path
import tempfile
import os

# Import the function to test
try:
    from code.analysis.stats import validate_stratification
except ImportError:
    # Fallback if running from project root
    from code.analysis.stats import validate_stratification

def test_validate_stratification_success():
    """
    Test that validate_stratification correctly calculates mean differences
    and saves the report when given valid stimuli data.
    """
    # Create a temporary stimuli file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        stimuli_data = [
            {"id": "1", "condition": "perspective_taking", "vader_score": 0.8},
            {"id": "2", "condition": "perspective_taking", "vader_score": 0.9},
            {"id": "3", "condition": "control_summarization", "vader_score": 0.75},
            {"id": "4", "condition": "control_summarization", "vader_score": 0.85},
        ]
        json.dump(stimuli_data, f)
        temp_path = f.name

    try:
        result = validate_stratification(Path(temp_path))
        
        assert result["validation_status"] == "completed"
        assert result["condition_counts"]["perspective_taking"] == 2
        assert result["condition_counts"]["control_summarization"] == 2
        
        # Check means: PT (0.8+0.9)/2 = 0.85, Control (0.75+0.85)/2 = 0.8
        assert abs(result["mean_sentiment_scores"]["perspective_taking"] - 0.85) < 0.001
        assert abs(result["mean_sentiment_scores"]["control_summarization"] - 0.80) < 0.001
        
        # Diff = 0.05
        assert abs(result["absolute_difference"] - 0.05) < 0.001
        
        # Check report file was created
        report_path = Path("data/processed/stratification_report.json")
        assert report_path.exists()
        
        with open(report_path, 'r') as rf:
            saved_report = json.load(rf)
            assert saved_report == result
            
    finally:
        os.unlink(temp_path)
        if Path("data/processed/stratification_report.json").exists():
            Path("data/processed/stratification_report.json").unlink()

def test_validate_stratification_missing_file():
    """
    Test that validate_stratification raises FileNotFoundError for missing file.
    """
    with pytest.raises(FileNotFoundError):
        validate_stratification(Path("nonexistent/path/stimuli.json"))

def test_validate_stratification_insufficient_data():
    """
    Test that validate_stratification raises ValueError if one condition is missing.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        stimuli_data = [
            {"id": "1", "condition": "perspective_taking", "vader_score": 0.8},
            {"id": "2", "condition": "perspective_taking", "vader_score": 0.9},
        ]
        json.dump(stimuli_data, f)
        temp_path = f.name

    try:
        with pytest.raises(ValueError):
            validate_stratification(Path(temp_path))
    finally:
        os.unlink(temp_path)