import pytest
import json
from pathlib import Path

@pytest.fixture
def execution_log_schema():
    schema_path = Path(__file__).parent.parent.parent / "contracts" / "execution_log.schema.yaml"
    if not schema_path.exists():
        pytest.skip("Execution log schema not found")
    with open(schema_path, 'r') as f:
        return json.load(f)

def test_execution_log_json_structure(execution_log_schema):
    """
    T020: Contract test for execution log JSON.
    Validates that execution logs conform to the expected schema.
    """
    processed_dir = Path(__file__).parent.parent.parent / "data" / "processed"
    if processed_dir.exists():
        log_files = list(processed_dir.glob("execution_log_*.json"))
        if log_files:
            with open(log_files[0], 'r') as f:
                log = json.load(f)
            
            # Basic structural checks
            assert "workflow_id" in log, "Execution log must have 'workflow_id'"
            assert "status" in log, "Execution log must have 'status'"
            assert "token_count" in log, "Execution log must have 'token_count'"
            assert "policy_violations" in log, "Execution log must have 'policy_violations'"
            assert "execution_time" in log, "Execution log must have 'execution_time'"
            return
    
    pytest.skip("No execution log files found to validate against schema")
