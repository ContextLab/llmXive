"""
Integration test for end-to-end encoding pipeline on sample data.

This test verifies the complete flow from ground-truth label extraction
through VAE encoding of image crops.

Prerequisites:
- T008-run: Ground-truth labels must exist at data/interim/ground_truth_labels.parquet
- T009a-run: Latent vectors must exist at data/interim/latent_vectors_unlabeled.parquet
"""
import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest
import pandas as pd
import numpy as np

# Project imports (relative to code/ directory)
from data.preprocess import load_raw_dataset, extract_ground_truth_labels
from models.vae_loader import load_vae_cpu
from analysis.separability import run_power_analysis

# Project root path (assuming tests/ is at same level as code/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_ROOT = PROJECT_ROOT / "code"
DATA_ROOT = PROJECT_ROOT / "data"
INTERIM_ROOT = DATA_ROOT / "interim"
RESULTS_ROOT = DATA_ROOT / "results"

# Ensure directories exist
INTERIM_ROOT.mkdir(parents=True, exist_ok=True)
RESULTS_ROOT.mkdir(parents=True, exist_ok=True)


class TestEncodingPipeline:
    """Integration tests for the encoding pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.sample_path = INTERIM_ROOT / "sample_omnidoc.parquet"
        self.gt_labels_path = INTERIM_ROOT / "ground_truth_labels.parquet"
        self.latent_vectors_path = INTERIM_ROOT / "latent_vectors_unlabeled.parquet"

        # Ensure required files exist (from prerequisites)
        assert self.gt_labels_path.exists(), (
            f"Ground truth labels not found at {self.gt_labels_path}. "
            "Please run T008-run first."
        )

    def test_ground_truth_extraction_complete(self):
        """Test that ground truth labels are correctly extracted and saved."""
        # Load the extracted labels
        df = pd.read_parquet(self.gt_labels_path)

        # Verify required columns exist
        required_columns = [
            'bbox_x_min', 'bbox_y_min', 'bbox_width', 'bbox_height',
            'modality_label', 'image_id'
        ]
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"

        # Verify data types
        assert df['modality_label'].dtype in ['object', 'str', 'category'], \
            "modality_label should be string or category"

        # Verify no null values in critical columns
        assert not df['modality_label'].isnull().any(), \
            "modality_label contains null values"
        assert not df['bbox_x_min'].isnull().any(), \
            "bbox_x_min contains null values"

        # Verify label distribution
        label_counts = df['modality_label'].value_counts()
        assert len(label_counts) > 0, "No labels found in ground truth"

    def test_vae_cpu_loading(self):
        """Test that VAE model loads successfully on CPU."""
        try:
            vae_model = load_vae_cpu()
            assert vae_model is not None, "VAE model is None"
            # Verify model is on CPU
            device = next(vae_model.parameters()).device
            assert device.type == 'cpu', f"Model not on CPU, got {device}"
        except Exception as e:
            pytest.fail(f"VAE CPU loading failed: {str(e)}")

    def test_latent_vector_encoding(self):
        """Test that latent vectors are correctly encoded from image crops."""
        assert self.latent_vectors_path.exists(), (
            f"Latent vectors not found at {self.latent_vectors_path}. "
            "Please run T009a-run first."
        )

        # Load latent vectors
        df = pd.read_parquet(self.latent_vectors_path)

        # Verify required columns
        required_columns = ['image_id', 'bbox_id', 'latent_vector', 'modality_label']
        for col in required_columns:
            assert col in df.columns, f"Missing column in latent vectors: {col}"

        # Verify latent vector dimensions (should be consistent)
        sample_vector = df['latent_vector'].iloc[0]
        if isinstance(sample_vector, np.ndarray):
            vector_dim = len(sample_vector)
            assert vector_dim > 0, "Latent vector dimension is 0"

            # Check all vectors have same dimension
            for idx, vector in enumerate(df['latent_vector']):
                if isinstance(vector, np.ndarray):
                    assert len(vector) == vector_dim, \
                        f"Inconsistent latent vector dimension at index {idx}"

        # Verify no null latent vectors
        assert not df['latent_vector'].isnull().any(), \
            "Latent vectors contain null values"

        # Verify modality labels match ground truth
        gt_df = pd.read_parquet(self.gt_labels_path)
        gt_labels = set(gt_df['modality_label'].unique())
        latent_labels = set(df['modality_label'].unique())
        assert latent_labels.issubset(gt_labels), \
            f"Latent labels {latent_labels} not subset of ground truth {gt_labels}"

    def test_end_to_end_pipeline_consistency(self):
        """Test consistency across the entire encoding pipeline."""
        # Load ground truth
        gt_df = pd.read_parquet(self.gt_labels_path)
        gt_count = len(gt_df)

        # Load latent vectors
        latent_df = pd.read_parquet(self.latent_vectors_path)
        latent_count = len(latent_df)

        # Verify counts match (each ground truth region should have a latent vector)
        assert gt_count == latent_count, \
            f"Ground truth count ({gt_count}) != latent vector count ({latent_count})"

        # Verify image_id consistency
        gt_image_ids = set(gt_df['image_id'].unique())
        latent_image_ids = set(latent_df['image_id'].unique())
        assert gt_image_ids == latent_image_ids, \
            "Image ID mismatch between ground truth and latent vectors"

        # Verify modality label consistency
        for image_id in gt_image_ids:
            gt_labels = set(gt_df[gt_df['image_id'] == image_id]['modality_label'])
            latent_labels = set(latent_df[latent_df['image_id'] == image_id]['modality_label'])
            assert gt_labels == latent_labels, \
                f"Modality label mismatch for image {image_id}"

    def test_pipeline_output_integrity(self):
        """Test that all pipeline outputs maintain data integrity."""
        # Load data
        gt_df = pd.read_parquet(self.gt_labels_path)
        latent_df = pd.read_parquet(self.latent_vectors_path)

        # Check for duplicate image_id + bbox_id combinations
        latent_df['composite_id'] = latent_df['image_id'].astype(str) + '_' + latent_df['bbox_id'].astype(str)
        assert latent_df['composite_id'].duplicated().sum() == 0, \
            "Duplicate image_id + bbox_id combinations found"

        # Verify bounding box coordinates are valid
        assert (gt_df['bbox_x_min'] >= 0).all(), "Invalid bbox_x_min values"
        assert (gt_df['bbox_y_min'] >= 0).all(), "Invalid bbox_y_min values"
        assert (gt_df['bbox_width'] > 0).all(), "Invalid bbox_width values"
        assert (gt_df['bbox_height'] > 0).all(), "Invalid bbox_height values"

    def test_power_analysis_compatibility(self):
        """Test that encoded data is compatible with power analysis requirements."""
        # Load latent vectors
        latent_df = pd.read_parquet(self.latent_vectors_path)

        # Verify we have enough samples for analysis
        sample_count = len(latent_df)
        assert sample_count >= 10, \
            f"Insufficient samples ({sample_count}) for power analysis"

        # Verify modality balance (at least some of each)
        label_counts = latent_df['modality_label'].value_counts()
        assert len(label_counts) >= 2, \
            f"Need at least 2 modality classes, found {len(label_counts)}"

        # Verify we can compute statistics
        for label in label_counts.index:
            subset = latent_df[latent_df['modality_label'] == label]
            assert len(subset) >= 2, \
                f"Insufficient samples for modality {label} for statistical analysis"


def test_pipeline_execution_summary():
    """
    Generate a summary report of the pipeline execution.
    This function can be run standalone to verify pipeline status.
    """
    summary = {
        "status": "unknown",
        "checks": {},
        "errors": []
    }

    try:
        # Check ground truth labels
        if (INTERIM_ROOT / "ground_truth_labels.parquet").exists():
            gt_df = pd.read_parquet(INTERIM_ROOT / "ground_truth_labels.parquet")
            summary["checks"]["ground_truth_exists"] = True
            summary["checks"]["ground_truth_count"] = len(gt_df)
        else:
            summary["checks"]["ground_truth_exists"] = False
            summary["errors"].append("Ground truth labels not found")

        # Check latent vectors
        if (INTERIM_ROOT / "latent_vectors_unlabeled.parquet").exists():
            latent_df = pd.read_parquet(INTERIM_ROOT / "latent_vectors_unlabeled.parquet")
            summary["checks"]["latent_vectors_exists"] = True
            summary["checks"]["latent_vector_count"] = len(latent_df)
            summary["checks"]["latent_vector_dim"] = len(latent_df['latent_vector'].iloc[0]) if len(latent_df) > 0 else 0
        else:
            summary["checks"]["latent_vectors_exists"] = False
            summary["errors"].append("Latent vectors not found")

        # Check consistency
        if summary["checks"].get("ground_truth_exists") and summary["checks"].get("latent_vectors_exists"):
            gt_count = summary["checks"]["ground_truth_count"]
            latent_count = summary["checks"]["latent_vector_count"]
            summary["checks"]["count_match"] = gt_count == latent_count
            if gt_count != latent_count:
                summary["errors"].append(f"Count mismatch: GT={gt_count}, Latent={latent_count}")

        # Final status
        if not summary["errors"]:
            summary["status"] = "PASS"
        else:
            summary["status"] = "FAIL"

    except Exception as e:
        summary["status"] = "ERROR"
        summary["errors"].append(str(e))

    # Write summary to results
    summary_path = RESULTS_ROOT / "pipeline_integration_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"Pipeline integration summary written to: {summary_path}")
    print(f"Status: {summary['status']}")
    if summary["errors"]:
        print("Errors:")
        for error in summary["errors"]:
            print(f"  - {error}")

    return summary


if __name__ == "__main__":
    # Run as standalone script
    import sys
    sys.path.insert(0, str(CODE_ROOT))

    summary = test_pipeline_execution_summary()
    if summary["status"] != "PASS":
        sys.exit(1)