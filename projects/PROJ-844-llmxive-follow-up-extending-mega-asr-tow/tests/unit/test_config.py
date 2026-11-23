"""
Basic sanity checks for the project configuration.
"""
import pytest
from config import (
    SEED,
    SAMPLE_SIZE,
    SNR_LEVELS,
    RT60_LEVELS,
    CCM_THRESHOLD,
    SSS_ABSOLUTE_THRESHOLD,
    WER_MULTIPLIER,
    FDR,
    R2_TARGET,
    get_config,
)

def test_constants_defined():
    """All required constants must be present and of the expected type."""
    assert isinstance(SEED, int) and SEED == 42
    assert isinstance(SAMPLE_SIZE, int) and SAMPLE_SIZE >= 50000
    assert isinstance(SNR_LEVELS, list) and len(SNR_LEVELS) == 9
    assert isinstance(RT60_LEVELS, list) and len(RT60_LEVELS) == 6
    assert isinstance(CCM_THRESHOLD, float) and CCM_THRESHOLD == 0.5
    assert isinstance(SSS_ABSOLUTE_THRESHOLD, float) and SSS_ABSOLUTE_THRESHOLD == 0.5
    assert isinstance(WER_MULTIPLIER, float) and WER_MULTIPLIER == 2.0
    assert isinstance(FDR, float) and FDR == 0.05
    assert isinstance(R2_TARGET, float) and R2_TARGET == 0.6

def test_get_config_returns_dict():
    cfg = get_config()
    assert isinstance(cfg, dict)
    # The config must contain the top‑level keys we expect
    for key in ("paths", "hyperparameters", "models", "datasets"):
        assert key in cfg
