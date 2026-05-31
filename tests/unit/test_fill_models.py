"""T003 — unit tests for fill/models.py (FetchedSource, FillProvenance, FillResult)."""

from __future__ import annotations

import pytest

from llmxive.fill.models import FetchedSource, FillProvenance, FillResult

# ---------------------------------------------------------------------------
# FetchedSource
# ---------------------------------------------------------------------------


class TestFetchedSource:
    def _make(self, **overrides) -> FetchedSource:
        defaults = dict(
            channel="oeis",
            source_id="A002863",
            url="https://oeis.org/A002863",
            title="Prime knots",
            text="13 9988\n14 46972",
            authority=0,
        )
        defaults.update(overrides)
        return FetchedSource(**defaults)

    def test_construction_happy_path(self):
        src = self._make()
        assert src.channel == "oeis"
        assert src.source_id == "A002863"
        assert src.url == "https://oeis.org/A002863"
        assert src.title == "Prime knots"
        assert "9988" in src.text
        assert src.authority == 0

    def test_title_may_be_none(self):
        src = self._make(title=None)
        assert src.title is None

    def test_empty_text_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            self._make(text="")

    def test_frozen(self):
        src = self._make()
        with pytest.raises((AttributeError, TypeError)):
            src.channel = "wikipedia"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# FillProvenance
# ---------------------------------------------------------------------------


class TestFillProvenance:
    def _make(self, **overrides) -> FillProvenance:
        defaults = dict(
            value="9988",
            source_id="A002863",
            url="https://oeis.org/A002863",
            quote="13 9988",
            channel="oeis",
            conflicts=[],
        )
        defaults.update(overrides)
        return FillProvenance(**defaults)

    def test_construction_happy_path(self):
        prov = self._make()
        assert prov.value == "9988"
        assert prov.channel == "oeis"
        assert prov.conflicts == []

    def test_conflicts_list(self):
        conflict = {"value": "9999", "source_id": "wiki", "url": "https://en.wikipedia.org", "channel": "wikipedia"}
        prov = self._make(conflicts=[conflict])
        assert len(prov.conflicts) == 1
        assert prov.conflicts[0]["value"] == "9999"

    def test_to_dict(self):
        prov = self._make()
        d = prov.to_dict()
        assert d["value"] == "9988"
        assert d["channel"] == "oeis"
        assert d["conflicts"] == []

    def test_frozen(self):
        prov = self._make()
        with pytest.raises((AttributeError, TypeError)):
            prov.value = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# FillResult
# ---------------------------------------------------------------------------


class TestFillResult:
    def _make_provenance(self) -> FillProvenance:
        return FillProvenance(
            value="9988",
            source_id="A002863",
            url="https://oeis.org/A002863",
            quote="13 9988",
            channel="oeis",
            conflicts=[],
        )

    def test_filled_status(self):
        prov = self._make_provenance()
        r = FillResult.filled("9988", prov, ["oeis"])
        assert r.status == "filled"
        assert r.value == "9988"
        assert r.provenance is prov
        assert r.channels_tried == ["oeis"]
        assert r.reason == ""

    def test_blocked_status(self):
        r = FillResult.blocked("no source found", ["oeis", "wikipedia"])
        assert r.status == "blocked"
        assert r.value is None
        assert r.provenance is None
        assert r.channels_tried == ["oeis", "wikipedia"]
        assert r.reason == "no source found"

    def test_status_must_be_valid(self):
        prov = self._make_provenance()
        with pytest.raises(ValueError, match="'filled' or 'blocked'"):
            FillResult(
                status="unknown",
                value="9988",
                provenance=prov,
                channels_tried=[],
                reason="",
            )

    def test_filled_requires_value(self):
        prov = self._make_provenance()
        with pytest.raises(ValueError, match="non-null value"):
            FillResult(
                status="filled",
                value=None,
                provenance=prov,
                channels_tried=[],
                reason="",
            )

    def test_filled_requires_provenance(self):
        with pytest.raises(ValueError, match="non-null provenance"):
            FillResult(
                status="filled",
                value="9988",
                provenance=None,
                channels_tried=[],
                reason="",
            )

    def test_blocked_allows_null_value_and_provenance(self):
        r = FillResult(
            status="blocked",
            value=None,
            provenance=None,
            channels_tried=["oeis"],
            reason="not found",
        )
        assert r.status == "blocked"

    def test_status_in_allowed_set(self):
        prov = self._make_provenance()
        r = FillResult.filled("9988", prov, [])
        assert r.status in {"filled", "blocked"}

    def test_frozen(self):
        r = FillResult.blocked("no source", [])
        with pytest.raises((AttributeError, TypeError)):
            r.status = "filled"  # type: ignore[misc]
