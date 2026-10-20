"""
Data Leakage Guard
------------------
Provides two lightweight utilities used by the split‑half validator to
guarantee strict separation between training and test subject sets.

The functions are deliberately simple – they only perform set
operations and raise an exception if a violation is detected.
"""

from typing import Iterable, Set

class LeakageError(RuntimeError):
    """Raised when training and test subject sets overlap."""
    pass


def verify_no_leakage(train_ids: Iterable[str], test_ids: Iterable[str]) -> None:
    """
    Ensure that ``train_ids`` and ``test_ids`` are disjoint.
    Raises ``LeakageError`` if any identifier appears in both sets.
    """
    train_set: Set[str] = set(train_ids)
    test_set: Set[str] = set(test_ids)
    overlap = train_set.intersection(test_set)
    if overlap:
        raise LeakageError(f"Data leakage detected: overlapping subject IDs {overlap}")


def force_memory_isolation(subject_ids: Iterable[str]) -> Set[str]:
    """
    Return a *new* ``set`` containing the supplied identifiers.  This
    helper exists so that callers can explicitly copy their subject
    collections, making accidental shared‑state bugs easier to spot.
    """
    return set(subject_ids)
