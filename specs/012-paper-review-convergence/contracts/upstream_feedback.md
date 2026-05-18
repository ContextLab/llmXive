# Contract: UpstreamFeedbackAnnotation (arxiv-intake guardrail)

## Purpose

For arxiv-intake papers (third-party submissions with a frozen `paper/source/`), the writing-revision and science-revision pipelines can't modify the manuscript. Instead, the consolidated action items are recorded as an annotation on the project. The project's final outcome is restricted to `PAPER_ACCEPTED` (with caveats noted) or `BRAINSTORMED` (rejection).

## Path

```
projects/<PROJ-ID>/upstream_feedback.yaml
```

## Schema

```yaml
project_id: PROJ-564-qwen-image-vae-2-0-technical-report
arxiv_id: "2510.12345"                                   # mirrored from paper/metadata.json
schema_version: 1
rounds:
  - round_number: 1
    triggered_at: '2026-05-17T14:01:45Z'
    verdict_class: writing                                # writing | science | fatal
    note: "First reviewer round; specialists agree the paper is solid but flagged 4 writing nits."
    action_items:
      - id: a3f1c9b2e5d8
        text: "Add explicit value for hyperparameter β_k in Section 4.1."
        severity: writing
      - id: 7b4d2e1c6f90
        text: "Discuss why the unified model surpasses single-domain experts."
        severity: writing
```

## Routing rules

For an arxiv-intake project:

1. **All specialists accept** (gate passes) → `PAPER_ACCEPTED` (no annotation needed).
2. **At least one writing OR science action item, no fatal** → write a new `Round` to `upstream_feedback.yaml`; transition to `PAPER_ACCEPTED` with caveats. The web dashboard surfaces the annotation on the project's card.
3. **At least one fatal action item** → write a new `Round` (verdict_class=fatal); transition to `BRAINSTORMED`.

The `paper_revision_in_progress` stage is NOT used for arxiv-intake projects — no speckit revision pipeline is kicked off.

## Detection rule

A project is arxiv-intake iff:

```python
def is_arxiv_intake(project_dir: Path) -> bool:
    return (project_dir / "paper" / "metadata.json").is_file() and not (
        project_dir / "paper" / "specs"
    ).is_dir()
```

(This matches the existing detection used by `paper_reviewer.py`.)

## Test commitments

- `tests/unit/test_upstream_feedback_writer.py` — round-trip schema validation.
- `tests/real_call/test_arxiv_intake_no_source_mutation.py` — drive an arxiv-intake fixture through a writing-class verdict; assert `paper/source/` is unchanged AND `upstream_feedback.yaml` contains the consolidated action items.

## Anti-patterns

- ❌ Attempting to call `revision_planner.run_revision_pipeline()` on an arxiv-intake project — the `revision_planner` MUST guard against this and raise `ArxivIntakeError` if called with such a project.
- ❌ Overwriting `upstream_feedback.yaml` on each round — rounds are append-only.
