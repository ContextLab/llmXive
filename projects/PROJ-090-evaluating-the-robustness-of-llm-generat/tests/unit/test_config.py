import pytest

def test_config_constants():
    """
    Verify that the high‑level configuration constants are defined
    and have sensible types/values.
    """
    import code.config as cfg

    # MODEL_NAME should be a non‑empty string
    assert isinstance(cfg.MODEL_NAME, str) and cfg.MODEL_NAME

    # QUANTIZATION is expected to be one of the supported strings
    assert cfg.QUANTIZATION in ("4bit", "8bit", "none")

    # DEVICE is fixed to cpu for the current CPU‑first pipeline
    assert cfg.DEVICE == "cpu"

    # GEN_TIMEOUT should be a positive integer
    assert isinstance(cfg.GEN_TIMEOUT, int) and cfg.GEN_TIMEOUT > 0

    # SEED should be an integer
    assert isinstance(cfg.SEED, int)