# Spec 005 outline — Librarian agent + Phase 1 re-validation

**Status**: Outline only (handoff note for next session). Not yet a Spec Kit feature.
**Date**: 2026-05-06
**Triggered by**: user observation in spec 004 that (a) literature-search behavior is duplicated across `flesh_out`, `reference_validator`, and the spec-003 citation resolver; (b) the gap-analysis fallback when no relevant papers are found should instead trigger a multi-step expanded search; (c) Single-Source-of-Truth Constitutional Principle I says these duplicated implementations should be consolidated.
**Predecessors**: spec 003 (Phase 1 testing) + spec 004 (Phase 2 testing)

## Goal

Build a `librarian` agent that consolidates literature search + citation verification into a single canonical implementation, then re-validate all Phase 1 agents that depend on lit search behavior.

## Scope (3 user stories, P1 each)

### US1 — `librarian` agent: validated literature search, single source of truth

A `librarian` agent that takes a search term (or list of terms) and returns a list of verified citations. The agent's contract:

**Input**: a search term plus optional context (project field, idea body, etc.).

**Output**: per citation:
- DOI / arXiv ID / HTTPS URL (the canonical pointer)
- bibliographic info (title, authors, venue, year)
- summary of content (1-3 sentences) grounded in the actual fetched content (not hallucinated)
- verification verdict: pointer resolves, content matches the bibliographic claim, summary is faithful

**Internals**:
1. **Web search** (Semantic Scholar API, arXiv API, Google Scholar via `scholarly`, etc.) for the term.
2. **Download** each candidate's PDF / HTML / abstract.
3. **Verify**: (a) URL/address resolves, (b) bibliographic info from search matches primary source, (c) summary derived from actual content (not the search snippet).
4. **Return** structured JSON.

Re-uses the spec-003 citation resolver pattern for verification (or extracts shared code into a utility).

### US2 — Multi-step expanded search when results are thin

When an initial search returns < N (default 5) verified citations, the librarian:

**Step 1**: brainstorms an expanded list of terms accommodating alternative naming, ranked by relevance to the originating query. The LLM is asked: "What are 10-20 alternative phrasings, related concepts, or sub-area terms that might surface relevant papers if the original search missed them?"

**Step 2**: iterates over those terms, performing at least 10 distinct searches, accumulating verified citations until ≥5 are found OR the term list is exhausted.

**Step 3**: returns the verified citations PLUS a record of which expanded terms were searched (for the log + the idea's `.md` file).

The agent updates:
- run-log entry with expanded terms used + per-term hit count
- the calling project's idea.md (if applicable) with a "Search trail" subsection naming the expanded terms.

### US3 — Re-validate Phase 1 agents under librarian-backed lit search

After the librarian agent is built, re-validate two Phase 1 agents whose behavior may shift:

**research_question_validator** — its 4-check audit (phenomenon-vs-method, circularity, triviality, narrowing) may rely indirectly on lit-search-driven evidence. Re-run the full Phase 1 pipeline (brainstorm → flesh_out → validator → project_initializer) on the carry-forward canonicals (PROJ-261-evaluating-, PROJ-262-predicting-) and confirm the validator's verdicts still hold.

**flesh_out** — its citation-fetching behavior was a primary trigger for spec 005. Re-run flesh_out on the canonicals; confirm:
- `idea.md` now includes a "Search trail" subsection per US2
- citations are now librarian-validated (not just regex-resolved)
- the previously-empty Literature gap analysis sections are now populated with real cited literature (the gap-analysis-as-feature path from spec 003 should only fire when the librarian's expanded search ALSO returns nothing — a much stricter trigger)

If validator or flesh_out's behavior on the canonicals materially changes, the spec 003 + spec 004 reports gain an addendum noting the shift and the new audit verdicts.

## Touch points

| File | Change |
|-|-|
| `src/llmxive/agents/librarian.py` | NEW — agent class |
| `agents/prompts/librarian.md` | NEW — prompt |
| `agents/registry.yaml` | NEW entry; existing `lit_search` tool → DEPRECATE or refactor |
| `src/llmxive/tools/lit_search.py` | refactor to call librarian, OR remove (callers go to librarian directly) |
| `src/llmxive/agents/flesh_out.py` (or its prompt) | change: call librarian instead of lit_search |
| `src/llmxive/agents/reference_validator.py` (or its prompt) | change: call librarian for verification step |
| `tests/phase1/citation_resolver.py` | refactor: re-export librarian's verification logic (or deprecate, since librarian subsumes it) |
| `tests/phase2/test_librarian.py` (NEW) | extensive tests covering many domains: every project we've brainstormed thus far (CS, chemistry, biology, physics, neuroscience, etc.) |
| `notes/2026-05-NN-spec-005-librarian-diagnostic.md` | NEW — diagnostic report mirroring spec 003 / spec 004 structure |

## Test substrate (US3 input)

The carry-forward projects from spec 004's manifest:
- PROJ-261-evaluating-the-impact-of-code-duplicatio (CS)
- PROJ-262-predicting-molecular-dipole-moments-with (chemistry)

Plus optional broader-domain coverage drawing from the larger pool of brainstormed projects in `projects/` (the cron-driven runs have produced ~40+ projects across all default fields). For US1 testing the librarian on diverse terms, sample one project per field.

## Open design questions for `/speckit-clarify`

1. **Web-search backend choice** — Semantic Scholar API + arXiv API only (free, no rate-limit issues for this scale)? Or also Google Scholar via `scholarly` (richer but rate-limited)? Or a real web-search service via DARTMOUTH_CHAT_API_KEY?
2. **Verification depth** — does "verify summary matches content" require downloading full PDFs (slow), or is the abstract enough? PDF gives more truth-grounding; abstract is faster.
3. **Caching** — librarian queries can be expensive; should results be cached on disk (e.g., keyed on `sha256(term)`)? If yes, where + how does cache invalidation work?
4. **Failure mode** — what does the librarian do if EVEN the expanded multi-step search finds <5 verified citations? Surface an explicit `librarian_inconclusive.yaml` sentinel; let the caller decide whether to gap-analyze, escalate to human, or fail.
5. **Re-validation scope of US3** — re-run Phase 1 from brainstorm forward, OR re-run only flesh_out + validator on the existing canonical idea bodies? The latter is cheaper but doesn't catch cascading shifts.

## Anticipated effort

- US1 (librarian implementation + tests): ~2-3 days (the verification protocol is the hardest part, especially with PDFs)
- US2 (expanded search): ~0.5 day given US1's substrate
- US3 (re-validation): ~1 day for flesh_out + validator on 2 canonicals
- **Total**: ~4-5 days

## Carry-forward to spec 006+

If spec 005 closes cleanly, the librarian becomes available to all paper-side agents (paper_writing, paper_implementer, reference_validator) and downstream phase-test specs (006-007 etc. — Phase 3-4 testing). This is the highest-leverage piece of infrastructure across the whole pipeline after the four Phase 1 agents.

## Suggested workflow

When the user is ready to start spec 005:

1. `/speckit-specify` with the bullet "build a librarian agent per `notes/2026-05-06-spec-005-librarian-outline.md`; re-validate flesh_out + research_question_validator on the carry-forward projects from spec 004"
2. `/speckit-clarify` — resolve the 5 open design questions above
3. `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze` → `/speckit-implement` (mirror spec 004's flow)

Will produce a separate PR. Spec 005's diagnostic report will mirror spec 003's structure.
