# Quickstart: Agentic Pipeline Refactor

**Audience**: Anyone (maintainer, contributor, or fork operator) who wants
the new agentic pipeline running on a clean fork of `llmXive`.

## Prerequisites

- A GitHub fork of `llmXive` with Actions enabled.
- `DARTMOUTH_CHAT_API_KEY` configured as a repository secret.
  - Status today: already configured per user (verified at spec time).
- (Recommended) `DARTMOUTH_API_KEY` repository secret if `langchain-dartmouth`
  needs the developer.dartmouth.edu key for non-chat endpoints.
- (Recommended) `HF_TOKEN` repository secret for the Hugging Face fallback.
- Python 3.11 locally if you want to run the pipeline outside Actions.

## 1. Install (local)

```bash
git clone https://github.com/<you>/llmXive.git
cd llmXive
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .            # reads pyproject.toml at repo root
```

## 2. Run preflight (fail-fast verification)

```bash
python -m llmxive preflight
```

Expected output (success):

```text
[preflight] DARTMOUTH_CHAT_API_KEY: present
[preflight] HF_TOKEN: present
[preflight] git: 2.x on PATH
[preflight] pdflatex: present
[preflight] agents/registry.yaml: 18 agents, validated against contracts/
[preflight] every prompt template referenced exists
[preflight] dartmouth backend reachable (HTTP 200)
[preflight] huggingface backend reachable (HTTP 200)
[preflight] OK — ready to run
```

Any failure exits non-zero with a one-line, agent-specific reason
(Constitution Principle V).

## 3. Resolve Dartmouth model identifiers

The agent registry stores a *preferred* `default_model`, but the
canonical list of available models is discovered at runtime:

```bash
python -m llmxive backends list-models --backend dartmouth
# prints e.g.:
#   on-prem: codellama-13b-hf
#   on-prem: meta.llama-3-2-11b-vision-instruct
#   on-prem: <whatever ChatDartmouth.list() returns today>
#   cloud:   openai.gpt-4.1-mini-2025-04-14
#   cloud:   <whatever CloudModelListing.list() returns today>
```

If you want to pin a different default model for an agent, edit
`agents/registry.yaml` for that one agent — exactly one file changes
(SC-006).

## 4. Run the pipeline once (locally)

```bash
python -m llmxive run --max-tasks 1
```

This will:

1. Acquire the per-project lock for whichever project the scheduler picks.
2. Invoke exactly one agent for one task.
3. Append a run-log entry under `state/run-log/<YYYY-MM>/`.
4. Update `state/projects/<PROJ-ID>.yaml`.
5. Release the lock.
6. Print a one-line summary (no paid-API spend expected).

For the very first run on a fresh fork, `--max-tasks 1` is the safest
choice; subsequent runs can use `--max-tasks 5` (the default in the
scheduled workflow).

## 4a. Inspect a project's per-Spec-Kit scaffold

Each project is its own Spec Kit project. After the
Project-Initializer Agent runs, you'll find:

```bash
ls projects/PROJ-001-example/.specify/                  # Spec Kit scaffold
cat projects/PROJ-001-example/.specify/memory/constitution.md
ls projects/PROJ-001-example/specs/                      # one feature dir per project
ls projects/PROJ-001-example/specs/001-*/                # spec.md, plan.md, tasks.md, …
```

Once research is `research_accepted`, the paper Spec Kit appears too:

```bash
ls projects/PROJ-001-example/paper/.specify/
cat projects/PROJ-001-example/paper/.specify/memory/constitution.md
ls projects/PROJ-001-example/paper/specs/001-paper/
```

## 5. Trigger the scheduled workflow on GitHub

After the refactor PR is merged, the cron schedule (`0 */3 * * *`) takes
over. To trigger immediately:

```bash
gh workflow run llmxive-pipeline.yml
gh run watch
```

The workflow's run summary lists agents invoked, projects touched,
state transitions made, citations verified, and total wall time
(FR-026). Paid-API calls in the summary MUST be 0 (SC-002).

## 6. Inspect results

```bash
git pull                                    # the workflow committed
ls state/projects/                          # one yaml per project
cat state/projects/PROJ-001-*.yaml          # see current_stage and points
ls state/run-log/$(date +%Y-%m)/            # per-run jsonl
git log --oneline -- state/                 # full audit trail
```

The web interface (GitHub Pages, served from `web/`) reads its data
from `web/data/projects.json` (regenerated each run) and reflects every
change automatically.

## 7. Run a specific agent in isolation (debugging)

```bash
# Re-run only the Specifier Agent (drives /speckit.specify) for one project:
python -m llmxive agents run \
    --agent specifier \
    --project PROJ-001-some-project \
    --dry-run                              # preview without writing

# Or re-run the Tasker (drives /speckit.tasks + /speckit.analyze loop):
python -m llmxive agents run --agent tasker --project PROJ-001-some-project

# Or run a paper-stage agent:
python -m llmxive agents run --agent paper_specifier --project PROJ-001-some-project
python -m llmxive agents run --agent figure_generation --project PROJ-001-some-project
python -m llmxive agents run --agent proofreader      --project PROJ-001-some-project

# Or run a reviewer:
python -m llmxive agents run --agent research_reviewer --project PROJ-001-some-project
python -m llmxive agents run --agent paper_reviewer    --project PROJ-001-some-project
```

`--dry-run` prints what the agent would do without committing. Useful
when iterating on a prompt template.

## 8. Force task atomization (debugging long tasks)

If you suspect an agent task will exceed its wall-clock budget, force
the Atomizer:

```bash
python -m llmxive agents run \
    --agent task_atomizer \
    --project PROJ-001-some-project \
    --task code_generation
```

The Atomizer writes a tree of sub-task descriptions (under
`projects/<PROJ-ID>/code/.tasks/`) and the next scheduled run picks
them up. The Joiner is automatic — no manual step needed when the last
sibling completes.

## 9. Real-call test gate

Before opening a PR that touches `src/llmxive/`, `agents/`, or
`.github/workflows/`:

```bash
LLMXIVE_REAL_TESTS=1 pytest tests/real_call/
```

This makes real Dartmouth Chat + HF Inference calls (Constitution
Principle III). In CI, the same suite runs automatically gated on
file paths.

## 10. Revoke a paid-API mistake

The default registry has every agent's `paid_opt_in: false` and every
backend's `is_paid: false`. The agent-registry schema (`contracts/agent-registry.schema.yaml`)
asserts `paid_opt_in: const false` and `is_paid: const false` — so a
PR adding a paid backend without explicit schema relaxation FAILS the
contract test (Principle IV enforcement at schema level).

If you ever see `cost_estimate_usd > 0` in a run-log entry, that is a
contract violation — open an issue and audit the registry diff.

## Key file locations

| What | Path |
|-|-|
| Agent registry | `agents/registry.yaml` |
| Prompt templates | `agents/prompts/<agent>.md` |
| Research-project constitution template | `agents/templates/research_project_constitution.md` |
| Paper-project constitution template | `agents/templates/paper_project_constitution.md` |
| Pipeline entry point | `src/llmxive/cli.py` (run via `python -m llmxive`) |
| Spec Kit script wrappers | `src/llmxive/speckit/runner.py` |
| Project state | `state/projects/<PROJ-ID>.yaml` |
| Run-logs | `state/run-log/<YYYY-MM>/<run-id>.jsonl` |
| Citations | `state/citations/<PROJ-ID>.yaml` |
| Locks | `state/locks/<PROJ-ID>.lock` |
| Per-project research Spec Kit | `projects/<PROJ-ID>/.specify/`, `projects/<PROJ-ID>/specs/` |
| Per-project paper Spec Kit | `projects/<PROJ-ID>/paper/.specify/`, `projects/<PROJ-ID>/paper/specs/` |
| Per-project review records | `projects/<PROJ-ID>/reviews/research/`, `projects/<PROJ-ID>/paper/reviews/` |
| Cron workflow | `.github/workflows/llmxive-pipeline.yml` |
| Real-call CI | `.github/workflows/llmxive-real-call-tests.yml` |
| Web data feed | `web/data/projects.json` |
| Stage thresholds (authoritative) | `web/about.html` |

## Troubleshooting

| Symptom | Likely cause | Fix |
|-|-|-|
| Preflight: "DARTMOUTH_CHAT_API_KEY missing" | Secret not set | Add the secret in repo settings |
| Preflight: "dartmouth backend unreachable" | Quota or outage | Wait for fallback to HF; or check Dartmouth status |
| Run skipped: "lock held" | Prior run still in progress or crashed | Wait for `expires_at`, then re-run |
| Project blocked at "in_review" | Citation flagged | `cat state/citations/<PROJ-ID>.yaml` and fix the offending citation |
| `cost_estimate_usd > 0` in run-log | Paid backend opt-in active | Audit registry; revert opt-in |
