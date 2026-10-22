"""Placeholder test verifying the project skeleton is importable."""


def test_skeleton_present():
    from code import config  # noqa: F401

    assert config.SEED == 42
    assert config.NUM_CLUSTERS == 16