import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.forgetting_metrics import (
    ForgettingResult,
    RetentionMetrics,
    RuleIdentityRecord,
    load_test_instances,
    load_agent_state,
    get_agent_rule_ids,
    evaluate_agent_on_instances,
    calculate_retention_rate,
    compute_forgetting_metrics,
    compute_retention_metrics,
    save_forgetting_metrics,
    save_retention_metrics
)


class TestForgettingMetrics:
    """Unit tests for forgetting metrics calculation."""

    def test_load_test_instances_success(self, temp_data_dir):
        """Test loading test instances from a valid JSON file."""
        test_data = [
            {"id": "test_1", "domain": "logic", "rule_set_id": "rs1", "instance_data": {"problem": "A->B", "solution": "B"}},
            {"id": "test_2", "domain": "grid", "rule_set_id": "rs2", "instance_data": {"problem": "grid_3x3", "solution": "path"}}
        ]
        
        test_file = temp_data_dir / "test_instances.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_test_instances(str(test_file))
        assert len(result) == 2
        assert result[0]['id'] == 'test_1'
        assert result[1]['id'] == 'test_2'

    def test_load_test_instances_not_found(self, temp_data_dir):
        """Test that loading from a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_test_instances(str(temp_data_dir / "nonexistent.json"))

    def test_load_test_instances_invalid_format(self, temp_data_dir):
        """Test that loading a non-list JSON raises ValueError."""
        test_file = temp_data_dir / "invalid.json"
        with open(test_file, 'w') as f:
            json.dump({"not": "a list"}, f)
        
        with pytest.raises(ValueError):
            load_test_instances(str(test_file))

    def test_load_agent_state_success(self, temp_data_dir):
        """Test loading agent state from a valid JSON file."""
        state_data = {
            "population": [
                {"rule_set": [{"rule_id": "rule_1"}, {"rule_id": "rule_2"}]},
                {"rule_set": [{"rule_id": "rule_3"}]}
            ],
            "generation_count": 10
        }
        
        state_file = temp_data_dir / "agent_state.json"
        with open(state_file, 'w') as f:
            json.dump(state_data, f)
        
        result = load_agent_state(str(state_file))
        assert result['generation_count'] == 10
        assert len(result['population']) == 2

    def test_get_agent_rule_ids_from_list_population(self, temp_data_dir):
        """Test extracting rule IDs from a list-based population."""
        state_data = {
            "population": [
                {"rule_set": [{"rule_id": "r1"}, {"rule_id": "r2"}]},
                {"rule_set": [{"rule_id": "r3"}]}
            ]
        }
        
        state_file = temp_data_dir / "state.json"
        with open(state_file, 'w') as f:
            json.dump(state_data, f)
        
        state = load_agent_state(str(state_file))
        rule_ids = get_agent_rule_ids(state)
        
        assert len(rule_ids) == 3
        assert "r1" in rule_ids
        assert "r2" in rule_ids
        assert "r3" in rule_ids

    def test_get_agent_rule_ids_empty_population(self, temp_data_dir):
        """Test extracting rule IDs from an empty population."""
        state_data = {"population": []}
        
        state_file = temp_data_dir / "state.json"
        with open(state_file, 'w') as f:
            json.dump(state_data, f)
        
        state = load_agent_state(str(state_file))
        rule_ids = get_agent_rule_ids(state)
        
        assert len(rule_ids) == 0

    def test_get_agent_rule_ids_no_population_key(self, temp_data_dir):
        """Test extracting rule IDs when population key is missing."""
        state_data = {"generation_count": 5}
        
        state_file = temp_data_dir / "state.json"
        with open(state_file, 'w') as f:
            json.dump(state_data, f)
        
        state = load_agent_state(str(state_file))
        rule_ids = get_agent_rule_ids(state)
        
        assert len(rule_ids) == 0

    def test_calculate_retention_rate_full(self):
        """Test retention rate calculation with 100% retention."""
        initial = {"r1", "r2", "r3"}
        final = {"r1", "r2", "r3"}
        
        rate = calculate_retention_rate(initial, final)
        assert rate == 1.0

    def test_calculate_retention_rate_partial(self):
        """Test retention rate calculation with partial retention."""
        initial = {"r1", "r2", "r3", "r4"}
        final = {"r1", "r2"}
        
        rate = calculate_retention_rate(initial, final)
        assert rate == 0.5

    def test_calculate_retention_rate_zero(self):
        """Test retention rate calculation with 0% retention."""
        initial = {"r1", "r2"}
        final = {"r3", "r4"}
        
        rate = calculate_retention_rate(initial, final)
        assert rate == 0.0

    def test_calculate_retention_rate_empty_initial(self):
        """Test retention rate calculation with empty initial set."""
        initial = set()
        final = {"r1", "r2"}
        
        rate = calculate_retention_rate(initial, final)
        assert rate == 0.0

    def test_compute_forgetting_metrics(self, temp_data_dir):
        """Test computing forgetting metrics."""
        # Create initial metrics
        initial_data = {"accuracy": 0.9, "metrics": {"accuracy": 0.9}}
        initial_file = temp_data_dir / "initial.json"
        with open(initial_file, 'w') as f:
            json.dump(initial_data, f)
        
        # Create final metrics
        final_data = {"accuracy": 0.7, "metrics": {"accuracy": 0.7}}
        final_file = temp_data_dir / "final.json"
        with open(final_file, 'w') as f:
            json.dump(final_data, f)
        
        result = compute_forgetting_metrics(
            run_id="test_run",
            condition="sequential",
            initial_metrics_path=str(initial_file),
            final_metrics_path=str(final_file)
        )
        
        assert result.run_id == "test_run"
        assert result.condition == "sequential"
        assert result.initial_accuracy == 0.9
        assert result.final_accuracy == 0.7
        # Forgetting rate = (0.9 - 0.7) / 0.9 = 0.222...
        assert abs(result.forgetting_rate - 0.2222222222222222) < 1e-6

    def test_compute_forgetting_metrics_zero_initial(self, temp_data_dir):
        """Test computing forgetting metrics when initial accuracy is zero."""
        initial_data = {"accuracy": 0.0}
        initial_file = temp_data_dir / "initial.json"
        with open(initial_file, 'w') as f:
            json.dump(initial_data, f)
        
        final_data = {"accuracy": 0.0}
        final_file = temp_data_dir / "final.json"
        with open(final_file, 'w') as f:
            json.dump(final_data, f)
        
        result = compute_forgetting_metrics(
            run_id="test_run",
            condition="mixed",
            initial_metrics_path=str(initial_file),
            final_metrics_path=str(final_file)
        )
        
        assert result.forgetting_rate == 0.0

    def test_compute_forgetting_metrics_file_not_found(self, temp_data_dir):
        """Test that missing initial metrics file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compute_forgetting_metrics(
                run_id="test_run",
                condition="sequential",
                initial_metrics_path=str(temp_data_dir / "missing.json"),
                final_metrics_path=str(temp_data_dir / "final.json")
            )

    def test_compute_retention_metrics(self, temp_data_dir):
        """Test computing retention metrics."""
        # Create initial state
        initial_state = {
            "population": [
                {"rule_set": [{"rule_id": "r1"}, {"rule_id": "r2"}, {"rule_id": "r3"}]}
            ]
        }
        initial_file = temp_data_dir / "initial_state.json"
        with open(initial_file, 'w') as f:
            json.dump(initial_state, f)
        
        # Create final state
        final_state = {
            "population": [
                {"rule_set": [{"rule_id": "r1"}, {"rule_id": "r2"}]}
            ]
        }
        final_file = temp_data_dir / "final_state.json"
        with open(final_file, 'w') as f:
            json.dump(final_state, f)
        
        result = compute_retention_metrics(
            run_id="test_run",
            condition="coevolving",
            initial_state_path=str(initial_file),
            final_state_path=str(final_file)
        )
        
        assert result.run_id == "test_run"
        assert result.retention_rate == 2/3  # 2 out of 3 retained
        assert len(result.rule_identity_record['retained_rule_ids']) == 2
        assert len(result.rule_identity_record['lost_rule_ids']) == 1

    def test_save_forgetting_metrics(self, temp_data_dir):
        """Test saving forgetting metrics to JSON."""
        results = [
            ForgettingResult(
                run_id="run_1",
                condition="sequential",
                initial_accuracy=0.9,
                final_accuracy=0.7,
                forgetting_rate=0.222,
                initial_metrics_source="initial.json",
                final_metrics_source="final.json"
            )
        ]
        
        output_file = temp_data_dir / "output.json"
        save_forgetting_metrics(results, str(output_file))
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['run_id'] == "run_1"
        assert data[0]['forgetting_rate'] == 0.222

    def test_save_retention_metrics(self, temp_data_dir):
        """Test saving retention metrics to JSON."""
        results = [
            RetentionMetrics(
                run_id="run_1",
                condition="mixed",
                rule_identity_record={
                    "initial_rule_ids": ["r1", "r2"],
                    "final_rule_ids": ["r1"],
                    "retained_rule_ids": ["r1"],
                    "lost_rule_ids": ["r2"],
                    "retention_rate": 0.5
                },
                retention_rate=0.5,
                initial_state_source="initial.json",
                final_state_source="final.json"
            )
        ]
        
        output_file = temp_data_dir / "output.json"
        save_retention_metrics(results, str(output_file))
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['run_id'] == "run_1"
        assert data[0]['retention_rate'] == 0.5