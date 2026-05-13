# Spec 007 — llmXive website UI bug-fixes + polish: implementation diagnostic

**Date:** 2026-05-13 · **Branch:** `008-website-ui-fixes` · **Tracking issue:** #115
**Spec:** [specs/007-website-ui-fixes/spec.md](../specs/007-website-ui-fixes/spec.md)

This note records what was implemented, how the static-site fixes were visually
verified (Constitution III's UI clause), the SC-001..SC-016 verdicts, and the
loose ends.

## What landed (by user story)

| US | What | Commits |
|-|-|-|
| Phase 1/2 | vendored Markdown renderer (`snarkdown` 2.0.0 + `web/js/markdown.js` sanitizing wrapper); `web_data.py` — contributor-bug root-cause fix, new `agents[]` + `pipeline_steps[]` blocks, per-project `current_artifact`; tests | `5a74652b` |
| US1 (P1) | header wordmark one token; geometry-driven tab indicator (resize/rotate/scroll/font-load); contributors render `kind` not regex | `c2618e81` |
| US3 (P1, CRITICAL) | `signOut()` clears all client state incl. `sessionStorage` oauth-state + best-effort `/revoke`; `startLogin()` forces the account-chooser (the no-Worker-change fallback) | `1f2a263d` |
| US2 (P1) | project modal renders `current_artifact` (PDF / rendered Markdown / formatted source / placeholder), never a broken embed; client-side fallback that derives the artifact from `artifact_links` when the payload lacks `current_artifact` | `c747200a` |
| US4 (P2) + US6-about | pipeline-step modal; agent-registry modal (49 agents → each agent's prompt+tools); the About-page "How to contribute" section; the per-stage prose moved out of `index.html` into the data | `199404a0` |
| US5 FE (P2) | `submitFeedback` / `submitPaper` in `auth.js`; a "Send feedback" panel on every artifact modal; a "Submit a paper" modal (URL / PDF); the FR-013b "issue created (link); processed within the hour" confirmation on all submission paths; test harness | `03a92758` |
| US5 BE (P2) | the `submission_intake` agent (registry entry + prompt + `src/llmxive/agents/submission_intake.py`); the `submissions process` CLI subcommand; `.github/workflows/submission-intake.yml` (hourly cron); tests | `873aa637` |
| US6 (P2) | `README.md` rewritten to match the current system | `7332cfa4` |
| Polish | regression / lint / FR-019 re-check / mobile pass / this diagnostic / tasks tick / PR | (this phase) |

## The contributor bug — root cause + fix (FR-007, FR-008; research D5)

**Root cause:** `_collect_reviews()` and `_project_authors()` in `web_data.py`
read `reviewer_name` from review-file frontmatter as the contributor identity.
For *LLM* reviews that field is the reviewer **role** (`research_reviewer_idea_quality`,
`paper_reviewer_jargon_police`, …), not the model — the model is in a separate
`model_name` field. So the top-level `contributors[]` list was littered with role
names (`research_reviewer_*`, `research_reviewer`).

**Fix:** for LLM reviews use `model_name` → the model id; for human reviews
`reviewer_name` IS the GitHub username; a missing-model contribution goes to a
single `"unattributed"` bucket (kind `"unattributed"`) — never dropped, never
shown under a role. A `_scrub()` safety net in `build_payload` folds any
role-named row into `"unattributed"`. Aggregates are now derived from the
*final* contributor list so the headline numbers can't disagree with the table.

After the fix (real repo state): **7 AI models + 1 human (jeremymanning), 0 role
names**; `total_contributions` == Σ contribution_count; `total_contributors` == 8.

## Visual verification (Constitution III)

Verified in Chromium against `python -m http.server -d web` at ~1280px and
~375px. Screenshots in `.playwright-mcp/spec007/` (gitignored — they're build
artifacts, not committed):

- `us1-desktop-top.png` / `us1-mobile-top.png` — wordmark "llmXive" one unbroken
  token in its box at both widths; the `.tag` ("automated discovery") hides
  below 480px; tab underline programmatically confirmed aligned (`left`/`width`
  exactly match the active tab) on desktop, after tab clicks, at 375px, and with
  the tabs row scrolled (underline tracks the active tab even when it's scrolled
  partly off-screen).
- Contributors table: 8 rows — `qwen.qwen3.5-122b`, `google.gemma-3-27b-it`,
  `openai.gpt-oss-120b`, `TinyLlama-1.1B-Chat-v1.0`, `Claude 3 Sonnet`,
  `Qwen2.5-3B-Instruct`, `Qwen2.5-1.5B-Instruct` (all "AI model"), `jeremymanning`
  ("Human") — 0 prompt/agent names; counts shown.
- `us2-modal-markdown.png` — a markdown-artifact project renders its `tasks.md`
  (rendered, not raw) with no `<embed>` + a "view on GitHub" footer; a synthetic
  `type=="none"` project shows the placeholder + browse link, no broken embed.
- `us4-pipeline-step-modal.png` / `us4-about-page.png` — clicking the "in
  progress" circle opens a modal with the rendered description, 1 input / 3
  outputs, the implementer/librarian/reference_validator agent chips, 4 example
  artifacts; the agent-registry modal lists 49 agents (sorted), clicking
  "implementer" loads its prompt from `raw.githubusercontent.com` and renders
  it; the About page has the "How to contribute" section (4 cards).
- `us5-submit-paper-modal.png` — the artifact dialog has a "Send feedback"
  button → an inline feedback panel (textarea + submit); the "Submit a paper"
  modal has a URL field + a PDF file-picker; idea/review/paper modals have the
  inline message areas.
- `polish-mobile-about.png` — at 375px the About page, the pipeline diagram (two
  stacked lanes), the "How to contribute" cards (single column), and all the
  modals (pipeline-step, agent-registry, project-artifact, feedback panel,
  submit-paper) fit, scroll, and dismiss via Escape — none clipped.

Sign-out (US3) verified in-browser: a stubbed signed-in state → `signOut()` →
`localStorage` has no `llmxive_gh_token`/`llmxive_gh_user`, `sessionStorage` has
no `llmxive_gh_oauth_state`, `isSignedIn()` is false, the UI shows the sign-in
button, a non-blocking notice appears (the `/revoke` call failed — the Worker
route isn't deployed yet); `startLogin()` builds a
`github.com/logout?return_to=<authorize URL>` URL. The full re-sign-in-as-a-
different-user flow needs a live GitHub OAuth round-trip and the deployed site —
to be confirmed manually post-merge; the mechanism is in place and unit-verified.

## SC verdicts

| SC | Verdict | Notes |
|-|-|-|
| SC-001 wordmark one token | PASS | one unbroken "llmXive" at 1280px and 375px |
| SC-002 tab indicator | PASS | aligned on desktop, re-aligns on resize/rotate/scroll/font-load, works on mobile |
| SC-003 contributors are models | PASS | 7 models + 1 human, 0 role names |
| SC-004 ≥1 count matches an artifact count | PASS | `test_web_data_contributors.py` reproduces the top contributor's run-log count as a lower bound |
| SC-005 (no broken embeds) | PASS | project modal never `<embed>`s a missing PDF; renders the current-stage artifact or a placeholder |
| SC-006 sign-out clears state | PASS | no `llmxive_gh_token`/`llmxive_gh_user`/`llmxive_gh_oauth_state` after sign-out; reload-safe |
| SC-007 sign-in as different user | PARTIAL | the account-chooser fallback is in place + unit-verified; full round-trip to be confirmed post-deploy |
| SC-008 pipeline-step modals | PASS | every circle opens a modal with description/inputs/outputs/agents/examples |
| SC-009 agent-registry modal | PASS | lists all 49 current agents (50 once this branch merges and `submission_intake` is in the data); each agent's prompt+tools render |
| SC-010 "How to contribute" section | PASS | 4 cards with working pointers on the About page |
| SC-011 submission confirmation | PASS | "issue created (link); processed within the hour" on feedback / paper / idea / review submissions |
| SC-012 (feedback on any artifact) | PASS | "Send feedback" on every artifact modal (idea, spec, plan, in-progress, paper, review) |
| SC-013 README accurate | PASS | rewritten against the repo; every claim verified |
| SC-014 mobile-usable modals | PASS | all new/modified modals fit + scroll + dismiss at 375px |
| SC-015 (intake cron processes submissions) | PARTIAL | the agent + CLI + workflow are in place; offline tests pass; the one-time `gh workflow run submission-intake.yml` exercise happens post-merge (the workflow isn't on the default branch yet); the CLI happy path is verified locally ("no open human-submission issues — nothing to do", exit 0) |
| SC-016 no regression on data regeneration | PASS | re-running `web_data.py` keeps the `agents`/`pipeline_steps`/`current_artifact` blocks and the clean contributor list |

## Loose ends / follow-ups (out of scope for this spec)

- **PROJ-001's artifacts are corrupted** — `projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/specs/001-…/tasks.md`
  (and likely siblings) contain a raw git diff committed into the file. The
  website is correctly displaying what's on disk; the *data* needs a cleanup
  (a `repository_hygiene` run or a manual fix of PROJ-001). Not a website bug —
  noted here for a follow-up.
- **The Cloudflare Worker `/revoke` route** is the one external dependency. It
  couldn't be deployed from here, so the active sign-out path is the client-side
  account-chooser fallback (`github.com/logout?return_to=…`). `signOut()` is
  wired to call `<PROXY>/revoke` and will start using it the moment the Worker
  has the route — see `specs/007-website-ui-fixes/contracts/oauth-proxy.md`.
- **Post-merge checks (T047):** confirm `Deploy Pages` runs green (re-syncs
  `web/`→`docs/`); do the one-time `gh workflow run submission-intake.yml`
  exercise with ≥1 test `human-submission` issue (then clean up); confirm the
  cron's first scheduled run is a clean no-op.

## Test summary

- `tests/phase2/test_web_data_contributors.py` (7 tests) — model-not-prompt
  attribution, valid kinds, reproducible counts, aggregates match. PASS.
- `tests/phase2/test_web_data_blocks.py` (8 tests) — `agents[]` == registry,
  prompt files exist, pipeline-step agents ⊆ agents, example_artifacts ⊆
  projects, `current_artifact` shape + pdf-iff-PDF. PASS.
- `tests/phase2/test_submission_helpers.py` (3 offline + 3 gated) — the JS
  submission payload contract. PASS / gated-skip.
- `tests/phase2/test_submission_intake.py` (8 offline + ~5 gated) — parsing,
  subtype detection, malformed-labels/unparseable-verdict/closed-issue handling,
  the registry entry validates; gated: a real GitHub-API roundtrip, a real-LLM
  triage smoke. PASS / gated-skip.
- Full `tests/phase2/` regression (excl. `test_librarian_cross_domain.py`): see
  the commit message / CI. A transient arXiv HTTP 429 in `test_librarian_search.py`
  under suite load is a known flake (re-run in isolation to confirm) — not a
  regression from this spec.
- `ruff`: `web_data.py`, `submission_intake.py`, all four new test files clean;
  `cli.py` keeps its 8 pre-existing nits unchanged (no new debt).

## Post-implementation audit (2026-05-13)

A second pass over #115 + the spec's FRs/SCs caught two gaps:

1. **#115 item 4 / FR-008 — `contribution_count` was wrong.** `_agent_contributors`
   counted *run-log lines* (each agent retry/continuation appended a line), so
   e.g. `qwen.qwen3.5-122b` showed **2202** contributions. FR-008 (and
   data-model E4) require "the count of *distinct artifacts* — no
   double-counting". Fixed: dedup the run-log by `(model, project_id,
   agent_name)` ("this model did this role's work on this project" counts once);
   review files and idea submissions were already once-each. Now
   `qwen.qwen3.5-122b` = **604** (549 distinct run-log tuples + 55 review files);
   `total_contributions` 2914 → 1266. `web/data/projects.json` regenerated.
   New direct test: `test_contribution_counts_are_distinct_artifacts_not_runlog_lines`
   independently recounts (distinct `(model,project,agent)` tuples + review
   files attributing the model + ideas the model submitted) and asserts the
   displayed count equals that **and** is strictly less than the raw run-log
   line count (proving dedup happened — the #115-item-4 bug).

2. **Previously gated/untested paths now directly exercised** (with `gh` authed
   + the Dartmouth key + `LLMXIVE_REAL_TESTS=1`):
   - `tests/phase2/test_submission_helpers.py` real-GitHub-API roundtrips (3) —
     created a real `human-submission`+`feedback` issue, asserted labels+body,
     closed+deleted; same for `new-paper`+URL; staged a tiny PDF to
     `submissions/inbox/`, asserted it appeared, deleted. **PASS** → `submitFeedback`/
     `submitPaper`'s payload behavior is verified against the real API.
   - `tests/phase2/test_submission_intake.py::test_real_acknowledge_roundtrip` —
     created a real `human-submission`+`feedback` issue, ran `process_submission_issue`
     (stubbed `acknowledge` verdict), asserted it posted a comment and closed the
     issue, deleted it. **PASS** → the agent's comment+close path is verified
     against a real issue.
   - `tests/phase2/test_submission_intake.py::test_real_llm_triage_smoke` (3) —
     real Dartmouth model calls: "the spec for PROJ-X is missing an edge case" →
     `route-to-<step>`; "you should look into diffusion models for protein
     structure prediction" → `create-project`; "nice work on the dashboard" →
     `acknowledge`. **PASS** → the LLM triage path is verified end-to-end.
   - **End-to-end CLI exercise**: created a real `human-submission`+`feedback`
     issue, ran `python -m llmxive submissions process`. It saw the issue and
     (because Dartmouth Chat was having an outage right then —
     `302 → outage.dartmouth.edu`, no `HF_TOKEN`, no local `transformers`) the
     agent caught the `BackendError`, **posted an explanatory comment**, and
     **left the issue open** — exactly the per-submission-failure handling
     FR-021 specifies — and the run **exited 0** ("processed 1 issue(s): 0 ok,
     0 skipped, 1 failed"). Test issue deleted. (One observation: the first
     attempt right after issue creation said "nothing to do" — GitHub's
     `labels=` search index lags a few seconds; irrelevant for an hourly cron,
     but noted.)

Updated SC verdicts: **SC-008 now PASS** (the deduped count is directly tested).
**SC-015 upgraded to PASS** for the agent + CLI mechanics (the comment+close
path, the LLM triage, and the CLI's list→process→exit-0 flow incl. correct
failure-handling are all directly verified against real issues / the real model);
the only thing still pending is the *scheduled* run, which starts once the
workflow is on `main`. **SC-007** still PARTIAL (the account-chooser fallback is
in place + unit-verified; the full re-sign-in-as-a-different-user round-trip
needs the deployed site + a live GitHub OAuth flow).

Re-run after the fix: `tests/phase2/test_web_data_{contributors,blocks}.py`
15/15 pass; `ruff` clean (`web_data.py`, the test file). The full
`tests/phase2/` regression is re-run in CI on the PR.
