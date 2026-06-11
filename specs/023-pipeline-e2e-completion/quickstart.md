# Quickstart: Pipeline End-to-End Completion

**Feature**: 023-pipeline-e2e-completion

## Setup

```bash
cd ~/llmXive && source .venv/bin/activate   # or: pip install -e ".[dev]"
export LLMXIVE_REAL_TESTS=1                 # for real-call suites
# DARTMOUTH_CHAT_API_KEY resolves via llmxive.credentials if not in env
```

## Verify each story

**US1 — review decisions persist and are consumed**

```bash
# offline regressions
pytest tests/unit -k "advancement or graph or revision" -q
# real-state demonstration: one pass on a project under paper review with
# current verdicts → saved state carries revision_spec_path; the NEXT pass
# dispatches the revision implementer (not reviewers)
python -m llmxive run --project PROJ-565-<slug> --max-tasks 1
python - <<'EOF'
import json; print(json.load(open("projects/<id>/.llmxive/config.json")).get("revision_spec_path"))
EOF
python -m llmxive run --project PROJ-565-<slug> --max-tasks 1   # implementer pass
```

**US2 — funnel flows**

```bash
pytest tests/unit -k "scheduler" -q   # incl. new distribution-share tests
# the distribution test samples the scheduler over the real population and
# asserts idea stages get a non-vanishing share (FR-006)
# lane: .github/workflows/pipeline-validate-ideas.yml drains flesh_out_complete
```

**US3 — the traversal**

```bash
# PROJ-552 progresses via the scheduled lanes; observe stage + history:
python - <<'EOF'
import json, glob
cfg = json.load(open(glob.glob("projects/PROJ-552-*/.llmxive/config.json")[0]))
print(cfg["current_stage"]); [print(t) for t in cfg.get("stage_history", [])[-5:]]
EOF
# completion proof: history brainstormed → … → posted; DOI in
# projects/PROJ-552-*/paper/signoff.yaml; audit-passing PDF (pdf audit below)
```

**US4 — rare escalation**

```bash
pytest tests/unit -k "escalation or feasib" -q
# the three parked projects re-process automatically (FR-018):
python -m llmxive run --project PROJ-545-<slug> --max-tasks 1   # etc. 553, 557
ls state/escalations/        # ≈ empty in steady state
```

**US5 — sign-off vote**

```bash
pytest tests/unit -k "signoff" -q
# gate machinery extends the existing `project signoff` CLI path:
python -m llmxive project signoff --help
# real round-trip (test context, Zenodo sandbox): drive a paper to the
# gate, react 👍 with a maintainer account, watch the poll lane mint+close.
```

**US6 — paper shelf**

```bash
pytest tests/unit -k "paper_status or web_data or pdf" -q
python -m llmxive pdf audit --help          # rendering audit entry point
python - <<'EOF'
from llmxive.agents.status_reporter import regenerate_web_data
from pathlib import Path; regenerate_web_data(repo_root=Path("."))
EOF
cat state/paper_status/<id>.json            # status record, no silent fallbacks
```

## Full gates (before any push)

```bash
pytest tests/unit tests/contract tests/integration -q          # offline
LLMXIVE_REAL_TESTS=1 pytest tests/real_call -m "not slow" -q   # real-call subset
```
