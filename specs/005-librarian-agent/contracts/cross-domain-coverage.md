# Contract: Cross-domain coverage test (US4)

**Test module**: `tests/phase2/test_librarian_cross_domain.py`
**Diagnostic-report section**: `§ 4 Cross-domain coverage`
**Schema base**: data-model.md E8 (CrossDomainTestRow)

## Coverage requirement

Test the librarian on **at least one project per default field** from `agents/registry.yaml`'s field pool: biology, chemistry, computer science, materials science, neuroscience, physics, psychology, statistics. Total: **8 fields, 8 test rows**.

## Test substrate selection

Per research.md Decision 8: for each field, pick the **most-recently-brainstormed project** in that field from the existing cron-driven cohort under `projects/`. Selection algorithm:

```python
for field in DEFAULT_FIELDS:
    candidates = [
        p for p in projects
        if p.state.field == field and p.state.current_stage in {"brainstormed", "flesh_out_complete", "validated", "project_initialized"}
    ]
    test_project = max(candidates, key=lambda p: p.state.created_at)
```

Selected project IDs are recorded in the diagnostic report's § 4 table (one row per field).

## Sample search term derivation

For each test project, the sample search term is derived from the project's `idea/<slug>.md` `## Research question` section's first sentence (or, if the section is absent, the project's title). Algorithm:

```python
research_question = parse_section(idea_md, "Research question")
if research_question:
    sample_term = first_sentence(research_question)
else:
    sample_term = project.title
sample_term = truncate_to_500_chars(sample_term)
```

The sample term is then passed to the librarian as `LibrarianAgent.invoke(term=sample_term, context={"field": field, "idea_body_excerpt": ..., "target_n": 5})`.

## Per-field test invocation contract

For each field's test invocation:

1. Spawn the librarian against Semantic Scholar + arXiv with the sample term.
2. Capture the resulting `LibrarianResult` JSON (per `librarian-json-output.md` contract).
3. Record a CrossDomainTestRow in the report's § 4 table:

| Field | Project ID | Sample term | Outcome | Verified count | Expansion fired? | PDF sample size | Manual audit verdict | Notes |
|-|-|-|-|-|-|-|-|-|

4. Run a manual audit on **one randomly-selected verified citation** from the result. Audit checks:
   - URL resolves (visit + visually confirm a real paper)
   - Title matches the librarian's claim
   - Summary is a faithful (not hallucinated) overview
5. Record the audit verdict (`pass` / `fail` / `mixed`) in the row.

## Per-field acceptance verdict

A field's test passes iff:
- LibrarianResult.outcome ∈ {`success`, `success_after_expansion`} (NOT `failed`; `exhausted` allowed but flagged as MIXED)
- `len(verified_citations) >= 1` (any verified citation is sufficient — fields with thin English-language coverage may not hit target_n=5)
- Manual audit verdict on the sampled citation is `pass`

A field's test fails iff:
- LibrarianResult.outcome == `failed` for any non-transient reason
- Manual audit verdict is `fail` (e.g., URL doesn't resolve, title mismatch, summary clearly hallucinated)

A `mixed` verdict (e.g., 4 of 5 verified citations pass audit, 1 doesn't) is recorded with details + a defect entry per the spec's defects-table convention.

## Aggregate acceptance criterion

Per SC-001 + SC-002:
- ALL 8 fields must complete (no `failed` outcomes)
- ≥80% of returned citations across all 8 invocations pass the three verification checks (manual audit on the random samples corroborates this)

## Defect-categorization for cross-domain failures

| Symptom | Severity | Likely cause | Resolution path |
|-|-|-|-|
| Field's test outcome is `failed` (backend totally unreachable) | n/a (transient) | Semantic Scholar / arXiv outage | Re-run; not a librarian defect |
| Field's test outcome is `failed` (all candidates fail verification) | HIGH | Likely a librarian verification logic regression | Patch verify.py; bump prompt_version per FR-020 |
| Manual audit verdict is `fail` | CRITICAL | Hallucination or wrong-paper resolution | Patch summary-grounding logic OR title-overlap threshold; bump prompt_version |
| Manual audit verdict is `mixed` (4/5 pass) | MEDIUM | One citation slipped through verification | Document which one + why; consider tightening thresholds |
| Field's outcome is `exhausted` | LOW (informational) | Field has thin English literature for the project's question (legitimate) | Note in report; no fix required |

## Test run-cost expectation

| Item | Cost |
|-|-|
| 8 librarian invocations × 1 initial query each | 8 Semantic Scholar + 8 arXiv API calls |
| Worst case: 8 × expansion (~5 fired, generously) × 20 expanded queries | +200 backend calls |
| 8 × ~3 PDF samples per invocation | ~24 PDF downloads (~5MB each, 5-30s each) |
| 8 × LLM brainstorm call (when expansion fires) | ~5 Dartmouth Chat calls |
| Total wall-clock | ~30-60 minutes single-threaded; ~10 min with parallel test invocations |
| API cost | $0 (all backends free) |

## Quoted in the diagnostic report

§ 4 of the diagnostic report quotes:

1. The 8-row CrossDomainTestRow table verbatim (with the manual-audit verdict for each).
2. A short prose summary of any field that produced a `failed` or `mixed` verdict.
3. The aggregate verification-pass rate (across all 8 fields × N citations).
4. Defect rows in § 5's table for any `mixed`/`fail` verdicts.
