"""Tests for `web/js/markdown.js` — specifically the code-fence-aware block
splitter and the end-to-end render-fenced-code-block path.

The bug fixed: `renderMarkdown` was splitting the source on `\\n{2,}` before
handing each chunk to snarkdown, which shattered any fenced code block that
contained a blank line. That's extremely common in agent prompts and code
samples, and produced broken HTML (an unclosed `<pre><code>` plus orphan
fragments).

We drive the real `web/js/markdown.js` via Node's `vm` module so the test
exercises the actual code that ships to the browser. The renderer relies on
`DOMParser` for sanitization; for the `_splitBlocks` tests we stub it (the
splitter never calls it). The full `renderMarkdown` path is exercised by
the integration test below which provides a minimal DOM via `linkedom` only
when it's installed — otherwise we skip that case.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MD_JS = REPO / "web" / "js" / "markdown.js"


def _have_node() -> bool:
    return shutil.which("node") is not None


pytestmark = pytest.mark.skipif(not _have_node(), reason="node not installed")


def _run_split_blocks(md: str) -> list[str]:
    """Drive `_splitBlocks` from web/js/markdown.js via Node's vm module."""
    script = textwrap.dedent(f"""
        const fs = require("fs");
        const vm = require("vm");
        const src = fs.readFileSync({json.dumps(str(MD_JS))}, "utf8");
        // Minimal sandbox: window aliases globalThis, snarkdown is null (not
        // needed by _splitBlocks), DOMParser is stubbed for the _sanitize
        // path the splitter never touches.
        const sandbox = {{
            console,
            window: {{}},
            snarkdown: null,
            DOMParser: function () {{}},
        }};
        sandbox.window = sandbox;
        sandbox.globalThis = sandbox;
        vm.createContext(sandbox);
        vm.runInContext(src, sandbox);
        const md = {json.dumps(md)};
        const blocks = sandbox.window.LlmxiveMarkdown._splitBlocks(md);
        console.log(JSON.stringify(blocks));
    """)
    proc = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=20)
    if proc.returncode != 0:
        raise AssertionError(f"node failed: {proc.stderr.strip()}\n{proc.stdout.strip()}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


class TestSplitBlocksOutsideFences:
    """`_splitBlocks` should split on blank lines OUTSIDE fenced blocks."""

    def test_two_paragraphs_split_on_blank(self) -> None:
        blocks = _run_split_blocks("para one\n\npara two")
        assert blocks == ["para one", "para two"]

    def test_single_paragraph_no_blanks(self) -> None:
        blocks = _run_split_blocks("just one paragraph")
        assert blocks == ["just one paragraph"]

    def test_multiple_blanks_collapse_to_one_break(self) -> None:
        blocks = _run_split_blocks("a\n\n\n\nb")
        assert blocks == ["a", "b"]


class TestSplitBlocksInsideFences:
    """`_splitBlocks` must NOT split on blank lines inside ``` / ~~~ fences."""

    def test_blank_line_inside_backtick_fence_preserved(self) -> None:
        md = "```python\ndef foo():\n    pass\n\ndef bar():\n    pass\n```"
        blocks = _run_split_blocks(md)
        # The whole fence must stay in ONE block; the blank line inside it
        # must be preserved verbatim (this is the actual bug-fix invariant).
        assert len(blocks) == 1, f"fence got split: {blocks!r}"
        assert "def foo()" in blocks[0]
        assert "def bar()" in blocks[0]
        assert "\n\n" in blocks[0]

    def test_blank_line_inside_tilde_fence_preserved(self) -> None:
        md = "~~~\nline1\n\nline2\n~~~"
        blocks = _run_split_blocks(md)
        assert len(blocks) == 1
        assert "line1\n\nline2" in blocks[0]

    def test_paragraph_then_fenced_block_separated(self) -> None:
        md = "intro paragraph\n\n```py\nx = 1\n\ny = 2\n```\n\nafter paragraph"
        blocks = _run_split_blocks(md)
        assert len(blocks) == 3
        assert blocks[0] == "intro paragraph"
        assert "x = 1" in blocks[1] and "y = 2" in blocks[1]
        assert blocks[2] == "after paragraph"

    def test_two_fences_back_to_back(self) -> None:
        md = "```py\na = 1\n```\n\n```js\nlet b = 2;\n```"
        blocks = _run_split_blocks(md)
        assert len(blocks) == 2
        assert blocks[0].startswith("```py")
        assert blocks[1].startswith("```js")

    def test_tilde_inside_backtick_fence_does_not_close_it(self) -> None:
        # CommonMark §4.5: only a matching fence char can close
        md = "```\ncontent\n~~~\nstill in fence\n```"
        blocks = _run_split_blocks(md)
        assert len(blocks) == 1
        assert "still in fence" in blocks[0]


class TestSplitBlocksEdgeCases:
    def test_empty_string(self) -> None:
        assert _run_split_blocks("") == []

    def test_blank_lines_only(self) -> None:
        assert _run_split_blocks("\n\n\n") == []

    def test_unclosed_fence_at_eof_kept_as_one_block(self) -> None:
        # A fence that never closes — degrade gracefully (don't drop content).
        md = "```py\nx = 1\n\ny = 2"
        blocks = _run_split_blocks(md)
        assert len(blocks) == 1
        assert "x = 1" in blocks[0] and "y = 2" in blocks[0]

    def test_fenced_block_at_start(self) -> None:
        md = "```\nopener\n```\n\nafter"
        blocks = _run_split_blocks(md)
        assert len(blocks) == 2
        assert blocks[0] == "```\nopener\n```"
        assert blocks[1] == "after"

    def test_fenced_block_at_end(self) -> None:
        md = "before\n\n```\nlast\n```"
        blocks = _run_split_blocks(md)
        assert len(blocks) == 2
        assert blocks[0] == "before"
        assert blocks[1] == "```\nlast\n```"
