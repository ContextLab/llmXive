# Quickstart — spec 007 (website UI bug-fixes + polish, #115)

The maintainer's hands-on guide to landing spec 007. Order: do the data-layer + the auth/security fix + the docs first (lowest risk, highest value, no visual iteration), then the static-site UI fixes (visual iteration), then the maintenance-agent backend, then verify + deploy.

## 0. Preflight

```bash
git switch 008-website-ui-fixes        # the feature branch (already created)
python -c "import llmxive.web_data; print('ok')"
# the site is a no-build static app — just serve web/ locally to view it:
python -m http.server -d web 8000      # then open http://localhost:8000
# GitHub-API tests need a token; LLM tests need DARTMOUTH_CHAT_API_KEY + LLMXIVE_REAL_TESTS=1.
```

## 1. `web_data.py` — the new blocks + the contributor fix (FR-006, FR-007, FR-008; contracts/projects-json-delta.md)

1. **Root-cause the contributor bug first** (research D5): regenerate `web/data/projects.json` (`python -c "from pathlib import Path; from llmxive.web_data import write_payload; write_payload(Path('.'))"`) and inspect `contributors[]` — if it's now correct, the live bug was just stale data; if a row still names a prompt/agent, find the code path (likely the review-walk reading `agent_name`) and fix it to read/normalize `model_name`, bucketing unknowns as `"unattributed"`; if counts are off, dedup by `(contributor, artifact)`.
2. Add `kind` (`"llm"|"human"|"unattributed"`) to each contributor row (it's mostly there — make it explicit and authoritative).
3. Emit the new top-level `agents[]` block from `agents/registry.yaml` (E1) and `pipeline_steps[]` from the `Stage` enum + `STAGE_TO_AGENT` + the per-stage blurbs (move those blurbs out of `web/index.html` into here) + recent artifacts (E2). Add `current_artifact` to each per-project entry (E3).
4. Tests: `tests/phase2/test_web_data_contributors.py` (no row's `name` is a prompt name; ≥1 row's count matches an independently-counted fixture total) + `tests/phase2/test_web_data_blocks.py` (`agents[]` count == registry size + every `prompt_path` exists; every `Stage` in `pipeline_steps[]`; `current_artifact` shapes valid). Real fixtures — no mocks as the primary path. `python -m pytest tests/phase2/test_web_data_*.py -q`.
5. Regenerate `web/data/projects.json`, `git add` it. Commit (`spec-007: web_data — agents/pipeline_steps blocks + current_artifact + contributor fix (#115)`).

## 2. Auth: sign-out + grant revocation (FR-010, FR-011; contracts/auth-js-delta.md, contracts/oauth-proxy.md)

1. `web/js/auth.js`: in `signOut()` — also `sessionStorage.removeItem(KEY_STATE)`; after the local clear + `renderSlot()`, `POST <PROXY>/revoke` with `{ token }` (best-effort; failure → `console.warn` + a small non-blocking notice).
2. **The Cloudflare Worker** (external repo): add the `POST /revoke` route — `DELETE https://api.github.com/applications/{CLIENT_ID}/grant` with `Authorization: Basic base64(CLIENT_ID:CLIENT_SECRET)` and body `{access_token: token}`; same CORS as the existing route. Deploy it. **If you can't add the route**, take the fallback instead: in `web/js/auth.js` `startLogin()`, force GitHub's account-chooser (navigate to `https://github.com/logout?return_to=<encoded authorize URL>`). Either way, FR-011's acceptance (re-sign-in as a different user) must pass.
3. **Verify manually** (Constitution III, UI clause): sign in as user A → sign out → check `localStorage`/`sessionStorage` are clean and the UI shows signed-out → start the OAuth flow → GitHub re-prompts → sign in as user B → the UI shows user B. Screenshot. Commit (`spec-007: sign-out clears all state + revokes the OAuth grant (#115)`).

## 3. Submission helpers + the per-artifact feedback UI (FR-012..015, FR-013b; contracts/auth-js-delta.md)

1. `web/js/auth.js`: add `submitFeedback({target_id, target_kind, target_stage, content})` → `human-submission`+`feedback` issue; `submitPaper({url}|{pdfFile})` → `human-submission`+`new-paper` issue (URL inline, or stage the PDF via the Contents API to `submissions/inbox/<…>.pdf` with a ≤10 MB cap and reference it). Export them.
2. `web/js/app.js` / `dialog.js`: add a "submit feedback" control to **every** artifact modal (idea, spec, plan, in-progress research, paper, review — not just brainstormed); add a top-level "submit a paper" entry point. On success → show the FR-013b message in the modal (✓ created [issue #N](url); "processed within the next hour"); apply the same message to the existing `submitIdea`/`submitReview` flows. On failure → inline error + preserve the form.
3. Test the helpers against the real repo (create a test issue, assert labels/body, then close+delete; for a PDF, assert a `submissions/inbox/` file appeared, then clean up). Commit (`spec-007: submitFeedback/submitPaper + per-artifact feedback UI + confirmation message (#115)`).

## 4. Static-site UI fixes (FR-001..005, FR-009, FR-009b, FR-017; contracts/site-ui-fixes.md)

1. Vendor the Markdown lib → `web/js/vendor/markdown.min.js` + `web/js/vendor/README.md` (name/version/license/source). Add the sanitizing wrapper.
2. `web/index.html` + `web/css/site.css`: wordmark `white-space: nowrap` + box (FR-001).
3. `web/js/app.js` + `web/css/site.css`: the tab-indicator `getBoundingClientRect`-based `positionUnderline()` on click + rAF-debounced `resize` + `orientationchange` + `document.fonts.ready` (FR-002).
4. `web/index.html` + `web/js/app.js`: `data-step` on the pipeline circles + the pipeline-step modal (FR-003); the agent-registry modal + its entry point (FR-004); the "How to contribute" section (FR-005); new modal CSS (desktop + mobile).
5. `web/js/app.js`: the project-modal artifact resolution (PDF → rendered Markdown → formatted source → placeholder; never a broken embed) using `current_artifact` + the vendored renderer (FR-009).
6. Drop the `/qwen|gemma|…/i` regex in `app.js`; render the contributor `kind` from the data.
7. **Visual verification** (Constitution III): serve `web/` locally; at ~1280px and ~375px, walk the `contracts/site-ui-fixes.md` checklist; screenshot each item. Commit (`spec-007: static-site fixes — wordmark, tab indicator, pipeline+agent modals, how-to-contribute, artifact rendering (#115)`).

## 5. Maintenance agent + intake cron (FR-020, FR-021; contracts/submission-intake-agent.md, contracts/submission-intake-workflow.md)

1. `agents/registry.yaml`: add the `submission_intake` entry (E7; `purpose` ≤ 200 chars; `default_model: gemma.gemma3.27b`). `agents/prompts/submission_intake.md`: the triage prompt (sub-type + body + candidate targets + valid steps → structured verdict; be conservative). `src/llmxive/agents/submission_intake.py`: `SubmissionIntakeAgent` + `process_submission_issue(issue, *, repo_root, gh) -> IntakeResult` per the contract (parse labels → triage via one LLM call → act → comment + close on `ok`; comment + leave open on `failed`; `skipped` if already done; reuse the brainstorm/paper-init/project-creation paths — don't duplicate).
2. The entry point: a `python -m llmxive submissions process` subcommand (or `scripts/process_submissions.py`) — precondition checks (token, the `human-submission` label exists, the import works) → list open `human-submission` issues → `process_submission_issue` each → exit 0 unless a precondition failed.
3. `.github/workflows/submission-intake.yml`: hourly `schedule` + `workflow_dispatch`; `permissions: {contents: write, issues: write}`; checkout `@v5` + setup-python `@v6` + `pip install -e .` + the entry point; push any file moves as a `[skip ci]` commit.
4. Tests: `tests/phase2/test_submission_intake.py` — parser/edge (malformed labels → `failed` no-close; unparseable verdict → `failed`); real-GitHub-API (create test issues of each sub-type → run → assert comment+close / PDF-moved); real-LLM triage smoke (gated); idempotency (run twice → 2nd is `skipped`). `python -m pytest tests/phase2/test_submission_intake.py -q`.
5. **Exercise the workflow once manually**: create a test `human-submission`+`feedback` issue on the repo → `gh workflow run submission-intake.yml` → confirm it processed (comment + close), then a `new-paper`+URL one, then a `new-paper`+staged-PDF one (assert the PDF moved). Commit (`spec-007: submission_intake agent + hourly intake cron (#115)`).

## 6. README rewrite (FR-016)

1. Rewrite `README.md` to match the current system: the two Spec-Kit pipelines (research + paper) and their stages; the agent registry (count + a pointer to `agents/registry.yaml`, incl. `submission_intake`); the public website (`context-lab.com/llmXive`) and how to use it (submit ideas / feedback / papers; review; browse); the spec-driven `/speckit-*` workflow; how to contribute. **Verify every claim against the current repo** (Constitution II). Commit (`spec-007: rewrite README to match the current system (#115)`).

## 7. Verify + deploy

1. Full regression: `python -m pytest tests/phase2/ -q --ignore=tests/phase2/test_librarian_cross_domain.py` (a transient arXiv 429 in `test_librarian_search.py` is a known flake, not a regression); ruff clean on touched Python (`ruff check src/llmxive/web_data.py src/llmxive/agents/submission_intake.py tests/phase2/`).
2. Re-verify FR-019: re-run `web_data.py`; the new blocks + contributor fix are still present.
3. Push the branch; open the PR against `main`; wait for the `real-call` CI to pass.
4. After merge: confirm the `Deploy Pages` workflow runs green (re-syncs `web/`→`docs/`); confirm the new `Submission Intake` cron's first scheduled run (or do a `workflow_dispatch`) processes cleanly.
5. Tick the `tasks.md` checkboxes; update the implementation diagnostic with the screenshots + the SC-001..016 verdicts; post the PR link on issue #115.

## Rollback

- The site fixes are markup/JS/CSS — revert the `web/` (and `docs/`) commits to restore the prior site.
- The `submission_intake` agent + cron: remove the registry entry + the workflow file + the module; open `human-submission` issues are harmless (just unprocessed) until then.
- The Cloudflare-Worker `/revoke` route: removing it reverts to "sign-out is local-only" (the FR-010 part still works); the fallback account-chooser change in `auth.js` would also need reverting if it was taken.
