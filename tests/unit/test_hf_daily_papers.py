"""Tests for the HF daily-papers cron submitter.

Covers:
- top-N selection (sorted by upvotes desc, ties by arxiv_id for determinism)
- malformed entries skipped (don't crash, don't count)
- limit truncation
- issue payload exactly matches the contract used by `web/js/auth.js::submitPaper`
  (link variant) — including labels and the `**URL:** / **Submitter:**` fields
  that `submission_intake._parse_new_paper_body` keys off
- dry-run produces previews without filing
- the submitter literal is `github-actions[bot]`
"""

from __future__ import annotations

from datetime import UTC

from llmxive.hf_daily_papers import (
    BOT_SUBMITTER,
    ISSUE_LABELS,
    Paper,
    build_issue,
    fetch_top_papers,
    submit_top_papers,
)


def _entry(arxiv_id: str, title: str, upvotes: int, *, summary: str = "") -> dict:
    """Mimic the relevant subset of the HF daily-papers JSON shape."""
    return {
        "paper": {
            "id": arxiv_id,
            "title": title,
            "summary": summary or f"Summary for {arxiv_id}",
            "upvotes": upvotes,
        }
    }


class TestFetchTopPapers:
    def test_sorts_by_upvotes_desc(self) -> None:
        raw = [_entry("2605.01000", "low", 1), _entry("2605.02000", "high", 100),
               _entry("2605.03000", "mid", 50)]
        effective_date, out = fetch_top_papers("2026-05-13", limit=3, raw_json=raw)
        assert effective_date == "2026-05-13"  # raw_json passed → no fallback
        assert [p.upvotes for p in out] == [100, 50, 1]
        assert out[0].arxiv_id == "2605.02000"

    def test_ties_break_by_arxiv_id(self) -> None:
        # Deterministic tie-break so reruns + tests are stable.
        raw = [_entry("2605.09000", "B", 10), _entry("2605.01000", "A", 10)]
        _, out = fetch_top_papers("2026-05-13", limit=2, raw_json=raw)
        assert [p.arxiv_id for p in out] == ["2605.01000", "2605.09000"]

    def test_limit_truncates(self) -> None:
        raw = [_entry(f"2605.{i:05d}", f"t{i}", i) for i in range(20)]
        _, out = fetch_top_papers("2026-05-13", limit=5, raw_json=raw)
        assert len(out) == 5
        # newest upvotes first
        assert out[0].upvotes == 19

    def test_malformed_entries_skipped(self) -> None:
        raw = [
            _entry("2605.01000", "good", 5),
            {},                                        # no paper key
            {"paper": {}},                             # empty paper
            {"paper": {"id": "", "title": "no id", "upvotes": 99}},   # missing id
            {"paper": {"id": "2605.02000", "title": "", "upvotes": 99}},  # missing title
            "not a dict",                              # type error
        ]
        _, out = fetch_top_papers("2026-05-13", limit=10, raw_json=raw)
        assert [p.arxiv_id for p in out] == ["2605.01000"]

    def test_non_int_upvotes_coerced_to_zero(self) -> None:
        raw = [{"paper": {"id": "2605.0", "title": "weird", "upvotes": "many"}}]
        _, out = fetch_top_papers("2026-05-13", limit=1, raw_json=raw)
        assert out[0].upvotes == 0


class TestBuildIssue:
    def _paper(self) -> Paper:
        return Paper(arxiv_id="2605.09530", title="MemPrivacy: …",
                     summary="abstract", upvotes=128)

    def test_labels_match_submit_dialog(self) -> None:
        payload = build_issue(self._paper())
        # Same labels as web/js/auth.js::submitPaper link variant.
        assert payload["labels"] == list(ISSUE_LABELS)
        assert "human-submission" in payload["labels"]
        assert "new-paper" in payload["labels"]

    def test_title_matches_dialog_format(self) -> None:
        payload = build_issue(self._paper())
        # "New paper (link): <first 80 chars of url>"
        assert payload["title"].startswith("New paper (link): ")
        assert "arxiv.org/abs/2605.09530" in payload["title"]

    def test_body_contains_required_fields(self) -> None:
        payload = build_issue(self._paper())
        body = payload["body"]
        # `_parse_new_paper_body` keys off these exact labels.
        assert "- **URL:** https://arxiv.org/abs/2605.09530" in body
        assert f"- **Submitter:** {BOT_SUBMITTER}" in body
        # context lines for human readers
        assert "upvotes: 128" in body
        assert "Hugging Face daily-papers" in body

    def test_submitter_defaults_to_bot(self) -> None:
        payload = build_issue(self._paper())
        assert f"**Submitter:** {BOT_SUBMITTER}" in payload["body"]
        # And the bot literal is the exact GH bot identity we expect.
        assert BOT_SUBMITTER == "github-actions[bot]"


class TestSubmitTopPapers:
    def test_dry_run_does_not_call_gh(self) -> None:
        raw = [_entry("2605.01000", "A", 10), _entry("2605.02000", "B", 5)]
        result = submit_top_papers("2026-05-13", limit=2, dry_run=True, raw_json=raw)
        assert result.dry_run is True
        assert result.fetched == 2
        assert len(result.filed) == 2
        # No issue numbers — these are previews.
        assert all(r["issue_number"] is None for r in result.filed)
        # Each preview includes the rendered body
        assert all("Submitted paper" in r["preview_body"] for r in result.filed)

    def test_dry_run_respects_limit(self) -> None:
        raw = [_entry(f"2605.{i:05d}", f"t{i}", i) for i in range(10)]
        result = submit_top_papers("2026-05-13", limit=3, dry_run=True, raw_json=raw)
        assert len(result.filed) == 3

    def test_no_papers_to_file_yields_empty_result(self) -> None:
        result = submit_top_papers("2026-05-13", limit=5, dry_run=True, raw_json=[])
        assert result.fetched == 0
        assert result.filed == []
        assert result.skipped == []


class TestDateFallback:
    """Tests for the date-bucket fallback chain added in the post-spec-010 fix.

    HF daily-papers buckets are populated by HF's editorial pipeline in the
    late afternoon UTC. Running at 23:59 UTC + cron schedule drift can put
    the request past midnight (the new day's bucket is empty → HTTP 400).
    """

    def test_today_utc_defaults_to_yesterday(self) -> None:
        from datetime import datetime, timedelta

        from llmxive.hf_daily_papers import _today_utc

        expected = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
        assert _today_utc() == expected

    def test_fetch_falls_back_on_400(self, monkeypatch) -> None:
        """When the requested date returns 400, walk back one day and retry."""
        import urllib.error

        from llmxive.hf_daily_papers import _fetch_daily_json

        calls: list[str] = []

        def fake_one(date: str, *, timeout: float = 30.0):
            calls.append(date)
            if date == "2026-05-15":
                raise urllib.error.HTTPError(
                    url="x", code=400, msg="Bad Request", hdrs=None, fp=None,
                )
            return [{"paper": {"id": "2605.fallback", "title": "ok", "upvotes": 1}}]

        monkeypatch.setattr(
            "llmxive.hf_daily_papers._fetch_daily_json_one", fake_one
        )
        effective, data = _fetch_daily_json("2026-05-15", fallback_days=1)
        assert effective == "2026-05-14"
        assert calls == ["2026-05-15", "2026-05-14"]
        assert data[0]["paper"]["id"] == "2605.fallback"

    def test_fetch_falls_back_on_404(self, monkeypatch) -> None:
        """404 (alternative HF response shape) also triggers fallback."""
        import urllib.error

        from llmxive.hf_daily_papers import _fetch_daily_json

        def fake_one(date: str, *, timeout: float = 30.0):
            if date == "2026-05-15":
                raise urllib.error.HTTPError(
                    url="x", code=404, msg="Not Found", hdrs=None, fp=None,
                )
            return []

        monkeypatch.setattr(
            "llmxive.hf_daily_papers._fetch_daily_json_one", fake_one
        )
        effective, data = _fetch_daily_json("2026-05-15", fallback_days=1)
        assert effective == "2026-05-14"
        assert data == []

    def test_fetch_does_not_swallow_5xx(self, monkeypatch) -> None:
        """5xx errors should propagate — they indicate transient HF issues,
        not a date-bucket problem."""
        import urllib.error

        import pytest

        from llmxive.hf_daily_papers import _fetch_daily_json

        def fake_one(date: str, *, timeout: float = 30.0):
            raise urllib.error.HTTPError(
                url="x", code=503, msg="Service Unavailable", hdrs=None, fp=None,
            )

        monkeypatch.setattr(
            "llmxive.hf_daily_papers._fetch_daily_json_one", fake_one
        )
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            _fetch_daily_json("2026-05-15", fallback_days=1)
        assert excinfo.value.code == 503

    def test_fetch_raises_when_all_fallback_attempts_400(
        self, monkeypatch
    ) -> None:
        """If every date in the fallback chain returns 400, raise the last
        HTTPError so the caller can surface a meaningful failure."""
        import urllib.error

        import pytest

        from llmxive.hf_daily_papers import _fetch_daily_json

        def fake_one(date: str, *, timeout: float = 30.0):
            raise urllib.error.HTTPError(
                url="x", code=400, msg="Bad Request", hdrs=None, fp=None,
            )

        monkeypatch.setattr(
            "llmxive.hf_daily_papers._fetch_daily_json_one", fake_one
        )
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            _fetch_daily_json("2026-05-15", fallback_days=2)
        assert excinfo.value.code == 400
