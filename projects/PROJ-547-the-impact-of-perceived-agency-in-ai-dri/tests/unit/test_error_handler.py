import pytest
from unittest.mock import patch, MagicMock

from code.utils.error_handler import PipelineError, handle_error, log_and_exit


def test_handle_error_decorator():
    @handle_error
    def func():
        raise PipelineError("test error")

    with patch("code.utils.error_handler.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        with pytest.raises(SystemExit) as exc:
            func()
        assert exc.value.code == 1
        # Ensure the logger recorded an error containing our message
        mock_logger.error.assert_called_once()
        logged_msg = mock_logger.error.call_args[0][0]
        assert "test error" in logged_msg


def test_log_and_exit():
    with patch("code.utils.error_handler.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        with pytest.raises(SystemExit) as exc:
            log_and_exit("fatal failure", code=2)
        assert exc.value.code == 2
        mock_logger.error.assert_called_once_with("fatal failure")