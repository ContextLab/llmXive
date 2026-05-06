# Feature Specification: Librarian Agent (canonical literature search + citation verification) + Phase 1 re-validation

**Feature Branch**: `008-librarian-agent` *(spec dir is `specs/005-librarian-agent/` — branch number diverges from spec number per `/speckit-specify` allowance because the git-feature hook counts branches across the repo, not spec dirs; same convention as specs 003 + 004)*
**Created**: 2026-05-06
**Status**: Draft
**Input**: User description: "build a 'librarian' agent per the design outlined in `notes/2026-05-06-spec-005-librarian-outline.md` … consolidates the duplicated lit-search behavior currently scattered across `flesh_out`, `reference_validator`, and the spec-003 citation resolver (Constitutional Principle I — single source of truth) … verifies that the URL/address resolves, the bibliographic info matches the primary source, and the summary is faithful to the actual fetched content (not hallucinated) … multi-step expanded search when fewer than 5 verified citations are found … re-validate `research_question_validator` and `flesh_out` on the spec-004 carry-forward canonicals."

## Context (carried from spec 004)

This spec is a continuation of spec 004 (Phase 2 testing, merged via PR #109 / commit `a00b01e`). Spec 004 named two carry-forward canonicals — PROJ-261-evaluating-the-impact-of-code-duplicatio (CS) and PROJ-262-predicting-molecular-dipole-moments-with (chemistry) — both at `current_stage: project_initialized` on `main`.

Spec 004's diagnostic surfaced a structural concern beyond Phase 2's scope: literature-search-and-verification logic is duplicated across (a) `flesh_out`'s `lit_search` tool, (b) `reference_validator`'s primary-source-comparison logic, and (c) the spec-003 `tests/phase1/citation_resolver.py` Stage-1 mechanical resolver. Per the parent constitution's Principle I (Single Source of Truth), these should consolidate into one canonical implementation.

A second, related defect surfaced during the Phase 1 carry-forward: when `flesh_out`'s initial lit search returned no on-topic results (e.g., PROJ-261's clone-density-vs-LLM-perplexity question yielded only one off-topic hit on Semantic Scholar), the agent fell back to a "literature gap analysis" path with weak grounding — listing search terms attempted but not exhaustively expanding the query space. This spec promotes that fallback into a structured multi-step expansion: brainstorm 10-20 alternative phrasings, iterate over them, accumulate verified citations until ≥5 are found OR the term list is exhausted.

After the librarian is built, **Phase 1 must be re-validated** because `flesh_out` and `research_question_validator` both consume lit-search output. If the librarian materially changes that output's shape or quality, the Phase 1 carry-forward verdict from specs 003-004 may need to be re-affirmed (or re-examined).

## Clarifications

### Session 2026-05-06

- Q: Web-search backend choice → A: Semantic Scholar API + arXiv API only. Both free, public, academically focused (no SEO noise); excellent STEM coverage. Avoids Google Scholar / `scholarly` TOS fragility and the Dartmouth-web-search-endpoint dependency. Starts narrow; future spec can expand if needed.
- Q: Verification depth — PDF or abstract → A: Adaptive — abstract-only for bulk verification; ≥10% PDF sample per librarian invocation for summary-grounding audit. Catches worst-case hallucinations without paying 5-30s/citation PDF cost on every verification. Sample is randomly drawn from the returned verified citations; PDF-checked subset receives a stricter `summary_grounded_pdf: bool` flag in the JSON output.
- Q: Expansion-exhausted failure mode → A: Return the partial list with `outcome: "exhausted"`; caller (typically flesh_out) decides next action. Matches fail-fast philosophy + the spec-003 "gap-analysis-as-feature" pattern. Librarian does NOT unilaterally escalate to `human_input_needed` (too aggressive — librarian can't judge whether thin literature is a project-killer or a feature) and does NOT fall through to gap-analysis-as-feature internally (couples concerns the spec keeps separate).
- Q: Per-invocation wall-clock budget → A: 600s (10 min). Covers the worst-case path of 1 initial search + 20-term brainstorm (1 LLM call) + 20 expanded searches + 5 PDF downloads + abstract verifications + retry margin. Matches `flesh_out`'s budget (the most frequent caller).

**Defaults applied without blocking clarification** (raise via `/speckit-clarify` if any need to change):
- **Caching strategy**: results cached on disk under `state/librarian-cache/<sha256>.json`, keyed on `sha256(normalized search term)`. Cache TTL: 30 days for arXiv hits, 7 days for HTTP HEAD verifications, 90 days for DOI bibliographic info. Cache invalidation: explicit `--no-cache` flag + automatic on TTL expiry.
- **Re-validation scope of US3**: re-run `flesh_out` and `research_question_validator` only (NOT brainstorm) on the existing canonical idea bodies. The carry-forward projects' brainstormed seeds remain authoritative; spec 005 is testing whether better lit search changes the downstream verdict.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Librarian agent: canonical search + verification (Priority: P1)

A pipeline maintainer (or any agent that needs literature) invokes the `librarian` agent with a search term plus optional context (project field, idea body excerpt). The librarian: (a) issues a real web search against one or more configured backends, (b) collects candidate citations (DOI / arXiv ID / HTTPS URL), (c) downloads each candidate's primary source, (d) verifies the URL/address resolves AND the search-result-claimed bibliographic info matches the primary source AND the summary the librarian generates is faithful to the actual fetched content (not hallucinated), and (e) returns structured JSON with the verified citations. Any citation that fails any of the three verification checks is excluded from the result set, with the failure reason logged.

**Why this priority**: This is the core capability. Every other story (US2 expanded search, US3 re-validation) builds on this. Without it, the spec accomplishes nothing.

**Independent Test**: Can be fully tested by invoking the librarian with a known-good term ("attention mechanisms transformers") and asserting that the returned JSON contains ≥1 verified citation whose DOI/arXiv ID/URL resolves to a real paper, whose title-token-overlap with the bibliographic claim is ≥0.7 (per the existing `CITATION_TITLE_OVERLAP_THRESHOLD`), and whose summary matches the abstract or first 500 words of the primary source. Test against a known-bad term ("xyzzy quantum unicorn protocol") and assert empty result with documented "no candidates found" reason.

**Acceptance Scenarios**:

1. **Given** a known-good search term in any default field, **When** the librarian is invoked, **Then** at least one verified citation is returned with DOI/arXiv/URL + bibliographic info + summary, AND the URL resolves AND title-token-overlap ≥0.7 with the primary source AND the summary matches the primary source's content.
2. **Given** a known-bad term that no real paper addresses, **When** the librarian is invoked, **Then** the result is an empty verified-citations list AND a `reason: "no candidates passed verification"` field is populated AND a structured log of which candidates were considered + why each was excluded is returned.
3. **Given** any agent in the existing pipeline (`flesh_out`, `reference_validator`, the spec-003 citation resolver) that previously used its own lit-search logic, **When** that agent is rewired to call the librarian, **Then** behavior is preserved or improved — no regression in the existing test suite.

---

### User Story 2 - Multi-step expanded search when initial results are thin (Priority: P1)

When the librarian's initial search for the user-provided term returns fewer than **5** verified citations, it triggers a multi-step expansion:

1. **Step 1 — term brainstorming**: the librarian uses the LLM (Dartmouth Chat by default) to generate 10-20 alternative phrasings, related concepts, sub-area terms, or domain-adjacent variants of the original query, ranked by approximate relevance to the originating context (project field + idea-body excerpt).
2. **Step 2 — iterative search**: the librarian iterates over the expanded list, performing **at least 10** distinct searches (deduplicated against the original term), accumulating verified citations across all queries.
3. **Step 3 — termination**: the loop terminates when ≥5 verified citations have been accumulated OR the expanded term list is exhausted.
4. **Step 4 — log + idea-body update**: the librarian records the expanded terms used + per-term hit count to the run-log JSONL entry. If the calling project's `idea/<slug>.md` is provided, the librarian appends (or updates) a `## Search trail` subsection naming each expanded term + the verified citations it surfaced.

**Why this priority**: The original gap-analysis fallback in spec 003 was too weak — it listed terms attempted but didn't exhaustively expand. Multi-step expansion catches real papers that initial-term search misses due to alternative naming, sub-areas, or adjacent fields. Without this, the librarian's value-add over the existing one-shot tools is marginal.

**Independent Test**: Can be tested by invoking the librarian with a deliberately-narrow term that returns <5 hits ("ablation density LLM perplexity"), confirming that the multi-step expansion fires, that ≥10 distinct searches are performed, and that the final verified-citations list contains 5 (if the field has the literature) OR explicitly fewer-than-5 with `reason: "expanded search exhausted at <N> verified citations"`. The Search trail subsection in the calling project's idea.md must list each expanded term + per-term hit count.

**Acceptance Scenarios**:

1. **Given** a search term that returns fewer than 5 verified citations on initial query, **When** the librarian runs, **Then** the multi-step expansion fires AND ≥10 distinct queries are issued AND the final list contains either 5 verified citations OR an explicit "expanded search exhausted" reason.
2. **Given** a calling project's idea.md path, **When** the librarian's multi-step expansion completes, **Then** a `## Search trail` subsection is written (or updated) naming each expanded term + hit count + the verified citations attributed to that term.
3. **Given** the run-log JSONL is captured, **When** an expansion has fired, **Then** the entry contains `expanded_terms: [<term>, …]` and `per_term_hit_count: {<term>: N, …}` fields populated.

---

### User Story 3 - Re-validate Phase 1 (`flesh_out` + `research_question_validator`) on the spec-004 carry-forward canonicals (Priority: P1)

After US1 + US2 are implemented, the maintainer re-runs `flesh_out` and `research_question_validator` on the spec-004 carry-forward canonicals (PROJ-261 + PROJ-262) under the new librarian-backed lit search. Per the iteration-convention change committed in spec 004, this happens **in place** on the canonicals (not via sibling spawning); each iteration is a separate git commit on the feature branch.

The maintainer captures: (a) the librarian's full output (verified citations + Search trail + run-log entry) for each canonical's flesh_out re-run; (b) the new flesh_out output's `idea/<slug>.md` (with the new Search trail + librarian-verified citations), compared via `git diff` to the prior version; (c) the new validator verdict (validated / validator_revise / validator_rejected), compared to spec 003's verdict on the same project. Any verdict shift is itself a finding — either the librarian surfaced new evidence that legitimately reshapes the question (good), or the validator's logic is sensitive to lit-search output in a way that needs documenting (also good — that's what testing surfaces).

**Why this priority**: Phase 1 verdicts in specs 003-004 implicitly assumed the existing lit-search behavior. If the librarian materially changes that, the carry-forward decision needs re-affirming (or revising). Without this re-validation, spec 005's claim of "better lit search across the pipeline" is unproven on the projects where it most matters.

**Independent Test**: Can be tested per project by re-running `flesh_out` then `research_question_validator` on each canonical, capturing the resulting `idea/<slug>.md` + run-log entries + new state YAML, and rendering an independent verdict on whether the validator's output is at least as well-grounded as the prior verdict. Discrepancies are recorded in the diagnostic report.

**Acceptance Scenarios**:

1. **Given** spec-004's canonical PROJ-261 + PROJ-262 at `current_stage: project_initialized`, **When** `flesh_out` is re-run on each (forcing the project back to `flesh_out_in_progress` via a deliberate state edit) under the new librarian-backed lit search, **Then** the re-run completes against the real backend, the librarian-verified citations are visible in the output `idea/<slug>.md`, the Search trail subsection lists the expanded terms used (or, if no expansion was needed, a single-term subsection), and the run-log records the librarian's behavior.
2. **Given** the re-fleshed canonicals, **When** `research_question_validator` is invoked, **Then** the verdict is captured (validated / validator_revise / validator_rejected) AND compared to spec 003's verdict on the same projects. Any shift is documented in the diagnostic report's defects table OR explicitly accepted as legitimate evidence-driven re-evaluation.
3. **Given** all three Phase 1 agents (flesh_out, validator, project_initializer) complete on each canonical, **When** the carry-forward decision is re-rendered, **Then** the resulting state matches the spec-004 final state OR the spec-005 carry-forward manifest documents the change.

---

### User Story 4 - Cross-domain test coverage for the librarian (Priority: P1)

Before US3 (re-validation) runs, the librarian is tested on at least one project per default field from `agents/registry.yaml`'s field pool: biology, chemistry, computer science, materials science, neuroscience, physics, psychology, statistics. For each test project, a sample search term is derived from the project's `idea/<slug>.md` (typically the research question itself or a key methodology phrase), the librarian is invoked, and the result set is audited: (a) verified citations are real (URLs resolve, titles match), (b) summaries are faithful (spot-check 1-2 against the primary source), (c) failure modes (paywalls, redirects, 401/403, dead URLs) are handled gracefully without crashing the agent.

**Why this priority**: The existing pipeline projects span 8 fields; the librarian must work in all of them. A regression in any field breaks the broader pipeline.

**Independent Test**: Can be tested by enumerating one project per field (existing brainstormed projects are sufficient — the cron-driven cohort already covers all fields), invoking the librarian on each, and rendering a per-field pass/fail verdict in the diagnostic report's "Cross-domain coverage" section.

**Acceptance Scenarios**:

1. **Given** at least 8 projects covering each default field, **When** the librarian is invoked on a sample search term per project, **Then** each invocation completes without crashing AND returns either ≥1 verified citation OR a documented "no candidates found" reason AND the report tabulates per-field result counts + verification pass rates.
2. **Given** the cross-domain audit runs, **When** a field surfaces a failure mode unique to that domain (e.g., chemistry paywall patterns, biology dataset-citation conventions), **Then** the failure is logged as a defect with severity AND either fixed in this PR OR deferred to a follow-up issue with rationale.

---

### User Story 5 - Verbatim diagnostic report (Priority: P1)

A single Markdown file at `notes/2026-05-NN-spec-005-librarian-diagnostic.md` (date filled in at end of work) captures: every librarian invocation's input + output + verification log; every cross-domain test project + verdict; every Phase 1 re-validation result with `git diff` against the prior idea body; every defect (CRITICAL / HIGH / MEDIUM / LOW with file:line + status). Mirrors spec 003 + spec 004's report structure.

**Why this priority**: The diagnostic report IS the evidence that the librarian works. Without it, all the testing is invisible to future readers.

**Independent Test**: Reading the report top-to-bottom, every claim ("librarian works on chemistry", "PROJ-262's validator verdict held under librarian-backed re-run") traces to a quoted artifact (run-log JSONL, idea-body diff, librarian JSON output).

**Acceptance Scenarios**:

1. **Given** US1-US4 complete, **When** the diagnostic report is generated, **Then** every librarian invocation made during testing is quoted with its input, output, and verification log; every cross-domain field has a verdict row; every re-validation produces a side-by-side diff vs the prior idea body.
2. **Given** the report identifies any defect, **When** the defect is summarized in § 4, **Then** it has severity + file:line + status (`Fixed in <SHA>` / `Deferred to issue #<N>` / `Accepted (not addressed) — rationale: …`).

---

### User Story 6 - Carry-forward decision (Priority: P2)

After US3 + US5 complete, the maintainer formally selects which projects carry forward to spec 006 (Phase 3 — Specifier + Clarifier testing). If the Phase 1 re-validation in US3 confirmed PROJ-261 + PROJ-262's spec-004 verdicts, both canonicals carry forward unchanged. If US3 surfaced a verdict shift on either, the affected canonical's status is documented and a decision is made (carry forward anyway with the new verdict, OR fall back to the spec-004 state, OR open a follow-up issue).

The selection is recorded in `specs/005-librarian-agent/carry-forward.yaml` with the now-familiar schema (extended from spec 004's): project_id, final_state, final_commit, agents_run (now including `librarian: iterations: N`), justification.

**Why this priority**: Same as spec-004's US6 — without this gate, spec 006 has to re-discover the substrate. P2 because it's a thin bridge, not a self-contained capability.

**Independent Test**: Reading the manifest + confirming each named project ID exists at `current_stage: project_initialized` (or whatever final state US3 produced), each named final_commit resolves on the feature branch, the librarian's run-log entries are present.

**Acceptance Scenarios**:

1. **Given** US3 completes with verdicts captured, **When** `carry-forward.yaml` is written, **Then** it names 1-2 project IDs with metadata: `final_state`, `final_commit`, `agents_run` (including `librarian: iterations: N` and re-run iteration counts for `flesh_out` + `research_question_validator`), `justification`.
2. **Given** the manifest is written, **When** the spec is closed, **Then** the matching tracker checkboxes in #107 (or the corresponding agent-tracking issues) are advanced.

---

### Edge Cases

- **Web-search backend down or rate-limited**: the librarian must distinguish backend-side failure (TransientBackendError → retry per existing router policy) from agent-side defect (mishandled response → CRITICAL defect in the report).
- **Candidate citation resolves but content is paywalled**: per spec-003's pattern (401/403 + redirect history → ambiguous, not unreachable), the librarian classifies these as `verification_partial` — bibliographic info verified, summary degraded to abstract-only with a flag in the JSON output.
- **DOI redirects to a different paper than the bibliographic claim**: this is the most insidious failure mode — the URL resolves but the content doesn't match. The librarian MUST detect this via title-token-overlap < threshold AND mark the citation excluded with a `reason: "title mismatch"` log entry.
- **arXiv API returns multiple matches for an ID prefix**: the librarian narrows to the exact match by ID, not partial. If multiple papers share an ID prefix (rare but possible for legacy arXiv IDs), the librarian flags ambiguous and declines to verify.
- **Summary hallucination**: the librarian's summary MUST be derived from the actual fetched content (PDF or abstract), not the LLM's recall. Verification step compares librarian-generated summary against fetched content via cosine similarity OR token-overlap; below threshold ⇒ excluded with `reason: "summary not grounded"`.
- **Multi-step expansion infinite loop**: if every expanded term also returns <5 hits, the loop has a hard cap of N expanded terms (default 20). Termination after the cap with `reason: "expanded search exhausted"` is the documented outcome — not infinite retry.
- **Cross-domain term collision**: a search term that's ambiguous across fields (e.g., "attention" in CS vs neuroscience) MUST be disambiguated by passing the calling project's field as context to the search backend. The librarian's prompt explicitly receives field context and uses it to filter.
- **Cache poisoning**: cache entries store the full verified-citation JSON; if a cached entry was written before a verification bug was fixed, stale results may surface. Mitigation: cache invalidation on librarian prompt-version bumps (per the spec-003 semver policy).
- **Phase 1 re-validation flips a verdict**: if `research_question_validator` outputs `validator_rejected` on a canonical that previously passed, the carry-forward state must be honestly documented — even if it means downgrading PROJ-261 or PROJ-262's status. Don't paper over the regression.
- **flesh_out's idea body diverges materially after re-run**: if the new librarian-backed flesh_out produces an idea body with a different research question (e.g., the Search trail's expanded terms suggested a more focused question), the diagnostic report MUST quote the diff and call out the change explicitly.
- **Run-log gap on librarian crash**: same as spec 003/004 — the run-log entry MUST still be appended with `outcome: failure` + populated `failure_reason` even when the agent crashes mid-search.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement a `librarian` agent that consolidates literature-search-and-verification logic per Constitutional Principle I, replacing the duplicated implementations in `flesh_out`'s `lit_search` tool, `reference_validator`'s primary-source comparison, and the spec-003 `tests/phase1/citation_resolver.py` mechanical resolver. Per Q1 clarification, the librarian uses **Semantic Scholar API + arXiv API only** as its initial-search backends — both free, public, academically focused, and adequate for STEM coverage. Google Scholar / Dartmouth-web-search are explicitly out of scope for this spec; future specs may expand the backend list if these two prove insufficient.

  **Semantic Scholar API key required**: the unauthenticated free tier rate-limits the `/graph/v1/paper/search` endpoint to the point where it returns 429 on the first call (verified empirically during preflight). The librarian therefore requires an authenticated key obtained for free via the Semantic Scholar partner-portal form (linked in the 429 response: https://www.semanticscholar.org/product/api#api-key-form). Key resolution uses the same pattern as `DARTMOUTH_CHAT_API_KEY`: env var `SEMANTIC_SCHOLAR_API_KEY` first, then `~/.config/llmxive/credentials.toml` field `semantic_scholar_api_key`. Loaded by `llmxive.credentials.load_semantic_scholar_key()`. arXiv API requires no key.
- **FR-002**: The librarian MUST accept inputs `{search_term: str, context: {field: str, idea_body_excerpt: str | None, target_n: int = 5} | None}` and return a JSON structure listing verified citations with `{doi_or_arxiv_or_url, bibliographic_info: {title, authors, venue, year}, summary, verification_log}`.
- **FR-003**: For each candidate citation, the librarian MUST verify (a) the URL/address resolves (via real HTTP HEAD/GET, not metadata-only), (b) the bibliographic info matches the primary source via title-token-overlap ≥ `CITATION_TITLE_OVERLAP_THRESHOLD` (default 0.7, inheriting from the parent constitution), (c) the summary the librarian generates is faithful to the actual fetched content via summary-grounding score ≥ `SUMMARY_GROUNDING_THRESHOLD` (default 0.5; introduced by this spec; same threshold pattern as title-token-overlap). Per Q2 clarification, summary-grounding uses an **adaptive depth policy**: bulk verification reads the abstract only (fast, ~1-2s/citation); a randomly-sampled subset of **≥10% of the returned verified citations** (minimum 1 sample per invocation) ALSO has its full PDF downloaded and re-verified for summary grounding (using the same 0.5 threshold). Each citation in the JSON output carries a `summary_grounded_pdf: bool` flag indicating whether it was in the PDF sample. Any candidate failing any check is excluded with the failure reason logged.
- **FR-004**: When the initial search returns fewer than 5 verified citations, the librarian MUST trigger a multi-step expanded search per US2 (10-20 LLM-brainstormed alternative terms ranked by relevance to the context, ≥10 distinct queries iterated, accumulation until ≥5 verified citations OR term list exhausted, hard cap of 20 expanded terms). Per Q3 clarification, when the expansion exhausts without reaching 5 verified citations, the librarian MUST return the partial list with `outcome: "exhausted"` and let the caller decide next action — it MUST NOT escalate to `human_input_needed.yaml` and MUST NOT fall through to internal gap-analysis-as-feature (those are caller-side decisions).
- **FR-005**: If a calling project's `idea/<slug>.md` path is provided, the librarian MUST append (or update if already present) a `## Search trail` subsection naming each expanded term + per-term verified-citation count + the citations themselves.
- **FR-006**: The librarian MUST emit a run-log JSONL entry containing `agent_name: "librarian"`, `expanded_terms: [...]`, `per_term_hit_count: {...}`, `verified_citation_count`, `outcome` (`success` / `failed` / `partial` / `exhausted`), `failure_reason` if applicable.
- **FR-007**: System MUST rewire `flesh_out`'s lit-search-driven prompt path to call the librarian instead of the existing `lit_search` tool. Behavior change: the new flesh_out output's "Related work" or "Literature gap analysis" section is now librarian-verified.
- **FR-008**: System MUST rewire `reference_validator`'s verification logic to call the librarian's per-citation verify step. Behavior change: validator no longer duplicates HTTP HEAD / DOI resolution code; it consumes the librarian's verdict.
- **FR-009**: System MUST update `tests/phase1/citation_resolver.py` to either (a) delegate to the librarian's verify step and become a thin wrapper, or (b) be deprecated with a banner and a redirect (the librarian is now the canonical resolver). Spec 003's existing tests MUST still pass.
- **FR-010**: System MUST register the librarian in `agents/registry.yaml` with default backend Dartmouth, fallback HuggingFace + local, default model selected appropriately (the librarian's brainstorming step uses an LLM; the verification step does not — pick a model balancing quality + cost). Initial `prompt_version: 1.0.0`. Per Q4 clarification, `wall_clock_budget_seconds: 600` (10 min) — covers worst-case expansion + 10% PDF sample + retry margin; matches `flesh_out`'s budget.
- **FR-011**: System MUST cache librarian results on disk under `state/librarian-cache/<sha256_of_term>.json` with TTL per the defaults documented in Clarifications (30d arXiv, 7d HTTP HEAD, 90d DOI). `--no-cache` flag bypasses cache.
- **FR-012**: System MUST test the librarian on at least one project per default field (biology, chemistry, computer science, materials science, neuroscience, physics, psychology, statistics) drawn from existing brainstormed projects. Each test produces a verdict row in the diagnostic report's cross-domain coverage table.
- **FR-013**: System MUST re-run `flesh_out` and `research_question_validator` in place on the spec-004 carry-forward canonicals (PROJ-261-evaluating-... and PROJ-262-predicting-...) under librarian-backed lit search. The re-run uses the in-place iteration convention from spec 004 (no sibling-iter directories); each step is a git commit on the feature branch.
- **FR-014**: System MUST capture the diagnostic findings in `notes/2026-05-NN-spec-005-librarian-diagnostic.md` (date stamp filled at completion), mirroring spec 003 + spec 004's 8-section structure, with verbatim quotes of librarian outputs + idea-body diffs + run-log entries + defect tables.
- **FR-015**: For each CRITICAL or HIGH defect identified, system MUST either (a) apply a fix in this PR with an "After fix" report section quoting corrected behavior, or (b) defer to a follow-up GitHub issue with rationale.
- **FR-016**: System MUST never advance state silently when the librarian fails — empty result with no documented reason, partial results without the partial flag, or run-log entries missing populated `failure_reason` are CRITICAL defects (Constitution Principle V).
- **FR-017**: System MUST commit all real-project artifacts produced (re-fleshed canonicals' idea/<slug>.md, librarian-cache entries that document the reproducible search trail, run-log entries, state YAMLs).
- **FR-018**: System MUST formally select the carry-forward projects to spec 006 (Phase 3) and record the selection in `specs/005-librarian-agent/carry-forward.yaml` per US6.
- **FR-019**: All fixes applied as part of this work MUST land as separate commits with messages referencing the parent issue (#107 tracking) and the report section that motivated the fix.
- **FR-020**: Iteration on the librarian's prompt at `agents/prompts/librarian.md`, the registry entry, or the implementation MUST follow the prompt-version semver policy from spec 003: MAJOR for output-contract-breaking, MINOR for behavior, PATCH for prose; bump in the same commit as the patch.
- **FR-021**: System MUST cap fix-and-re-run iterations per agent at 5 cycles (per spec 003 / 004 FR-005). Hitting the cap forces a deferral decision.
- **FR-022**: Any agent that needs literature search going forward (paper-side agents like `paper_writing`, `paper_implementer`, plus any future research-side agents) MUST call the librarian directly. New duplicative implementations are forbidden by Principle I.
- **FR-023**: The librarian's verification logic MUST be **deterministic** for a given input + cache state — re-running the same query must produce the same JSON output (modulo the `verification_log` timestamp).

### Key Entities *(include if feature involves data)*

- **Search term**: a short string supplied by the caller (or LLM-generated during US2 expansion). Identity: the term itself (deduplicated via case-insensitive normalization).
- **Verified citation**: a record `{primary_pointer (DOI / arXiv ID / HTTPS URL), bibliographic_info (title, authors, venue, year), summary, verification_log}` where every claim is verified against the primary source. Failure on any check ⇒ excluded.
- **Search trail**: a structured record of the expansion process: original term + ranked list of expanded alternatives + per-term hit count + cumulative verified-citation list. Persisted in (a) the run-log JSONL entry and (b) the calling project's `idea/<slug>.md` `## Search trail` subsection.
- **Librarian cache entry**: a file at `state/librarian-cache/<sha256>.json` containing the full verified-citations JSON for a normalized search term, with TTL metadata per FR-011.
- **Cross-domain test result**: a row in the diagnostic report's per-field table listing `{field, project_id, sample_term, verified_count, pass_rate, defects}`.
- **Re-validation result**: a comparison record per canonical: `{project_id, prior_verdict (from spec 003/004), new_verdict, idea_body_diff, validator_run_log, judgment ("verified" | "shifted" | "regressed")}`.
- **Carry-forward manifest**: `specs/005-librarian-agent/carry-forward.yaml` extending spec 004's schema with `librarian: {iterations: N, final_run_log_path: ...}` per project.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The `librarian` agent runs end-to-end against the real Dartmouth Chat backend AND real web-search backend(s) on at least 8 distinct projects covering all default fields. Zero mock/fake calls.
- **SC-002**: For every test invocation, ≥80% of returned citations pass the three verification checks (URL resolves AND title-token-overlap ≥0.7 AND summary grounded). The other ≤20% are EXCLUDED with documented reason — no false positives in the result set.
- **SC-003**: When initial search returns <5 verified citations, the multi-step expansion fires AND ≥10 distinct queries are issued AND the final list contains either 5 verified citations OR documented "exhausted" reason. Verified empirically on at least 3 of the 8 cross-domain test projects.
- **SC-004**: The diagnostic report quotes every librarian invocation made during testing (verbatim input + output + verification log) — no invocation omitted.
- **SC-005**: Both spec-004 carry-forward canonicals (PROJ-261, PROJ-262) are re-fleshed in place under librarian-backed lit search. Each new `idea/<slug>.md` contains a `## Search trail` subsection AND librarian-verified citations replace the prior citations.
- **SC-006**: `research_question_validator` is re-run on each re-fleshed canonical. The new verdict is compared to spec 003's verdict, AND any shift is documented in the diagnostic report's defects table OR explicitly accepted as evidence-driven re-evaluation.
- **SC-007**: At least one deliberate failure mode (web-search backend unreachable / DOI redirects to wrong paper / candidate paywalled) is induced and the resulting run-log entry verifies that failure paths are loud per Constitution Principle V.
- **SC-008**: For every CRITICAL or HIGH defect identified, an "After fix" report section quotes the corrected behavior OR a follow-up issue link is recorded — no defect silently dropped.
- **SC-009**: Iteration is bounded per agent (≤5 fix-and-re-run cycles) so the spec converges in finite time; if the cap is hit the residual defect is explicitly deferred.
- **SC-010**: The carry-forward manifest is concrete enough that spec 006 can read it and pick up the named projects + librarian-verified substrate without re-discovering anything.
- **SC-011**: Existing test suites (`tests/phase1/test_citation_resolver.py`, `tests/phase1/test_idempotency.py`, `tests/phase1/test_project_id_lock.py`, `tests/real_call/`) continue to pass after the librarian is wired into `flesh_out` + `reference_validator` + the citation resolver. No regression in any spec-003 or spec-004 test.
- **SC-012**: The librarian's verification is deterministic for a fixed cache state — re-invoking with the same term + context produces identical citation lists (modulo timestamp).

## Assumptions

- The Dartmouth Chat backend (`DARTMOUTH_CHAT_API_KEY` in `~/.config/llmxive/credentials.toml`) is reachable; if not, the test surfaces that as a transient failure and stops, no mock fallback.
- A Semantic Scholar API key (`SEMANTIC_SCHOLAR_API_KEY` env var OR `semantic_scholar_api_key` field in the same credentials file) is installed before the librarian's real-search tests run. Free key obtained via the form linked in Semantic Scholar's 429 response. Tests that require the key are marked `@pytest.mark.skipif(not has_semantic_scholar_key, reason="...")` so they pass-or-skip cleanly when the key is missing; CI fails the spec only when the key IS available and the tests still fail.
- The carry-forward manifest from spec 004 (`specs/004-phase2-project-bootstrap-testing/carry-forward.yaml`) is authoritative; PROJ-261 + PROJ-262 remain valid carry-forward inputs.
- The cron-driven brainstormed cohort already in `projects/` covers all 8 default fields with at least 1 project each. (Verified during preflight; if a field is missing, US4 picks the closest neighbor and notes the gap.)
- Existing project numbering is unique post the spec-004 PR-#109 fix (Q1B file lock + Q3A duplicate rename). This spec inherits that fix.
- The new in-place iteration convention from spec 004 applies — no `-iterN` sibling directories. Each iteration is a git commit on the feature branch.
- Real web-search calls cost time but not money on the maintainer's home connection. Cache mitigates repeat runs.
- Librarian cache files (`state/librarian-cache/*.json`) are committed to git so the diagnostic is reproducible from any checkout.
- The diagnostic report file path is `notes/2026-05-NN-spec-005-librarian-diagnostic.md`, with the actual date filled in at completion.
- The carry-forward manifest path is `specs/005-librarian-agent/carry-forward.yaml`; spec 006 (Phase 3 testing) and beyond reference it.
- A maintainer (human in the loop) renders the final per-citation judgment on a sample (≥10% of returned citations) — automated verification handles the bulk, but spot-checks are the trust signal.

## Open design questions (for `/speckit-clarify`)

The 5 design questions from the outline note. Three highest-impact are flagged as `[NEEDS CLARIFICATION]` markers per spec-kit policy; the other two have reasonable defaults applied and are noted in Clarifications:

1. ~~Web-search backend choice~~ → **Resolved Q1**: Semantic Scholar API + arXiv API only (see Clarifications section).
2. ~~Verification depth — PDF or abstract~~ → **Resolved Q2**: Adaptive — abstract for bulk, ≥10% PDF sample for grounding audit (see Clarifications section).
3. ~~Expansion-exhausted failure mode~~ → **Resolved Q3**: Return partial list + `outcome: "exhausted"`; caller decides (see Clarifications section).
