"""Unit tests for src/utils/config.py (T002)."""

import random

import numpy as np

from src.utils.config import (
    GLOBAL_SEED,
    assert_seeded,
    compute_file_hash,
    get_data_root,
    get_project_root,
    get_last_seed,
    set_seed,
)


def test_set_seed_is_deterministic():
    set_seed(123)
    a = [random.random() for _ in range(5)]
    b = np.random.rand(5)
    set_seed(123)
    c = [random.random() for _ in range(5)]
    d = np.random.rand(5)
    assert a == c
    np.testing.assert_array_equal(b, d)


def test_set_seed_records_state():
    set_seed(42)
    assert get_last_seed() == 42
    assert_seeded()  # must not raise


def test_assert_seeded_fails_loudly(monkeypatch):
    import src.utils.config as cfg

    monkeypatch.setattr(cfg, "_SEED_STATE", {"seed": None})
    try:
        assert_seeded()
    except RuntimeError as e:
        assert "set_seed" in str(e)
    else:
        raise AssertionError("assert_seeded should raise RuntimeError")


def test_set_seed_rejects_bad_type():
    try:
        set_seed("not-an-int")
    except TypeError:
        pass
    else:
        raise AssertionError("set_seed should reject non-int seeds")


def test_default_seed_constant():
    assert isinstance(GLOBAL_SEED, int)


def test_path_and_hash_helpers(tmp_path):
    root = get_project_root()
    assert root.exists()
    assert get_data_root() == root / "data"

    f = tmp_path / "f.txt"
    f.write_bytes(b"hello")
    assert compute_file_hash(str(f)) == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )