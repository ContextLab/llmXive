from llmxive.grounding.entailment import _parse_verdict, locate_passages


def test_locate_passages_finds_number_window():
    text = ("Intro paragraph. " * 50 +
            "We found a correlation of r=0.42 between crossing number and braid index. " +
            "Later text. " * 50)
    passages = locate_passages(text, claim="correlation between crossing number and braid index",
                               number="0.42")
    assert any("r=0.42" in p for p in passages)
    assert len(passages) <= 5


def test_locate_passages_no_number_uses_overlap():
    text = "Alpha beta. The braid index predicts complexity strongly. Gamma delta."
    passages = locate_passages(text, claim="braid index predicts complexity", number=None)
    assert any("braid index predicts complexity" in p for p in passages)


def test_parse_verdict_grounded():
    v = _parse_verdict('```yaml\nstatus: grounded\nevidence: "r=0.42 ..."\nnote: ok\n```')
    assert v.status == "grounded" and "0.42" in v.evidence


def test_parse_verdict_contradicted_and_unknown_defaults_not_found():
    assert _parse_verdict("status: contradicted\nevidence: x\nnote: y").status == "contradicted"
    assert _parse_verdict("garbage").status == "not_found"  # unparseable -> not_found
