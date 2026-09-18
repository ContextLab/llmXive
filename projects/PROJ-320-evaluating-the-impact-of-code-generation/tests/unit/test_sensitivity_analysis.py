"""
Unit tests for sensitivity analysis module.

Tests for T026: Implement sensitivity analysis using secondary detector cohort.
"""
import pytest
import json
import math
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.sensitivity_analysis import (
    load_metrics_with_detector_scores,
    filter_by_detector_cohort,
    run_sensitivity_tests,
    save_sensitivity_results,
    run_sensitivity_analysis
)


class TestLoadMetricsWithDetectorScores:
    """Tests for loading and merging metrics with detector scores."""
    
    def test_load_and_merge_data(self, tmp_path):
        """Test that metrics and labeled data are correctly merged."""
        # Create mock metrics file
        metrics_file = tmp_path / "metrics.csv"
        metrics_file.write_text(
            "pr_id,comment_count,time_to_merge_minutes,review_cycles,complexity_score\n"
            "1,10,120,2,5.5\n"
            "2,5,60,1,3.2\n"
            "3,15,180,3,7.8\n"
        )
        
        # Create mock labeled file
        labeled_file = tmp_path / "labeled.csv"
        labeled_file.write_text(
            "pr_id,source_type,confidence_score,flagged,detector_score\n"
            "1,llm,0.85,False,0.72\n"
            "2,human,0.90,False,0.15\n"
            "3,llm,0.78,True,0.81\n"
        )
        
        # Load and merge
        result = load_metrics_with_detector_scores(metrics_file, labeled_file)
        
        assert len(result) == 3
        assert 'detector_score' in result[0]
        assert 'confidence_score' in result[0]
        assert result[0]['detector_score'] == 0.72
        assert result[1]['source_type'] == 'human'
    
    def test_missing_pr_id_handling(self, tmp_path):
        """Test that PRs without matching labeled data are handled."""
        # Create mock metrics file with extra PR
        metrics_file = tmp_path / "metrics.csv"
        metrics_file.write_text(
            "pr_id,comment_count,time_to_merge_minutes,review_cycles,complexity_score\n"
            "1,10,120,2,5.5\n"
            "99,20,240,4,9.0\n"
        )
        
        # Create mock labeled file without PR 99
        labeled_file = tmp_path / "labeled.csv"
        labeled_file.write_text(
            "pr_id,source_type,confidence_score,flagged,detector_score\n"
            "1,llm,0.85,False,0.72\n"
        )
        
        # Load and merge - should only return matching PRs
        result = load_metrics_with_detector_scores(metrics_file, labeled_file)
        
        assert len(result) == 1
        assert result[0]['pr_id'] == 1


class TestFilterByDetectorCohort:
    """Tests for filtering dataset by detector cohort."""
    
    def test_filter_llm_with_high_detector_score(self):
        """Test that only LLMs with high detector scores are selected."""
        data = [
            {'source_type': 'llm', 'detector_score': 0.85},
            {'source_type': 'llm', 'detector_score': 0.45},
            {'source_type': 'llm', 'detector_score': 0.72},
            {'source_type': 'human', 'detector_score': 0.15},
            {'source_type': 'human', 'detector_score': 0.20},
        ]
        
        primary, secondary = filter_by_detector_cohort(data, threshold=0.7)
        
        # Primary should include all LLMs + humans
        assert len(primary) == 5
        assert len([r for r in primary if r['source_type'] == 'llm']) == 3
        
        # Secondary should include only high-scoring LLMs + humans
        assert len(secondary) == 4  # 2 high-scoring LLMs + 2 humans
        assert len([r for r in secondary if r['source_type'] == 'llm']) == 2
    
    def test_threshold_parameter(self):
        """Test that threshold parameter works correctly."""
        data = [
            {'source_type': 'llm', 'detector_score': 0.75},
            {'source_type': 'llm', 'detector_score': 0.65},
            {'source_type': 'human', 'detector_score': 0.15},
        ]
        
        # With threshold 0.7
        _, secondary_low = filter_by_detector_cohort(data, threshold=0.7)
        assert len([r for r in secondary_low if r['source_type'] == 'llm']) == 1
        
        # With threshold 0.6
        _, secondary_high = filter_by_detector_cohort(data, threshold=0.6)
        assert len([r for r in secondary_high if r['source_type'] == 'llm']) == 2


class TestRunSensitivityTests:
    """Tests for running statistical tests on cohorts."""
    
    def test_returns_both_cohort_results(self):
        """Test that results contain both primary and secondary cohort analyses."""
        primary_cohort = [
            {'source_type': 'llm', 'comment_count': 10, 'time_to_merge_minutes': 120, 'review_cycles': 2},
            {'source_type': 'human', 'comment_count': 5, 'time_to_merge_minutes': 60, 'review_cycles': 1},
        ]
        secondary_cohort = [
            {'source_type': 'llm', 'comment_count': 12, 'time_to_merge_minutes': 140, 'review_cycles': 3},
            {'source_type': 'human', 'comment_count': 5, 'time_to_merge_minutes': 60, 'review_cycles': 1},
        ]
        
        results = run_sensitivity_tests(primary_cohort, secondary_cohort, metrics=['comment_count'])
        
        assert 'primary_cohort' in results
        assert 'secondary_cohort' in results
        assert 'comparison' in results
        assert 'comment_count' in results['comparison']
    
    def test_comparison_interpretation(self):
        """Test that comparison correctly identifies significance preservation."""
        # Mock data where significance is preserved
        primary_cohort = [
            {'source_type': 'llm', 'comment_count': 15, 'time_to_merge_minutes': 200, 'review_cycles': 3},
            {'source_type': 'human', 'comment_count': 5, 'time_to_merge_minutes': 50, 'review_cycles': 1},
            {'source_type': 'llm', 'comment_count': 12, 'time_to_merge_minutes': 180, 'review_cycles': 2},
            {'source_type': 'human', 'comment_count': 8, 'time_to_merge_minutes': 70, 'review_cycles': 1},
        ]
        secondary_cohort = [
            {'source_type': 'llm', 'comment_count': 18, 'time_to_merge_minutes': 220, 'review_cycles': 4},
            {'source_type': 'human', 'comment_count': 5, 'time_to_merge_minutes': 50, 'review_cycles': 1},
            {'source_type': 'llm', 'comment_count': 14, 'time_to_merge_minutes': 190, 'review_cycles': 3},
            {'source_type': 'human', 'comment_count': 8, 'time_to_merge_minutes': 70, 'review_cycles': 1},
        ]
        
        results = run_sensitivity_tests(primary_cohort, secondary_cohort, metrics=['comment_count'])
        
        # Check that comparison structure is correct
        comparison = results['comparison']['comment_count']
        assert 'primary_p_value' in comparison
        assert 'secondary_p_value' in comparison
        assert 'significance_preserved' in comparison
        assert 'interpretation' in comparison


class TestSaveSensitivityResults:
    """Tests for saving sensitivity analysis results."""
    
    def test_saves_json_file(self, tmp_path):
        """Test that results are saved as valid JSON."""
        results = {
            'primary_cohort': {'comment_count': {'p_value': 0.03}},
            'secondary_cohort': {'comment_count': {'p_value': 0.04}},
            'comparison': {'comment_count': {'significance_preserved': True}},
            'metadata': {'detector_threshold': 0.7}
        }
        
        output_path = tmp_path / "results.json"
        save_sensitivity_results(results, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == results
    
    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        results = {'test': 'data'}
        output_path = tmp_path / "subdir" / "nested" / "results.json"
        
        save_sensitivity_results(results, output_path)
        
        assert output_path.exists()


class TestRunSensitivityAnalysis:
    """Integration tests for the full sensitivity analysis pipeline."""
    
    def test_full_pipeline_with_mock_data(self, tmp_path):
        """Test the complete pipeline with mock data files."""
        # Create mock data files
        metrics_file = tmp_path / "metrics.csv"
        metrics_file.write_text(
            "pr_id,comment_count,time_to_merge_minutes,review_cycles,complexity_score\n"
            "1,10,120,2,5.5\n"
            "2,5,60,1,3.2\n"
            "3,15,180,3,7.8\n"
            "4,8,90,2,4.1\n"
            "5,12,150,2,6.0\n"
        )
        
        labeled_file = tmp_path / "labeled.csv"
        labeled_file.write_text(
            "pr_id,source_type,confidence_score,flagged,detector_score\n"
            "1,llm,0.85,False,0.72\n"
            "2,human,0.90,False,0.15\n"
            "3,llm,0.78,True,0.81\n"
            "4,human,0.88,False,0.22\n"
            "5,llm,0.82,False,0.75\n"
        )
        
        output_file = tmp_path / "results.json"
        
        # Run analysis
        results = run_sensitivity_analysis(
            metrics_path=metrics_file,
            labeled_path=labeled_file,
            output_path=output_file,
            detector_threshold=0.7
        )
        
        # Verify output file exists
        assert output_file.exists()
        
        # Verify results structure
        assert 'primary_cohort' in results
        assert 'secondary_cohort' in results
        assert 'comparison' in results
        assert 'metadata' in results
        
        # Verify metadata
        assert results['metadata']['detector_threshold'] == 0.7
        assert 'primary_cohort_size' in results['metadata']
        assert 'secondary_cohort_size' in results['metadata']
    
    def test_file_not_found_error(self, tmp_path):
        """Test that FileNotFoundError is raised when input files don't exist."""
        with pytest.raises(FileNotFoundError):
            run_sensitivity_analysis(
                metrics_path=tmp_path / "nonexistent.csv",
                labeled_path=tmp_path / "labeled.csv"
            )
    
    def test_empty_dataset_error(self, tmp_path):
        """Test that ValueError is raised for empty datasets."""
        # Create empty metrics file
        metrics_file = tmp_path / "metrics.csv"
        metrics_file.write_text("pr_id,comment_count,time_to_merge_minutes,review_cycles,complexity_score\n")
        
        labeled_file = tmp_path / "labeled.csv"
        labeled_file.write_text("pr_id,source_type,confidence_score,flagged,detector_score\n")
        
        with pytest.raises(ValueError, match="No data found"):
            run_sensitivity_analysis(
                metrics_path=metrics_file,
                labeled_path=labeled_file,
                output_path=tmp_path / "results.json"
            )


class TestSensitivityAnalysisIntegration:
    """Integration tests verifying FR-008 compliance."""
    
    def test_secondary_detector_cohort_isolation(self, tmp_path):
        """Test that secondary cohort only includes PRs with high detector scores."""
        # Create data with varying detector scores
        metrics_file = tmp_path / "metrics.csv"
        metrics_file.write_text(
            "pr_id,comment_count,time_to_merge_minutes,review_cycles,complexity_score\n"
            "1,10,120,2,5.5\n"
            "2,5,60,1,3.2\n"
            "3,15,180,3,7.8\n"
            "4,8,90,2,4.1\n"
            "5,12,150,2,6.0\n"
            "6,9,100,2,4.5\n"
        )
        
        labeled_file = tmp_path / "labeled.csv"
        labeled_file.write_text(
            "pr_id,source_type,confidence_score,flagged,detector_score\n"
            "1,llm,0.85,False,0.72\n"  # High score
            "2,human,0.90,False,0.15\n"
            "3,llm,0.78,True,0.81\n"  # High score
            "4,human,0.88,False,0.22\n"
            "5,llm,0.82,False,0.75\n"  # High score
            "6,llm,0.65,False,0.45\n"  # Low score - should be excluded from secondary
        )
        
        output_file = tmp_path / "results.json"
        
        results = run_sensitivity_analysis(
            metrics_path=metrics_file,
            labeled_path=labeled_file,
            output_path=output_file,
            detector_threshold=0.7
        )
        
        # Secondary cohort should have 3 LLMs (high scores) + 2 humans = 5 total
        assert results['metadata']['secondary_cohort_size'] == 5
        
        # Primary cohort should have 4 LLMs (all) + 2 humans = 6 total
        assert results['metadata']['primary_cohort_size'] == 6
    
    def test_statistical_robustness_check(self, tmp_path):
        """Test that the analysis correctly identifies when significance is preserved."""
        # Create data where we expect consistent results
        metrics_file = tmp_path / "metrics.csv"
        metrics_file.write_text(
            "pr_id,comment_count,time_to_merge_minutes,review_cycles,complexity_score\n"
            "1,20,250,4,8.0\n"
            "2,5,60,1,3.0\n"
            "3,18,220,3,7.5\n"
            "4,7,80,2,3.5\n"
            "5,22,280,5,9.0\n"
            "6,6,70,1,3.2\n"
        )
        
        labeled_file = tmp_path / "labeled.csv"
        labeled_file.write_text(
            "pr_id,source_type,confidence_score,flagged,detector_score\n"
            "1,llm,0.90,False,0.85\n"
            "2,human,0.92,False,0.12\n"
            "3,llm,0.88,False,0.82\n"
            "4,human,0.91,False,0.18\n"
            "5,llm,0.95,False,0.88\n"
            "6,human,0.89,False,0.15\n"
        )
        
        output_file = tmp_path / "results.json"
        
        results = run_sensitivity_analysis(
            metrics_path=metrics_file,
            labeled_path=labeled_file,
            output_path=output_file,
            detector_threshold=0.8
        )
        
        # Check that comparison results are generated
        assert 'comment_count' in results['comparison']
        comparison = results['comparison']['comment_count']
        
        # Verify comparison structure
        assert 'primary_p_value' in comparison
        assert 'secondary_p_value' in comparison
        assert 'significance_preserved' in comparison
        assert 'interpretation' in comparison