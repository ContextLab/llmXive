"""
Unit tests for compressibility score calculation.
"""
import pytest
import json
import csv
from pathlib import Path
import tempfile
import os
from unittest.mock import Mock, patch
from config import Config
from models.compressibility_score import CompressibilityCalculator


class TestCompressibilityCalculator:
    """Tests for the CompressibilityCalculator class."""
    
    @pytest.fixture
    def config(self):
        """Create a mock config for testing."""
        config = Mock(spec=Config)
        config.data_raw_dir = Path("/tmp/test_traces")
        config.data_processed_dir = Path("/tmp/test_processed")
        return config
    
    def test_calculate_score_basic(self, config):
        """Test basic score calculation."""
        calculator = CompressibilityCalculator(config)
        
        # 5 rules, 10 tool calls = 0.5 compressibility
        score = calculator.calculate_score(5, 10)
        assert score == 0.5
        
        # 2 rules, 10 tool calls = 0.2 compressibility
        score = calculator.calculate_score(2, 10)
        assert score == 0.2
        
        # 10 rules, 10 tool calls = 1.0 compressibility
        score = calculator.calculate_score(10, 10)
        assert score == 1.0
    
    def test_calculate_score_edge_cases(self, config):
        """Test edge cases in score calculation."""
        calculator = CompressibilityCalculator(config)
        
        # Zero trace length should return infinity
        score = calculator.calculate_score(5, 0)
        assert score == float('inf')
        
        # Single rule, single tool call
        score = calculator.calculate_score(1, 1)
        assert score == 1.0
    
    def test_process_trace_above_threshold(self, config):
        """Test processing a trace that meets the fidelity threshold."""
        calculator = CompressibilityCalculator(config, fidelity_threshold=0.90)
        
        induction_result = {
            'fidelity': 0.95,
            'ruleset_size': 4
        }
        trace_length = 10
        
        result = calculator.process_trace("trace_001", induction_result, trace_length)
        
        assert result is not None
        assert result['trace_id'] == "trace_001"
        assert result['trace_length'] == 10
        assert result['ruleset_size'] == 4
        assert result['fidelity'] == 0.95
        assert result['compressibility_score'] == 0.4
        assert result['meets_fidelity_threshold'] is True
    
    def test_process_trace_below_threshold(self, config):
        """Test processing a trace that doesn't meet the fidelity threshold."""
        calculator = CompressibilityCalculator(config, fidelity_threshold=0.90)
        
        induction_result = {
            'fidelity': 0.85,
            'ruleset_size': 4
        }
        trace_length = 10
        
        result = calculator.process_trace("trace_001", induction_result, trace_length)
        
        assert result is None
    
    def test_process_trace_at_threshold(self, config):
        """Test processing a trace exactly at the fidelity threshold."""
        calculator = CompressibilityCalculator(config, fidelity_threshold=0.90)
        
        induction_result = {
            'fidelity': 0.90,
            'ruleset_size': 4
        }
        trace_length = 10
        
        result = calculator.process_trace("trace_001", induction_result, trace_length)
        
        assert result is not None
        assert result['compressibility_score'] == 0.4
    
    def test_process_all_traces_integration(self, config):
        """Integration test for processing all traces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            traces_dir = tmpdir_path / "traces"
            processed_dir = tmpdir_path / "processed"
            traces_dir.mkdir()
            processed_dir.mkdir()
            
            # Create mock trace files
            trace_data_1 = {
                'exact_tool_sequence': [
                    {'tool': 'create_slide', 'args': {'title': 'Slide 1'}},
                    {'tool': 'add_text', 'args': {'text': 'Hello'}},
                    {'tool': 'add_image', 'args': {'path': 'img1.png'}},
                    {'tool': 'format_text', 'args': {'bold': True}},
                    {'tool': 'save', 'args': {}}
                ],
                'final_state': {'slides': 1}
            }
            
            trace_data_2 = {
                'exact_tool_sequence': [
                    {'tool': 'create_slide', 'args': {'title': 'Slide 2'}},
                    {'tool': 'add_text', 'args': {'text': 'World'}},
                    {'tool': 'save', 'args': {}}
                ],
                'final_state': {'slides': 1}
            }
            
            with open(traces_dir / "session_trace_001.json", 'w') as f:
                json.dump(trace_data_1, f)
            
            with open(traces_dir / "session_trace_002.json", 'w') as f:
                json.dump(trace_data_2, f)
            
            # Create mock induction results
            induction_results = {
                'trace_001': {
                    'fidelity': 0.95,
                    'ruleset_size': 3
                },
                'trace_002': {
                    'fidelity': 0.85,  # Below threshold
                    'ruleset_size': 2
                }
            }
            
            induction_path = processed_dir / "rule_induction_results.json"
            with open(induction_path, 'w') as f:
                json.dump(induction_results, f)
            
            output_path = processed_dir / "per_trace_scores.csv"
            
            # Update config paths
            config.data_raw_dir = traces_dir
            config.data_processed_dir = processed_dir
            
            calculator = CompressibilityCalculator(config, fidelity_threshold=0.90)
            results = calculator.process_all_traces(traces_dir, induction_path, output_path)
            
            # Only trace_001 should be in results (trace_002 is below threshold)
            assert len(results) == 1
            assert results[0]['trace_id'] == 'trace_001'
            assert results[0]['compressibility_score'] == 0.6  # 3 rules / 5 tool calls
            
            # Verify CSV was written correctly
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['trace_id'] == 'trace_001'
                assert float(rows[0]['compressibility_score']) == 0.6
