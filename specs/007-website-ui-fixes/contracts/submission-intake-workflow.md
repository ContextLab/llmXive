# Contract: `.github/workflows/submission-intake.yml` — hourly intake cron (FR-021)

**New file**: `.github/workflows/submission-intake.yml`. **Maps to**: FR-021; data-model E9. **Mirrors**: the existing `pipeline-*.yml` workflows (hourly schedule, `pip install -e .`, a Python entry point).

## Workflow shape

```yaml
name: Submission Intake
on:
  schedule:
    - cron: "0 * * * *"     # hourly
  workflow_dispatch: {}      # for the one-time manual exercise (Constitution III) + ad-hoc runs
permissions:
  contents: write            # commit file moves (the staged PDF → its canonical home; inbox cleanup)
  issues: write              # comment on + close human-submission issues
concurrency:
  group: submission-intake
  cancel-in-progress: false
jobs:
  intake:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v6
        with: { python-version: "3.11" }
      - run: pip install -e .
      - name: Process open human-submission issues
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DARTMOUTH_CHAT_API_KEY: ${{ secrets.DARTMOUTH_CHAT_API_KEY }}
        run: python -m llmxive submissions process     # (or: python scripts/process_submissions.py)
      # If the agent committed file moves, push them:
      - name: Push changes if any
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --cached --quiet || git commit -m "submission-intake: process submissions [skip ci]"
          git push || true
```
(Exact entry-point name — a new `submissions process` CLI subcommand vs. a `scripts/process_submissions.py` — decided at `/speckit-tasks`; the contract is "a Python entry point that lists open `human-submission` issues and calls `submission_intake.process_submission_issue` on each".)

## The entry point's behavior (FR-021)

1. **Precondition checks first** (Constitution V — fail fast): a `GITHUB_TOKEN` is present; the `human-submission` label exists on the repo (create it if missing — `feedback` / `new-paper` too); `from llmxive.agents.submission_intake import process_submission_issue` imports. Any of these failing → exit non-zero with a clear message (don't proceed).
2. List open issues with label `human-submission` (paginated).
3. For each, call `process_submission_issue(issue, repo_root=…, gh=…)`:
   - `ok` → the agent already commented + closed; log it.
   - `skipped` → already handled; log and move on.
   - `failed` → the agent already left an explanatory comment and the issue stays open; log the error and **continue to the next submission** (do not abort the run).
4. Exit **0** unless a precondition (step 1) failed — a per-submission error never fails the run (FR-021).

## Idempotency

- Closed issues aren't returned by the "open issues with label `human-submission`" query → re-runs naturally skip handled submissions.
- A partly-processed submission (e.g. the agent created the project but crashed before closing the issue) is re-attempted: the agent's `skipped` check ("does the target project already exist? is the PDF already moved?") makes the retry a near-no-op that just finishes the close.
- Two cron runs can't both process the same issue destructively because of the `concurrency` group + the `skipped` check.

## Cost (Constitution IV)

GitHub Actions free minutes (an hourly job processing 0–handful issues is cheap); the agent's LLM calls use the existing free Dartmouth/HF backends via the router; the `GITHUB_TOKEN` is free and repo-scoped.

## Acceptance

- The workflow YAML is valid (`python -c "import yaml; yaml.safe_load(open('.github/workflows/submission-intake.yml'))"`).
- A manual `workflow_dispatch` run: with ≥1 test `human-submission` issue open, the run processes it (comment + close on success, or `failed` + comment + still-open if unprocessable), exits 0, and — if file moves happened — pushed a `[skip ci]` commit.
- With no open submissions, the run exits 0 quickly (no-op).
- A precondition failure (e.g. unset token in a test invocation) exits non-zero with a clear message.
