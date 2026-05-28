"""Contract tests for the on-disk summary manifest (spec 015 T010, FR-007).

Validates the inode-table manifest schema and the no-dangling-pointer invariant.
"""

from __future__ import annotations

import json

import pytest

from llmxive.tools.summarize import desummarize, summarize

BUDGET = 400


def _overflowing_doc() -> str:
    return "".join(
        f"## S{i}\nhttps://ex.test/{i} 10.1/{i:04d} FR-{i:03d} value={i}.{i}\n\n"
        for i in range(60)
    )


def _manifest_path(block: str):
    from pathlib import Path
    first = block.splitlines()[0]
    return Path(first.split("manifest=", 1)[1].strip())


def test_manifest_schema_and_content_files(tmp_path):
    block = summarize(_overflowing_doc(), goal="preserve every URL/DOI/id",
                      token_budget=BUDGET, cache_dir=tmp_path)
    mpath = _manifest_path(block)
    manifest = json.loads(mpath.read_text())
    assert manifest["schema"] == "llmxive-summary/1"
    for key in ("root_hash", "goal", "model", "token_budget", "created_at", "entries"):
        assert key in manifest, f"manifest missing {key}"
    assert manifest["entries"], "manifest has no entries"
    for e in manifest["entries"]:
        for key in ("element_id", "kind", "file", "critical", "summary"):
            assert key in e, f"entry missing {key}"
        assert e["kind"] in ("content", "pointer")
        assert (mpath.parent / e["file"]).exists(), f"missing target for {e['element_id']}"


def test_no_dangling_pointer_detected(tmp_path):
    block = summarize(_overflowing_doc(), goal="preserve every URL/DOI/id",
                      token_budget=BUDGET, cache_dir=tmp_path)
    mpath = _manifest_path(block)
    manifest = json.loads(mpath.read_text())
    # delete a referenced content file -> desummarize must raise, never silently skip
    victim = mpath.parent / manifest["entries"][0]["file"]
    victim.unlink()
    with pytest.raises(FileNotFoundError):
        desummarize(block)


def test_missing_manifest_raises(tmp_path):
    block = summarize(_overflowing_doc(), goal="preserve every URL/DOI/id",
                      token_budget=BUDGET, cache_dir=tmp_path)
    mpath = _manifest_path(block)
    # remove the whole manifest tree -> desummarize must raise (no silent empty result)
    mpath.unlink()
    with pytest.raises(FileNotFoundError):
        desummarize(block)
