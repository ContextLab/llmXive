import pytest
from config import get_config, Config

def test_quantization_constants_defined():
    """Verify T009b: QUANTIZATION_MAX and QUANTIZATION_MIN are defined in Config."""
    cfg = get_config()
    
    # Assert attributes exist
    assert hasattr(cfg, 'QUANTIZATION_MIN'), "QUANTIZATION_MIN not found in Config"
    assert hasattr(cfg, 'QUANTIZATION_MAX'), "QUANTIZATION_MAX not found in Config"
    
    # Assert values match Uniform INT8 range [-128, 127]
    assert cfg.QUANTIZATION_MIN == -128, f"Expected QUANTIZATION_MIN=-128, got {cfg.QUANTIZATION_MIN}"
    assert cfg.QUANTIZATION_MAX == 127, f"Expected QUANTIZATION_MAX=127, got {cfg.QUANTIZATION_MAX}"
    
    # Assert they are integers
    assert isinstance(cfg.QUANTIZATION_MIN, int), "QUANTIZATION_MIN must be int"
    assert isinstance(cfg.QUANTIZATION_MAX, int), "QUANTIZATION_MAX must be int"