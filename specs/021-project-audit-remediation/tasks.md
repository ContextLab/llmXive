# Tasks — Spec 021 (Project-Audit Remediation, issue #294)

## Phase 0 — Reconcile canonical truth (FR-001..004)

- [X] T001 Zero-reference sweep of the legacy config/JS universe
      (sub-agent audit; `code_execution_manager`/`src/core` "live" refs
      were circular within the orphan island).
- [X] T002 Delete `pipeline_config.yaml`, `pipeline_schema.json`, the
      configurable-pipeline scripts, the JS-era layer (`src/core/`,
      `scripts/*.js`, root `package.json`/lockfile), `prompts/`,
      `system_prompts/`, and the legacy test island.
- [X] T003 Fix `web_data.py` research/paper review stage descriptions
      (convergence gate, no points, advisory human reviews); regenerate
      `web/data/projects.json`.
- [X] T004 Fix stale `advancement.py` docstring.
- [X] T005 Reconcile model prose to registry (`README.md`,
      `web/index.html`, `router.py` comment → Gemma 4 31B /
      `google.gemma-4-31B-it`), evidence: run-log + `KNOWN_FREE_MODELS`.
- [X] T006 Add `tests/unit/test_config_consistency.py` (6 guards).

## Phase 1 — Determinism + typed boundaries (FR-005..007)

- [X] T007 `JUDGE_TEMPERATURE = 0.0` on every judge call (#112 root
      cause 1).
- [X] T008 Frozen per-verdict disk cache `state/librarian-cache/judge/`
      keyed by (normalized query, primary pointer, prompt-content hash);
      fail-open never cached (#112 root cause 2); wired through
      `filter_by_relevance` → librarian agent.
- [X] T009 Local backend: honor `temperature=0` as greedy (fix
      `temperature or 0.7` bug), use chat template for instruct models,
      cache loaded checkpoints.
- [X] T010 Judge uses `REASONING_MAX_TOKENS` (router token policy).
- [X] T011 `MalformedResponseError` + bounded retry-with-feedback loop in
      `Agent.run`; reviewers raise it for frontmatter/YAML/schema
      failures with a contract-specific format reminder.
- [X] T012 Unit suites: `test_relevance_judge_determinism.py` (12),
      `test_agent_malformed_response_retry.py` (4).

## Phase 2 — Eval gate (FR-008)

- [X] T013 `eval/promptfoo/` — config + router-backed Python provider +
      production-parser assertion.
- [X] T014 `.github/workflows/prompt-eval.yml` gating
      `agents/prompts/**` PRs (`--repeat 3`).
- [X] T015 Local smoke run (local backend): provider + assertion
      mechanics validated; assertion correctly rejects contract-violating
      output.

## Phase 3 — Real-call validation (SC-001..002, Constitution III)

- [X] T016 `tests/real_call/test_relevance_judge_real.py` — 3× identical
      verdicts + cache replay with real inference (local backend run:
      2 passed, 77 s; Dartmouth default for nightly CI). Registered in
      the slow-module list.
- [X] T017 Real-call claim-layer set against live sources (OEIS,
      Wikipedia, Wikidata; receipts; compute; local backend): 23 passed,
      5 skipped (skips = Dartmouth-key-only fill steps, covered nightly).
- [X] T018 Full offline suite green, including 12 pre-existing
      claims-layer failures present on `origin/main` root-caused and
      fixed (see notes/2026-06-10-issue-294-audit-remediation.md).

## Phase 4 — Docs + issue bookkeeping (SC-003)

- [X] T019 README (models SSoT prose), CLAUDE.md plan pointer,
      website About text; spec 021 artifacts; notes report.
- [X] T020 GitHub issues: #294 close-out report; #112 fixed+closed;
      #256 status comment (specs 016–020 implemented) + close; #216 and
      #263 status comments with follow-up scope.
