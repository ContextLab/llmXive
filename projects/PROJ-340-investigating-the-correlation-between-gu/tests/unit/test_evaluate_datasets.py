"""
Unit tests for the evaluate_datasets module (T050).
"""
import pytest
import os
import sys
from pathlib import Path
import csv
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from evaluate_datasets import (
    evaluate_data_quality,
    evaluate_variable_completeness,
    evaluate_privacy_constraints,
    evaluate_dataset,
    generate_evaluation_matrix
)

class TestEvaluateDataQuality:
    def test_large_sample_shotgun_psg(self):
        ds = {
            "n_samples": 300,
            "microbiome_type": "Shotgun",
            "sleep_type": "PSG"
        }
        res = evaluate_data_quality(ds)
        assert res["score"] > 80
        assert "Large sample size" in res["notes"][0]
        assert "Shotgun" in res["notes"][1]
        assert "Polysomnography" in res["notes"][2]

    def test_small_sample_16s_actigraphy(self):
        ds = {
            "n_samples": 50,
            "microbiome_type": "16S",
            "sleep_type": "Actigraphy"
        }
        res = evaluate_data_quality(ds)
        assert res["score"] < 80
        assert "Small sample size" in res["notes"][0]

class TestEvaluateVariableCompleteness:
    def test_complete_dataset(self):
        ds = {
            "has_microbiome": True,
            "has_sleep": True
        }
        res = evaluate_variable_completeness(ds)
        assert res["is_complete"] is True
        assert len(res["missing_microbiome_vars"]) == 0
        assert len(res["missing_sleep_vars"]) == 0

    def test_missing_sleep(self):
        ds = {
            "has_microbiome": True,
            "has_sleep": False
        }
        res = evaluate_variable_completeness(ds)
        assert res["is_complete"] is False
        assert len(res["missing_sleep_vars"]) > 0

class TestEvaluatePrivacyConstraints:
    def test_open_access(self):
        ds = {"privacy": "Open"}
        res = evaluate_privacy_constraints(ds)
        assert res["score"] == 100
        assert res["access_level"] == "Open"

    def test_restricted_access(self):
        ds = {"privacy": "Restricted"}
        res = evaluate_privacy_constraints(ds)
        assert res["score"] == 50
        assert res["access_level"] == "Restricted"

class TestEvaluateDatasetIntegration:
    def test_full_evaluation(self):
        ds = {
            "name": "TestDS",
            "source": "Test",
            "n_samples": 250,
            "has_microbiome": True,
            "has_sleep": True,
            "microbiome_type": "Shotgun",
            "sleep_type": "PSG",
            "privacy": "Open"
        }
        res = evaluate_dataset(ds)
        assert res["final_weighted_score"] > 80
        assert res["recommendation"] == "Suitable"
        assert res["is_complete"] is True

class TestGenerateEvaluationMatrix:
    def test_csv_generation(self, tmp_path):
        output_file = tmp_path / "test_matrix.csv"
        datasets = [
            {
                "name": "DS1", "source": "Src1", "n_samples": 200,
                "has_microbiome": True, "has_sleep": True,
                "microbiome_type": "16S", "sleep_type": "Actigraphy",
                "privacy": "Open"
            }
        ]
        generate_evaluation_matrix(datasets, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["dataset_name"] == "DS1"
            assert rows[0]["is_complete"] == "True"