"""
Unit tests for the sensitivity report generator (Task T034).
"""
import json
import tempfile
from pathlib import Path
import pytest

# Import the module under test
# Adjust import path based on execution context
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.sensitivity_report_generator import (
    load_power_curve_results,
    generate_sensitivity_summary,
    render_markdown_report
)


@pytest.fixture
def mock_power_curve_data():
    """Create a mock dataset matching the expected structure."""
    return {
        "paradigms": {
            "Motor": {
                "kernels": {
                    "4mm": {
                        "empirical_rate": 0.85,
                        "effect_size": 0.65
                    },
                    "8mm": {
                        "empirical_rate": 0.72,
                        "effect_size": 0.58
                    }
                }
            },
            "WorkingMemory": {
                "kernels": {
                    "4mm": {
                        "empirical_rate": 0.60,
                        "effect_size": 0.45
                    },
                    "8mm": {
                        "empirical_rate": 0.58,
                        "effect_size": 0.44
                    }
                }
            }
        }
    }


@pytest.fixture
def temp_input_file(mock_power_curve_data):
    """Create a temporary JSON file with mock data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_power_curve_data, f)
        return Path(f.name)


def test_load_power_curve_results(temp_input_file):
    """Test loading data from a JSON file."""
    data = load_power_curve_results(temp_input_file)
    assert "paradigms" in data
    assert "Motor" in data["paradigms"]
    assert data["paradigms"]["Motor"]["kernels"]["4mm"]["empirical_rate"] == 0.85


def test_generate_sensitivity_summary(mock_power_curve_data):
    """Test the calculation of sensitivity metrics."""
    summary = generate_sensitivity_summary(mock_power_curve_data)
    
    assert "paradigms" in summary
    assert "Motor" in summary["paradigms"]
    assert "WorkingMemory" in summary["paradigms"]
    
    # Check Motor paradigm (High Sensitivity expected: 0.85 - 0.72 = 0.13 > 0.10)
    motor_diff = summary["paradigms"]["Motor"]["difference"]
    assert motor_diff["replication_rate_diff"] == pytest.approx(0.13)
    assert motor_diff["is_high_sensitivity"] is True
    
    # Check Working Memory paradigm (Low Sensitivity expected: 0.60 - 0.58 = 0.02)
    wm_diff = summary["paradigms"]["WorkingMemory"]["difference"]
    assert wm_diff["replication_rate_diff"] == pytest.approx(0.02)
    assert wm_diff["is_high_sensitivity"] is False
    
    # Check global summary
    assert summary["global_summary"]["high_sensitivity_count"] == 1
    assert summary["global_summary"]["total_paradigms"] == 2


def test_render_markdown_report(mock_power_curve_data):
    """Test that the markdown report is generated correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_report.md"
        
        summary = generate_sensitivity_summary(mock_power_curve_data)
        render_markdown_report(summary, output_path)
        
        assert output_path.exists()
        
        content = output_path.read_text()
        assert "# Preprocessing Sensitivity Analysis Report" in content
        assert "Motor" in content
        assert "WorkingMemory" in content
        assert "High Sensitivity Detected" in content
        assert "0.13" in content or "13%" in content # Approximate check for diff
        assert "results/paper/sensitivity_report.md" not in content # Ensure we don't hardcode wrong paths in content logic
        
        # Verify the "High Sensitivity" flag is present for Motor
        assert "🔴" in content