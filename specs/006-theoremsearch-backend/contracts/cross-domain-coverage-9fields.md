# Contract: cross-domain coverage — the `mathematics` parametrization (spec 006)

**Base contract**: `specs/005-librarian-agent/contracts/cross-domain-coverage.md` — the per-field librarian-invocation coverage test. **Unchanged** except: the field list grows from 8 to 9 (adds `mathematics`), and the test must record the new `math_classifier` audit field per result.

**Test module**: `tests/phase2/test_librarian_cross_domain.py`

## The change

```python
# BEFORE (spec 005):
DEFAULT_FIELDS = [
    "biology", "chemistry", "computer science", "materials science",
    "neuroscience", "physics", "psychology", "statistics",
]

# AFTER (spec 006):
DEFAULT_FIELDS = [
    "biology", "chemistry", "computer science", "materials science",
    "mathematics", "neuroscience", "physics", "psychology", "statistics",
]
```

(The same list also lives in `src/llmxive/cli.py` as `default_fields` — FR-A09 updates both. Consolidating them into one canonical constant is out of scope for this amendment; tracked as a hygiene follow-up in GitHub issue #116, to be done after #113 lands.)

The test is `@pytest.mark.parametrize("field", DEFAULT_FIELDS)` over `test_librarian_field_coverage(field)` — adding `"mathematics"` automatically gives it a `mathematics` case. **No new skip logic is needed**: the existing test already handles "no brainstormed project for this field" by skipping with a documented reason (`pytest.skip(f"no brainstormed project for field={field!r}")`) — so before the 5 seed math projects are brainstormed, the `mathematics` case skips cleanly; after, it runs against the most-recently-brainstormed math project.

## Per-field assertions (unchanged from spec 005, plus the new field)

For each field's invocation, the test asserts (same as spec 005):
- `outcome ∈ {"success", "success_after_expansion", "exhausted"}` — NOT `"failed"` (a `failed` outcome is a hard test failure unless it's a documented transient like a total-backend-outage).
- `len(verified_citations) >= 1`.
- Records a `CrossDomainTestRow` to `/tmp/cross-domain-results-<field>.json` (the existing diagnostic artifact).

**New for spec 006** — also assert/record per result:
- The result has a `math_classifier` key with shape `{"invoked": bool, "verdict": bool | null, "error": str | null}`.
- For `field == "mathematics"`: `math_classifier == {"invoked": false, "verdict": null, "error": null}` (TheoremSearch queried unconditionally; classifier not called).
- For the other 8 fields: `math_classifier["invoked"] is True` AND (`math_classifier["verdict"] in (True, False)` OR `math_classifier["error"] is not None`) — i.e. the classifier was consulted and either gave a verdict or failed (a fail is tolerated, not a test failure).
- Optionally: extend `CrossDomainTestRow` with `theoremsearch_hit_count` (count of `verified_citations` whose `verification_log.backend == "theoremsearch"`) — a diagnostic-only field; decided at /speckit-tasks.

## Acceptance (maps to SC-A05, SC-A07, SC-A08)

- `DEFAULT_FIELDS` has 9 entries including `"mathematics"` (SC-A05, also enforced via `cli.py`'s `default_fields`).
- Running the `mathematics` parametrization: passes (outcome non-`failed`, ≥1 verified citation) if ≥1 math project is brainstormed, OR skips with a documented reason if not — never a hard fail (SC-A07).
- Running all 9 parametrizations under the bumped `librarian_prompt_version` (1.6.0): the 8 pre-existing fields still pass (no regression — SC-A08); the cross-domain run is the standard post-prompt-bump regression check, same as every prior librarian fix-up.
- The PROJ-261 + PROJ-262 re-validation (separate from this test, run via the existing re-validation procedure) still produces `judgment: verified` for both under 1.6.0 (SC-A08).

## Note on cost / runtime

Spec-005 fix-up #5 raised the librarian's wall-clock soft target to 1800s/invocation and the full 8-field cross-domain run took ~2.5h. Adding a 9th field (`mathematics`, which always queries TheoremSearch + does the arXiv-resolve round-trips) adds roughly one more invocation's worth — call it ~3h for the 9-field run. The math-classifier adds at most one LLM call per non-math invocation (cached per-project; first run pays it, re-runs don't). This is acceptable for a CI/manual regression suite that already runs in hours; the soft target is not enforced.
