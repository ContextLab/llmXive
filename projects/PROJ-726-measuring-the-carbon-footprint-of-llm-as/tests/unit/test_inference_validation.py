import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from run_inference import count_loc, run_inference_with_tracking

class TestInferenceValidation:
    """
    Tests for T016: Validation to exclude prompts that failed to generate 
    code or resulted in empty strings.
    """

    def test_count_loc_empty_string(self):
        """Test that empty strings return 0 LOC."""
        assert count_loc("") == 0
        assert count_loc(None) == 0

    def test_count_loc_whitespace_only(self):
        """Test that whitespace-only strings return 0 LOC."""
        assert count_loc("   ") == 0
        assert count_loc("\n\n\n") == 0
        assert count_loc("  \n  \n  ") == 0

    def test_count_loc_valid_code(self):
        """Test LOC counting for valid code."""
        code = "def hello():\n    print('world')"
        assert count_loc(code) == 2

    def test_count_loc_mixed_whitespace(self):
        """Test LOC counting with mixed empty lines."""
        code = "def hello():\n\n    print('world')\n\n"
        assert count_loc(code) == 2

    def test_run_inference_excludes_empty_generation(self):
        """
        Integration test to verify that run_inference_with_tracking
        excludes prompts with empty generation results.
        
        This test mocks the generate_code function to simulate
        a prompt that returns an empty string, ensuring it is
        excluded from the final results.
        """
        import unittest.mock as mock
        from run_inference import generate_code, save_results

        # Create a mock dataset
        mock_prompts = [
            {"prompt_id": "valid_1", "prompt": "Write a function to add two numbers"},
            {"prompt_id": "empty_gen", "prompt": "This will generate empty code"},
            {"prompt_id": "valid_2", "prompt": "Write a loop"}
        ]

        # Mock the generate_code function
        def mock_generate(model, tokenizer, prompt, max_length=128):
            if prompt.startswith("This will generate empty"):
                return ""
            return "print('hello')"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test_results.json"
            
            # Mock model and tokenizer
            mock_model = mock.MagicMock()
            mock_tokenizer = mock.MagicMock()

            with mock.patch('run_inference.generate_code', side_effect=mock_generate):
                with mock.patch('run_inference.EmissionsTracker') as mock_tracker_class:
                    mock_tracker = mock.MagicMock()
                    mock_tracker.stop.return_value = 0.001
                    mock_tracker_class.return_value = mock_tracker
                    
                    run_inference_with_tracking(
                        mock_prompts, 
                        mock_model, 
                        mock_tokenizer, 
                        output_file
                    )

                    # Load results
                    with open(output_file, 'r') as f:
                        results = json.load(f)

                    # Verify that the empty generation prompt is excluded
                    result_ids = [r['prompt_id'] for r in results]
                    
                    assert 'valid_1' in result_ids, "Valid prompt 1 should be included"
                    assert 'valid_2' in result_ids, "Valid prompt 2 should be included"
                    assert 'empty_gen' not in result_ids, "Empty generation prompt should be excluded"
                    
                    # Verify all results have non-empty generated_code and loc_count > 0
                    for result in results:
                        assert result['generated_code'].strip(), \
                            f"Result {result['prompt_id']} has empty generated_code"
                        assert result['loc_count'] > 0, \
                            f"Result {result['prompt_id']} has 0 LOC"

    def test_run_inference_excludes_zero_loc(self):
        """
        Test that prompts generating code with 0 LOC (whitespace only)
        are excluded from results.
        """
        import unittest.mock as mock
        
        mock_prompts = [
            {"prompt_id": "valid_1", "prompt": "Write code"},
            {"prompt_id": "whitespace_gen", "prompt": "Generate whitespace"},
            {"prompt_id": "valid_2", "prompt": "More code"}
        ]

        def mock_generate(model, tokenizer, prompt, max_length=128):
            if prompt.startswith("Generate whitespace"):
                return "   \n  \n   "
            return "def x(): pass"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test_results.json"
            mock_model = mock.MagicMock()
            mock_tokenizer = mock.MagicMock()

            with mock.patch('run_inference.generate_code', side_effect=mock_generate):
                with mock.patch('run_inference.EmissionsTracker') as mock_tracker_class:
                    mock_tracker = mock.MagicMock()
                    mock_tracker.stop.return_value = 0.001
                    mock_tracker_class.return_value = mock_tracker
                    
                    run_inference_with_tracking(
                        mock_prompts, 
                        mock_model, 
                        mock_tokenizer, 
                        output_file
                    )

                    with open(output_file, 'r') as f:
                        results = json.load(f)

                    result_ids = [r['prompt_id'] for r in results]
                    
                    assert 'valid_1' in result_ids
                    assert 'valid_2' in result_ids
                    assert 'whitespace_gen' not in result_ids, \
                        "Whitespace-only generation should be excluded (0 LOC)"