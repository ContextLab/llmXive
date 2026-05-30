"""T028 — unit tests for fill/channels/wikidata.py pure parsers.

Tests _parse_search and _parse_entity on inline real-shaped fixture dicts.
No network calls. Verifies that search_and_fetch exists and has the right signature.
"""

from __future__ import annotations

import pytest

from llmxive.fill.channels.wikidata import _parse_entity, _parse_search, search_and_fetch


# ---------------------------------------------------------------------------
# Fixtures: real-shaped Wikidata API responses (captured structure)
# ---------------------------------------------------------------------------

SEARCH_RESPONSE = {
    "searchinfo": {"search": "capital Australia"},
    "search": [
        {
            "id": "Q408",
            "title": "Q408",
            "pageid": 616,
            "repository": "wikidata",
            "url": "//www.wikidata.org/wiki/Q408",
            "concepturi": "http://www.wikidata.org/entity/Q408",
            "label": "Australia",
            "description": "country in Oceania",
            "match": {"type": "label", "language": "en", "text": "Australia"},
        },
        {
            "id": "Q3960",
            "title": "Q3960",
            "pageid": 4064,
            "repository": "wikidata",
            "url": "//www.wikidata.org/wiki/Q3960",
            "concepturi": "http://www.wikidata.org/entity/Q3960",
            "label": "Canberra",
            "description": "capital city of Australia",
            "match": {"type": "description", "language": "en", "text": "capital city of Australia"},
        },
    ],
    "success": 1,
}

ENTITY_RESPONSE_Q408 = {
    "entities": {
        "Q408": {
            "type": "item",
            "id": "Q408",
            "labels": {
                "en": {"language": "en", "value": "Australia"},
            },
            "descriptions": {
                "en": {"language": "en", "value": "country in Oceania"},
            },
            "claims": {
                # P36 = capital
                "P36": [
                    {
                        "mainsnak": {
                            "snaktype": "value",
                            "property": "P36",
                            "datavalue": {
                                "value": {"entity-type": "item", "id": "Q3960"},
                                "type": "wikibase-entityid",
                            },
                        },
                        "type": "statement",
                        "rank": "preferred",
                    }
                ],
                # P30 = continent
                "P30": [
                    {
                        "mainsnak": {
                            "snaktype": "value",
                            "property": "P30",
                            "datavalue": {
                                "value": {"entity-type": "item", "id": "Q538"},
                                "type": "wikibase-entityid",
                            },
                        },
                        "type": "statement",
                        "rank": "normal",
                    }
                ],
                # P856 = official website (string)
                "P856": [
                    {
                        "mainsnak": {
                            "snaktype": "value",
                            "property": "P856",
                            "datavalue": {
                                "value": "https://www.australia.gov.au/",
                                "type": "string",
                            },
                        },
                        "type": "statement",
                        "rank": "preferred",
                    }
                ],
            },
        }
    },
    "success": 1,
}

ENTITY_RESPONSE_MISSING = {
    "entities": {
        "Q99999999": {"id": "Q99999999", "missing": ""},
    },
    "success": 1,
}

EMPTY_SEARCH_RESPONSE = {
    "searchinfo": {"search": "zorblax frobnication"},
    "search": [],
    "success": 1,
}


# ---------------------------------------------------------------------------
# _parse_search
# ---------------------------------------------------------------------------

class TestParseSearch:
    def test_returns_list_of_tuples(self):
        result = _parse_search(SEARCH_RESPONSE)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_first_result_australia(self):
        result = _parse_search(SEARCH_RESPONSE)
        qid, label, description = result[0]
        assert qid == "Q408"
        assert label == "Australia"
        assert "Oceania" in description

    def test_second_result_canberra(self):
        result = _parse_search(SEARCH_RESPONSE)
        qid, label, description = result[1]
        assert qid == "Q3960"
        assert label == "Canberra"
        assert "capital" in description

    def test_empty_search_returns_empty_list(self):
        result = _parse_search(EMPTY_SEARCH_RESPONSE)
        assert result == []

    def test_malformed_no_search_key(self):
        result = _parse_search({})
        assert result == []

    def test_item_without_id_skipped(self):
        data = {"search": [{"label": "No ID item", "description": "no id here"}]}
        result = _parse_search(data)
        assert result == []


# ---------------------------------------------------------------------------
# _parse_entity
# ---------------------------------------------------------------------------

class TestParseEntity:
    def test_returns_tuple_for_valid_entity(self):
        result = _parse_entity(ENTITY_RESPONSE_Q408, "Q408")
        assert result is not None
        label, text = result
        assert label == "Australia"

    def test_description_in_text(self):
        result = _parse_entity(ENTITY_RESPONSE_Q408, "Q408")
        assert result is not None
        _, text = result
        assert "Oceania" in text

    def test_string_claim_in_text(self):
        """String-typed claim values should appear in the text blob."""
        result = _parse_entity(ENTITY_RESPONSE_Q408, "Q408")
        assert result is not None
        _, text = result
        assert "australia.gov.au" in text

    def test_entity_claim_id_in_text(self):
        """wikibase-entityid claim values (Q-ids) should appear in text blob."""
        result = _parse_entity(ENTITY_RESPONSE_Q408, "Q408")
        assert result is not None
        _, text = result
        # P36: Q3960 (capital = Canberra) should be in the blob
        assert "Q3960" in text

    def test_missing_entity_returns_none(self):
        result = _parse_entity(ENTITY_RESPONSE_MISSING, "Q99999999")
        assert result is None

    def test_nonexistent_qid_returns_none(self):
        result = _parse_entity(ENTITY_RESPONSE_Q408, "Q999")
        assert result is None

    def test_empty_entities_returns_none(self):
        result = _parse_entity({"entities": {}}, "Q408")
        assert result is None


# ---------------------------------------------------------------------------
# search_and_fetch signature and return type
# ---------------------------------------------------------------------------

class TestSearchAndFetchSignature:
    def test_function_exists(self):
        assert callable(search_and_fetch)

    def test_returns_list(self, monkeypatch):
        """Monkeypatch _retry_request to return no-search response."""
        import llmxive.fill.channels.wikidata as wd_mod
        from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id

        class _FakeResp:
            status_code = 200
            def json(self):
                return EMPTY_SEARCH_RESPONSE

        monkeypatch.setattr(wd_mod, "_retry_request", lambda *a, **kw: _FakeResp())

        cid = compute_claim_id(ClaimKind.ENTITY_FACT, "test", "ctx")
        claim = Claim(
            claim_id=cid,
            kind=ClaimKind.ENTITY_FACT,
            raw_text="test claim",
            canonical="test claim",
            context="ctx",
            artifact_path="test/p.md",
            source_type="external",
            status=ClaimStatus.PENDING,
            resolved_value=None,
            evidence=None,
            resolver=None,
            attempts=0,
            updated_at="2026-05-30T00:00:00Z",
        )
        result = search_and_fetch("zorblax frobnication", claim)
        assert isinstance(result, list)
        assert result == []

    def test_returns_fetched_sources_from_fixture(self, monkeypatch):
        """With a valid search + entity response, returns FetchedSource objects."""
        import llmxive.fill.channels.wikidata as wd_mod
        from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
        from llmxive.fill.models import FetchedSource

        call_count = [0]

        class _FakeResp:
            def __init__(self, data):
                self._data = data
                self.status_code = 200

            def json(self):
                return self._data

        def _fake_retry(method, url, *, headers=None, params=None, timeout=30.0, max_attempts=3):
            call_count[0] += 1
            if call_count[0] == 1:
                return _FakeResp(SEARCH_RESPONSE)
            return _FakeResp(ENTITY_RESPONSE_Q408)

        monkeypatch.setattr(wd_mod, "_retry_request", _fake_retry)

        cid = compute_claim_id(ClaimKind.ENTITY_FACT, "capital Australia", "ctx")
        claim = Claim(
            claim_id=cid,
            kind=ClaimKind.ENTITY_FACT,
            raw_text="The capital of Australia is Sydney",
            canonical="The capital of Australia is Sydney",
            context="ctx",
            artifact_path="test/p.md",
            source_type="external",
            status=ClaimStatus.PENDING,
            resolved_value=None,
            evidence=None,
            resolver=None,
            attempts=0,
            updated_at="2026-05-30T00:00:00Z",
        )
        result = search_and_fetch("capital Australia", claim)
        assert isinstance(result, list)
        assert len(result) >= 1
        src = result[0]
        assert isinstance(src, FetchedSource)
        assert src.channel == "wikidata"
        assert src.source_id == "Q408"
        assert src.url == "https://www.wikidata.org/wiki/Q408"
        assert "Australia" in src.text
        assert src.authority == 1  # AUTHORITY["wikidata"]
