import pytest
import time
from src.utils.timeout_wrapper import set_global_timeout, check_timeout

def test_timeout_triggers_exit(tmp_path, monkeypatch):
    """
    Verify that check_timeout exits with code 143 when the deadline is passed.
    """
    # Mock the logs directory to avoid polluting project logs
    monkeypatch.setattr("src.utils.timeout_wrapper.Path", lambda *args: tmp_path)
    
    # Set a timeout in the past
    set_global_timeout(-1.0) 
    
    with pytest.raises(SystemExit) as e:
        check_timeout()
    
    assert e.value.code == 143

def test_timeout_does_not_trigger_within_limit():
    """
    Verify that check_timeout does not exit if the deadline is in the future.
    """
    # Set a long timeout
    set_global_timeout(100.0)
    
    # Should not raise SystemExit
    check_timeout()
