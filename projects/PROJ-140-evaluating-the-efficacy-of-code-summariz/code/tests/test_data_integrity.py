"""
Unit tests for data integrity checks in the code summarization bug localization pipeline.

This module verifies:
1. Defects4J stratified methods file integrity (JSON structure, required fields)
2. Summary CSV integrity (row counts match, required columns present)
3. Interaction logs integrity (timestamp precision, valid participant IDs)
4. Anonymization mapping integrity (bijective mapping, no data loss)
5. Analysis results integrity (all comparisons present, valid statistical values)
"""
import unittest
import os
import sys
import json
import csv
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.hash_artifacts import hash_file, verify_file_hash
from utils.models import Participant, Task, Summary, InteractionLog, AnalysisResult
from data_prep.download_defects4j import parse_defects4j_data
from data_prep.generate_summaries import load_stratified_methods, save_summaries_to_csv
from utils.interaction_logger import load_raw_logs
from utils.anonymize_logs import create_anonymization_mapping, anonymize_logs


class TestDataIntegrity(unittest.TestCase):
    """Test suite for data integrity verification across the pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data"
        self.data_dir.mkdir(parents=True)
        
        # Create test data files
        self.stratified_methods_file = self.data_dir / "stratified_methods.json"
        self.summary_file = self.data_dir / "summaries.csv"
        self.raw_logs_file = self.data_dir / "raw_logs.csv"
        self.anonymized_logs_file = self.data_dir / "anonymized_logs.csv"
        self.mapping_file = self.data_dir / "anonymization_mapping.json"
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_stratified_methods_json_structure(self):
        """Verify Defects4J stratified methods JSON has required structure and fields."""
        # Create valid test data
        test_data = {
            "metadata": {
                "source": "Defects4J",
                "version": "1.0",
                "total_methods": 60
            },
            "strata": [
                {
                    "stratum_id": "complexity_low",
                    "methods": [
                        {
                            "method_id": "method_001",
                            "project": "Lang",
                            "bug_id": "1",
                            "method_name": "testMethod",
                            "line_count": 10,
                            "complexity_score": 2.5,
                            "has_comments": True
                        }
                    ]
                }
            ]
        }
        
        with open(self.stratified_methods_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load and validate
        with open(self.stratified_methods_file, 'r') as f:
            data = json.load(f)
        
        # Check required top-level keys
        self.assertIn("metadata", data)
        self.assertIn("strata", data)
        
        # Check metadata fields
        self.assertIn("source", data["metadata"])
        self.assertIn("version", data["metadata"])
        self.assertIn("total_methods", data["metadata"])
        
        # Check stratum structure
        self.assertIsInstance(data["strata"], list)
        self.assertGreater(len(data["strata"]), 0)
        
        for stratum in data["strata"]:
            self.assertIn("stratum_id", stratum)
            self.assertIn("methods", stratum)
            self.assertIsInstance(stratum["methods"], list)
            
            for method in stratum["methods"]:
                # Verify all required method fields
                required_fields = [
                    "method_id", "project", "bug_id", "method_name",
                    "line_count", "complexity_score", "has_comments"
                ]
                for field in required_fields:
                    self.assertIn(field, method, f"Missing field: {field}")
                
                # Type validations
                self.assertIsInstance(method["method_id"], str)
                self.assertIsInstance(method["project"], str)
                self.assertIsInstance(method["bug_id"], str)
                self.assertIsInstance(method["line_count"], int)
                self.assertIsInstance(method["complexity_score"], (int, float))
                self.assertIsInstance(method["has_comments"], bool)
                
                # Value constraints
                self.assertGreater(method["line_count"], 0)
                self.assertGreaterEqual(method["complexity_score"], 0)
    
    def test_summary_csv_integrity(self):
        """Verify summary CSV has correct columns and row counts match source."""
        # Create test stratified methods
        test_methods = {
            "metadata": {"total_methods": 3},
            "strata": [
                {
                    "stratum_id": "stratum_1",
                    "methods": [
                        {
                            "method_id": "m1", "project": "Lang", "bug_id": "1",
                            "method_name": "test1", "line_count": 10,
                            "complexity_score": 2.0, "has_comments": True
                        },
                        {
                            "method_id": "m2", "project": "Lang", "bug_id": "2",
                            "method_name": "test2", "line_count": 15,
                            "complexity_score": 3.0, "has_comments": False
                        }
                    ]
                }
            ]
        }
        
        # Save test data
        with open(self.stratified_methods_file, 'w') as f:
            json.dump(test_methods, f)
        
        # Generate summaries (using the real function)
        from data_prep.generate_summaries import load_stratified_methods, generate_llm_sim_summary, generate_rule_summary
        
        methods = load_stratified_methods(self.stratified_methods_file)
        
        summaries = []
        for method in methods:
            llm_summary = generate_llm_sim_summary(method)
            rule_summary = generate_rule_summary(method)
            summaries.append({
                "method_id": method["method_id"],
                "llm_summary": llm_summary,
                "rule_summary": rule_summary
            })
        
        # Save summaries
        save_summaries_to_csv(summaries, self.summary_file)
        
        # Validate CSV structure
        with open(self.summary_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check required columns
            required_columns = ["method_id", "llm_summary", "rule_summary"]
            for col in required_columns:
                self.assertIn(col, reader.fieldnames, f"Missing column: {col}")
            
            # Check row count matches source
            self.assertEqual(len(rows), len(methods), 
                           "Summary row count does not match source method count")
            
            # Check for duplicate method IDs
            method_ids = [row["method_id"] for row in rows]
            self.assertEqual(len(method_ids), len(set(method_ids)), 
                           "Duplicate method IDs found in summaries")
            
            # Check summary content is not empty
            for row in rows:
                self.assertTrue(len(row["llm_summary"]) > 0, "LLM summary is empty")
                self.assertTrue(len(row["rule_summary"]) > 0, "Rule summary is empty")
    
    def test_interaction_logs_timestamp_precision(self):
        """Verify interaction logs have valid timestamps with required precision."""
        # Create test raw logs
        test_logs = [
            {
                "participant_id": "P001",
                "task_id": "T001",
                "condition": "llm",
                "timestamp_ms": 1699999999999,
                "selected_line": 5,
                "ground_truth_line": 5
            },
            {
                "participant_id": "P001",
                "task_id": "T001",
                "condition": "rule",
                "timestamp_ms": 1699999999999 + 150,  # 150ms later
                "selected_line": 7,
                "ground_truth_line": 5
            }
        ]
        
        with open(self.raw_logs_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=test_logs[0].keys())
            writer.writeheader()
            writer.writerows(test_logs)
        
        # Load and validate
        logs = load_raw_logs(self.raw_logs_file)
        
        self.assertEqual(len(logs), len(test_logs), "Log count mismatch")
        
        for log in logs:
            # Check required fields
            self.assertIn("participant_id", log)
            self.assertIn("task_id", log)
            self.assertIn("condition", log)
            self.assertIn("timestamp_ms", log)
            self.assertIn("selected_line", log)
            self.assertIn("ground_truth_line", log)
            
            # Validate timestamp is positive integer
            self.assertIsInstance(log["timestamp_ms"], int)
            self.assertGreater(log["timestamp_ms"], 0)
            
            # Validate line numbers are positive
            self.assertIsInstance(log["selected_line"], int)
            self.assertIsInstance(log["ground_truth_line"], int)
            self.assertGreater(log["selected_line"], 0)
            self.assertGreater(log["ground_truth_line"], 0)
            
            # Validate condition is one of expected values
            self.assertIn(log["condition"], ["llm", "rule", "baseline"])
    
    def test_anonymization_mapping_bijective(self):
        """Verify anonymization mapping is bijective (one-to-one and onto)."""
        # Create test logs
        test_logs = [
            {"participant_id": "P001", "task_id": "T001", "condition": "llm", 
             "timestamp_ms": 1000, "selected_line": 5, "ground_truth_line": 5},
            {"participant_id": "P002", "task_id": "T001", "condition": "rule", 
             "timestamp_ms": 2000, "selected_line": 7, "ground_truth_line": 5},
            {"participant_id": "P003", "task_id": "T001", "condition": "baseline", 
             "timestamp_ms": 3000, "selected_line": 3, "ground_truth_line": 5}
        ]
        
        with open(self.raw_logs_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=test_logs[0].keys())
            writer.writeheader()
            writer.writerows(test_logs)
        
        # Create mapping
        mapping = create_anonymization_mapping(test_logs)
        
        # Save mapping
        with open(self.mapping_file, 'w') as f:
            json.dump(mapping, f)
        
        # Verify bijective property
        original_ids = set(mapping.keys())
        anonymized_ids = set(mapping.values())
        
        # One-to-one: no two original IDs map to same anonymized ID
        self.assertEqual(len(original_ids), len(anonymized_ids), 
                       "Mapping is not one-to-one (duplicate anonymized IDs)")
        
        # All original IDs are present
        self.assertEqual(len(original_ids), len(test_logs), 
                       "Not all participant IDs are in mapping")
        
        # Verify no empty or None values
        for key, value in mapping.items():
            self.assertIsNotNone(key)
            self.assertIsNotNone(value)
            self.assertNotEqual(key, "")
            self.assertNotEqual(value, "")
    
    def test_anonymized_logs_no_data_loss(self):
        """Verify anonymized logs contain all data from raw logs (except PIDs)."""
        # Create test logs
        test_logs = [
            {"participant_id": "P001", "task_id": "T001", "condition": "llm", 
             "timestamp_ms": 1000, "selected_line": 5, "ground_truth_line": 5},
            {"participant_id": "P002", "task_id": "T001", "condition": "rule", 
             "timestamp_ms": 2000, "selected_line": 7, "ground_truth_line": 5}
        ]
        
        with open(self.raw_logs_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=test_logs[0].keys())
            writer.writeheader()
            writer.writerows(test_logs)
        
        # Anonymize logs
        anonymize_logs(self.raw_logs_file, self.anonymized_logs_file, self.mapping_file)
        
        # Load both files
        with open(self.raw_logs_file, 'r', newline='') as f:
            raw_reader = csv.DictReader(f)
            raw_rows = list(raw_reader)
        
        with open(self.anonymized_logs_file, 'r', newline='') as f:
            anon_reader = csv.DictReader(f)
            anon_rows = list(anon_reader)
        
        # Same number of rows
        self.assertEqual(len(raw_rows), len(anon_rows), 
                       "Row count changed after anonymization")
        
        # All non-PID fields preserved exactly
        for raw_row, anon_row in zip(raw_rows, anon_rows):
            self.assertEqual(raw_row["task_id"], anon_row["task_id"])
            self.assertEqual(raw_row["condition"], anon_row["condition"])
            self.assertEqual(raw_row["timestamp_ms"], anon_row["timestamp_ms"])
            self.assertEqual(raw_row["selected_line"], anon_row["selected_line"])
            self.assertEqual(raw_row["ground_truth_line"], anon_row["ground_truth_line"])
            
            # PID should be different and anonymized
            self.assertNotEqual(raw_row["participant_id"], anon_row["participant_id"])
            self.assertTrue(anon_row["participant_id"].startswith("A"))  # Anonymized prefix
    
    def test_analysis_results_completeness(self):
        """Verify analysis results contain all required comparisons and valid values."""
        # Create test analysis results
        test_results = {
            "mcnemar_tests": {
                "baseline_vs_llm": {"p_value": 0.03, "odds_ratio": 2.5, "significant": True},
                "baseline_vs_rule": {"p_value": 0.15, "odds_ratio": 1.2, "significant": False},
                "llm_vs_rule": {"p_value": 0.08, "odds_ratio": 1.8, "significant": False}
            },
            "lme_models": {
                "baseline_vs_llm": {"p_value": 0.02, "cohen_d": 0.8, "significant": True},
                "baseline_vs_rule": {"p_value": 0.20, "cohen_d": 0.3, "significant": False},
                "llm_vs_rule": {"p_value": 0.12, "cohen_d": 0.5, "significant": False}
            },
            "effect_sizes": {
                "baseline_vs_llm": {"odds_ratio": 2.5, "ci_lower": 1.2, "ci_upper": 4.1},
                "baseline_vs_rule": {"odds_ratio": 1.2, "ci_lower": 0.8, "ci_upper": 1.8},
                "llm_vs_rule": {"odds_ratio": 1.8, "ci_lower": 0.9, "ci_upper": 3.5}
            }
        }
        
        results_file = Path(self.test_dir) / "analysis_results.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f)
        
        # Validate structure
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        # Check required sections
        self.assertIn("mcnemar_tests", data)
        self.assertIn("lme_models", data)
        self.assertIn("effect_sizes", data)
        
        # Check all comparisons present
        expected_comparisons = ["baseline_vs_llm", "baseline_vs_rule", "llm_vs_rule"]
        
        for comparison in expected_comparisons:
            # McNemar tests
            self.assertIn(comparison, data["mcnemar_tests"])
            self.assertIn("p_value", data["mcnemar_tests"][comparison])
            self.assertIn("odds_ratio", data["mcnemar_tests"][comparison])
            self.assertIn("significant", data["mcnemar_tests"][comparison])
            
            # LME models
            self.assertIn(comparison, data["lme_models"])
            self.assertIn("p_value", data["lme_models"][comparison])
            self.assertIn("cohen_d", data["lme_models"][comparison])
            self.assertIn("significant", data["lme_models"][comparison])
            
            # Effect sizes
            self.assertIn(comparison, data["effect_sizes"])
            self.assertIn("odds_ratio", data["effect_sizes"][comparison])
            self.assertIn("ci_lower", data["effect_sizes"][comparison])
            self.assertIn("ci_upper", data["effect_sizes"][comparison])
        
        # Validate numerical values
        for comparison in expected_comparisons:
            # p-values should be in [0, 1]
            mcnemar_p = data["mcnemar_tests"][comparison]["p_value"]
            lme_p = data["lme_models"][comparison]["p_value"]
            self.assertGreaterEqual(mcnemar_p, 0)
            self.assertLessEqual(mcnemar_p, 1)
            self.assertGreaterEqual(lme_p, 0)
            self.assertLessEqual(lme_p, 1)
            
            # Odds ratios should be positive
            self.assertGreater(data["mcnemar_tests"][comparison]["odds_ratio"], 0)
            self.assertGreater(data["effect_sizes"][comparison]["odds_ratio"], 0)
            
            # Cohen's d should be reasonable
            self.assertGreaterEqual(data["lme_models"][comparison]["cohen_d"], 0)
            
            # CI bounds should be consistent
            ci_lower = data["effect_sizes"][comparison]["ci_lower"]
            ci_upper = data["effect_sizes"][comparison]["ci_upper"]
            self.assertLessEqual(ci_lower, ci_upper)
    
    def test_artifact_hash_verification(self):
        """Verify artifact hashes can be generated and verified correctly."""
        # Create test file
        test_file = Path(self.test_dir) / "test_artifact.txt"
        test_content = "Test artifact content for hash verification"
        test_file.write_text(test_content)
        
        # Generate hash
        hash_value = hash_file(test_file)
        
        # Verify hash
        is_valid = verify_file_hash(test_file, hash_value)
        self.assertTrue(is_valid, "Hash verification failed for valid file")
        
        # Modify file and verify hash fails
        test_file.write_text("Modified content")
        is_valid = verify_file_hash(test_file, hash_value)
        self.assertFalse(is_valid, "Hash verification should fail for modified file")
    
    def test_file_integrity_preservation(self):
        """Verify that files maintain integrity through read/write cycles."""
        # Create test JSON file
        test_data = {
            "key1": "value1",
            "key2": 123,
            "key3": [1, 2, 3],
            "nested": {"inner_key": "inner_value"}
        }
        
        test_file = Path(self.test_dir) / "test_integrity.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        # Read back and compare
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(test_data, loaded_data, "Data changed after JSON read/write cycle")
        
        # Create test CSV file
        test_csv_data = [
            {"col1": "a", "col2": "b", "col3": "c"},
            {"col1": "1", "col2": "2", "col3": "3"}
        ]
        
        csv_file = Path(self.test_dir) / "test_integrity.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=test_csv_data[0].keys())
            writer.writeheader()
            writer.writerows(test_csv_data)
        
        # Read back and compare
        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            loaded_rows = list(reader)
        
        self.assertEqual(len(test_csv_data), len(loaded_rows), "CSV row count mismatch")
        for original, loaded in zip(test_csv_data, loaded_rows):
            self.assertEqual(original, loaded, "CSV row data mismatch")

if __name__ == '__main__':
    unittest.main()