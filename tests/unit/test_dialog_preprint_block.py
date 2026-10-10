"""`web/js/dialog.js` must link a preprint's SOURCE and name its licence.

The ingested bodies are no longer committed or mirrored (the arXiv
Non-exclusive Distribution License grants distribution to arXiv.org and is
silent on anyone else), so `preprint.original_pdf` is null for them and the
modal has to point at the paper where it actually lives.

These drive the REAL shipped `web/js/dialog.js` through Node's `vm` module, the
same way `test_markdown_renderer.py` drives markdown.js. `_preprintBlockHTML`
is pure string building, so a `window` stub is the only scaffolding needed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DIALOG_JS = REPO / "web" / "js" / "dialog.js"

SOURCE = {
    "arxiv_id": "2606.18216",
    "url": "https://arxiv.org/abs/2606.18216",
    "license": "arXiv Non-exclusive Distribution License",
    "license_url": "http://arxiv.org/licenses/nonexclusive-distrib/1.0/",
    "reviewed_version": {"file": "original.pdf", "sha256": "c" * 64, "bytes": 9128866},
}

#: ``node -e`` does not put the script path in ``process.argv``, so the inputs
#: come through the environment rather than positionally.
_DRIVER = """
const fs = require('fs'), vm = require('vm');
const sandbox = { window: { LlmxiveData: {} }, document: {} };
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(process.env.DIALOG_JS, 'utf8'), sandbox, { filename: 'dialog.js' });
const api = sandbox.window.LlmxiveDialog;
if (!api || !api._test || typeof api._test.preprintBlockHTML !== 'function') {
  throw new Error('dialog.js no longer exposes the preprint-block test seam');
}
process.stdout.write(api._test.preprintBlockHTML(JSON.parse(process.env.PREPRINT_JSON)));
"""


def _render(preprint: dict) -> str:
    node = shutil.which("node")
    if node is None:  # pragma: no cover - environment without node
        pytest.skip("node is not installed")
    done = subprocess.run(
        [node, "-e", _DRIVER],
        env={**os.environ, "DIALOG_JS": str(DIALOG_JS),
             "PREPRINT_JSON": json.dumps(preprint)},
        capture_output=True, text=True, timeout=120,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    return done.stdout


def test_the_source_link_licence_and_reviewed_digest_all_render():
    html = _render({"original_source": SOURCE, "original_pdf": None,
                    "peer_review_pdf": {"repo_path": "p.pdf"}})
    assert 'href="https://arxiv.org/abs/2606.18216"' in html
    assert "Original paper (at the source)" in html
    assert 'href="http://arxiv.org/licenses/nonexclusive-distrib/1.0/"' in html
    assert "arXiv Non-exclusive Distribution License" in html
    assert "original.pdf" in html and "cccccccccccc" in html and "9128866" in html
    # The honesty clause: the live link is not necessarily the reviewed bytes.
    assert "may differ" in html


def test_an_unhosted_original_shows_no_embedded_paper_toggle():
    html = _render({"original_source": SOURCE, "original_pdf": None,
                    "peer_review_pdf": {"repo_path": "p.pdf"}})
    assert "Paper (llmXive PDF)" not in html, "nothing is hosted to embed"
    assert "Automated-review report" in html, "our own review PDF still embeds"


def test_a_still_hosted_original_keeps_its_toggle():
    html = _render({"original_source": SOURCE,
                    "original_pdf": {"repo_path": "o.pdf"}, "peer_review_pdf": None})
    assert "Paper (llmXive PDF)" in html


def test_a_legacy_entry_without_the_source_block_still_links():
    """Back-compat: an older payload has only `source_url`."""
    html = _render({"source_url": "https://arxiv.org/abs/2605.00001"})
    assert 'href="https://arxiv.org/abs/2605.00001"' in html
    assert "Licence" not in html, "no licence is claimed when none is recorded"


def test_no_source_at_all_renders_no_link():
    html = _render({})
    assert "Original paper (at the source)" not in html
    assert "arxiv.org" not in html


def test_hostile_metadata_is_escaped():
    html = _render({"original_source": dict(
        SOURCE,
        license='<script>alert(1)</script>',
        url='javascript:alert(1)"<script>',
        reviewed_version={"file": "<img src=x onerror=alert(1)>", "sha256": "d" * 64, "bytes": 1},
    )})
    assert "<script>" not in html
    assert "<img src=x" not in html
    assert "&lt;script&gt;" in html
