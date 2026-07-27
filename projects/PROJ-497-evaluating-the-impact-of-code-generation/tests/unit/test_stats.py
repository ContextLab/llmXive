"""
Unit tests for stats.py module.
"""
import json
import os
import tempfile
import unittest
import pandas as pd
from pathlib import Path

# Import the module under test
import sys
sys.path.insert(0, 'code')
from stats import (
    extract_task_id_from_path,
    extract_source_type,
    count_lines_of_code,
    parse_vulnerability_report,
    calculate_per_sample_stats,
    aggregate_analysis_dataset
)


class TestExtractTaskId(unittest.TestCase):
    """Tests for extract_task_id_from_path function."""

    def test_generated_path(self):
        """Test extraction from generated code path."""
        path = "data/generated/starcoder/humaneval/0/samples/sample_0.py"
        result = extract_task_id_from_path(path)
        self.assertEqual(result, "humaneval/0")

    def test_human_path(self):
        """Test extraction from human code path."""
        path = "data/human/humaneval/1/solution.py"
        result = extract_task_id_from_path(path)
        self.assertEqual(result, "humaneval/1")

    def test_mbpp_path(self):
        """Test extraction from MBPP benchmark path."""
        path = "data/generated/codegen/mbpp/100/samples/sample_5.py"
        result = extract_task_id_from_path(path)
        self.assertEqual(result, "mbpp/100")

    def test_invalid_path(self):
        """Test extraction from invalid path."""
        path = "invalid/path/to/file.py"
        result = extract_task_id_from_path(path)
        self.assertEqual(result, "unknown/unknown")


class TestExtractSourceType(unittest.TestCase):
    """Tests for extract_source_type function."""

    def test_llm_source(self):
        """Test LLM source detection."""
        path = "data/generated/starcoder/humaneval/0/samples/sample_0.py"
        result = extract_source_type(path)
        self.assertEqual(result, "LLM")

    def test_human_source(self):
        """Test Human source detection."""
        path = "data/human/humaneval/1/solution.py"
        result = extract_source_type(path)
        self.assertEqual(result, "Human")

    def test_unknown_source(self):
        """Test unknown source detection."""
        path = "data/other/file.py"
        result = extract_source_type(path)
        self.assertEqual(result, "Unknown")


class TestCountLinesOfCode(unittest.TestCase):
    """Tests for count_lines_of_code function."""

    def test_simple_code(self):
        """Test counting lines in simple code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def hello():\n    print('Hello')\n\nx = 1\n")
            temp_path = f.name

        try:
            loc = count_lines_of_code(temp_path)
            self.assertGreater(loc, 0)
            self.assertEqual(loc, 3)  # 3 non-empty, non-comment lines
        finally:
            os.unlink(temp_path)

    def test_with_comments(self):
        """Test that comments are excluded."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# Comment\nx = 1\n# Another comment\ny = 2\n")
            temp_path = f.name

        try:
            loc = count_lines_of_code(temp_path)
            self.assertEqual(loc, 2)  # Only x=1 and y=2
        finally:
            os.unlink(temp_path)

    def test_empty_file(self):
        """Test counting lines in empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_path = f.name

        try:
            loc = count_lines_of_code(temp_path)
            self.assertEqual(loc, 0)
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        loc = count_lines_of_code("nonexistent_file.py")
        self.assertEqual(loc, 0)


class TestParseVulnerabilityReport(unittest.TestCase):
    """Tests for parse_vulnerability_report function."""

    def test_valid_report(self):
        """Test parsing a valid vulnerability report."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = [
                {"file_path": "test.py", "cwe_id": "CWE-79", "severity": "high", "line_number": 10},
                {"file_path": "test.py", "cwe_id": "CWE-89", "severity": "critical", "line_number": 15}
            ]
            json.dump(data, f)
            temp_path = f.name

        try:
            result = parse_vulnerability_report(temp_path)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["file_path"], "test.py")
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        result = parse_vulnerability_report("nonexistent.json")
        self.assertEqual(result, [])

    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            result = parse_vulnerability_report(temp_path)
            self.assertEqual(result, [])
        finally:
            os.unlink(temp_path)


class TestCalculatePerSampleStats(unittest.TestCase):
    """Tests for calculate_per_sample_stats function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = os.path.join(self.temp_dir, "vulnerability_reports.json")
        self.output_path = os.path.join(self.temp_dir, "raw_vulnerability_counts.csv")

        # Create test vulnerability data
        vuln_data = [
            {
                "file_path": "data/generated/starcoder/humaneval/0/samples/sample_0.py",
                "cwe_id": "CWE-79",
                "severity": "high",
                "line_number": 10
            },
            {
                "file_path": "data/generated/starcoder/humaneval/0/samples/sample_0.py",
                "cwe_id": "CWE-89",
                "severity": "critical",
                "line_number": 15
            },
            {
                "file_path": "data/human/humaneval/1/solution.py",
                "cwe_id": "CWE-119",
                "severity": "medium",
                "line_number": 5
            }
        ]

        with open(self.input_path, 'w') as f:
            json.dump(vuln_data, f)

        # Create dummy Python files for LOC counting
        os.makedirs("data/generated/starcoder/humaneval/0/samples", exist_ok=True)
        os.makedirs("data/human/humaneval/1", exist_ok=True)

        with open("data/generated/starcoder/humaneval/0/samples/sample_0.py", 'w') as f:
            f.write("def test():\n    x = 1\n    return x\n")

        with open("data/human/humaneval/1/solution.py", 'w') as f:
            f.write("# Human solution\ny = 2\n")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Clean up dummy files
        shutil.rmtree("data/generated", ignore_errors=True)
        shutil.rmtree("data/human", ignore_errors=True)

    def test_calculate_stats(self):
        """Test calculation of per-sample statistics."""
        df = calculate_per_sample_stats(self.input_path, self.output_path)

        # Check output file exists
        self.assertTrue(os.path.exists(self.output_path))

        # Check DataFrame structure
        self.assertIn('task_id', df.columns)
        self.assertIn('source_type', df.columns)
        self.assertIn('file_path', df.columns)
        self.assertIn('lines_of_code', df.columns)
        self.assertIn('vulnerability_count', df.columns)

        # Check data
        self.assertEqual(len(df), 2)  # 2 unique files

        # Check specific values
        llm_row = df[df['source_type'] == 'LLM'].iloc[0]
        self.assertEqual(llm_row['vulnerability_count'], 2)

        human_row = df[df['source_type'] == 'Human'].iloc[0]
        self.assertEqual(human_row['vulnerability_count'], 1)


class TestAggregateAnalysisDataset(unittest.TestCase):
    """Tests for aggregate_analysis_dataset function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = os.path.join(self.temp_dir, "raw_vulnerability_counts.csv")
        self.output_path = os.path.join(self.temp_dir, "aggregated_analysis_dataset.csv")

        # Create test data
        data = {
            'task_id': ['humaneval/0', 'humaneval/0', 'humaneval/1', 'humaneval/1'],
            'source_type': ['LLM', 'LLM', 'Human', 'Human'],
            'file_path': ['a.py', 'b.py', 'c.py', 'd.py'],
            'lines_of_code': [10, 15, 20, 25],
            'vulnerability_count': [2, 3, 1, 0]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.input_path, index=False)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_aggregate_data(self):
        """Test aggregation of per-sample data."""
        result_df = aggregate_analysis_dataset(self.input_path, self.output_path)

        # Check output file exists
        self.assertTrue(os.path.exists(self.output_path))

        # Check DataFrame structure
        self.assertIn('task_id', result_df.columns)
        self.assertIn('source_type', result_df.columns)
        self.assertIn('lines_of_code', result_df.columns)
        self.assertIn('vulnerability_count', result_df.columns)
        self.assertIn('sample_count', result_df.columns)

        # Check aggregation logic
        # LLM humaneval/0 should have mean vuln count = (2+3)/2 = 2.5
        llm_row = result_df[
            (result_df['task_id'] == 'humaneval/0') &
            (result_df['source_type'] == 'LLM')
        ].iloc[0]

        self.assertAlmostEqual(llm_row['vulnerability_count'], 2.5, places=1)
        self.assertEqual(llm_row['sample_count'], 2)

        # Human should have single value
        human_row = result_df[
            (result_df['task_id'] == 'humaneval/1') &
            (result_df['source_type'] == 'Human')
        ].iloc[0]

        self.assertEqual(human_row['vulnerability_count'], 0.5)  # mean of 1 and 0
        self.assertEqual(human_row['sample_count'], 2)


if __name__ == '__main__':
    unittest.main()