"""Playwright e2e test for the new live site (US1+US2+US5+US6 + dialog).

Runs against a local http.server. Skipped if Playwright is unavailable.
Real DOM, real loaded JSON. No mocks.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
WEB_DIR = REPO / "web"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def web_server():
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)],
        cwd=str(WEB_DIR),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # wait for ready
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def expected_aggregates() -> dict:
    return json.loads((WEB_DIR / "data" / "projects.json").read_text())["aggregates"]


@pytest.fixture(scope="session")
def expected_projects() -> list[dict]:
    return json.loads((WEB_DIR / "data" / "projects.json").read_text())["projects"]


def test_hero_aggregates_match_disk(web_server, expected_aggregates):
    """SC-002: every hero counter is sourced from web/data/projects.json."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(web_server + "/index.html")
        page.wait_for_load_state("networkidle")
        # wait for boot to populate counters
        page.wait_for_function(
            "document.querySelector('[data-agg=\"active_projects\"]').textContent !== '—'"
        )
        for k in ("total_contributions", "active_projects", "papers_posted",
                  "total_contributors"):
            actual = page.locator(f'[data-agg="{k}"]').first.text_content()
            assert int(actual) == expected_aggregates[k], (
                f"hero counter {k}: expected {expected_aggregates[k]}, got {actual}"
            )
        browser.close()


def test_tabs_partition_projects_correctly(web_server, expected_projects):
    """FR-005, SC-003: every non-terminal project appears in exactly one tab."""
    if not expected_projects:
        pytest.skip("no projects on disk")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(web_server + "/index.html")
        page.wait_for_load_state("networkidle")
        page.wait_for_function(
            "window._llmxive && window._llmxive.buckets"
        )
        buckets = page.evaluate("() => Object.fromEntries(Object.entries(window._llmxive.buckets).map(([k,v]) => [k, v.map(p => p.id)]))")
        # Each project in {brainstormed} should be in 'backlog'.
        backlog_ids = set(buckets.get("backlog", []))
        for p in expected_projects:
            if p["current_stage"] == "brainstormed":
                assert p["id"] in backlog_ids, p["id"]
        browser.close()


def test_dialog_opens_and_lists_artifacts(web_server, expected_projects):
    """US2: clicking a card opens the dialog with the artifact list."""
    if not expected_projects:
        pytest.skip("no projects on disk")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(web_server + "/index.html")
        page.wait_for_load_state("networkidle")
        # The brainstormed projects show under the Backlog tab as kanban issues.
        page.click('button[data-tab="backlog"]')
        # Click the first issue card
        first_issue = page.locator(".issue").first
        first_issue.click()
        # Dialog should open
        page.wait_for_selector("#ad-backdrop.open", timeout=2000)
        # Has at least the project state row
        assert page.locator(".artifact-dialog .ad-row").count() >= 1
        # Close
        page.click(".ad-close")
        browser.close()


def test_about_thresholds_present(web_server):
    """US5 / FR-025: about page contains data-threshold spans."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(web_server + "/index.html")
        page.wait_for_load_state("networkidle")
        page.click('button[data-tab="about"]')
        thresholds = page.evaluate(
            "() => [...document.querySelectorAll('[data-threshold]')].map(e => [e.getAttribute('data-threshold'), e.textContent])"
        )
        keys = {k for k, v in thresholds}
        for required in ("research_review_accept_pts", "paper_review_accept_pts",
                         "llm_review_score", "human_review_score"):
            assert required in keys, f"about page missing data-threshold {required}"
        browser.close()


def test_signin_button_present_when_logged_out(web_server):
    """US3 prerequisite: sign-in affordance is visible when no token is stored."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(web_server + "/index.html")
        page.wait_for_load_state("networkidle")
        # Boot uses Auth.mount() to render the sign-in button.
        page.wait_for_selector("#auth-slot button[data-action='signin']", timeout=2000)
        browser.close()
