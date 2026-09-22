"""
Unit tests to verify config imports work correctly.
"""
def test_config_import():
    """Ensure config module can be imported."""
    import code.config as config
    assert hasattr(config, 'PROJECT_ROOT')
