import os
import sys
import json
import csv
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from benchmark.generate_failure_report import generate_report, load_jsonl, load_csv_as_dict

class TestGenerateFailureReport:
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_generate_report_empty_failures(self, temp_dir):
        """Test report generation when there are no failures."""
        analysis_results = []
        benchmark_results = {}
        
        report = generate_report(analysis_results, benchmark_results)
        
        assert "No failures detected" in report
        assert "Executive Summary" in report

    def test_generate_report_with_failures(self, temp_dir):
        """Test report generation with mixed failure types."""
        analysis_results = [
            {
                "scene_id": "scene_001",
                "failure_type": "Semantic Gap",
                "reason": "Ambiguous preposition 'above'",
                "symbolic_prediction": "left",
                "ground_truth": "above",
                "vlm_prediction": "above"
            },
            {
                "scene_id": "scene_002",
                "failure_type": "Geometric Ambiguity",
                "reason": "Multiple valid configurations",
                "symbolic_prediction": "none",
                "ground_truth": "right",
                "vlm_prediction": "right"
            },
            {
                "scene_id": "scene_003",
                "failure_type": "Semantic Gap",
                "reason": "Unknown object category",
                "symbolic_prediction": "left",
                "ground_truth": "right",
                "vlm_prediction": "right"
            }
        ]
        
        benchmark_results = {
            "scene_001": {
                "scene_id": "scene_001",
                "symbolic_prediction": "left",
                "ground_truth": "above",
                "vlm_prediction": "above"
            },
            "scene_002": {
                "scene_id": "scene_002",
                "symbolic_prediction": "none",
                "ground_truth": "right",
                "vlm_prediction": "right"
            },
            "scene_003": {
                "scene_id": "scene_003",
                "symbolic_prediction": "left",
                "ground_truth": "right",
                "vlm_prediction": "right"
            }
        }
        
        exclusion_log = {
            "total_excluded": 5,
            "invalid_geometry": 3,
            "missing_constraints": 2
        }
        
        report = generate_report(analysis_results, benchmark_results, exclusion_log)
        
        # Check summary
        assert "Total Failures Analyzed: 3" in report
        assert "Excluded Scenes: 5" in report
        
        # Check proportions
        assert "Semantic Gap" in report
        assert "66.67%" in report # 2/3
        assert "Geometric Ambiguity" in report
        assert "33.33%" in report # 1/3
        
        # Check specific sections
        assert "## Semantic Gap Analysis" in report
        assert "proportion of failures attributable to **Semantic Gap**" in report
        
        # Check examples
        assert "scene_001" in report
        assert "scene_002" in report
        assert "Ambiguous preposition" in report

    def test_generate_report_no_exclusion_log(self, temp_dir):
        """Test report generation when exclusion log is missing."""
        analysis_results = [
            {"scene_id": "s1", "failure_type": "Test", "reason": "Test reason"}
        ]
        benchmark_results = {}
        
        report = generate_report(analysis_results, benchmark_results, exclusion_log=None)
        
        assert "Excluded Scenes" not in report
        assert "Total Failures Analyzed: 1" in report

    def test_load_jsonl(self, temp_dir):
        """Test loading JSONL file."""
        test_file = temp_dir / "test.jsonl"
        data = [
            {"id": 1, "val": "a"},
            {"id": 2, "val": "b"}
        ]
        with open(test_file, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        
        loaded = load_jsonl(test_file)
        assert len(loaded) == 2
        assert loaded[0]["id"] == 1
        assert loaded[1]["val"] == "b"

    def test_load_csv_as_dict(self, temp_dir):
        """Test loading CSV file into dictionary."""
        test_file = temp_dir / "test.csv"
        data = [
            {"scene_id": "s1", "col2": "val1"},
            {"scene_id": "s2", "col2": "val2"}
        ]
        with open(test_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["scene_id", "col2"])
            writer.writeheader()
            writer.writerows(data)
        
        loaded = load_csv_as_dict(test_file)
        assert "s1" in loaded
        assert loaded["s2"]["col2"] == "val2"
        assert "s3" not in loaded