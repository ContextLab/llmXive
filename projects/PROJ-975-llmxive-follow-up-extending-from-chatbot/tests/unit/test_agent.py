import pytest
import logging
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the agent module functions/classes
from code.agent import SkillLibrary, calculate_retrieval_precision, run_task, append_to_log
from code.utils import get_embedding
from code.logging_config import get_logger

class TestRetrievalFailureHandling:
    """
    Unit tests for T019: Verify retrieval failure handling (missing skill)
    logs specific error and does not hallucinate.
    """

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up temporary directories and mock logger for each test."""
        self.tmp_dir = tmp_path
        self.log_file = self.tmp_dir / "test_experiment_log.csv"
        self.raw_dir = self.tmp_dir / "data" / "raw"
        self.raw_dir.mkdir(parents=True)
        
        # Create a temporary skills.json with a known skill
        self.skills_data = [
            {
                "id": "skill_001",
                "name": "add_numbers",
                "description": "Adds two numbers together",
                "code": "def add_numbers(a, b): return a + b",
                "embedding": [0.1] * 384  # Mock embedding
            }
        ]
        self.skills_file = self.raw_dir / "skills.json"
        with open(self.skills_file, 'w') as f:
            json.dump(self.skills_data, f)

        # Configure a test logger that writes to our temp file
        self.logger = get_logger("test_agent")
        self.logger.handlers = []
        # Use a FileHandler to capture logs
        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.ERROR)

        yield

        # Cleanup handled by tmp_path fixture

    def test_missing_skill_logs_specific_error(self):
        """
        Verify that when a task requires a skill that is not in the library,
        the agent logs a specific error message and does not proceed.
        """
        # Create a SkillLibrary with only skill_001
        lib = SkillLibrary(self.skills_file)
        
        # Simulate a task that requires a missing skill
        task = {
            "id": "task_999",
            "description": "This task needs a missing skill",
            "ground_truth": ["skill_999"],  # This skill does not exist
            "parameters": {}
        }

        # We need to mock the embedding retrieval to return a dummy vector
        # so we can test the retrieval logic without heavy computation
        dummy_embedding = [0.0] * 384

        with patch('code.agent.get_embedding', return_value=dummy_embedding):
            # Run the task
            result = run_task(task, lib, self.logger)

        # Verify the result indicates failure
        assert result['success'] is False
        assert 'missing' in result['error'].lower() or 'not found' in result['error'].lower()

        # Verify the specific error was logged
        log_content = self.log_file.read_text()
        assert "skill_999" in log_content
        assert "missing" in log_content.lower() or "not found" in log_content.lower()

    def test_no_hallucination_on_missing_skill(self):
        """
        Verify that the agent does NOT hallucinate (invent) a solution
        when a required skill is missing. It must fail explicitly.
        """
        lib = SkillLibrary(self.skills_file)
        
        task = {
            "id": "task_998",
            "description": "Task requiring missing skill",
            "ground_truth": ["skill_missing_123"],
            "parameters": {}
        }

        dummy_embedding = [0.0] * 384

        with patch('code.agent.get_embedding', return_value=dummy_embedding):
            result = run_task(task, lib, self.logger)

        # Assert failure
        assert result['success'] is False
        
        # Assert the error message is explicit about the missing skill
        # and does not claim success or a fake solution
        assert result['error'] is not None
        assert "hallucinate" not in result.get('error', '').lower()
        assert "skill_missing_123" in result['error']

    def test_retrieval_precision_zero_on_missing_ground_truth(self):
        """
        Verify that retrieval precision is calculated as 0.0 when
        the retrieved set does not overlap with the missing ground truth.
        """
        lib = SkillLibrary(self.skills_file)
        task = {
            "id": "task_997",
            "description": "Task with missing ground truth",
            "ground_truth": ["skill_nonexistent"],
            "parameters": {}
        }

        # Mock embedding to trigger retrieval
        dummy_embedding = [0.0] * 384

        with patch('code.agent.get_embedding', return_value=dummy_embedding):
            result = run_task(task, lib, self.logger)

        # Precision should be 0.0 because no retrieved skill matches the missing ground truth
        assert result['retrieval_precision'] == 0.0
        assert result['success'] is False

    def test_graceful_failure_with_logging(self):
        """
        Verify that the agent fails gracefully, logs the event, and does not crash.
        """
        lib = SkillLibrary(self.skills_file)
        
        # Multiple missing skills
        task = {
            "id": "task_996",
            "description": "Task with multiple missing skills",
            "ground_truth": ["skill_a", "skill_b", "skill_c"],
            "parameters": {}
        }

        dummy_embedding = [0.0] * 384

        # Ensure no exception is raised
        with patch('code.agent.get_embedding', return_value=dummy_embedding):
            try:
                result = run_task(task, lib, self.logger)
                # If we get here without crashing, the test passes for stability
                assert result is not None
                assert result['success'] is False
            except Exception as e:
                pytest.fail(f"Agent crashed instead of failing gracefully: {e}")

        # Verify log file was written and contains error info
        assert self.log_file.exists()
        log_content = self.log_file.read_text()
        assert "skill_a" in log_content or "skill_b" in log_content or "skill_c" in log_content

class TestEdgeCases:
    """Additional edge case tests for retrieval failure."""

    def test_empty_library_retrieval(self):
        """Test retrieval when the skill library is empty."""
        tmp_dir = tempfile.mkdtemp()
        try:
            empty_skills_path = os.path.join(tmp_dir, "empty_skills.json")
            with open(empty_skills_path, 'w') as f:
                json.dump([], f)
            
            lib = SkillLibrary(empty_skills_path)
            task = {
                "id": "task_empty",
                "description": "Task with empty library",
                "ground_truth": ["any_skill"],
                "parameters": {}
            }

            dummy_embedding = [0.0] * 384
            with patch('code.agent.get_embedding', return_value=dummy_embedding):
                result = run_task(task, lib, logging.getLogger("test_empty"))
            
            assert result['success'] is False
            assert "empty" in result['error'].lower() or "no skills" in result['error'].lower()
        finally:
            shutil.rmtree(tmp_dir)

    def test_partial_ground_truth_missing(self):
        """Test when some ground truth skills exist and others are missing."""
        tmp_dir = tempfile.mkdtemp()
        try:
            # Create a skills file with only one of the required skills
            skills_data = [
                {
                    "id": "skill_exists",
                    "name": "exists",
                    "description": "exists",
                    "code": "pass",
                    "embedding": [0.1] * 384
                }
            ]
            skills_path = os.path.join(tmp_dir, "partial_skills.json")
            with open(skills_path, 'w') as f:
                json.dump(skills_data, f)

            lib = SkillLibrary(skills_path)
            task = {
                "id": "task_partial",
                "description": "Partial ground truth",
                "ground_truth": ["skill_exists", "skill_missing"],
                "parameters": {}
            }

            dummy_embedding = [0.0] * 384
            with patch('code.agent.get_embedding', return_value=dummy_embedding):
                result = run_task(task, lib, logging.getLogger("test_partial"))
            
            # Should fail because not all ground truth skills are available
            assert result['success'] is False
            assert "skill_missing" in result['error']
        finally:
            shutil.rmtree(tmp_dir)