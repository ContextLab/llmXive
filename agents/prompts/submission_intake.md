# Submission-Intake Prompt

**Version**: 1.0.0
**Used by**: `src/llmxive/agents/submission_intake.py` (`SubmissionIntakeAgent` / `process_submission_issue(...)`), invoked hourly by `.github/workflows/submission-intake.yml` over open `human-submission` GitHub issues.
**Default backend**: dartmouth (fallback huggingface, then local).

## Purpose

Triage **one** human-submission GitHub issue that arrived from the public llmXive website. The issue is either:

- **`feedback`** — a human's comment on a specific project/artifact (or a general remark / a brand-new idea), or
- **`new-paper`** — a paper submitted for consideration/review, by URL or as an uploaded PDF staged under `submissions/inbox/`.

For a `feedback` issue, this prompt is rendered to decide **what to do with it**: route it to the right pipeline step (as a comment on that project's tracking issue, optionally nudging the project's state), turn it into a brand-new brainstormed project, or just acknowledge it. **Be conservative** — prefer commenting / acknowledging over forcibly mutating project state; prefer routing to an existing project over creating a new one unless the feedback is clearly a brand-new idea.

(For `new-paper` issues the agent doesn't need an LLM call — it files the paper directly. This prompt is only for `feedback` triage.)

## Inputs (substituted into the user message)

- `{{feedback}}` — the human's feedback text.
- `{{target_context}}` — what we know about the named target: the project's id/title/current stage and which artifact the named stage corresponds to (or "(no target named)" / "(target project not found)").
- `{{valid_steps}}` — the list of valid pipeline step keys the verdict may route to (e.g. `flesh_out, specified, clarified, planned, tasked, in_progress, research_review, paper_spec, …`).

## Output contract

**Reply with EXACTLY ONE line of JSON — nothing before or after it.** Shape:

```json
{"target": "<project id, or \"new\">", "action": "<route-to-<step> | create-project | acknowledge>", "rationale": "<one short sentence>"}
```

- `target`: the project id the feedback is about (echo it from `{{target_context}}` when a target was named and found); `"new"` only when `action` is `create-project`.
- `action`:
  - `route-to-<step>` — the feedback is about an existing project and points at a specific step (`<step>` ∈ `{{valid_steps}}`). The agent will post the feedback as a comment on that project's tracking issue and, only if the routing is unambiguous and safe, nudge the project toward that step. Default to routing-as-a-comment.
  - `create-project` — the feedback is really a *new research idea*, not feedback on existing work. The agent will create a `brainstormed` project from it.
  - `acknowledge` — the feedback is off-topic, non-actionable, a thank-you, or too vague to route. The agent will post a brief acknowledgement and close the issue.
- `rationale`: one sentence (≤25 words), no markdown.

If you are unsure, prefer `acknowledge` (or `route-to-<the project's current step>` when a real project is named) over `create-project` or an aggressive route. An unparseable reply is treated as a failure — the agent leaves the issue open with an explanatory comment for a maintainer.

## Guidance

- "The spec for PROJ-X is missing an edge case about Y" → `{"target":"PROJ-X","action":"route-to-clarified","rationale":"asks for a missing edge case in the spec — route to the clarify step on PROJ-X"}`
- "PROJ-X's tasks.md double-counts the data-prep step" → route to `tasked` (or `planned`).
- "You should look into using diffusion models for protein folding" (a topic, not a critique of existing work) → `{"target":"new","action":"create-project","rationale":"a brand-new research idea, not feedback on an existing project"}`
- "Nice work on the dashboard!" / "thanks" / "interesting" → `{"target":null,"action":"acknowledge","rationale":"a non-actionable remark"}`
- A named project that doesn't exist → `acknowledge` ("couldn't find that project").
