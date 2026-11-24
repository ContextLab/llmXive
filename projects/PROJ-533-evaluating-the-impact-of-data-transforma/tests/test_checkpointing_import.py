import pytest
from code.utils.checkpointing import save_state, load_state, delete_checkpoint

def test_checkpointing_functions_exist():
    # Simple sanity check that the functions can be imported and called without error.
    state = {"step": "test", "value": 42}
    run_id = "test_run"

    # Save state
    save_state(run_id, state)

    # Load state and verify contents
    loaded = load_state(run_id)
    assert loaded == state

    # Delete checkpoint and ensure it is gone
    delete_checkpoint(run_id)
    assert load_state(run_id) is None