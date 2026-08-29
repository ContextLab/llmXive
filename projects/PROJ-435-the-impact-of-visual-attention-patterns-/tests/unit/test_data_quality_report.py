import os
import sys
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.data_quality_report import generate_quality_report

class TestGenerateQualityReport:
    def test_generate_quality_report(self):
        exclusion_log = [
            "Participant 1 excluded: data loss > 20%",
            "Participant 2 excluded: missing ROI"
        ]
        preprocessed_df = pd.DataFrame({
            'participant_id': [3, 4, 5],
            'headline_id': ['H1', 'H1', 'H2']
        })
        hash_registry = {
            'data/raw/eye_tracking_raw.parquet': 'abc123'
        }
        
        report = generate_quality_report(exclusion_log, preprocessed_df, hash_registry)
        
        assert 'excluded_participants' in report
        assert 'total_participants' in report
        assert 'reasons' in report
        assert report['excluded_participants'] == 2
        assert report['total_participants'] == 5 # 3 remaining + 2 excluded
