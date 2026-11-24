import pytest

from utils.data_leakage_guard import verify_no_leakage, LeakageError, force_memory_isolation


def test_verify_no_leakage_passes():
    train = ["sub-01", "sub-02", "sub-03"]
    test = ["sub-04", "sub-05"]
    # Should not raise
    verify_no_leakage(train, test)


def test_verify_no_leakage_fails():
    train = ["sub-01", "sub-02"]
    test = ["sub-02", "sub-03"]
    with pytest.raises(LeakageError):
        verify_no_leakage(train, test)


def test_force_memory_isolation_returns_copy():
    original = ["sub-01", "sub-02"]
    copied = force_memory_isolation(original)
    assert copied == set(original)
    # Mutating the original list must not affect the copy
    original.append("sub-03")
    assert "sub-03" not in copied
