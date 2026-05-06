# Data Model: Librarian Agent + Phase 1 Re-Validation

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-05-06

## Purpose

Concrete schema for every entity the spec produces, consumes, or transforms. Every cross-module API contract on the librarian sub-package roots in one of these entities; every contract file under `contracts/` references this document.

---

## E1. SearchTerm

A normalized query string passed to the librarian.

**Identity**: `case-insensitive-lowercase + collapsed-whitespace + stripped-punctuation` of the input. Two terms with identical normalized form share a cache key.

**Fields**:
- `raw` (str) — exactly as the caller supplied it
- `normalized` (str) — derived form used for cache keys + dedup

**Validation rules**:
- Non-empty after normalization
- ≤500 chars (rejecting pathologically long queries)

**Lifecycle**: ephemeral (no persisted form except inside cache file metadata).

---

## E2. Candidate

A pre-verification record returned from a search backend (Semantic Scholar or arXiv).

**Identity**: tuple `(backend_name, primary_pointer)` where primary_pointer is the first available of `{arxiv_id, doi, paper_id (Semantic Scholar's internal ID), url}`.

**Fields**:
- `backend` (enum: `"semantic_scholar"` | `"arxiv"`) — which backend returned this
- `primary_pointer` (str) — DOI / arXiv ID / HTTPS URL
- `claimed_title` (str) — title as the search backend reports it
- `claimed_authors` (list[str])
- `claimed_year` (int | None)
- `claimed_venue` (str | None)
- `claimed_abstract` (str | None) — search-result-claimed abstract (may be truncated or absent depending on backend)

**Relationships**: 1 Candidate → 0-1 VerifiedCitation (after verification). Failed verification = no VerifiedCitation, just a VerificationFailure log entry.

**Validation rules**:
- `primary_pointer` non-empty
- `backend` matches the validated enum

---

## E3. VerifiedCitation

The librarian's output unit: a Candidate that has passed all three verification checks.

**Identity**: same as Candidate (`(backend, primary_pointer)` tuple).

**Fields**:
- `primary_pointer` (str) — DOI / arXiv ID / HTTPS URL (stable canonical form)
- `bibliographic_info` (object):
  - `title` (str) — verified against primary source via title-token-overlap ≥0.7
  - `authors` (list[str])
  - `year` (int)
  - `venue` (str | None)
- `summary` (str) — librarian-generated, ≤500 words, faithful to fetched content
- `summary_grounded_pdf` (bool | None) — True if PDF-sample audit confirmed grounding; False if abstract-only verification passed but not PDF-sampled; None if PDF was inaccessible (paywall/corrupt) and only abstract-level verification ran
- `verification_log` (object):
  - `url_resolves` (bool)
  - `final_url` (str) — after redirect-follow
  - `redirect_chain` (list[str])
  - `http_status` (int)
  - `title_token_overlap_score` (float, 0-1)
  - `summary_grounding_score` (float, 0-1)
  - `pdf_sample_score` (float | None) — populated only when `summary_grounded_pdf` is True or False
  - `verified_at` (ISO-8601 UTC)

**Relationships**: belongs-to one LibrarianResult (E5). Identity invariant: a VerifiedCitation can appear in at most one LibrarianResult per cache key.

**Validation rules**:
- All three verification checks passed (URL resolves AND title-token-overlap ≥0.7 AND summary grounding ≥ threshold)
- `summary` derived from fetched content, NOT LLM recall
- `verification_log` populated for every check

---

## E4. VerificationFailure

A record for a Candidate that failed one or more verification checks.

**Identity**: same as Candidate.

**Fields**:
- `candidate` (Candidate) — the failed input
- `reason` (enum):
  - `"url_not_resolves"` — HTTP HEAD failed
  - `"title_mismatch"` — token-overlap < threshold
  - `"summary_not_grounded"` — summary doesn't match abstract
  - `"summary_not_grounded_pdf"` — PDF sample disagreed with abstract
  - `"paywall_partial"` — verified at abstract level but PDF inaccessible (this is RECORDED but the Candidate may still appear in VerifiedCitation with `summary_grounded_pdf: None`)
  - `"timeout"` — verification exceeded its per-citation deadline (60s)
- `details` (str) — human-readable specifics (failed score values, error messages, etc.)
- `failed_at` (ISO-8601 UTC)

**Relationships**: appears in LibrarianResult.verification_failures list. Sibling to VerifiedCitation (one or the other per Candidate, never both).

---

## E5. LibrarianResult

The complete output of a single librarian invocation.

**Storage**: returned as JSON to the caller. Cached at `state/librarian-cache/<sha256>.json`. Logged in run-log JSONL.

**Fields**:
- `term_input` (SearchTerm) — what was queried
- `context` (object):
  - `field` (str | None)
  - `idea_body_excerpt` (str | None) — first 1000 chars of calling project's idea body, if provided
  - `target_n` (int, default 5)
- `outcome` (enum):
  - `"success"` — ≥target_n verified citations found on initial search
  - `"success_after_expansion"` — ≥target_n found after multi-step expansion
  - `"exhausted"` — expansion ran but couldn't reach target_n; partial list returned
  - `"failed"` — backend completely unreachable / unrecoverable error
- `verified_citations` (list[VerifiedCitation]) — the actual results, ordered by relevance (Semantic Scholar's relevance score for that term)
- `verification_failures` (list[VerificationFailure]) — for transparency / debugging
- `expansion` (object | None) — populated only when expansion fired:
  - `original_term` (str)
  - `expanded_terms_ranked` (list[(str, int)]) — (term, rank) tuples
  - `per_term_hit_count` (dict[str, int]) — verified hits accumulated per expanded term
  - `total_queries_issued` (int) — total Semantic Scholar + arXiv calls
- `pdf_sample` (object):
  - `sampled_count` (int) — how many citations had PDF audit
  - `sample_size_target` (int) — ceiling(0.10 * verified_count) with min 1
  - `sampled_pointers` (list[str]) — primary_pointers of the sampled subset
- `started_at` / `ended_at` / `duration_seconds` — wall-clock timing
- `cache_status` (enum: `"miss"` | `"hit"` | `"refreshed_after_ttl"`)
- `librarian_prompt_version` (str) — for cache-invalidation matching

**Validation rules**:
- `outcome` consistent with `verified_citations` length: `success`/`success_after_expansion` ⇒ len ≥ target_n; `exhausted` ⇒ len < target_n; `failed` ⇒ len = 0
- `pdf_sample.sampled_count` ≥ ceiling(0.10 * len(verified_citations)) with min 1, when `len(verified_citations) > 0`
- `expansion` non-None iff outcome ∈ {`success_after_expansion`, `exhausted`}

---

## E6. SearchTrail

The Markdown subsection appended to a calling project's `idea/<slug>.md`. Documents the librarian's expanded terms + verified citations for that project's research question.

**Storage**: in-place inside `projects/<id>/idea/<slug>.md` as a `## Search trail` subsection.

**Format** (verbatim contract; see also `contracts/search-trail-md.md`):

```markdown
## Search trail

**Generated by**: librarian (prompt v<X.Y.Z>) on <ISO-8601 UTC>
**Outcome**: <success | success_after_expansion | exhausted>
**Original term**: <term>
**Verified citation count**: <N>

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | <original term> | <N> |
| 1 | <expanded term 1> | <N> |
| 2 | <expanded term 2> | <N> |
| ... | ... | ... |

### Verified citations

1. **<Title>** (<Year>). <Authors>. <Venue>. [DOI/arXiv/URL](<pointer>). PDF-sampled: <Yes | No | Inaccessible>.
2. ...
```

**Lifecycle**: written once on first librarian invocation for that project. On re-invocation (e.g., flesh_out re-running on the same project), the existing subsection is REPLACED (not appended) with the new trail. Old trails are visible via `git log -- <file>`.

**Validation rules**:
- Every row in "Search terms used" table corresponds to a key in `LibrarianResult.expansion.per_term_hit_count` (or just the original term if no expansion)
- "Verified citations" list contains exactly `len(LibrarianResult.verified_citations)` items
- DOI/arXiv/URL is the SAME `primary_pointer` from the corresponding VerifiedCitation

---

## E7. LibrarianCacheEntry

A persisted on-disk record of one LibrarianResult.

**Storage**: `state/librarian-cache/<sha256>.json`. Cache key = sha256 of `(normalized_term, field, target_n, librarian_prompt_version)`.

**Fields** (matches Decision 6 schema in research.md):
- `term_normalized` (str)
- `field` (str | None)
- `target_n` (int)
- `result` (LibrarianResult — full embedded JSON)
- `fetched_at` (ISO-8601 UTC)
- `ttls` (object):
  - `arxiv` (int seconds; default 2592000 = 30d)
  - `http_head` (int; default 604800 = 7d)
  - `doi_bib` (int; default 7776000 = 90d)
- `prompt_version` (str)

**Validation rules**:
- `result` is a complete LibrarianResult (not a partial/lazy reference)
- `fetched_at` ≤ now
- `prompt_version` matches the prompt version that produced `result`; on prompt bump, cache entries with old prompt_version are invalidated

**Lifecycle**: created on cache miss, read on cache hit, deleted on TTL expiry or explicit `--no-cache` flag.

---

## E8. CrossDomainTestRow

A single row in the diagnostic report's per-field cross-domain coverage table (US4).

**Storage**: ephemeral (in-memory during test execution); persisted into the diagnostic report's `§ 4 Cross-domain coverage` table.

**Fields**:
- `field` (str) — biology / chemistry / etc.
- `project_id` (str) — the test project sampled from the cron-cohort for that field
- `sample_term` (str) — derived from the project's research question
- `librarian_result_outcome` (enum) — same as LibrarianResult.outcome
- `verified_count` (int)
- `expansion_fired` (bool)
- `pdf_sample_size` (int)
- `manual_audit_verdict` (enum: `"pass"` | `"fail"` | `"mixed"`) — maintainer's spot-check verdict on a random verified citation from this row
- `notes` (str | None)

**Lifecycle**: 8 rows total (one per default field). Generated during US4 testing; quoted in the diagnostic report.

---

## E9. RevalidationResult

A comparison record per Phase 1 canonical (US3): how the new librarian-backed flesh_out + validator behave vs the spec-003/004 verdicts.

**Storage**: ephemeral; persisted into the diagnostic report's `§ 5 Phase 1 re-validation` section.

**Fields**:
- `project_id` (str) — PROJ-261-evaluating-... or PROJ-262-predicting-...
- `prior_state` (object) — captured from the canonical's `state/projects/<id>.yaml` BEFORE re-validation
  - `current_stage` (str)
  - `flesh_out_iteration_count` (int) — from history.jsonl
  - `validator_verdict` (str | None) — last known
- `new_state` (object) — captured AFTER re-validation
  - same shape
- `idea_body_diff` (str) — `git diff <prev-commit>:<idea path> <curr-commit>:<idea path>`
- `librarian_run_log_path` (str) — relative path to the run-log JSONL line for the librarian invocation that backed flesh_out's lit search
- `validator_run_log_path` (str) — analogous for the validator's run
- `judgment` (enum):
  - `"verified"` — new verdict matches prior; carry-forward unchanged
  - `"shifted_legitimate"` — new verdict differs but maintainer accepts the new evidence
  - `"shifted_regressed"` — new verdict differs in a way that's worse (defect; either fix or defer)
- `judgment_rationale` (str)

**Lifecycle**: 2 records total (one per carry-forward canonical). Generated during US3.

---

## E10. CarryForwardManifest

YAML file at `specs/005-librarian-agent/carry-forward.yaml` naming the projects spec 006 will operate on.

**Schema** (extends spec 004's schema with one new field):

```yaml
spec: "005-librarian-agent"
generated_at: <ISO-8601 UTC>
final_commit: <git SHA>
projects:
  - project_id: <id>
    final_state: <stage>
    final_commit: <SHA>
    audited_iter_id: <id>
    agents_run:
      - { name: brainstorm, iterations: <N>, final_iter_id: <id> }
      - { name: flesh_out, iterations: <N>, final_iter_id: <id> }
      - { name: research_question_validator, iterations: <N>, final_iter_id: <id> }
      - { name: project_initializer, iterations: <N>, final_iter_id: <id> }
      - { name: librarian, iterations: <N>, final_run_log_path: <path> }  # NEW field
    revalidation_judgment: <"verified" | "shifted_legitimate" | "shifted_regressed">  # NEW field
    justification: |
      <one paragraph covering: did flesh_out produce a Search trail subsection?
       did validator's verdict hold under librarian-backed lit search?
       any caveats for spec 006>
```

**Validation rules**:
- `agents_run` list MUST include `librarian` entry with at least one iteration
- `revalidation_judgment` corresponds to E9 RevalidationResult.judgment
- Every named `project_id` exists at the named `final_state` on the named `final_commit`

---

## Cross-entity invariants

- **Every VerifiedCitation in a LibrarianResult ⇒ exactly one row in the corresponding SearchTrail**.
- **Every cache hit on E7 ⇒ result.librarian_prompt_version == cache.prompt_version**.
- **Every cross-domain test (E8) on a project ⇒ a librarian invocation runs against that project's research question; the LibrarianResult is cached at `state/librarian-cache/<sha256>.json` and the row's verdict cites it**.
- **Every revalidation result (E9) for PROJ-26{1,2} ⇒ judgment is documented in E10's `revalidation_judgment` field**.
- **No VerifiedCitation in a LibrarianResult can fail the URL-resolves check** (URL-fail ⇒ VerificationFailure, never VerifiedCitation).

---

## Out of scope (deliberately not modeled)

- **Multi-language search**: the librarian queries in English only. Non-English papers may surface but won't be sub-ranked.
- **Author-disambiguation**: the librarian doesn't try to resolve same-name-different-person; it just records the search backend's claim.
- **Citation network analysis** (e.g., "papers that cite this paper"): out of scope; future spec if needed.
- **Per-citation full-text indexing**: librarian extracts first ~1000 words for grounding; deeper search needs a different tool.
- **OpenAlex / PubMed integration**: out of scope per Q1; future spec can extend the backend list.
