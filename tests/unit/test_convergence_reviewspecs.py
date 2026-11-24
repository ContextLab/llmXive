

def test_the_strict_bar_partitions_the_registry_exactly():
    """The strict bar migrated from a hard-coded stage-name set in `engine.py` to a
    `ReviewSpec` field. This is the guard that the migration lost nothing AND added
    nothing: exactly the JUDGMENT stages are strict, every authoring stage stays lenient.

    Both directions matter. Losing a strict stage would let a gate report acceptance for
    a panel that did not accept; making an authoring stage strict would re-introduce
    spec-023 defect #24, where kicking back on prose polish burned PROJ-552's panels to
    their cap.
    """
    from llmxive.convergence.reviewspecs import _build_registry

    strict = {stage for stage, spec in _build_registry().items() if spec.strict_acceptance}
    assert strict == {"research_review", "paper_review"}, (
        "the registry's strict set drifted from the judgment stages"
    )


def test_a_directly_built_spec_derives_its_bar_from_the_stage():
    """A spec built WITHOUT the argument must still get the right bar.

    This is the regression the migration introduced and this guards: moving the strict
    set out of `engine.py` silently dropped every directly-constructed judgment spec to
    the lenient bar, because nobody passes an argument that did not exist before. The
    tri-state default (`None` -> derive from the stage) is what closes it.
    """
    from llmxive.convergence.types import ReviewSpec

    def _spec(stage, **kw):
        return ReviewSpec(stage=stage, artifacts=[], reviewers=[], reviser=None,
                          kickback_routing={}, overflow_goal="g", **kw)

    assert _spec("research_review").strict_acceptance is True
    assert _spec("paper_review").strict_acceptance is True
    # authoring stages stay lenient — spec-023 defect #24
    assert _spec("clarified").strict_acceptance is False
    assert _spec("some_future_stage").strict_acceptance is False
    # and an EXPLICIT value always wins over the derivation
    assert _spec("research_review", strict_acceptance=False).strict_acceptance is False
    assert _spec("clarified", strict_acceptance=True).strict_acceptance is True
