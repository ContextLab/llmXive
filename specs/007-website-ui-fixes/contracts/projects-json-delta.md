# Contract: `web/data/projects.json` delta + the contributor fix

**Built by**: `src/llmxive/web_data.py` (`build_payload` / `_project_to_entry` / the `_*_contributors` functions). **Consumed by**: `web/js/data.js` → `web/js/app.js` (the dashboard). **Regenerated**: every build + by the pipeline crons (`status_reporter`). **Maps to**: FR-003, FR-004, FR-006, FR-007, FR-008, FR-009; data-model E1, E2, E3, E4.

## New top-level keys

```jsonc
{
  "schema_version": "...",        // NOT bumped — the new keys (agents, pipeline_steps, per-project current_artifact) are purely additive; old consumers ignore them. (Resolved at /speckit-analyze.)
  "generated_at": "...",
  "aggregates": { ... },          // unchanged
  "projects": [ { ... , "current_artifact": { ... } }, ... ],   // each entry GAINS current_artifact (E3)
  "contributors": [ { "name": ..., "kind": ..., "contribution_count": ..., "areas": [...] }, ... ],  // FIXED (E4)
  "agents": [ { ... }, ... ],     // NEW (E1) — one per agents/registry.yaml entry
  "pipeline_steps": [ { ... }, ... ]   // NEW (E2) — one per pipeline stage (both lanes)
}
```

### `agents[]` (E1)

Each: `{ name, purpose, prompt_path, prompt_github_url, prompt_raw_url, registry_github_url, tools: [str], default_backend, default_model, inputs: [str], outputs: [str] }`. Derived from `agents/registry.yaml`. **Test obligation**: count == number of registry entries; every `prompt_path` exists on disk; `prompt_github_url` / `prompt_raw_url` are correctly-formed `github.com/.../blob/main/<path>` / `raw.githubusercontent.com/.../main/<path>`.

### `pipeline_steps[]` (E2)

Each: `{ key, name, lane: "research"|"paper", order: int, description, inputs: [str], outputs: [str], agents: [str], example_artifacts: [{project_id, title, github_url}] }`. `description`/`inputs`/`outputs` consolidated from the `Stage` enum + its docstrings + the per-stage blurbs (moved here from the About-page HTML — so the prose is defined once); `agents` from `STAGE_TO_AGENT` (+ tool-style agents the stage calls, e.g. `librarian`); `example_artifacts` = the most-recent ≈3–5 projects at/past that stage. **Test obligation**: every `Stage` appears; `agents` names ⊆ `agents[].name`; `example_artifacts` `project_id`s ⊆ `projects[].id`; `example_artifacts` may be empty.

### per-project `current_artifact` (E3)

`{ type: "pdf"|"markdown"|"latex"|"json"|"yaml"|"none", repo_path: str|null, github_url: str|null, raw_url: str|null }`. `type == "pdf"` iff the project has a published paper PDF (and then the existing `pdf_url` is the source); otherwise `type` reflects the current-stage artifact's format and `repo_path`/`github_url`/`raw_url` point at it; `type == "none"` iff there's no displayable artifact yet (all of `repo_path`/`github_url`/`raw_url` null). **Test obligation**: when `type != "none"`, `repo_path` exists; `type == "pdf"` ⇔ published PDF present.

## Fixed: `contributors[]` (E4) — FR-007, FR-008

- Each row's `name` MUST be a **model identifier** (normalized, e.g. `qwen.qwen3.5-122b`) for AI work, a GitHub username for humans, or the literal `"unattributed"` — **never** a prompt/agent name (`brainstorm`, `flesh_out`, `librarian`, `specifier`, `clarifier`, `planner`, `tasker`, `implementer`, `reviewer`, `paper_*`, `figure_generation`, `statistician`, `proofreader`, `latex_*`, `citation_validator`, `submission_intake`, …).
- Each row MUST have an explicit `kind ∈ {"llm","human","unattributed"}` — the site renders this directly; **the JS MUST NOT regex-guess** model-ness from the name (the current `app.js` `/qwen|gemma|claude|tinyllama|gpt|mistral|llama/i` test on `item.submitter` is removed; `data.js`/`app.js` use `kind`).
- A contribution whose model can't be determined goes into the single `"unattributed"` row (kind `"unattributed"`) — never dropped, never shown under a prompt name.
- `contribution_count` MUST equal the count of **distinct artifacts** that contributor produced as recorded in canonical state — no double-counting (the same artifact counted in two builder passes), no phantom entries.

**Root-cause-first (D5)**: the implementer first determines whether the live bug is stale `projects.json` / a code path emitting `agent_name` (e.g. the review-walk) / double-counting, fixes the *builder* accordingly, then regenerates `web/data/projects.json` and commits the regenerated file.

## Acceptance

- `python -m pytest tests/phase2/test_web_data_blocks.py tests/phase2/test_web_data_contributors.py` passes (real fixtures, no mocks as the primary path).
- The regenerated `web/data/projects.json` validates against the above; the site renders the new modals + a corrected Contributors list (visually verified).
- After a pipeline-cron tick (or a simulated `web_data.py` re-run), the new blocks + the contributor fix are still correct (FR-019).
