# Contract: `submission_intake` maintenance agent (FR-020)

**New module**: `src/llmxive/agents/submission_intake.py` · **New prompt**: `agents/prompts/submission_intake.md` · **New registry entry**: `agents/registry.yaml` `submission_intake` · **Invoked by**: the `.github/workflows/submission-intake.yml` cron (see `contracts/submission-intake-workflow.md`). **Maps to**: FR-020; data-model E7, E8.

## Registry entry (E7)

```yaml
- name: submission_intake
  purpose: Triage human-submission GitHub issues from the website — route feedback to the right
    pipeline step / create a project / file a submitted paper / acknowledge — then comment and close.
  inputs: [issue]
  outputs: [project]            # tool-style; does not own a project stage
  prompt_path: agents/prompts/submission_intake.md
  prompt_version: 1.0.0             # for consistency with the other registry entries
  default_backend: dartmouth
  fallback_backends: [huggingface, local]
  default_model: gemma.gemma3.27b   # fast — triage is a quick classification
  wall_clock_budget_seconds: 300
```
(Must pass the existing `agent-registry` schema — `purpose` ≤ 200 chars, etc.)

## Module API

```python
@dataclasses.dataclass(frozen=True)
class IntakeResult:
    status: str            # "ok" | "failed" | "skipped"
    action: str | None     # "routed-to-step" | "created-project" | "filed-paper" | "acknowledged" | None
    target: str | None     # project/artifact id acted on / created, or None
    error: str | None
    comment_url: str | None

class SubmissionIntakeAgent(Agent):  # follows agents/base.Agent
    ...

def process_submission_issue(
    issue: dict,            # the GitHub issue object (number, title, body, labels, html_url, user)
    *,
    repo_root: "Path",
    gh,                     # a GitHub API client (the same ghFetch-equivalent the cron uses; reuse an existing helper if one exists, else a thin wrapper)
    registry_entry: "AgentRegistryEntry" = None,   # defaults to registry.get("submission_intake")
) -> IntakeResult: ...
```

## Behavior

1. **Parse** the issue's labels — must include `human-submission` + exactly one of `feedback` / `new-paper` (else → `IntakeResult(status="failed", error="malformed labels")` + a comment "couldn't determine submission type"; do NOT close).
2. **For `feedback`**: parse the body's `target_id` / `target_kind` / `target_stage` / `content`. Gather the candidate target context (the project's current state + which artifact `target_stage` corresponds to). **One LLM call** (render `agents/prompts/submission_intake.md` with the feedback content + the target context + the list of valid pipeline steps): the model returns a tight structured verdict — `{ target: <project/artifact id or "new">, action: <"route-to-<step>" | "create-project" | "acknowledge">, rationale: <one sentence> }`, parsed defensively. Then act:
   - `route-to-<step>`: post a comment on the *project's tracking issue* relaying the feedback + the implied step, and (if appropriate and safe) nudge the project's state toward that step via the existing state mechanism — **conservatively**: prefer "comment on the project issue so a human/the next agent run picks it up" over forcibly mutating state, unless the routing is unambiguous (decided per case; err toward commenting).
   - `create-project`: if the feedback is really a *new idea*, route it through the existing brainstorm path (create a `brainstormed` project from the content) — reuse `cli._cmd_brainstorm`'s project-creation helpers / `idea_lifecycle`, do NOT duplicate.
   - `acknowledge`: post a brief acknowledgement comment on the `human-submission` issue.
3. **For `new-paper`**: parse the body's `url` or the `submissions/inbox/<…>.pdf` reference. Create-or-link the relevant project (and a `paper/` scaffold / a review entry as appropriate — reuse the existing paper-init / project-creation paths; don't duplicate). If a staged PDF: `git`-move it (via the Contents API: read → `PUT` at the canonical path → `DELETE` the inbox copy) to `projects/PROJ-###-…/paper/submitted/<…>.pdf` (or wherever the triage decides); if a URL: record it in the project's metadata. (If `submissions/inbox/` has an orphan PDF with no referencing open issue, clean it up.)
4. **In all `ok` cases**: post a brief comment on the `human-submission` issue describing what was done (with links to the created/affected project/comment), then **close the issue**.
5. **On any LLM failure / unparseable response / unexpected error**: post an explanatory comment on the issue ("intake agent couldn't process this automatically: <reason>; a maintainer will look") and return `IntakeResult(status="failed", error=...)` — **do not close** (the next cron tick retries; a maintainer can also handle it manually).
6. **Idempotency**: before acting, check whether the work is already done — the target project already exists, the PDF is already at its canonical path, the issue is already closed — and return `IntakeResult(status="skipped")` rather than re-doing it.

## Prompt (`agents/prompts/submission_intake.md`)

A small system+user prompt: given an issue's sub-type, body, and (for feedback) the candidate targets + valid pipeline steps, return the structured triage verdict (target / action / one-sentence rationale) — instruct the model to be conservative (prefer `acknowledge` or `route-to-<step>`-as-a-comment over aggressive state changes; prefer routing to an existing project over creating a new one unless it's clearly a brand-new idea). Output format: a tight YAML or single-line JSON, parsed defensively (an unparseable response → `failed` → comment + leave open).

## Test obligations (→ `tests/phase2/test_submission_intake.py`)

- **Parser/edge**: malformed labels → `failed`, no close, a comment posted; an unparseable LLM verdict → `failed`, no close.
- **Real GitHub API** (gated on a token): create a test issue labelled `human-submission`+`feedback` on the repo → run `process_submission_issue` → assert it posted a comment and closed the issue (then clean up). Same for `new-paper`+URL. For `new-paper`+staged-PDF: stage a tiny test PDF, create the issue, run the agent, assert the PDF moved to the canonical path and the inbox copy is gone and the issue is closed.
- **Real-LLM triage smoke** (gated on `DARTMOUTH_CHAT_API_KEY` + `LLMXIVE_REAL_TESTS=1`): a feedback issue with content like "the spec for PROJ-X is missing an edge case about Y" → the verdict targets PROJ-X with a `route-to-<spec-or-clarify-step>` action; a feedback issue with "you should look into Z" (a brand-new topic) → `create-project`; an off-topic/non-actionable issue → `acknowledge`.
- **Idempotency**: running twice over the same already-handled issue → the second run is a no-op (`skipped`), nothing duplicated.

## Acceptance

- The registry validates with the new entry; `python -c "from llmxive.agents.submission_intake import process_submission_issue"` imports.
- `pytest tests/phase2/test_submission_intake.py` passes (offline tests always; gated real tests when creds available).
- A manual `workflow_dispatch` run of the intake workflow (with ≥1 test submission open) processes it correctly (comment + close, or `failed` + comment + still-open if it genuinely can't).
