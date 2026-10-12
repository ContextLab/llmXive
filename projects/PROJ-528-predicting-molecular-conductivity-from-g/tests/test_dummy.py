"""
Minimal test to ensure the package imports correctly after the
modifications made for T001–T009.
"""
def test_imports():
    import code.descriptors  # noqa: F401
    import code.feature_importance  # noqa: F401
    import code.model_training  # noqa: F401
    import code.run_sensitivity_analysis  # noqa: F401
    import code.plotting  # noqa: F401
    assert True