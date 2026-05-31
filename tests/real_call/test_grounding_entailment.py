import os

import pytest

from llmxive.backends.dartmouth import DartmouthBackend
from llmxive.grounding.entailment import assess
from llmxive.grounding.full_text import RetrievedDoc

pytestmark = pytest.mark.skipif(os.environ.get("LLMXIVE_REAL_TESTS") != "1", reason="real-call")


def _doc(text):
    return RetrievedDoc("arxiv", "x", "arxiv", text, None, None, "u")


def test_assess_grounded_real_backend():
    doc = _doc("In our experiments the model achieved a BLEU score of 41.8 on WMT 2014 En-De.")
    v = assess("the model achieved a BLEU score of 41.8 on WMT 2014 English-to-German",
               doc, backend=DartmouthBackend(), model="qwen.qwen3.5-122b")
    assert v.status == "grounded"


def test_assess_contradicted_real_backend():
    doc = _doc("In our experiments the model achieved a BLEU score of 41.8 on WMT 2014 En-De.")
    v = assess("the model achieved a BLEU score of 99.9 on WMT 2014 English-to-German",
               doc, backend=DartmouthBackend(), model="qwen.qwen3.5-122b")
    assert v.status in ("contradicted", "not_found")
