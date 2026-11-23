"""Model-calling workflow jobs must carry the Hugging Face funded-provider settings.

Workflows are parsed with a loader that RAISES on a duplicate mapping key, because
GitHub Actions rejects such files while ``yaml.safe_load`` silently keeps the last one.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

WF = Path(__file__).resolve().parents[2] / ".github" / "workflows"
WANT = {
    "HF_TOKEN": "${{ secrets.HF_TOKEN }}",
    "LLMXIVE_HF_BILL_TO": "${{ vars.LLMXIVE_HF_BILL_TO }}",
    "LLMXIVE_FUNDED_LEDGER_ANCHOR": "${{ vars.LLMXIVE_FUNDED_LEDGER_ANCHOR }}",
}


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate keys in any mapping."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=True)
            if key in seen:
                raise yaml.constructor.ConstructorError(
                    None, None, f"duplicate mapping key {key!r}", key_node.start_mark
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def _load(path: Path):
    return yaml.load(path.read_text(), Loader=_StrictLoader)


def _env_blocks(node):
    if isinstance(node, dict):
        if isinstance(node.get("env"), dict):
            yield node["env"]
        for v in node.values():
            yield from _env_blocks(v)
    elif isinstance(node, list):
        for v in node:
            yield from _env_blocks(v)


@pytest.mark.parametrize("path", sorted(WF.glob("*.yml")), ids=lambda p: p.name)
def test_workflow_has_no_duplicate_mapping_keys(path):
    _load(path)


def test_every_model_calling_env_block_carries_the_hf_settings():
    seen = 0
    for path in sorted(WF.glob("*.yml")):
        for env in _env_blocks(_load(path)):
            if "secrets.DARTMOUTH_CHAT_API_KEY" in str(env.get("DARTMOUTH_CHAT_API_KEY", "")):
                seen += 1
                assert {k: env.get(k) for k in WANT} == WANT, path.name
    assert seen >= 12


def test_bill_to_is_a_variable_never_a_secret():
    assert "secrets.LLMXIVE_HF_BILL_TO" not in "".join(p.read_text() for p in WF.glob("*.yml"))
