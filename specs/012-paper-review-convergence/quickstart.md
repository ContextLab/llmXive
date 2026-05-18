# Quickstart: Paper Review Convergence

This is the operator's how-to for driving a paper through the new converging review pipeline. Read this after `spec.md` and `data-model.md`.

## 0. Prerequisites

```bash
# Standard llmXive setup
pip install -e ".[dev]"
python -m llmxive preflight    # validates env, keys, prompts, backends
```

Confirm a Dartmouth Chat API key is reachable:

```bash
python -c "from llmxive.credentials import load_dartmouth_key; print('OK' if load_dartmouth_key() else 'MISSING')"
```

## 1. Drive a home-grown paper through one revision cycle

Suppose a project `PROJ-100-my-experiment` is at `paper_review` with at least one prior round of reviews that flagged writing-class action items.

```bash
# Cron tick (or one-shot manual run) for paper review
python -m llmxive run --max-tasks 13 --stage paper_review --project PROJ-100-my-experiment
```

Expected sequence after the change ships:

1. 12 specialist reviewers + 1 lead reviewer each produce a `ReviewRecord` with `action_items`.
2. Advancement evaluator examines per-specialist most-recent verdicts.
3. Outcome (deterministic given the verdicts):
   - All specialists `accept` → `PAPER_ACCEPTED` (terminal).
   - Any `fatal` item → `BRAINSTORMED` + rejection rationale appended to idea record.
   - Otherwise (writing or science items, no fatal) → `PAPER_REVISION_IN_PROGRESS`.

If the outcome is `PAPER_REVISION_IN_PROGRESS`, the `revision_planner` is invoked in the same tick:

```bash
# Driven automatically by the advancement evaluator — no separate command needed
# Internally runs: speckit-specify → clarify → plan → tasks → analyze (auto-mode)
```

On success → `READY_FOR_IMPLEMENTATION` (with `revision_spec_path` field set).
On analyzer-stuck failure → `PAPER_REVISION_BLOCKED`.

## 2. Drive an arxiv-intake paper through the guardrail path

Suppose `PROJ-564-qwen-image-vae-2-0-technical-report` (arxiv-intake) is at `paper_review`.

```bash
python -m llmxive run --max-tasks 13 --stage paper_review --project PROJ-564-qwen-image-vae-2-0-technical-report
```

Expected:

1. 13 reviewers produce records.
2. Advancement evaluator detects arxiv-intake (presence of `paper/metadata.json` + absence of `paper/specs/`).
3. Outcome:
   - All accept → `PAPER_ACCEPTED`.
   - Any fatal → `BRAINSTORMED` + rejection rationale.
   - Writing/science items, no fatal → `PAPER_ACCEPTED` (with caveats) + new round appended to `projects/PROJ-564-.../upstream_feedback.yaml`.
4. `paper/source/` MUST be unchanged in all three outcomes.
5. The web dashboard's card for this paper surfaces the `upstream_feedback.yaml` content under a "Reviewer feedback (upstream)" header.

## 3. Re-review a paper that's been revised

After an implementer agent runs `speckit-implement` against a `READY_FOR_IMPLEMENTATION` project, the project transitions back to `PAPER_REVIEW`.

```bash
python -m llmxive run --max-tasks 13 --stage paper_review --project PROJ-100-my-experiment
```

Expected (per-specialist re-review protocol):

1. For each specialist that has ≥1 prior `ReviewRecord` for this project → that specialist's prompt uses the re-review block. Its prior action items are listed; the model checks (a) addressed? (b) new issues?
2. For each specialist with NO prior records (e.g., newly added) → full critique prompt.
3. The model emits one record per specialist. If every specialist's most-recent verdict is `accept` → `PAPER_ACCEPTED`.

If even one specialist re-flags an unaddressed item → another `PAPER_REVISION_IN_PROGRESS` round.

## 4. Inspect outcomes

```bash
# State of all paper-stage projects
python -m llmxive projects ls --stage paper_review,paper_revision_in_progress,paper_revision_blocked

# Diagnostic for a blocked project
cat specs/auto-revisions/PROJ-X-Y/round-N/result.yaml

# Upstream feedback for an arxiv-intake project
cat projects/PROJ-564-.../upstream_feedback.yaml
```

## 5. Manually unblock a paper_revision_blocked project

If the analyzer is genuinely stuck on a poorly-formed action item:

```bash
# 1. Edit the action items file to remove or rephrase
$EDITOR state/revisions/PROJ-X-Y/round-N.yaml

# 2. Reset state back to paper_minor_revision so the planner re-tries
llmxive project unblock PROJ-X-Y

# 3. Next cron tick re-attempts the auto-plan
```

The `unblock` command validates that the action items file was actually modified (no-op edits are rejected), and resets the round counter.

## 6. End-to-end smoke test (real LLM)

```bash
LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_paper_review_convergence_e2e.py -v
```

This test drives a small fixture project through one full review→revision→re-review cycle with the real Dartmouth backend. Expected runtime: ≤5 minutes.
