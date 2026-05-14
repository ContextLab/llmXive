"""Personality Registry website-surface smoke tests (T061, US6).

Pure-Python / no-browser. Checks the static-file structure of the
website matches what the modal needs:

  - `web/index.html` has the "Simulated personalities" prose section AND
    a button to open the Personality Registry modal.
  - `web/js/app.js` has the `openPersonalityRegistry` + `openPersonalityDetail`
    functions wired through delegated `[data-personality]` clicks.
  - `web/data/projects.json` has a non-empty `personalities` array with
    every required field present.
  - `docs/` mirrors of the above are in sync with `web/` (the pages.yml
    workflow copies them on deploy; locally they should match after
    `_build_personalities_block` runs).

A full DOM-level Playwright test is out of scope for this unit-test layer
(real-call grade only); manual verification covers it (see quickstart § 4).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


class TestIndexHtml:
    def test_has_simulated_personalities_section(self) -> None:
        html = (REPO / "web" / "index.html").read_text(encoding="utf-8")
        assert "Simulated personalities" in html
        assert 'id="simulated-personalities"' in html

    def test_has_personality_registry_trigger(self) -> None:
        html = (REPO / "web" / "index.html").read_text(encoding="utf-8")
        assert 'data-open-modal="personalities"' in html
        assert "Personality registry" in html


class TestAppJs:
    def test_has_open_personality_functions(self) -> None:
        js = (REPO / "web" / "js" / "app.js").read_text(encoding="utf-8")
        assert "openPersonalityRegistry" in js
        assert "openPersonalityDetail" in js

    def test_personality_click_delegation_wired(self) -> None:
        js = (REPO / "web" / "js" / "app.js").read_text(encoding="utf-8")
        assert 'data-personality' in js
        assert 'data-open-modal="personalities"' in js

    def test_personality_modal_uses_existing_md_body_pattern(self) -> None:
        """The registry detail view uses fetchAndRenderMarkdownInto for
        prompt rendering — same path as the Agent Registry (FR-023)."""
        js = (REPO / "web" / "js" / "app.js").read_text(encoding="utf-8")
        # The personality detail HTML uses `.am-prompt md-body` (mirror of
        # the agent detail view). Find the function body.
        idx = js.find("openPersonalityDetail")
        assert idx >= 0
        # Search forward a kilobyte for the markdown-render call.
        slice_ = js[idx:idx + 2000]
        assert "fetchAndRenderMarkdownInto" in slice_

    def test_display_name_appends_simulated_suffix_in_modal(self) -> None:
        """Every user-visible display of a persona name appends ' (simulated)' —
        per FR-010 there is NO place in the UI that shows the bare name."""
        js = (REPO / "web" / "js" / "app.js").read_text(encoding="utf-8")
        idx = js.find("openPersonalityRegistry")
        assert idx >= 0
        slice_ = js[idx:idx + 2500]
        # The rendered row text MUST include "(simulated)".
        assert '(simulated)' in slice_


class TestWebDataJsonHasPersonalities:
    def test_personalities_array_emitted(self) -> None:
        data = json.loads((REPO / "web" / "data" / "projects.json").read_text(encoding="utf-8"))
        assert "personalities" in data, "personalities block missing from projects.json"
        assert isinstance(data["personalities"], list)
        assert len(data["personalities"]) >= 10, (
            f"expected ≥ 10 personalities in projects.json, got {len(data['personalities'])}"
        )

    def test_every_entry_has_required_fields(self) -> None:
        data = json.loads((REPO / "web" / "data" / "projects.json").read_text(encoding="utf-8"))
        required = {"slug", "display_name", "summary", "sources",
                    "prompt_repo_path", "prompt_raw_url", "prompt_github_url"}
        for entry in data["personalities"]:
            missing = required - set(entry.keys())
            assert not missing, f"{entry.get('slug')!r}: missing fields {missing}"


class TestDocsSync:
    def test_docs_data_personalities_matches_web(self) -> None:
        """docs/data/projects.json should be a copy of web/data/projects.json
        after the local sync step (pages.yml does it on deploy). If they
        diverge, the deployed website's modal would be out of sync."""
        docs_path = REPO / "docs" / "data" / "projects.json"
        web_path = REPO / "web" / "data" / "projects.json"
        if not docs_path.is_file():
            pytest.skip("docs/data not synced yet")
        docs = json.loads(docs_path.read_text(encoding="utf-8"))
        web = json.loads(web_path.read_text(encoding="utf-8"))
        # Personality lists must match exactly.
        assert docs.get("personalities") == web.get("personalities")

    def test_docs_app_js_has_personality_functions(self) -> None:
        docs_js = REPO / "docs" / "js" / "app.js"
        if not docs_js.is_file():
            pytest.skip("docs/js/app.js not synced yet")
        js = docs_js.read_text(encoding="utf-8")
        assert "openPersonalityRegistry" in js
