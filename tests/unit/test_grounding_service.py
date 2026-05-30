# tests/unit/test_grounding_service.py
from llmxive.grounding.entailment import Verdict
from llmxive.grounding.full_text import RetrievedDoc
from llmxive.grounding.service import decide


def _doc(full=None, abstract=None, tier="s2"):
    return RetrievedDoc("doi", "10.x/y", tier, full, abstract, None, "u")


def test_decide_grounded_full_text_ok():
    ok, _reason = decide(_doc(full="body"), Verdict("grounded"))
    assert ok is True


def test_decide_contradicted_flags():
    ok, reason = decide(_doc(full="body"), Verdict("contradicted", note="says 9988"))
    assert ok is False and "contradict" in reason.lower()


def test_decide_not_found_full_text_flags():
    ok, _reason = decide(_doc(full="body"), Verdict("not_found"))
    assert ok is False


def test_decide_abstract_only_grounded_ok():
    ok, _reason = decide(_doc(abstract="abs", tier="abstract"), Verdict("grounded"))
    assert ok is True


def test_decide_abstract_only_not_found_flags():
    ok, reason = decide(_doc(abstract="abs", tier="abstract"), Verdict("not_found"))
    assert ok is False and "abstract" in reason.lower()
