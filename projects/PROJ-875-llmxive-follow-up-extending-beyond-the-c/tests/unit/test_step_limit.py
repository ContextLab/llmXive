import pytest
import os
import csv
import tempfile
import shutil
from code.agent_loop import AgentConfig, AgentState, TextAgent

class TestStepLimitLogic:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        path = tempfile.mkdtemp()
        yield path
        shutil.rmtree(path)

    def test_step_limit_enforcement(self, temp_dir):
        """
        Verify that the agent stops exactly when max_steps is reached.
        """
        max_steps = 5
        csv_path = os.path.join(temp_dir, "discarded_runs.csv")
        
        config = AgentConfig(
            max_steps=max_steps,
            timeout_log_path=csv_path
        )
        
        agent = TextAgent(config)
        result = agent.run([], "test_step_limit")
        
        assert result.is_timeout is True, "Agent should be marked as timeout"
        assert result.step_count == max_steps, f"Step count should be exactly {max_steps}, got {result.step_count}"
        assert "step_limit_timeout" in result.error_message or "Hard step limit" in result.error_message

    def test_discarded_runs_csv_creation(self, temp_dir):
        """
        Verify that the discarded_runs.csv is created and contains the timeout entry.
        """
        max_steps = 3
        csv_path = os.path.join(temp_dir, "discarded_runs.csv")
        
        config = AgentConfig(
            max_steps=max_steps,
            timeout_log_path=csv_path
        )
        
        agent = TextAgent(config)
        agent.run([], "test_csv_creation")
        
        assert os.path.exists(csv_path), "discarded_runs.csv must be created"
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1, "CSV should contain exactly one row for the timeout"
        assert rows[0]['run_id'] == "test_csv_creation"
        assert rows[0]['reason'] == 'step_limit_timeout'
        assert int(rows[0]['step_count']) == max_steps

    def test_step_limit_configurability(self, temp_dir):
        """
        Verify that the step limit is configurable and not hardcoded.
        """
        limits = [1, 10, 50]
        
        for limit in limits:
            csv_path = os.path.join(temp_dir, f"discarded_runs_{limit}.csv")
            config = AgentConfig(
                max_steps=limit,
                timeout_log_path=csv_path
            )
            agent = TextAgent(config)
            result = agent.run([], f"test_limit_{limit}")
            
            assert result.step_count == limit, f"Step count should match config {limit}"
            assert result.is_timeout is True