import pytest
import json
import os
import tempfile
from pathlib import Path
import sys
from src.results_aggregator import aggregate_and_write_results, process_and_save_analysis
from src.models import AnalysisResult


class TestResultsAggregator:
    """Tests for results aggregation."""
    
    def test_aggregate_and_write(self):
        """Test aggregation and writing."""
        result = AnalysisResult(
            t_statistic=2.0,
            p_value=0.05,
            effect_size=0.5,
            confidence_interval=[0.1, 0.9],
            method="t-test"
        )
        
        output_path = os.path.join(tempfile.gettempdir(), "agg_test.json")
        aggregate_and_write_results([result], output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert "results" in data
        
    def test_process_and_save(self):
        """Test processing and saving."""
        result = AnalysisResult(
            t_statistic=2.0,
            p_value=0.05,
            effect_size=0.5,
            confidence_interval=[0.1, 0.9],
            method="t-test"
        )
        
        output_path = os.path.join(tempfile.gettempdir(), "proc_test.json")
        process_and_save_analysis(result, output_path)
        
        assert os.path.exists(output_path)
