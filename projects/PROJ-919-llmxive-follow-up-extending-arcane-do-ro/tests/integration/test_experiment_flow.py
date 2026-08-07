"""
Integration test for full experiment flow (T023).

This test verifies the end-to-end flow of the ArcANE experiment pipeline:
1. Load existing axes from data/derived/axes.jsonl
2. Load existing probes from data/derived/probes.jsonl
3. Run the experiment runner to generate responses and scores
4. Validate that results are written to data/derived/results.jsonl
5. Validate that statistical analysis is performed and results written
6. Validate that timing information is captured

This test assumes:
- T013 (axes.jsonl) is complete with valid data
- T020 (probes.jsonl) is complete with valid data
- T024-T033 are implemented (experiment runner, judge service, stats engine)
"""
import json
import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any
import pytest

# Import from project modules
from src.services.axes_writer import read_axes_from_jsonl
from src.services.probes_writer import read_probes_from_jsonl
from src.services.experiment_runner import run_experiment
from src.analysis.stats_engine import aggregate_consistency_scores, validate_against_gold_standard, run_statistical_test
from src.lib.state_tracker import generate_run_id, log_experiment_state
from src.lib.utils import setup_logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test fixtures
@pytest.fixture
def sample_axes() -> List[Dict[str, Any]]:
    """Sample axes data for integration testing."""
    return [
        {
            "character": "test_char_1",
            "coarse": {
                "axis_name": "moral_compass",
                "description": "Tendency toward altruistic vs self-serving behavior",
                "scale": ["self-serving", "altruistic"]
            },
            "fine": {
                "axis_name": "risk_tolerance",
                "description": "Willingness to take calculated risks",
                "scale": ["cautious", "bold"],
                "source_text": "In chapter 3, the character hesitated before crossing the bridge..."
            },
            "validation": {
                "lexical_overlap": 0.2,
                "semantic_distance": 0.4,
                "passed": True
            }
        }
    ]

@pytest.fixture
def sample_probes() -> List[Dict[str, Any]]:
    """Sample probe data for integration testing."""
    return [
        {
            "character": "test_char_1",
            "probe_id": "probe_001",
            "scenario": "You are an alien observer studying a species that has never encountered technology. Describe how you would explain the concept of 'trust' to them.",
            "phase": "coarse",
            "axis_reference": "moral_compass",
            "semantic_distance": 0.85
        },
        {
            "character": "test_char_1",
            "probe_id": "probe_002",
            "scenario": "A civilization has just discovered fire. As an external observer, predict their societal evolution over the next millennium.",
            "phase": "fine",
            "axis_reference": "risk_tolerance",
            "semantic_distance": 0.78
        }
    ]

@pytest.fixture
def temp_data_dir(sample_axes: List[Dict], sample_probes: List[Dict]) -> Path:
    """Create temporary data directory with sample axes and probes."""
    temp_dir = Path(tempfile.mkdtemp())
    derived_dir = temp_dir / "data" / "derived"
    derived_dir.mkdir(parents=True)
    
    # Write sample axes
    axes_file = derived_dir / "axes.jsonl"
    with open(axes_file, 'w', encoding='utf-8') as f:
        for axis in sample_axes:
            f.write(json.dumps(axis) + '\n')
    
    # Write sample probes
    probes_file = derived_dir / "probes.jsonl"
    with open(probes_file, 'w', encoding='utf-8') as f:
        for probe in sample_probes:
            f.write(json.dumps(probe) + '\n')
    
    # Create gold standard directory
    gold_dir = temp_dir / "data" / "gold_standard"
    gold_dir.mkdir(parents=True)
    gold_file = gold_dir / "human_annotations.json"
    with open(gold_file, 'w', encoding='utf-8') as f:
        json.dump([
            {
                "character": "test_char_1",
                "scenario": "test_scenario",
                "ground_truth_score": 0.8,
                "ground_truth_phase": "coarse"
            }
        ], f)
    
    return temp_dir

@pytest.fixture
def mock_models():
    """Mock model loading to avoid actual model downloads."""
    with patch('src.services.experiment_runner.load_model') as mock_load, \
         patch('src.services.judge_service.load_model') as mock_judge_load, \
         patch('src.services.experiment_runner.generate_response') as mock_generate, \
         patch('src.services.judge_service.evaluate_response') as mock_evaluate:
        
        # Mock model loading
        mock_model = MagicMock()
        mock_load.return_value = mock_model
        mock_judge_load.return_value = mock_model
        
        # Mock response generation
        mock_generate.side_effect = [
            "This is a test response demonstrating consistent behavior aligned with the character's moral compass.",
            "This is another test response showing risk-averse behavior in a novel situation."
        ]
        
        # Mock judge evaluation
        mock_evaluate.return_value = {
            "score": 0.75,
            "adherence_flag": True,
            "reasoning": "Response aligns well with expected character behavior."
        }
        
        yield mock_load, mock_judge_load, mock_generate, mock_evaluate

def test_full_experiment_flow(temp_data_dir: Path, mock_models, sample_axes: List[Dict], sample_probes: List[Dict]):
    """
    Integration test for the full experiment flow.
    
    Verifies:
    1. Axes and probes are loaded correctly
    2. Experiment runner processes probes and generates responses
    3. Judge service evaluates responses and computes scores
    4. Results are written to results.jsonl
    5. Statistical analysis is performed
    6. Timing information is captured
    """
    # Setup logging
    setup_logging(level=logging.INFO)
    
    # Generate run ID
    run_id = generate_run_id()
    logger.info(f"Starting integration test with run_id: {run_id}")
    
    # Log experiment state
    log_experiment_state(
        run_id=run_id,
        parameters={"axes_file": "axes.jsonl", "probes_file": "probes.jsonl"},
        status="started"
    )
    
    # Load axes and probes
    axes_path = temp_data_dir / "data" / "derived" / "axes.jsonl"
    probes_path = temp_data_dir / "data" / "derived" / "probes.jsonl"
    
    axes = read_axes_from_jsonl(axes_path)
    probes = read_probes_from_jsonl(probes_path)
    
    assert len(axes) == 1, f"Expected 1 axis, got {len(axes)}"
    assert len(probes) == 2, f"Expected 2 probes, got {len(probes)}"
    logger.info(f"Loaded {len(axes)} axes and {len(probes)} probes")
    
    # Run experiment
    results_path = temp_data_dir / "data" / "derived" / "results.jsonl"
    stats_path = temp_data_dir / "data" / "derived" / "stats_results.json"
    timing_path = temp_data_dir / "data" / "derived" / "timing.log"
    
    experiment_results = run_experiment(
        axes=axes,
        probes=probes,
        results_path=str(results_path),
        run_id=run_id
    )
    
    # Verify results were written
    assert results_path.exists(), "Results file was not created"
    
    with open(results_path, 'r', encoding='utf-8') as f:
        results = [json.loads(line) for line in f if line.strip()]
    
    assert len(results) >= 2, f"Expected at least 2 results, got {len(results)}"
    logger.info(f"Generated {len(results)} experiment results")
    
    # Validate result structure
    for result in results:
        assert "character" in result, "Result missing 'character' field"
        assert "probe_id" in result, "Result missing 'probe_id' field"
        assert "response" in result, "Result missing 'response' field"
        assert "score" in result, "Result missing 'score' field"
        assert "phase" in result, "Result missing 'phase' field"
        assert "adherence_flag" in result, "Result missing 'adherence_flag' field"
    
    # Aggregate consistency scores
    stats_results = aggregate_consistency_scores(results, str(stats_path))
    assert stats_results is not None, "Statistical analysis failed"
    
    # Validate against gold standard
    gold_path = temp_data_dir / "data" / "gold_standard" / "human_annotations.json"
    gold_data = json.load(open(gold_path, 'r', encoding='utf-8'))
    
    validation_result = validate_against_gold_standard(results, gold_data)
    assert validation_result is not None, "Gold standard validation failed"
    assert "correlation" in validation_result, "Validation missing correlation metric"
    
    # Run statistical test
    test_result = run_statistical_test(results, stats_path)
    assert test_result is not None, "Statistical test execution failed"
    assert "p_value" in test_result, "Test result missing p-value"
    assert "test_type" in test_result, "Test result missing test type"
    
    # Verify timing log was created
    assert timing_path.exists(), "Timing log was not created"
    with open(timing_path, 'r', encoding='utf-8') as f:
        timing_content = f.read()
    assert "total_time" in timing_content, "Timing log missing total_time"
    
    # Update experiment state
    log_experiment_state(
        run_id=run_id,
        parameters={"axes_file": "axes.jsonl", "probes_file": "probes.jsonl"},
        status="completed"
    )
    
    logger.info(f"Integration test completed successfully with run_id: {run_id}")

def test_experiment_flow_with_insufficient_probes(temp_data_dir: Path, mock_models):
    """
    Test that the experiment flow handles cases with fewer than 50 probes gracefully.
    """
    # Load existing data
    axes_path = temp_data_dir / "data" / "derived" / "axes.jsonl"
    probes_path = temp_data_dir / "data" / "derived" / "probes.jsonl"
    
    axes = read_axes_from_jsonl(axes_path)
    probes = read_probes_from_jsonl(probes_path)
    
    # Run experiment with only 2 probes
    results_path = temp_data_dir / "data" / "derived" / "results_test2.jsonl"
    run_id = generate_run_id()
    
    experiment_results = run_experiment(
        axes=axes,
        probes=probes,
        results_path=str(results_path),
        run_id=run_id
    )
    
    # Verify results were written
    assert results_path.exists(), "Results file was not created"
    
    with open(results_path, 'r', encoding='utf-8') as f:
        results = [json.loads(line) for line in f if line.strip()]
    
    assert len(results) == 2, f"Expected 2 results for 2 probes, got {len(results)}"
    
    logger.info("Test with insufficient probes passed")

def test_experiment_flow_error_handling(temp_data_dir: Path):
    """
    Test that the experiment flow handles errors gracefully and logs them.
    """
    # Setup logging
    setup_logging(level=logging.INFO)
    
    # Load axes
    axes_path = temp_data_dir / "data" / "derived" / "axes.jsonl"
    axes = read_axes_from_jsonl(axes_path)
    
    # Create empty probes file to test error handling
    probes_path = temp_data_dir / "data" / "derived" / "empty_probes.jsonl"
    with open(probes_path, 'w', encoding='utf-8') as f:
        pass  # Empty file
    
    probes = read_probes_from_jsonl(probes_path)
    
    assert len(probes) == 0, "Expected 0 probes from empty file"
    
    # Run experiment with no probes
    results_path = temp_data_dir / "data" / "derived" / "results_empty.jsonl"
    run_id = generate_run_id()
    
    # This should handle the empty probes case gracefully
    experiment_results = run_experiment(
        axes=axes,
        probes=probes,
        results_path=str(results_path),
        run_id=run_id
    )
    
    # Verify empty results file was created
    assert results_path.exists(), "Results file was not created"
    
    logger.info("Error handling test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])