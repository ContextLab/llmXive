import re
from pathlib import Path

# Verify that each source entry in research.md contains a non‑empty URL
# and a non‑empty dataset identifier.

def _parse_research_md():
    md_path = Path("specs/001-predicting-the-impact-of-laser-surface-t/research.md")
    sources = []
    with md_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    table_started = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and "Source Name" in stripped:
            table_started = True
            continue
        if table_started:
            if not stripped.startswith("|"):
                break
            parts = [p.strip() for p in stripped.split("|")[1:-1]]
            if len(parts) != 5:
                continue
            name, src_type, verified, url_id, notes = parts
            url = None
            dataset_id = None
            for sub in url_id.split("<br>"):
                sub = sub.strip()
                if sub.startswith("http"):
                    url = sub
                elif sub.lower().startswith("dataset id:"):
                    dataset_id = sub.split(":", 1)[1].strip()
            sources.append({"name": name, "url": url, "dataset_id": dataset_id})
    return sources

def test_research_sources():
    sources = _parse_research_md()
    assert sources, "No sources found in research.md"
    for src in sources:
        assert src["url"], f"Source {src['name']} missing URL"
        assert src["dataset_id"], f"Source {src['name']} missing dataset_id"