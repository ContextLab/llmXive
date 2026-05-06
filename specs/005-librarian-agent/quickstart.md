# Quickstart: Spec 005 Implementation Runbook

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-05-06

This runbook is the maintainer's hands-on guide for landing the librarian agent + Phase 1 re-validation. Inspired by spec 004's quickstart; tighter because the librarian's substrate (Semantic Scholar + arXiv + the existing pipeline) is well-understood.

## Step 0 — Preflight

```bash
# Repo is on the spec-005 feature branch.
git branch --show-current  # → 008-librarian-agent

# Confirm carry-forward substrate exists (from spec 004 merge to main).
ls projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/
ls projects/PROJ-262-predicting-molecular-dipole-moments-with/

# Confirm Dartmouth Chat credentials.
python -c "from llmxive.credentials import load_dartmouth_key; print('ok' if load_dartmouth_key(prompt_if_missing=False) else 'missing')"

# Confirm Semantic Scholar + arXiv reachable.
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1" | head -c 200
curl -s "http://export.arxiv.org/api/query?id_list=1706.03762" | head -c 200

# Confirm git working tree is clean (or only modified .omc/cron files).
git status --short
```

If any preflight fails, stop and resolve before proceeding.

## Step 1 — Build the librarian sub-package (US1 core)

### 1a. Create the directory layout

```bash
mkdir -p src/llmxive/librarian tests/phase2 state/librarian-cache
touch src/llmxive/librarian/__init__.py tests/phase2/__init__.py
```

### 1b. Implement search clients (`src/llmxive/librarian/search.py`)

- `SemanticScholarClient` — wraps `https://api.semanticscholar.org/graph/v1/paper/search`. Token-bucket rate limiter (replenishment 2/sec, burst 5). Returns `Candidate` records.
- `ArxivClient` — wraps `http://export.arxiv.org/api/query`. 3-second sleep between calls. Returns `Candidate` records.
- Shared retry logic (3 attempts on 429/5xx with exponential backoff) per existing router pattern.

### 1c. Implement verify helper (`src/llmxive/librarian/verify.py`)

- `verify_citation(candidate, *, fetch_pdf: bool = False) -> VerifiedCitation | VerificationFailure`
- Three sequential checks: URL resolves → title-token-overlap ≥0.7 → summary grounded
- Returns full `verification_log` with all sub-scores

### 1d. Implement PDF sample (`src/llmxive/librarian/pdf_sample.py`)

- `sample_for_pdf_audit(verified, sample_rate=0.10) -> list[VerifiedCitation]` — picks ceiling(rate * len) with min 1
- `extract_pdf_text(url) -> str` — uses `pypdf`; first 1000 words; handles paywall + corrupt-PDF + size-limit gracefully
- Updates each sampled citation's `summary_grounded_pdf` flag + `pdf_sample_score`

### 1e. Implement cache (`src/llmxive/librarian/cache.py`)

- `cache_key(term_normalized, field, target_n, prompt_version) -> str` — sha256 hex
- `get(key) -> LibrarianResult | None` — checks TTL; returns None on miss/expired
- `set(key, result)` — writes JSON to `state/librarian-cache/<sha256>.json`

### 1f. Implement expansion (`src/llmxive/librarian/expand.py`)

- `expand_terms(original_term, context, n=20) -> list[(int, str)]` — calls Dartmouth Chat with the librarian expansion prompt; returns ranked list
- `iterate_until_target(original_term, expanded, target_n) -> ExpansionResult` — queries each backend per term, accumulates verified citations, terminates on target_n OR exhaustion

### 1g. Implement the agent class (`src/llmxive/agents/librarian.py`)

- Subclass `Agent` (from `llmxive.agents.base`). Wires the sub-package together.
- `build_messages` — emits the brainstorm prompt for the LLM step (only used when expansion fires; the rest is mechanical)
- `handle_response` — orchestrates: cache check → search → verify → maybe expand → PDF sample → cache write → return JSON

### 1h. Add the prompt (`agents/prompts/librarian.md`)

Initial v1.0.0 with two sections:
1. **Expansion brainstorm prompt** — what the LLM sees when expansion fires
2. **(Optional)** other LLM-driven sub-tasks if any emerge

### 1i. Register in `agents/registry.yaml`

```yaml
- name: librarian
  purpose: Canonical literature-search-and-citation-verification. Replaces lit_search + reference_validator's primary-source comparison + citation_resolver Stage-1.
  inputs: [idea]
  outputs: [idea]
  prompt_path: agents/prompts/librarian.md
  prompt_version: 1.0.0
  default_backend: dartmouth
  fallback_backends: [huggingface, local]
  default_model: qwen.qwen3.5-122b
  wall_clock_budget_seconds: 600
  paid_opt_in: false
```

### 1j. Commit

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/librarian/ src/llmxive/agents/librarian.py agents/prompts/librarian.md agents/registry.yaml
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "spec-005: librarian sub-package + agent class + prompt v1.0.0 (US1, FR-001 FR-010, #107)"
```

## Step 2 — Tests for the librarian (US1 verification)

### 2a. Unit tests (`tests/phase2/test_librarian_*.py`)

Per the contracts:

- `test_librarian_search.py` — Semantic Scholar + arXiv real-API tests (known-good queries return ≥1 candidate; rate limiter enforces token bucket)
- `test_librarian_verify.py` — three checks against fixtures (known-good arXiv passes; known-bad URL fails; DOI-redirect-resolves works)
- `test_librarian_expand.py` — given a thin-result term + context, the LLM-brainstormed list contains ≥10 alternatives ranked by relevance
- `test_librarian_pdf_sample.py` — random sampling + pypdf extraction on Vaswani paper
- `test_librarian_cache.py` — TTL respect + sha256 keying + invalidation on prompt-version bump

### 2b. Run

```bash
pytest tests/phase2/test_librarian_search.py -v
pytest tests/phase2/test_librarian_verify.py -v
pytest tests/phase2/test_librarian_expand.py -v
pytest tests/phase2/test_librarian_pdf_sample.py -v
pytest tests/phase2/test_librarian_cache.py -v
```

All must pass before continuing. Commit:

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add tests/phase2/
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "spec-005: librarian unit tests (5 modules, real Semantic Scholar+arXiv) (US1, FR-001, #107)"
```

## Step 3 — Rewire flesh_out + reference_validator + citation_resolver (FR-007/008/009)

### 3a. Rewire flesh_out

Edit `src/llmxive/agents/idea_lifecycle.py:173-177`:

```python
# Before:
from agents.tools.lit_search import lit_search
papers = lit_search(query=query, max_results=8)

# After:
from llmxive.agents.librarian import LibrarianAgent
from llmxive.agents import registry as registry_loader
librarian_entry = registry_loader.get("librarian")
librarian = LibrarianAgent(librarian_entry)
result = librarian.invoke(term=query, context={...}, idea_md_path=...)
papers = result.verified_citations
```

### 3b. Rewire reference_validator

Replace the inline title-token-overlap + URL-resolves logic with a call to `from llmxive.librarian.verify import verify_citation`.

### 3c. Deprecate `agents/tools/lit_search.py`

Add a banner at the top:

```python
"""DEPRECATED post spec 005 (2026-05-06).

This module has been replaced by the librarian agent at
`src/llmxive/agents/librarian.py`. Callers should import:

    from llmxive.agents.librarian import LibrarianAgent

This file is preserved for backwards compatibility. The `lit_search`
function below now delegates to the librarian.
"""

def lit_search(query, max_results=8):
    """DEPRECATED: thin wrapper around LibrarianAgent. Kept for tests
    that still import `from agents.tools.lit_search import lit_search`."""
    from llmxive.agents.librarian import LibrarianAgent
    from llmxive.agents import registry as registry_loader
    entry = registry_loader.get("librarian")
    librarian = LibrarianAgent(entry)
    result = librarian.invoke(term=query, context={"target_n": max_results})
    return result.verified_citations
```

### 3d. Convert `tests/phase1/citation_resolver.py` to a thin shim

The `extract_citations` and `resolve_one` functions stay (signature unchanged) but their bodies now delegate to `llmxive.librarian.verify`.

### 3e. Run regression

```bash
pytest tests/phase1/  # spec 003 + 004 tests
pytest tests/phase2/  # spec 005 librarian tests
```

All must pass. Commit:

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add src/llmxive/agents/idea_lifecycle.py src/llmxive/agents/reference_validator.py agents/tools/lit_search.py tests/phase1/citation_resolver.py
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "spec-005: rewire flesh_out + reference_validator + citation_resolver to librarian (FR-007/008/009, #107)"
```

## Step 4 — Cross-domain coverage tests (US4)

Implement `tests/phase2/test_librarian_cross_domain.py` per `contracts/cross-domain-coverage.md`:

```python
# For each of 8 default fields:
#   1. Pick most-recently-brainstormed project in that field
#   2. Derive sample_term from project's idea/<slug>.md
#   3. Invoke librarian; capture LibrarianResult
#   4. Manual audit on 1 random verified citation
#   5. Append CrossDomainTestRow to test artifacts

DEFAULT_FIELDS = ["biology", "chemistry", "computer science", "materials science",
                  "neuroscience", "physics", "psychology", "statistics"]

@pytest.mark.parametrize("field", DEFAULT_FIELDS)
def test_librarian_field_coverage(field):
    project = pick_most_recent_brainstormed_in_field(field)
    sample_term = derive_sample_term(project)
    librarian = LibrarianAgent(registry.get("librarian"))
    result = librarian.invoke(term=sample_term, context={"field": field, ...})
    assert result.outcome in {"success", "success_after_expansion", "exhausted"}
    assert len(result.verified_citations) >= 1  # any verification = pass
    # Manual audit: spot-check 1 random verified citation (recorded in test output)
```

Run:

```bash
pytest tests/phase2/test_librarian_cross_domain.py -v
```

Capture the 8 CrossDomainTestRow records into `/tmp/cross-domain-results.md` for the diagnostic report.

Commit:

```bash
PRE_COMMIT_ALLOW_NO_CONFIG=1 git add tests/phase2/test_librarian_cross_domain.py state/librarian-cache/
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "spec-005: cross-domain coverage tests (8 fields × 1 project each) (US4, FR-012, #107)"
```

## Step 5 — Phase 1 re-validation (US3)

For each canonical (PROJ-261, PROJ-262), follow the per-canonical procedure in `contracts/revalidation-runs.md`:

1. **Capture prior state** (state YAML + idea.md to `/tmp/$SIBLING-prior.*`)
2. **Roll state back** to `flesh_out_in_progress` (commit)
3. **Re-run flesh_out** with librarian-backed lit search (`python -m llmxive run --project $SIBLING --max-tasks 1`)
4. **Run validator** on the re-fleshed canonical (`python -m llmxive run ...` again)
5. **Run project_initializer** (skip-if-exists guard makes this a no-op for the constitution)
6. **Compute revalidation result** (RevalidationResult record per data-model.md E9)

Commit each step separately with messages referencing US3 + #107.

## Step 6 — Diagnostic report (US5)

Author `notes/2026-05-NN-spec-005-librarian-diagnostic.md` (date stamp filled at completion). Mirror spec 003 + 004 8-section structure:

1. Inputs (cross-domain test substrate + canonicals)
2. Librarian invocations (every test invocation quoted verbatim)
3. Outputs (LibrarianResult JSON per invocation; truncated >100 lines)
4. Cross-domain coverage table (8 rows from US4)
5. Phase 1 re-validation (RevalidationResult per canonical + side-by-side diff)
6. Defects table
7. Per-issue acceptance summary
8. Carry-forward decision

Commit + push.

## Step 7 — Carry-forward manifest (US6)

Author `specs/005-librarian-agent/carry-forward.yaml` per data-model.md E10:

```yaml
spec: "005-librarian-agent"
generated_at: <ISO-8601 UTC>
final_commit: <git SHA>
projects:
  - project_id: PROJ-261-evaluating-the-impact-of-code-duplicatio
    final_state: project_initialized
    final_commit: <SHA>
    audited_iter_id: PROJ-261-evaluating-the-impact-of-code-duplicatio
    agents_run:
      - { name: brainstorm, iterations: 1, ... }
      - { name: flesh_out, iterations: 2, ... }  # +1 for spec-005 re-run
      - { name: research_question_validator, iterations: 2, ... }  # +1
      - { name: project_initializer, iterations: 3, ... }  # spec-004 + spec-005 no-ops
      - { name: librarian, iterations: 1, final_run_log_path: state/run-log/2026-05/<run_id>.jsonl }
    revalidation_judgment: verified | shifted_legitimate | shifted_regressed
    justification: |
      ...
  - project_id: PROJ-262-...
    ...
```

Commit + push.

## Step 8 — Polish + close

Same pattern as spec 004:

```bash
# Full regression
pytest tests/phase1/ tests/phase2/

# Lint touched files
ruff check src/llmxive/librarian/ src/llmxive/agents/librarian.py tests/phase2/

# Tick agent sub-issue checkboxes (none specifically for librarian — it's a NEW agent; create issue post-spec)
# Post PR

gh pr create --base main --head 008-librarian-agent --title "Spec 005: librarian agent + Phase 1 re-validation" --body-file <(cat <<'EOF'
## Summary
...
EOF
)
```

## Estimated wall-clock

| Step | Duration |
|-|-|
| 0 (preflight) | 5 min |
| 1 (build librarian sub-package — 9 sub-steps) | ~3 days |
| 2 (unit tests) | ~1 day |
| 3 (rewire flesh_out + reference_validator + citation_resolver) | ~0.5 day |
| 4 (cross-domain tests, 8 fields × ~5 min each + 8 manual audits) | ~2 hours |
| 5 (Phase 1 re-validation, 2 canonicals × ~10 min each + judgment) | ~30 min |
| 6 (diagnostic report) | ~3 hours |
| 7 (carry-forward manifest) | ~30 min |
| 8 (polish + PR) | ~1 hour |

**Total**: ~5 days on the happy path. Up to ~1 week with iteration cycles.

## Common failure modes

- **Semantic Scholar 429s**: token bucket should prevent; if hit, sleep + retry per backend retry policy.
- **arXiv API rate limit**: 3-second inter-call sleep; if violated, `requests.get` returns 503; retry.
- **PDF download paywalled**: `summary_grounded_pdf: null`; citation still verified at abstract level.
- **DOI redirects to wrong paper**: title-token-overlap < 0.7 → verification failure with `reason: "title_mismatch"`.
- **Validator regresses on a re-fleshed canonical**: `judgment: "shifted_regressed"` → CRITICAL defect; investigate before US6.
- **Search trail subsection missing**: librarian wiring defect; check that flesh_out passes idea.md path.
