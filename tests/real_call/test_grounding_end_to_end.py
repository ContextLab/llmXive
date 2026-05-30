# tests/real_call/test_grounding_end_to_end.py
import os

import pytest

from llmxive.agents.grounding_guard import verify_grounding_and_clean
from llmxive.backends.dartmouth import DartmouthBackend

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1", reason="real-call"
)


def test_fabricated_number_on_real_paper_is_flagged(tmp_path):
    # Attention Is All You Need reports BLEU 28.4 (En-De); claim a fabricated 99.9.
    doc = (
        "The proposed model achieves a BLEU score of 99.9 on the WMT 2014 "
        "English-to-German task (arXiv:1706.03762)."
    )
    cleaned, report = verify_grounding_and_clean(
        doc, backend=DartmouthBackend(), model="qwen.qwen3.5-122b", repo_root=tmp_path
    )
    assert "[UNRESOLVED-CLAIM:" in cleaned and report.flagged_count >= 1


def test_real_number_on_real_paper_passes(tmp_path):
    # The paper reports BLEU 28.4 for English-to-German (41.8 is its
    # English-to-FRENCH score) — use the TRUE En-De number so a correctly
    # cited claim is NOT flagged.
    doc = (
        "The proposed model achieves a BLEU score of 28.4 on the WMT 2014 "
        "English-to-German task (arXiv:1706.03762)."
    )
    cleaned, _report = verify_grounding_and_clean(
        doc, backend=DartmouthBackend(), model="qwen.qwen3.5-122b", repo_root=tmp_path
    )
    assert "[UNRESOLVED-CLAIM:" not in cleaned
