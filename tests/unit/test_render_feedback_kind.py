"""D10 — the execution-feedback renderer must branch on the source KIND.

Locks ``data_source.render_feedback_block``: a ``pypi_package`` gets a
``pip install`` line; a ``data_url`` gets a download/stream recipe and is NEVER
told to ``pip install <url>``; and no verified block ever claims "loads 0 real
records".
"""
from __future__ import annotations

from llmxive.execution.data_source import render_feedback_block


def test_pypi_render_has_pip_install():
    rec = {
        "status": "verified", "kind": "pypi_package", "ref": "database-knotinfo",
        "access_python": "import database_knotinfo", "record_count": 250,
        "sample_fields": ["crossing_number"],
    }
    block = render_feedback_block(rec)
    assert "pip install database-knotinfo" in block
    assert "requirements.txt" in block
    assert "250" in block
    assert "0 real records" not in block


def test_data_url_render_no_pip_install():
    url = "https://example.org/data/knots.csv"
    rec = {
        "status": "verified", "kind": "data_url", "ref": url,
        "access_python": "import pandas as pd\npd.read_csv(url)", "record_count": 42,
        "sample_fields": ["a", "b"],
    }
    block = render_feedback_block(rec)
    # Never instruct installing a URL as a package.
    assert "pip install http" not in block.lower()
    assert "requirements.txt" not in block
    # The URL is offered as a download/stream target instead.
    assert f"`{url}`" in block
    assert "download" in block.lower() or "stream" in block.lower()
    assert "42" in block
    assert "0 real records" not in block


def test_missing_kind_defaults_to_pypi():
    # A legacy verified record without a ``kind`` still renders the pip path.
    rec = {"status": "verified", "ref": "somepkg", "access_python": "import somepkg",
           "record_count": 7}
    block = render_feedback_block(rec)
    assert "pip install somepkg" in block


def test_non_verified_records_render_empty():
    assert render_feedback_block(None) == ""
    assert render_feedback_block({"status": "none"}) == ""
    assert render_feedback_block({"status": "error", "transient": True}) == ""


def test_never_emits_zero_records_phrasing():
    rec = {"status": "verified", "kind": "pypi_package", "ref": "pkg",
           "access_python": "import pkg", "record_count": 5}
    assert "0 real records" not in render_feedback_block(rec)
