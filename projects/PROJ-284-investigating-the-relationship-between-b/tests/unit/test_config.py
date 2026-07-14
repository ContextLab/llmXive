"""
Verify that the config helper returns a dictionary with expected keys.
"""

from code.config import get_config
def test_get_config():
    cfg = get_config()
    assert isinstance(cfg, dict)
    assert "SCHAEFER_ATLAS_URL" in cfg