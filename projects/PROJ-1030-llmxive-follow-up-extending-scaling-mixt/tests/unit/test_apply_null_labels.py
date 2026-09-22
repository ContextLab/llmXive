"""
Unit tests for T024: apply_null_labels.py
"""

import pytest
import os
import json
import csv
import tempfile
from pathlib import Path
import pandas as pd

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from apply_null_labels import (
    process_labels_and_exclusions,
    save_labels_csv,
    save_excluded_log,
    CONFIDENCE_THRESHOLD
)

class TestProcessLabelsAndExclusions:
    """Test the core logic for identifying null labels and exclusions."""

    def test_low_confidence_triggers_null(self):
        """Test that low confidence scores trigger null labels."""
        temp_labels = {
            'clip_001': {
                'clip_id': 'clip_001',
                'label': 'valid',
                'reason': 'reconstructed',
                'confidence_score': 0.85,  # Below threshold
                'perturbation_type': 0
            }
        }

        labels, excluded = process_labels_and_exclusions(temp_labels, {}, {})

        assert len(labels) == 1
        assert labels[0]['label'] == 'null'
        assert labels[0]['clip_id'] == 'clip_001'
        assert len(excluded) == 1
        assert excluded[0]['clip_id'] == 'clip_001'
        assert 'Low confidence' in excluded[0]['reason']

    def test_high_confidence_preserves_label(self):
        """Test that high confidence scores preserve original labels."""
        temp_labels = {
            'clip_002': {
                'clip_id': 'clip_002',
                'label': 'invalid',
                'reason': 'gravity_violation',
                'confidence_score': 0.95,  # Above threshold
                'perturbation_type': 0
            }
        }

        labels, excluded = process_labels_and_exclusions(temp_labels, {}, {})

        assert len(labels) == 1
        assert labels[0]['label'] == 'invalid'
        assert len(excluded) == 0

    def test_simulation_failure_triggers_null(self):
        """Test that simulation failures trigger null labels."""
        temp_labels = {
            'clip_003': {
                'clip_id': 'clip_003',
                'label': 'null',
                'reason': 'simulation_timeout',
                'confidence_score': 0.95,
                'perturbation_type': 0
            }
        }

        labels, excluded = process_labels_and_exclusions(temp_labels, {}, {})

        assert len(labels) == 1
        assert labels[0]['label'] == 'null'
        assert len(excluded) == 1
        assert 'simulation' in excluded[0]['reason'].lower()

    def test_mixed_results(self):
        """Test processing of a mixed batch of labels."""
        temp_labels = {
            'clip_A': {'clip_id': 'clip_A', 'label': 'valid', 'reason': 'ok', 'confidence_score': 0.92, 'perturbation_type': 0},
            'clip_B': {'clip_id': 'clip_B', 'label': 'valid', 'reason': 'ok', 'confidence_score': 0.88, 'perturbation_type': 0},
            'clip_C': {'clip_id': 'clip_C', 'label': 'null', 'reason': 'sim_failed', 'confidence_score': 0.91, 'perturbation_type': 0},
            'clip_D': {'clip_id': 'clip_D', 'label': 'invalid', 'reason': 'collision', 'confidence_score': 0.96, 'perturbation_type': 1}
        }

        labels, excluded = process_labels_and_exclusions(temp_labels, {}, {})

        assert len(labels) == 4
        assert len(excluded) == 2

        # Check specific outcomes
        label_dict = {l['clip_id']: l for l in labels}
        assert label_dict['clip_A']['label'] == 'valid'
        assert label_dict['clip_B']['label'] == 'null'  # Low confidence
        assert label_dict['clip_C']['label'] == 'null'  # Sim failure
        assert label_dict['clip_D']['label'] == 'invalid'

        excluded_ids = [e['clip_id'] for e in excluded]
        assert 'clip_B' in excluded_ids
        assert 'clip_C' in excluded_ids

class TestSaveLabelsCsv:
    """Test saving labels to CSV."""

    def test_save_with_records(self, tmp_path):
        """Test saving non-empty labels."""
        records = [
            {'clip_id': 'c1', 'label': 'valid', 'reason': 'ok', 'confidence_score': 0.95, 'perturbation_type': 0},
            {'clip_id': 'c2', 'label': 'null', 'reason': 'low_conf', 'confidence_score': 0.85, 'perturbation_type': 0}
        ]
        output_path = str(tmp_path / 'labels.csv')

        save_labels_csv(records, output_path)

        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert list(df.columns) == ['clip_id', 'label', 'reason', 'confidence_score', 'perturbation_type']

    def test_save_empty_records(self, tmp_path):
        """Test saving empty labels creates header-only CSV."""
        records = []
        output_path = str(tmp_path / 'empty_labels.csv')

        save_labels_csv(records, output_path)

        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert len(df) == 0
        assert list(df.columns) == ['clip_id', 'label', 'reason', 'confidence_score', 'perturbation_type']

class TestSaveExcludedLog:
    """Test saving excluded samples to log."""

    def test_save_with_records(self, tmp_path):
        """Test saving non-empty excluded log."""
        records = [
            {'clip_id': 'c1', 'reason': 'low_conf', 'confidence_score': 0.85}
        ]
        output_path = str(tmp_path / 'excluded.log')

        save_excluded_log(records, output_path)

        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert len(df) == 1
        assert list(df.columns) == ['clip_id', 'reason', 'confidence_score']

    def test_save_empty_records(self, tmp_path):
        """Test saving empty excluded log creates header-only CSV."""
        records = []
        output_path = str(tmp_path / 'empty_excluded.log')

        save_excluded_log(records, output_path)

        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert len(df) == 0
        assert list(df.columns) == ['clip_id', 'reason', 'confidence_score']