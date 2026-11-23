"""
Integration test for the full Linguistic Accommodation pipeline end-to-end.

This test verifies that:
1. Data ingestion runs successfully and produces `data/processed/accommodation_metrics.csv`.
2. Emotion mapping runs successfully and produces `data/processed/final_dataset.csv`.
3. Statistical analysis runs successfully and produces `outputs/reports/statistical_summary.json`.
4. The final output contains expected keys and valid data types.
5. The pipeline respects the project directory structure and file paths.

Dependencies:
- T016-T022 (Data Ingestion)
- T026-T032 (Emotion Mapping)
- T036a, T038-T047 (Statistical Analysis)

Note: This test assumes the real DailyDialog dataset is available or can be downloaded.
If the download fails, the test will fail loudly as per project constraints.
"""

import os
import sys
import json
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports from code/
# Assuming this test is run from the project root or the parent of 'tests'
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from data.ingestion import main as ingestion_main
from analysis.emotion_mapping import main as emotion_main
from analysis.stats import main as stats_main
from utils import normalize_text, jaccard_similarity

# Constants for expected paths
RAW_DATA_PATH = project_root / "data" / "raw" / "daily_dialog_test.parquet"
PROCESSED_METRICS_PATH = project_root / "data" / "processed" / "accommodation_metrics.csv"
FINAL_DATASET_PATH = project_root / "data" / "processed" / "final_dataset.csv"
STAT_SUMMARY_PATH = project_root / "outputs" / "reports" / "statistical_summary.json"
EMOTION_DIST_PATH = project_root / "outputs" / "reports" / "emotion_distribution.json"

@pytest.fixture(autouse=True)
def ensure_directories():
    """Ensure required output directories exist before running tests."""
    (project_root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (project_root / "outputs" / "reports").mkdir(parents=True, exist_ok=True)
    (project_root / "outputs" / "figures").mkdir(parents=True, exist_ok=True)

def test_pipeline_end_to_end():
    """
    Run the full pipeline: Ingestion -> Emotion Mapping -> Stats.
    Verify intermediate and final artifacts exist and contain valid data.
    """
    # --- Step 1: Data Ingestion ---
    # We call the main function directly. It should handle downloading, processing, and saving.
    # Note: This might take a moment as it downloads/streams DailyDialog.
    try:
        ingestion_main()
    except Exception as e:
        pytest.fail(f"Ingestion step failed: {e}")

    assert PROCESSED_METRICS_PATH.exists(), "Ingestion did not produce accommodation_metrics.csv"
    
    # Validate ingestion output structure
    metrics_df = pd.read_csv(PROCESSED_METRICS_PATH)
    required_cols = ['conversation_id', 'speaker_a_turn', 'speaker_b_turn', 
                     'lexical_overlap', 'syntactic_similarity', 'sentence_length_variance']
    for col in required_cols:
        assert col in metrics_df.columns, f"Missing column in metrics: {col}"
    assert not metrics_df[['lexical_overlap', 'syntactic_similarity', 'sentence_length_variance']].isnull().any().any(), \
        "Metrics contain null values"

    # --- Step 2: Emotion Mapping ---
    try:
        emotion_main()
    except Exception as e:
        pytest.fail(f"Emotion mapping step failed: {e}")

    assert FINAL_DATASET_PATH.exists(), "Emotion mapping did not produce final_dataset.csv"
    
    # Validate final dataset structure
    final_df = pd.read_csv(FINAL_DATASET_PATH)
    assert 'emotional_intensity' in final_df.columns, "Missing emotional_intensity in final dataset"
    assert 'accommodation_score' in final_df.columns, "Missing accommodation_score in final dataset"
    
    # Check intensity values are in range 1-5
    assert final_df['emotional_intensity'].between(1, 5).all(), "Emotional intensity values out of range [1, 5]"

    assert EMOTION_DIST_PATH.exists(), "Emotion mapping did not produce emotion_distribution.json"
    with open(EMOTION_DIST_PATH, 'r') as f:
        dist_report = json.load(f)
    assert 'distribution' in dist_report, "Emotion distribution report missing 'distribution' key"

    # --- Step 3: Statistical Analysis ---
    try:
        stats_main()
    except Exception as e:
        pytest.fail(f"Statistical analysis step failed: {e}")

    assert STAT_SUMMARY_PATH.exists(), "Stats analysis did not produce statistical_summary.json"
    
    # Validate statistical summary content
    with open(STAT_SUMMARY_PATH, 'r') as f:
        stats_report = json.load(f)
    
    required_stats = ['correlation_coefficient', 'p_value', 'effect_size_interpretation', 
                      'bootstrap_ci_width', 'sample_size']
    for key in required_stats:
        assert key in stats_report, f"Missing key in statistical summary: {key}"
    
    # Verify correlation is a float and p-value is between 0 and 1
    assert isinstance(stats_report['correlation_coefficient'], (int, float)), "Correlation coefficient is not a number"
    assert 0 <= stats_report['p_value'] <= 1, "P-value out of range [0, 1]"
    
    # Verify effect size interpretation is a string
    assert isinstance(stats_report['effect_size_interpretation'], str), "Effect size interpretation is not a string"

    # --- Step 4: Verify Consistency ---
    # Ensure the number of records in final dataset matches the stats sample size
    assert stats_report['sample_size'] == len(final_df), \
        f"Sample size mismatch: stats says {stats_report['sample_size']}, dataset has {len(final_df)}"

    print("Pipeline end-to-end test passed successfully.")