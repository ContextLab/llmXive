# Quickstart — spec 006 (TheoremSearch backend + mathematics field)

A runbook for implementing + verifying this amendment. Steps are ordered; `/speckit-tasks` will turn them into a checklist.

## 0. Preflight (fail-fast checks)

```bash
# TheoremSearch reachable?
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://api.theoremsearch.com/search \
  -H "Content-Type: application/json" -d '{"query":"composition series","limit":1}'   # expect 200

# Dartmouth Chat creds present (for the math-classifier LLM call)?
source .venv/bin/activate
python -c "from llmxive.credentials import load_dartmouth_key; assert load_dartmouth_key(prompt_if_missing=False), 'no Dartmouth key'"

# Semantic Scholar key present (for the existing backend)?
python -c "from llmxive.credentials import load_semantic_scholar_key; assert load_semantic_scholar_key(prompt_if_missing=False), 'no SS key'"

# librarian-cache dir writable?
test -w state/librarian-cache/ || echo "WARN: state/librarian-cache not writable"
```

## 1. Add `mathematics` as the 9th default field (FR-A09)

- `src/llmxive/cli.py` — add `"mathematics"` to `default_fields` (line ~208-212; insert alphabetically: after `"materials science"`, before `"neuroscience"`).
- `tests/phase2/test_librarian_cross_domain.py` — add `"mathematics"` to `DEFAULT_FIELDS` (same alphabetical position).
- `agents/prompts/brainstorm.md` — add `mathematics` to the field-example list in the Inputs section (it's prose, not a hard enum: `e.g., \`biology\`, \`mathematics\`, \`materials-science\`, \`psychology\`, \`chemistry\``).
- *(Flagged, likely separate cleanup: the two copies of the field list — `cli.py` + the test — are a pre-existing duplication. Consolidating into one canonical constant is out of scope for this amendment but noted.)*

## 2. Brainstorm 5 seed math projects (FR-A10) — AFTER step 1

```bash
# (use whatever the project's brainstorm invocation is — e.g. via the CLI or run_one_step)
# Each must produce a project with field: mathematics.
# Verify:
grep -l 'field: mathematics' state/projects/PROJ-*.yaml | wc -l   # expect >= 5
```

## 3. Implement the TheoremSearch backend (FR-A01, FR-A02, FR-A05, FR-A06, FR-A07, FR-A08)

- NEW `src/llmxive/librarian/theoremsearch.py` — `TheoremSearchClient.search(term, *, limit=10) -> list[Candidate]` per `contracts/theoremsearch-client.md`: POST `/search`; for arXiv-sourced hits, strip the `vN` suffix, `arxiv_client.get_by_id(...)`, re-tag `backend="theoremsearch"`; skip non-arXiv; token-bucket rate limit (~2s); errors → `TransientBackendError`.
- NEW recorded fixture: `tests/phase2/fixtures/theoremsearch_search_response.json` (or inline in the test) — a real `/search` response with a mix of arXiv + ProofWiki hits, captured live (see notes on #111).

## 4. Implement the math-classifier (FR-A03, FR-A04)

- NEW `agents/prompts/math_classifier.md` — system+user prompt: *"You judge whether a research question is a pure-mathematics theorem/proof/formal-structure question (the kind where searching theorem statements helps). Reply `YES` or `NO` on the first line, then a one-sentence rationale."* + the question + idea excerpt in the user message.
- NEW `src/llmxive/librarian/math_classifier.py` — `classify(...) -> MathClassifierResult` + `is_math_theory_question(...) -> bool` per `contracts/math-classifier.md`: per-project verdict cache at `state/librarian-cache/math-classifier-verdicts.json` keyed by `f"{project_id}::{librarian_prompt_version}"`; fail-open to `False` with a loud stderr diagnostic on backend failure; don't cache error outcomes.

## 5. Wire into `LibrarianAgent.invoke()` (FR-A02, FR-A03, FR-A12 — schema; per data-model E-TS3/`contracts/librarian-json-output-delta.md`)

- Add `project_id: str | None = None` to `invoke()`'s signature.
- After the existing extracted-query search loop, before `_verify_each(candidates, query=term)`, add the math branch (see `research.md` D4 for the exact placement + pseudocode): `if field in ("mathematics", "statistics"): ts_hits = _theoremsearch_candidates(term, arxiv_client=arxiv_client); math_audit = {invoked:False,...}` / `elif (verdict, math_audit) := _maybe_math_question(...): ts_hits = ...` ; dedup `ts_hits` into `candidates` by `primary_pointer`.
- Add `math_classifier: dict[str, Any] = dataclasses.field(default_factory=dict)` to `LibrarianResult`; add `"math_classifier": self.math_classifier` to `to_dict()`; pass `math_classifier=math_audit` into the `LibrarianResult(...)` constructor (parallel to `relevance_judge=...`).
- `src/llmxive/agents/idea_lifecycle.py` (flesh_out) + `src/llmxive/agents/reference_validator.py` — pass `project_id=...` through to `librarian.invoke(...)`.

## 6. Bump the librarian prompt version (FR-A12) + update the registry comment (FR-A13)

- `agents/registry.yaml` — librarian entry: `prompt_version: 1.5.0` → `1.6.0`; update the entry comment to say "3 backends (Semantic Scholar + arXiv + TheoremSearch) + an LLM math-classifier for non-math fields."

## 7. Tests (FR-A02, FR-A04, FR-A11; SC-A01..A04, SC-A07, SC-A09)

```bash
source .venv/bin/activate
# Unit + parser tests (fast, no network):
python -m pytest tests/phase2/test_theoremsearch.py tests/phase2/test_math_classifier.py -v
# Real-call smokes (gated):
export LLMXIVE_REAL_TESTS=1
export DARTMOUTH_CHAT_API_KEY="$(python -c 'from llmxive.credentials import load_dartmouth_key; print(load_dartmouth_key(prompt_if_missing=False) or "")')"
python -m pytest tests/phase2/test_theoremsearch.py::test_real_api_smoke tests/phase2/test_math_classifier.py::test_real_llm_smoke -v
# Full Phase 2 regression (no cross-domain — that's the slow one):
python -m pytest tests/phase2/ -q --ignore=tests/phase2/test_librarian_cross_domain.py
# Lint:
ruff check src/llmxive/librarian/ src/llmxive/agents/librarian.py tests/phase2/
```

## 8. Cache wipe + cross-domain re-run (9 fields) + PROJ-261/262 re-validation (FR-A12; SC-A08)

```bash
# The 1.6.0 prompt bump invalidates the result cache — wipe it for a clean re-run:
rm -f state/librarian-cache/*.json   # (keeps the dir; the math-classifier-verdicts.json will be recreated)
# 9-field cross-domain (~3h):
export LLMXIVE_REAL_TESTS=1 ; export DARTMOUTH_CHAT_API_KEY="..." ; export SEMANTIC_SCHOLAR_API_KEY="..."
python -m pytest tests/phase2/test_librarian_cross_domain.py -v   # expect 9/9 PASS or mathematics-skipped
# PROJ-261 + PROJ-262 re-validation (the standard post-prompt-bump regression check — use the existing
# re-validation procedure from spec 005; expect judgment: verified for both):
python /path/to/rerun_both_revalidation.py   # (or the equivalent)
```

## 9. Manually inspect outputs (SC-A01, SC-A02, SC-A03)

- For a math project: confirm ≥1 verified citation has `verification_log.backend == "theoremsearch"` and a resolving arXiv ID; confirm the `math_classifier` audit object is `{"invoked": false, "verdict": null, "error": null}`.
- For a non-math project where the classifier should say "math" (e.g. a statistics project asking a concentration-inequality question): confirm `math_classifier == {"invoked": true, "verdict": true, "error": null}` and that TheoremSearch contributed candidates.
- For a non-math, non-theorem project (PROJ-261): confirm `math_classifier == {"invoked": true, "verdict": false, "error": null}` and zero `backend == "theoremsearch"` citations.
- Confirm no ProofWiki / Stacks-Project entries appear anywhere in `verified_citations`.

## 10. Doc updates (FR-A13)

- `notes/2026-05-07-spec-005-librarian-diagnostic.md` — append a "spec-006 amendment" section (3rd backend, math classifier, prompt 1.5.0→1.6.0, the `math_classifier` audit field, the 9-field re-run results, the PROJ-261/262 re-validation results).
- `specs/005-librarian-agent/spec.md` — the Q1 clarification line ("future spec may expand the backend list") gains "→ done in spec 006 (#113): added TheoremSearch."

## 11. Commit, push, PR (against `008-theoremsearch-backend` → `main`); update issue #113.
