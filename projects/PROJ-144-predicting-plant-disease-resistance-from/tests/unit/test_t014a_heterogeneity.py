"""
Unit tests for T014a: Detect label heterogeneity.
"""

import os
import sys
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.detect_label_heterogeneity import load_phenotype_files, analyze_heterogeneity
from utils.exceptions import DataUnavailableError


class TestLoadPhenotypeFiles:
    def test_load_single_phenotype_file(self, tmp_path):
        """Test loading a single phenotype file."""
        # Create test data
        study_dir = tmp_path / "data" / "raw"
        study_dir.mkdir(parents=True)

        df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3'],
            'measurement_method': ['method_A', 'method_A', 'method_A'],
            'assay_score': [0, 1, 0]
        })

        file_path = study_dir / "study_001_phenotype.csv"
        df.to_csv(file_path, index=False)

        # Load
        studies = load_phenotype_files(str(study_dir))

        assert "study_001" in studies
        assert len(studies["study_001"]) == 3
        assert list(studies["study_001"].columns) == ['sample_id', 'measurement_method', 'assay_score']

    def test_load_multiple_phenotype_files(self, tmp_path):
        """Test loading multiple phenotype files."""
        study_dir = tmp_path / "data" / "raw"
        study_dir.mkdir(parents=True)

        for i in range(3):
            df = pd.DataFrame({
                'sample_id': [f'S{i}_{j}' for j in range(5)],
                'measurement_method': ['method_A'] * 5,
                'assay_score': [0, 1, 0, 1, 0]
            })
            file_path = study_dir / f"study_{i:03d}_phenotype.csv"
            df.to_csv(file_path, index=False)

        studies = load_phenotype_files(str(study_dir))

        assert len(studies) == 3
        assert all(f"study_{i:03d}" in studies for i in range(3))

    def test_no_phenotype_files_raises_error(self, tmp_path):
        """Test that missing files raise DataUnavailableError."""
        study_dir = tmp_path / "data" / "raw"
        study_dir.mkdir(parents=True)

        with pytest.raises(DataUnavailableError, match="Raw phenotype files missing"):
            load_phenotype_files(str(study_dir))


class TestAnalyzeHeterogeneity:
    def test_single_study_no_heterogeneity(self):
        """Test analysis of a single study with uniform labels."""
        studies = {
            "study_001": pd.DataFrame({
                'sample_id': ['S1', 'S2', 'S3', 'S4'],
                'measurement_method': ['method_A', 'method_A', 'method_A', 'method_A'],
                'assay_score': [0, 1, 0, 1]
            })
        }

        report = analyze_heterogeneity(studies)

        assert report["total_studies"] == 1
        assert report["heterogeneity_detected"] is False
        assert report["summary"]["requires_harmonization"] is False

    def test_multiple_measurement_methods(self):
        """Test detection of multiple measurement methods."""
        studies = {
            "study_001": pd.DataFrame({
                'sample_id': ['S1', 'S2', 'S3', 'S4'],
                'measurement_method': ['method_A', 'method_B', 'method_A', 'method_B'],
                'assay_score': [0, 1, 0, 1]
            })
        }

        report = analyze_heterogeneity(studies)

        assert report["heterogeneity_detected"] is True
        assert "method_A" in report["details"]["measurement_methods"]
        assert "method_B" in report["details"]["measurement_methods"]

    def test_binary_ordinal_mix(self):
        """Test detection of binary and ordinal label mix."""
        studies = {
            "study_001": pd.DataFrame({
                'sample_id': ['S1', 'S2', 'S3', 'S4'],
                'measurement_method': ['method_A', 'method_A', 'method_A', 'method_A'],
                'assay_score': [0, 1, 0, 1]  # Binary
            }),
            "study_002": pd.DataFrame({
                'sample_id': ['S5', 'S6', 'S7', 'S8'],
                'measurement_method': ['method_A', 'method_A', 'method_A', 'method_A'],
                'assay_score': [1, 2, 3, 4]  # Ordinal
            })
        }

        report = analyze_heterogeneity(studies)

        assert report["heterogeneity_detected"] is True
        assert report["details"]["binary_ordinal_mix"] is True

    def test_multi_study_binary_scenario(self):
        """Test detection of multiple studies with binary labels."""
        studies = {
            "study_001": pd.DataFrame({
                'sample_id': ['S1', 'S2', 'S3'],
                'assay_score': [0, 1, 0]
            }),
            "study_002": pd.DataFrame({
                'sample_id': ['S4', 'S5', 'S6'],
                'assay_score': [1, 0, 1]
            })
        }

        report = analyze_heterogeneity(studies)

        # Multiple studies with binary labels should trigger heterogeneity
        assert report["details"]["multi_study_binary"] is True

    def test_no_measurement_method_column(self):
        """Test handling when measurement_method column is missing."""
        studies = {
            "study_001": pd.DataFrame({
                'sample_id': ['S1', 'S2', 'S3'],
                'phenotype': ['resistant', 'susceptible', 'resistant']
            })
        }

        report = analyze_heterogeneity(studies)

        assert report["total_studies"] == 1
        assert "phenotype" in report["studies_analyzed"][0]["columns_found"]