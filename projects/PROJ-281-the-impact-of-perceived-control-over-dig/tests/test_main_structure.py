"""
Smoke test to verify main pipeline stages are importable.
"""
import pytest
from code.main import (
    stage_01_data_ingestion,
    stage_02_preprocessing,
    stage_03_anxiety_scoring,
    stage_04_proxy_extraction,
    stage_05_merge_and_validate,
    stage_06_statistical_analysis,
    stage_07_visualization,
    run_pipeline
)

def test_all_stages_callable():
    assert callable(stage_01_data_ingestion)
    assert callable(stage_02_preprocessing)
    assert callable(stage_03_anxiety_scoring)
    assert callable(stage_04_proxy_extraction)
    assert callable(stage_05_merge_and_validate)
    assert callable(stage_06_statistical_analysis)
    assert callable(stage_07_visualization)
    assert callable(run_pipeline)
