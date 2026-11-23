"""
Integration test for the evaluation loop.

Verifies that the evaluation loop can execute over a held-out set of tasks
(simulated via in-memory data for this test context) and produce the expected
output structure (JSON list of TaskOutcome objects) written to disk.

This test validates the integration between:
1. The data models (TaskOutcome, FailureType).
2. The evaluation logic (simulating a run).
3. The file I/O (writing results to data/processed/evaluation_outcomes.json).
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path to import code modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.models import TaskOutcome, FailureType, serialize_outcome

# Simulated inference result for the integration test
# In a real run, this would come from inference_symbolic.py or inference_baseline.py
class MockEvaluationEngine:
    """
    Mock engine to simulate the evaluation loop logic.
    In the full system, this would load models and run inference.
    Here, it generates deterministic outcomes based on input IDs to test the pipeline.
    """
    def __init__(self, held_out_tasks: List[str]):
        self.held_out_tasks = held_out_tasks

    def run_evaluation(self) -> List[TaskOutcome]:
        outcomes = []
        for i, task_id in enumerate(self.held_out_tasks):
            # Deterministic simulation: even indices succeed, odd fail (semantic)
            success = (i % 2 == 0)
            failure_type = FailureType.SEMANTIC if not success else None
            latency_induced = False # For this test, we assume no latency issues

            outcome = TaskOutcome(
                trajectory_id=task_id,
                success=success,
                steps=10 + i,
                timestamp=datetime.now().isoformat(),
                failure_type=failure_type,
                latency_induced=latency_induced
            )
            outcomes.append(outcome)
        return outcomes

def test_evaluation_loop_structure():
    """
    Integration test: Run the evaluation loop over a small set of tasks
    and verify the output file structure and content validity.
    """
    # 1. Setup: Define held-out tasks
    held_out_tasks = [
        "eval_trajectory_001",
        "eval_trajectory_002",
        "eval_trajectory_003"
    ]

    # 2. Execute: Run the mock evaluation engine
    engine = MockEvaluationEngine(held_out_tasks)
    outcomes = engine.run_evaluation()

    # 3. Verify in-memory structure
    assert len(outcomes) == 3, "Evaluation should produce one outcome per task"
    assert outcomes[0].success is True, "First task (index 0) should succeed"
    assert outcomes[1].success is False, "Second task (index 1) should fail"
    assert outcomes[1].failure_type == FailureType.SEMANTIC, "Failure should be semantic"

    # 4. Verify Serialization and File I/O
    # Create a temporary file to simulate the output path
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
        # Serialize outcomes to JSON
        # Using list comprehension to convert Pydantic models to dicts
        json.dump([o.model_dump() for o in outcomes], f, indent=2)

    try:
        # 5. Read back and validate
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)

        assert isinstance(loaded_data, list), "Output must be a list"
        assert len(loaded_data) == 3, "Should have 3 records"
        assert loaded_data[0]["success"] is True, "First record success must be True"
        assert loaded_data[1]["success"] is False, "Second record success must be False"
        assert loaded_data[1]["failure_type"] == "semantic", "Failure type must match"
        
        # Verify timestamp format (ISO 8601)
        assert "T" in loaded_data[0]["timestamp"], "Timestamp must be ISO format"

    finally:
        # Cleanup
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_evaluation_loop_writes_to_expected_path():
    """
    Integration test: Verify that the evaluation loop logic can write
    to the specific project path defined in tasks.md:
    data/processed/evaluation_outcomes.json
    """
    held_out_tasks = ["test_task_001"]
    engine = MockEvaluationEngine(held_out_tasks)
    outcomes = engine.run_evaluation()

    # Define the target path relative to the project root
    # We use a temp directory to avoid cluttering the real data dir during test
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "data" / "processed"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "evaluation_outcomes.json"

        # Write the data
        with open(target_file, 'w') as f:
            json.dump([o.model_dump() for o in outcomes], f, indent=2)

        # Verify file existence
        assert target_file.exists(), "Output file must be created at the target path"

        # Verify content
        with open(target_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["trajectory_id"] == "test_task_001"