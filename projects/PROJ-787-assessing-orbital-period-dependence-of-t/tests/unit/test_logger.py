"""
Unit test for the ``code.utils.logger`` helper.

The test verifies that:
1. ``get_logger`` returns a ``logging.Logger`` instance.
2. The logger respects the level defined in the default configuration
   (INFO by default).
3. Handlers are attached exactly once even when ``get_logger`` is called
   multiple times for the same name.
"""
import logging

from code.utils import get_logger, get_config

def test_logger_is_configured_once():
    # Ensure the default config uses INFO level
    cfg = get_config()
    assert cfg.get("logging", {}).get("level", "INFO").upper() == "INFO"

    logger_name = "test_logger"
    logger1 = get_logger(logger_name)
    logger2 = get_logger(logger_name)

    # Same instance should be returned
    assert logger1 is logger2
    assert isinstance(logger1, logging.Logger)

    # Level should be INFO (or whatever the config says)
    assert logger1.level == logging.INFO

    # Handlers should not be duplicated
    handler_ids = {id(h) for h in logger1.handlers}
    assert len(handler_ids) == len(logger1.handlers)