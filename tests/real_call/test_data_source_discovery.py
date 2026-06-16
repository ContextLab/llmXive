"""Real-call test for autonomous data-source discovery.

Gated by ``LLMXIVE_REAL_TESTS=1`` AND a configured Dartmouth key — it makes
real ``openai.gpt-oss-120b`` calls and pip-installs the discovered package
(``database-knotinfo``) into an EPHEMERAL venv, so it is marked ``slow``.

Acceptance target (proven by the prototype): for the prime-knot-invariants
intent, discovery returns a VerifiedSource whose ``ref`` is the
``database-knotinfo`` PyPI package, with a non-zero record count > 10000 and a
working recipe using ``link_list`` (the correct top-level export). gpt-oss-120b
tends to first guess wrong APIs (``knotinfo``, ``database_knotinfo.csv``); the
introspect-and-fix repair loop must converge to ``link_list``.
"""
from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="LLMXIVE_REAL_TESTS not set",
)


def _have_dartmouth_key() -> bool:
    try:
        from llmxive.credentials import load_dartmouth_key

        return bool(load_dartmouth_key())
    except Exception:
        return False


_KNOT_INTENT = (
    "a dataset of prime knot invariants: crossing number, braid index, "
    "hyperbolic volume, and alternating classification for prime knots up to "
    "~13 crossings (KnotInfo / Knot Atlas census)"
)


@pytest.mark.slow
def test_discover_knotinfo_data_source() -> None:
    if not _have_dartmouth_key():
        pytest.skip("no Dartmouth API key configured")

    from llmxive.librarian.data_source_discovery import (
        VerifiedSource,
        discover_data_source,
    )

    result = discover_data_source(_KNOT_INTENT)

    assert isinstance(result, VerifiedSource), "discovery returned None"
    ref_norm = result.ref.lower().replace("_", "-")
    assert "database-knotinfo" in ref_norm, f"unexpected ref: {result.ref!r}"
    assert result.record_count > 10000, f"record_count={result.record_count}"
    assert "link_list" in result.access_python, (
        f"recipe did not converge to link_list:\n{result.access_python}"
    )
