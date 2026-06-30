# The research_review → research_accepted wall (2026-06-30)

## Goal
Get 10+ projects to "paper init" (`paper_drafting_init`). Flow:
`research_complete → research_review →(advancement)→ research_accepted
→(paper_initializer)→ paper_drafting_init`. At session start **0 projects had
EVER crossed research_review → research_accepted** (810 projects; 5 at
research_complete, 5 at research_review, 0 past).

## Root causes found (all are GENERAL, not per-project)

### 1. Reviewer reasoning-budget hang → coverage stuck at 3/7  [PRIMARY]
`base.Agent.run` called `chat_with_fallback` with NO `max_tokens` → the router's
**131072 GENERATION** default. A verdict is a SHORT reasoning output (~9.7K
measured); with a 128K budget a reasoning model reasons past the wall-clock
deadline and HANGS. The hang surface scales with prompt size, so the **large-prompt
artifact reviewers** (code_quality / data_quality / filesystem_hygiene /
implementation_correctness — they read code+data+48KB docs+tree) flap in CI while
the small-prompt prose reviewers (creativity / idea_quality / completeness) squeak
by. PROJ-552 sat at 3/7 from 06-15..06-30. With <7/7 current verdicts,
`advancement.evaluate` returns unchanged (neither accept nor revise) → nothing
advances. Reviewers run fine in isolation (~20s), which hid it.
**Fix (355c5d384):** `base.Agent.chat_max_tokens` (None=generation for generative
agents); Research/PaperReviewerAgent pin it to `REASONING_MAX_TOKENS` (32768) — the
same bound the convergence LLMReviewer already had. SSoT.

### 2. Two-tier exhaustion doom loop  [PRIMARY]
Even at 7/7, the 4 artifact reviewers vote `minor_revision` (writing severity:
file >200 lines, duplicate docs, log consolidation) → not unanimous accept →
revision spec → revise → re-review → SAME nits → ... at the round cap (3) it routed
to `RESEARCH_FULL_REVISION → in_progress → redo the SAME analysis → same nits`,
forever. Severity is verdict-derived (`_VERDICT_SEVERITY`: minor→writing,
major→science). PROJ-552: writing=17, science=0, rounds exhausted.
**Fix (2e7f5b13e):** at the round cap, branch on severity — science/fatal residue
→ RESEARCH_FULL_REVISION (redo, unchanged); **writing-only residue → advance to
RESEARCH_ACCEPTED**, carrying the residue to `paper_writing_residue.md` for the
paper stage. Science gate never relaxed. Matches the two-tier bar doc stages use.

### 3. Citation gate false-positives  [SECONDARY — 6/48 zone projects]
`agents/tools/citation_fetcher.py` classified ANY `status_code >= 400` (incl. 403)
as UNREACHABLE → hard-blocks (the gate blocks UNREACHABLE+MISMATCH). Real
bot-hostile academic hosts (publisher pages, OEIS behind Cloudflare, KnotInfo,
rate-limited registrars) 403/401/429 an automated client — the host EXISTS.
**Fix (pending):** 401/403/429 → `PENDING` (host present, title-unverifiable;
NON-blocking but honestly-not-VERIFIED, auditable). 404/DNS/conn/5xx still
MISMATCH/UNREACHABLE (anti-fabrication preserved). Mirror fix in
`librarian/verify.py` (`present_ambiguous` no longer requires a redirect first).
Note: only helps a blocked project once its citations are RE-verified (the gate
reads stored status; `validate_artifact_citations` re-fetches on artifact change).

## Status
- 355c5d384 (reviewer budget) + 2e7f5b13e (two-tier) PUSHED — the one-two punch.
- Citation fix tested, commit/push pending the full sweep.
- The fixes ENABLE crossings; the actual count accrues as the scheduled crons run.
- PROJ-552 specifically is still citation-blocked until its refs re-verify.

## Tests
test_research_review_flow.py (two-tier accept/redo), test_review_max_tokens_bound.py
(reviewer budget), test_citation_fetcher_access_gated.py + test_librarian_verify.py
(access-gated → PENDING/present, 404 still blocks).
