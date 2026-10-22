"""
Minimal test to confirm that the project skeleton imports correctly.
"""
def test_import_config():
    import code.config
    # The config module defines a global SEED constant
    assert hasattr(code.config, "SEED") and isinstance(code.config.SEED, int)