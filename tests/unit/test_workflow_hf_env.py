"""Model-calling workflow jobs must carry the Hugging Face funded-provider settings.

Only ``env:`` mappings may change; no workflow trigger (``on:``) may differ from HEAD.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / ".github" / "workflows"
WANT = {
    "HF_TOKEN": "${{ secrets.HF_TOKEN }}",
    "LLMXIVE_HF_BILL_TO": "${{ vars.LLMXIVE_HF_BILL_TO }}",
    "LLMXIVE_FUNDED_LEDGER_ANCHOR": "${{ vars.LLMXIVE_FUNDED_LEDGER_ANCHOR }}",
}


def _env_blocks(node):
    if isinstance(node, dict):
        if isinstance(node.get("env"), dict):
            yield node["env"]
        for v in node.values():
            yield from _env_blocks(v)
    elif isinstance(node, list):
        for v in node:
            yield from _env_blocks(v)


def test_every_model_calling_env_block_carries_the_hf_settings():
    seen = 0
    for path in sorted(WF.glob("*.yml")):
        for env in _env_blocks(yaml.safe_load(path.read_text())):
            if "secrets.DARTMOUTH_CHAT_API_KEY" in str(env.get("DARTMOUTH_CHAT_API_KEY", "")):
                seen += 1
                assert {k: env.get(k) for k in WANT} == WANT, path.name
    assert seen >= 12


def test_bill_to_is_a_variable_never_a_secret():
    assert "secrets.LLMXIVE_HF_BILL_TO" not in "".join(p.read_text() for p in WF.glob("*.yml"))


def _on_block(doc):
    # PyYAML parses the bare key `on` as boolean True.
    return doc[True] if True in doc else doc.get("on")


def test_no_workflow_trigger_differs_from_head():
    for path in sorted(WF.glob("*.yml")):
        rel = path.relative_to(ROOT).as_posix()
        head = subprocess.run(
            ["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, text=True
        )
        if head.returncode != 0:
            continue  # new file, nothing to compare
        old = yaml.safe_load(head.stdout)
        new = yaml.safe_load(path.read_text())
        assert _on_block(new) == _on_block(old), f"{path.name}: on: block changed"
