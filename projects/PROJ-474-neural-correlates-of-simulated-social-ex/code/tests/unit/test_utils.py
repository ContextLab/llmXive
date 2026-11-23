import logging
import pytest

from src.utils import log_exception

def test_log_exception_no_args(caplog):
    """Calling with no arguments should not raise and should log something."""
    with caplog.at_level(logging.ERROR):
        log_exception()
    # At least one record should have been emitted
    assert len(caplog.records) >= 1

@pytest.mark.parametrize(
    "callable_args, callable_kwargs",
    [
        (["my_logger"], {}),
        (["my_logger", RuntimeError("boom")], {}),
        ([], {"logger": logging.getLogger("test"), "exc": RuntimeError("boom")}),
        ([], {"exc": RuntimeError("boom")}),
    ],
)
def test_log_exception_various_signatures(callable_args, callable_kwargs, caplog):
    """All documented call signatures must be accepted."""
    with caplog.at_level(logging.ERROR):
        log_exception(*callable_args, **callable_kwargs)
    assert len(caplog.records) >= 1