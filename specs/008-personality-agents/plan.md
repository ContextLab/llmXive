# Implementation Plan: Simulated Personality Agents

**Branch**: `008-personality-agents` | **Date**: 2026-05-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/008-personality-agents/spec.md`

## Summary

Build a `personality` agent that runs every 30 minutes via GitHub Actions, selecting one persona at a time from a deterministic rotation over an on-disk pool of prompt files. Each persona — David Krakauer, Geoffrey West, Dan Rockmore, Socrates, Aristotle, Daniel Kahneman, Ada Lovelace, Marie Curie, Rosalind Franklin, von Neumann — gets one turn to (a) comment on an existing project artifact, (b) make a brief content contribution, or (c) propose a new arXiv paper, all in their characteristic voice grounded in their public-record writing. The output is committed through the existing review / feedback / submission-intake pipes with the unambiguous `"<Name> (simulated)"` attribution — never as the real person — and the librarian agent gates any citations they produce.

Two surfaces:

1. **Backend (the cron tick)** — `agents/prompts/personality.md` (the umbrella prompt + persona-shaping protocol), `agents/prompts/personalities/<Name>.md` (one file per persona, public-record-grounded), `src/llmxive/agents/personality.py` (the agent module), `state/personality_rotation.yaml` (the rotation pointer + history), `.github/workflows/pipeline-personality.yml` (the 30-minute cron). Reuses: existing `chat_with_fallback` LLM router (forced to Dartmouth Chat + `qwen-3.5-122b`), existing review-file writer (spec-005), existing feedback-submission pipe (spec-007), existing arXiv submission-intake workflow (the one PROJ-562 came through), librarian agent for citation verification (spec-005), contributor-aliases mechanism (spec-007 / PR #130).

2. **Frontend (the registry)** — new `web/data/projects.json` block `personalities: [{name, summary, prompt_repo_path, prompt_raw_url}, ...]` emitted by `src/llmxive/web_data.py` alongside the existing `agents:` block; new About-page prose section + "Personality registry" modal in `web/index.html` + `web/js/app.js` + `web/css/site.css`, modeled on the existing Agent Registry modal (which already does the same data-driven render + Markdown-with-syntax-highlighting that the personality registry needs).

The attribution wiring is the safety-critical piece: simulated personas have `kind=llm`, a fixed `model_name=qwen-3.5-122b`, and a canonical display name that **always** carries the `(simulated)` suffix anywhere a user can see it. The contributor-aliases resolver from spec-007 is explicitly extended with a guard that prevents merging `"Daniel Kahneman"` with `"Daniel Kahneman (simulated)"`.

## Technical Context

**Language/Version**: Python 3.11 (matches `pyproject.toml`). Frontend: ES2020 vanilla JS + plain CSS (no build step — matches the existing `web/` conventions).

**Primary Dependencies**: existing `llmxive` package (`chat_with_fallback`, agent runtime, run-log writer, project store); existing prompt-loading pattern (`agents/prompts/<name>.md` + frontmatter); existing review-file writer + submission-intake path; existing Prism.js vendored in `web/js/vendor/prism.min.js` (spec-007). No new Python or JS packages.

**Storage**: filesystem only. New paths: `agents/prompts/personalities/<Name>.md` (one per persona; canonical display name in front-matter); `state/personality_rotation.yaml` (a single tiny YAML file with `last_used:`, `history:` for audit, committed per tick — same pattern as existing pipeline state); `state/run-log/<YYYY-MM>/*.jsonl` (existing run-log; one entry per tick with `agent_name=personality`, `model_name=qwen-3.5-122b`, `model_kind=personality_simulator`, `personality=<Name>`).

**Testing**: pytest with real-call (`LLMXIVE_REAL_TESTS=1`) gating per the existing convention; rotation logic tested without real LLM calls (deterministic — selects next file alphabetically after the recorded pointer); per-persona one-shot integration test that drives one full tick through to a committed review file on a fixture project; voice-distinctness sanity test that compares two personas' outputs on the same fixture artifact and checks for non-trivial vocabulary divergence (NOT a hard pass/fail — used as a smoke test that the persona prompts are doing distinguishing work).

**Target Platform**: macOS/Linux developer workstation + GitHub Actions Ubuntu runner. Dartmouth Chat reachable.

**Project Type**: research-pipeline new-agent + website data block + frontend modal (touches three layers: agent runtime, data emitter, web UI).

**Performance Goals**: per-tick wall-clock ≤ 10 minutes (the cron's outer time budget per FR-017); inside the tick, the LLM call itself is the dominant cost (≤ 60s typical for `qwen-3.5-122b`). The 30-minute schedule has plenty of slack so SC-007 (≥ 90% scheduled-window success) is trivially achievable.

**Constraints**: every tick MUST use the `dartmouth` backend with `qwen-3.5-122b` and only that model (FR-015) — no fallback chain to other models, because part of the persona's identity is the consistent voice the model produces; concurrency is enforced via the workflow's `concurrency:` group (FR-016); the rotation pointer file is committed per tick (audit trail).

**Scale/Scope**: 10 personas in v1; 48 ticks/day × 30 days ≈ 1,440 contributions/month max (less if some abstain). All within Dartmouth Chat's free daily quota (100 calls/day per `agents/registry.yaml`) — well within budget. No new datasets.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution at `.specify/memory/constitution.md` v1.0.0 names five non-negotiable principles. Each is evaluated below.

### I. Single Source of Truth (NON-NEGOTIABLE)

- **Compliance**: PASS. Every external dependency the personality agent uses already exists in the codebase: the LLM router (`chat_with_fallback`), the review-file writer, the feedback-submission pipe, the arXiv intake workflow, the librarian, the run-log writer, the website data emitter, the contributor-aliases resolver, the Agent Registry modal pattern. The personality agent is itself a NEW canonical home for "AI persona that takes a turn at the project lanes" — no duplicate exists, and the spec forbids one. The Personality Registry modal explicitly mirrors the Agent Registry modal's behaviour and shares CSS (`.md-body`, `.about-modal`, `.am-prompt`) — no parallel CSS or template branches are added.

### II. Verified Accuracy (NON-NEGOTIABLE)

- **Compliance**: PASS — with one explicit mechanism. The persona prompts cite public-record sources (writings, talks, papers), and the source list itself is verified at authorship time by the human authoring the prompt — same as any other vendored reference. Personality-generated CONTRIBUTIONS that contain citations are routed through the librarian agent (FR-018) before any committed claim treats them as resolved. Unverifiable citations from a persona's output are held for human review, not merged.

### III. Robustness & Reliability (Real-World Testing)

- **Compliance**: PASS. The rotation logic is purely deterministic and has no LLM coupling — fully tested without real-LLM calls. The per-tick integration test makes a real LLM call (gated on `LLMXIVE_REAL_TESTS=1`, same convention as the rest of the project). The cron itself is exercised by an actual scheduled run on a sacrificial branch before the workflow is enabled on main.

### IV. Cost Effectiveness (Free-First)

- **Compliance**: PASS. Dartmouth Chat + `qwen-3.5-122b` is free per `agents/registry.yaml`. Worst-case usage: 48 ticks/day × 1 LLM call = 48 calls/day, well under the 100/day quota. The PDF-fetch path used by the existing arXiv intake (when a persona proposes a paper) is the same free GET we already use. No new paid services introduced.

### V. Fail Fast

- **Compliance**: PASS. Malformed personality files are skipped with a logged warning + non-zero error count (FR-001 + Story 2 scenario 2); rate-limited / timed-out ticks record a structured outcome and do NOT advance the rotation pointer (FR-017); concurrent ticks are serialized (FR-016); a personality picking a now-deleted artifact records a clean failure and does NOT advance the pointer (Edge Cases); a contribution that fails librarian verification is HELD for human review, never silently auto-merged.

## Project Structure

### Documentation (this feature)

```text
specs/008-personality-agents/
├── plan.md                       # This file (/speckit-plan command output)
├── research.md                   # Phase 0 output (/speckit-plan command)
├── data-model.md                 # Phase 1 output (/speckit-plan command)
├── quickstart.md                 # Phase 1 output (/speckit-plan command)
├── contracts/                    # Phase 1 output (/speckit-plan command)
│   ├── personality-prompt-frontmatter.schema.yaml
│   ├── rotation-state.schema.yaml
│   ├── run-log-entry.example.json
│   └── website-personalities-block.schema.json
├── checklists/
│   └── requirements.md           # Already written by /speckit-specify
└── tasks.md                      # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
agents/
├── prompts/
│   ├── personality.md                          # NEW: umbrella prompt — the per-tick decision protocol (catalog → choose → act → format)
│   └── personalities/                          # NEW: one persona prompt per file
│       ├── ada-lovelace.md
│       ├── aristotle.md
│       ├── daniel-kahneman.md
│       ├── dan-rockmore.md
│       ├── david-krakauer.md
│       ├── geoffrey-west.md
│       ├── john-von-neumann.md
│       ├── marie-curie.md
│       ├── rosalind-franklin.md
│       └── socrates.md
└── registry.yaml                               # MODIFIED: add `personality` agent entry

src/llmxive/
├── agents/
│   └── personality.py                          # NEW: the agent module — load pool, select via rotation, build catalog, call LLM, dispatch contribution to the right pipe
├── pipeline/
│   └── graph.py                                # MODIFIED: register `personality` as its own stage-independent task (runs against ANY project state)
└── web_data.py                                 # MODIFIED: emit `personalities:` block + extend contributor-aliases guard ("(simulated)" suffix never collapses into real-name entry)

state/
├── personality_rotation.yaml                   # NEW: rotation pointer + history (per-tick commit)
└── contributor_aliases.yaml                    # MODIFIED: add an `excluded_pairs:` section documenting "<Name>" must not merge with "<Name> (simulated)" (or rely solely on suffix-string check — see research.md)

.github/workflows/
└── pipeline-personality.yml                    # NEW: 30-minute cron, single-personality runner

web/
├── index.html                                  # MODIFIED: add "Simulated personalities" About section + "Personality registry" trigger button
├── js/
│   └── app.js                                  # MODIFIED: open Personality Registry modal (reuses _openAboutModal pattern), drill-down on persona row → Markdown + Prism
└── css/
    └── site.css                                # MODIFIED: minimal — the existing `.about-modal`, `.am-agent-list`, `.am-prompt`, `.md-body` rules already cover the new modal

tests/
├── unit/
│   └── test_personality_rotation.py            # NEW: deterministic rotation, malformed-file skip, missing-pointer recovery
├── integration/
│   └── test_personality_tick.py                # NEW: one full tick end-to-end on a fixture project, mocked-LLM (returns canned three-action-choice JSON)
└── real_call/
    └── test_personality_per_persona_real.py    # NEW: real-LLM, gated on LLMXIVE_REAL_TESTS=1, smoke-tests each persona once on a fixture artifact
```

**Structure Decision**: This is a research-pipeline new-agent + website-data + frontend-modal touch. The Python code lives under `src/llmxive/` (existing agent layout); the prompts live under `agents/prompts/` (existing prompt layout, with a new `personalities/` subdirectory for the per-persona files); the workflow lives alongside the existing `pipeline-*.yml` files. The website surface lives in `web/` (mirrored to `docs/` by the existing pages workflow per spec-007). No new top-level directories.

## Complexity Tracking

> Constitution Check passed with no violations. Section retained empty for traceability.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-|-|-|
| (none) | — | — |
