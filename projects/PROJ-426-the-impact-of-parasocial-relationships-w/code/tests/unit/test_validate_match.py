import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import yaml
from unittest.mock import patch, MagicMock

import sys
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.validation.validate_match import (
    calculate_match_rate,
    validate_match,
    MIN_MATCHED_USERS,
    MIN_MATCH_RATE
)

class TestCalculateMatchRate:
    def test_normal_case(self):
        rate = calculate_match_rate(1000, 800)
        assert rate == 0.8

    def test_zero_total(self):
        rate = calculate_match_rate(0, 0)
        assert rate == 0.0

    def test_perfect_match(self):
        rate = calculate_match_rate(500, 500)
        assert rate == 1.0

    def test_partial_match(self):
        rate = calculate_match_rate(100, 10)
        assert rate == 0.1

class TestValidateMatch:
    @pytest.fixture
    def temp_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create necessary subdirectories
            (tmp_path / "data" / "raw").mkdir(parents=True)
            (tmp_path / "data" / "processed").mkdir(parents=True)
            (tmp_path / "data" / "validation").mkdir(parents=True)
            yield tmp_path

    def test_successful_validation(self, temp_dirs):
        # Create mock data
        loneliness_data = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(1000)],
            'loneliness_score': [0.5] * 1000
        })
        matched_data = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(900)],
            'loneliness_score': [0.5] * 900
        })

        loneliness_path = temp_dirs / "data" / "raw" / "loneliness_dataset.parquet"
        matched_path = temp_dirs / "data" / "processed" / "matched_users.parquet"
        output_path = temp_dirs / "data" / "validation" / "match_report.yaml"

        loneliness_data.to_parquet(loneliness_path)
        matched_data.to_parquet(matched_path)

        with patch('src.validation.validate_match.LONELINESS_USERS_PATH', loneliness_path), \
             patch('src.validation.validate_match.MATCHED_USERS_PATH', matched_path), \
             patch('src.validation.validate_match.OUTPUT_REPORT_PATH', output_path):
            
            report = validate_match()

            assert report['status'] == 'pass'
            assert report['total_users'] == 1000
            assert report['matched_users'] == 900
            assert report['match_rate'] == 0.9
            assert output_path.exists()

    def test_low_match_rate_fails(self, temp_dirs):
        # Create mock data with low match rate
        loneliness_data = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(1000)],
            'loneliness_score': [0.5] * 1000
        })
        matched_data = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(100)],  # 10% match rate
            'loneliness_score': [0.5] * 100
        })

        loneliness_path = temp_dirs / "data" / "raw" / "loneliness_dataset.parquet"
        matched_path = temp_dirs / "data" / "processed" / "matched_users.parquet"
        output_path = temp_dirs / "data" / "validation" / "match_report.yaml"

        loneliness_data.to_parquet(loneliness_path)
        matched_data.to_parquet(matched_path)

        with patch('src.validation.validate_match.LONELINESS_USERS_PATH', loneliness_path), \
             patch('src.validation.validate_match.MATCHED_USERS_PATH', matched_path), \
             patch('src.validation.validate_match.OUTPUT_REPORT_PATH', output_path):
            
            with pytest.raises(RuntimeError) as exc_info:
                validate_match()
            
            assert "Power Insufficient" in str(exc_info.value)
            assert "Match rate" in str(exc_info.value)

    def test_low_matched_count_fails(self, temp_dirs):
        # Create mock data with low matched count
        loneliness_data = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(1000)],
            'loneliness_score': [0.5] * 1000
        })
        matched_data = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(400)],  # Below 500 threshold
            'loneliness_score': [0.5] * 400
        })

        loneliness_path = temp_dirs / "data" / "raw" / "loneliness_dataset.parquet"
        matched_path = temp_dirs / "data" / "processed" / "matched_users.parquet"
        output_path = temp_dirs / "data" / "validation" / "match_report.yaml"

        loneliness_data.to_parquet(loneliness_path)
        matched_data.to_parquet(matched_path)

        with patch('src.validation.validate_match.LONELINESS_USERS_PATH', loneliness_path), \
             patch('src.validation.validate_match.MATCHED_USERS_PATH', matched_path), \
             patch('src.validation.validate_match.OUTPUT_REPORT_PATH', output_path):
            
            with pytest.raises(RuntimeError) as exc_info:
                validate_match()
            
            assert "Power Insufficient" in str(exc_info.value)
            assert "Matched users" in str(exc_info.value)

    def test_missing_file_raises_error(self, temp_dirs):
        with patch('src.validation.validate_match.LONELINESS_USERS_PATH', temp_dirs / "nonexistent.parquet"), \
             patch('src.validation.validate_match.MATCHED_USERS_PATH', temp_dirs / "nonexistent2.parquet"):
            
            with pytest.raises(FileNotFoundError):
                validate_match()