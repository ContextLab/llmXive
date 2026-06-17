from reproducibility.logs import get_logger

def test_logger_has_debug():
    logger = get_logger()
    assert hasattr(logger, "debug"), "ReproducibilityLogger must implement debug()"
    # Ensure calling debug does not raise
    logger.debug("Test debug message")