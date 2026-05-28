# Implementation Plan: Pipeline-Wide Convergence Protocol + Recursive Summarizer + Review-Model Overhaul

**Branch**: `015-pipeline-convergence-protocol` | **Date**: 2026-05-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/015-pipeline-convergence-protocol/spec.md`

## Summary

Two reusable SSoT primitives plus thin per-step adapters make every reviewable llmXive pipeline step run an **identify → revise → re-review** convergence cycle with honest non-convergence handling and overflow safety, **remove the point system** in favor of unanimous-panel acceptance with advisory human/personality triage, add a **living-document** discussion loop, and fix all 10 audit bugs.

Technical approach (grounded in the code audit):
- **Generalize** the existing single-pass `paper_reviewer` chunk-summarizer into a new SSoT `summarize`/`desummarize` pair (`src/llmxive/tools/summarize.py`) that, on overflow, writes an **on-disk inode-table pointer hierarchy** (over-budget content → pointer file(s) → further pointers/summaries) preserving check-critical elements verbatim, and lets any agent recursively page content back in. `paper_reviewer` then calls it (no fork — SSoT).
- **Generalize** the existing 8-panel (research) and 12-panel (paper) reviewers + `rereview_block` machinery into a generic **convergence engine** (`src/llmxive/convergence/`) parameterized per step by a `ReviewSpec`, owning the R1→R2→R3 loop, the unanimous-accept test, the adaptive kickback + kickback record, and the per-round inspection trail (replacing the bespoke `tasker_rounds`).
- **Extend** the engine to the early steps that have no review today (idea, spec, plan, tasks + paper twins) via new multi-lens panels, and **collapse** the two parallel revision-routing schemes (`graph._decide_next_stage` transient stages vs `advancement.py` spec-012 pipeline) into the engine's converge/kickback outcome; `advancement.py` becomes a thin reader.
- **Replace** point scoring with unanimous-acceptance gating everywhere; route human/personality reviews through a new stage-aware **review-intake triage** as advisory inputs; re-express the public status model; amend the constitution's point-based "Review thresholds" clause.
- **Fix** the 10 audit bugs (publisher wiring, research-implementer prompt, dead analyze constant, unused `PAPER_ACCEPT_THRESHOLD`, dead escalations, self-review stub, prompt/stage-header drift, prompt input drift) + arXiv resilience.
- **Calibrate** every panel with a differential clean-vs-injected method + manual adjudication across all 9 `LIBRARIAN_DEFAULT_FIELDS`, validate domain-generality on a held-out field, and prove the goal property by traversing a real high-quality project end-to-end to `posted` in **all 9 domains** (real publication gated by a mandatory manual DOI sign-off).

## Technical Context

**Language/Version**: Python ≥3.11 (`pyproject.toml`; CI on 3.11).
**Primary Dependencies**: `pydantic>=2` (all schemas), `langchain>=0.3` / `langgraph>=0.2` (pipeline graph), `langchain-dartmouth>=0.3.1` (free model backend), `huggingface_hub` (HF daily-paper feed + dataset resolver), existing `pipeline/zenodo.py` (DOIs), system `lualatex`+`bibtex` (paper build).
**Model**: `qwen.qwen3.5-122b` (free; drives ~16 agents per `agents/registry.yaml`) via `backends/router.py:chat_with_fallback`. Budget is char-based (no token counter today): `max_tokens` default 32768 (router.py:78-87, "qwen 32K ctx"); corpus sizing uses `max_chars=180_000` (≈45K tokens) heuristic (`paper_reviewer.py:45,56`). DartmouthBackend enforces a free-only guard; credentials via `llmxive.credentials.load_dartmouth_key`.
**Storage**: filesystem — per-project state `state/projects/<PROJ-ID>.yaml` (`current_stage` on `Project`, `types.py:211`) + `<PROJ-ID>.history.jsonl`; run-log JSONL `state/run-log/<YYYY-MM>/<run-id>.jsonl` (`state/runlog.py`); opt-in inspection JSON `<spec_root>/inspections/<project_id>/<agent>.json` (`speckit/_inspection.py`); NEW summarizer pointer hierarchy under a per-project cache dir; project folders (`idea/`, `specs/`, `paper/`, `reviews/`, `code/`, `data/`).
**Testing**: `pytest>=8` (+ `pytest-asyncio`); real-call tests live under `tests/real_call/` + `tests/e2e/` and are skipped unless `LLMXIVE_REAL_TESTS=1` (`tests/conftest.py:10-16`); contract tests under `tests/contract/`; CI `.github/workflows/llmxive-real-call-tests.yml` runs `python -m llmxive.checks.{prompts,speckit_scripts,backends}` + `pytest tests/contract` + `pytest tests/real_call`. `ruff` + `mypy` configured.
**Target Platform**: Linux (CI / cron) + macOS (dev); GitHub Actions cron drivers per phase.
**Project Type**: Single Python package + CLI (`llmxive`) + langgraph-driven cron pipeline.
**Performance Goals**: keep every model call's assembled input within the ~32K-token budget via the summarizer (no silent truncation); per-round wall-clock budget on the convergence loop (FR-013); 9-domain end-to-end traversal completes (real compute, repeated for noise-robustness).
**Constraints**: free models only (Const. IV); real-call testing for core paths (Const. III); fail-fast preconditions (Const. V); SSoT — generalize/extend/delete, never fork (Const. I); verified accuracy with verbatim preservation + manual QC (Const. II); no global kickback cap (spec FR-017) reconciled with V (see Constitution Check); real public DOIs gated by manual maintainer sign-off (FR-054).
**Scale/Scope**: ~17 pipeline steps (research + paper tracks), 9 domains, 54 FRs / 14 SCs, 10 audit bug fixes + arXiv resilience.

## Constitution Check

*GATE: evaluated against Principles I–V + Development-Workflow gates. Re-checked after Phase 1.*

|Principle|Verdict|Notes|
|-|-|-|
| I. Single Source of Truth (NON-NEGOTIABLE) | **PASS / reinforced** | The feature is a consolidation: `paper_reviewer`'s summarizer is *replaced by a call into* `tools/summarize.py`; the 8/12-panel + `rereview_block` logic is *generalized into* one engine; the two revision-routing schemes *collapse* into the engine. Hard rule for implementation: every generalization MUST delete the old forked path and re-point callers (verify via grep), never leave a parallel copy. |
| II. Verified Accuracy (NON-NEGOTIABLE) | **PASS** | Summarizer preserves URLs/DOIs/ids/numbers verbatim (extraction, not LLM); calibration anchors are real peer-reviewed papers; manual QC co-evaluation; references validated before publish. |
| III. Robustness & Real-World Testing | **PASS** | Real Dartmouth calls drive all panels; summarizer validated on real over-budget artifacts; e2e runs to real `posted` with real Zenodo DOIs (manual sign-off) in 9 domains; no mock-only core tests. |
| IV. Cost Effectiveness (Free-First) | **PASS** | `qwen.qwen3.5-122b` free model; free-only guard retained; summarizer + disk cache reduce repeated calls. |
| V. Fail Fast | **PASS w/ justified nuance** | Engine fails fast on genuine precondition/agent/tool/backend failures (loud `human_input_needed`/`*_blocked`). The spec's "no global kickback cap, iterate-until-converge" (FR-017) is NOT a prohibited retry-forever-past-a-failed-precondition loop: each kickback is a *successful* cycle that produced provenance and is expected to improve the artifact. Recorded in Complexity Tracking. |
| Dev-Workflow: **Review thresholds (point system)** | **VIOLATION → constitution amendment required** | The constitution's "Review thresholds … LLM reviews count 0.5 points and human reviews count 1 point" directly conflicts with FR-019/020/024 (points removed; gate = unanimous panel acceptance). Authorized by the user's clarified decision. Resolution: amend `.specify/memory/constitution.md` (re-express the gate in convergence terms) with a Sync Impact Report + version bump, as a tracked task. Recorded in Complexity Tracking. |
| Dev-Workflow: real-call discipline, pre-push full-suite, frequent commits, reference validation | **PASS** | Honored by the task plan (TDD with real calls; full-suite gate; per-workstream commits; reference validation in publish path). |

No unjustified violations. Two items are tracked in Complexity Tracking below; both are explicitly authorized by the clarified spec.

## Project Structure

### Documentation (this feature)

```text
specs/015-pipeline-convergence-protocol/
├── plan.md              # This file
├── research.md          # Phase 0 — technical decisions
├── data-model.md        # Phase 1 — pydantic entities
├── quickstart.md        # Phase 1 — how to run primitives, a single-step convergence, calibration, an e2e domain run
├── contracts/           # Phase 1 — interface contracts
│   ├── summarize-api.md
│   ├── convergence-engine.md
│   ├── reviewspec-registry.md
│   ├── review-intake-triage.md
│   ├── kickback-record.md
│   └── publisher-signoff.md
├── checklists/requirements.md   # from /speckit-specify
├── STATUS.md            # NEW living progress doc (FR-052), updated as work progresses
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/llmxive/
├── tools/summarize.py           # NEW — summarize()/desummarize(), inode-table pointer hierarchy, preservation-contract goals, deterministic extraction
├── convergence/                 # NEW package — the generic SSoT engine
│   ├── __init__.py
│   ├── types.py                 # Concern, ConcernResponse, Verdict, ConvergenceResult, ReviewSpec, KickbackRecord, ProgressRecord (pydantic)
│   ├── engine.py                # R1→R2→R3 loop, unanimous-accept test, per-round budget, inspection trail
│   ├── kickback.py              # adaptive routing by worst unresolved severity; kickback record emission
│   ├── triage.py                # review-intake: quality filter + stage-aware aspect-mapping (advisory inputs)
│   └── reviewspecs.py           # per-stage ReviewSpec registry (idea/spec/plan/tasks/research-unit + paper twins; EXEMPT set)
├── calibration/                 # NEW — differential clean-vs-injected harness
│   ├── __init__.py
│   ├── injectors.py             # flaw injectors (trivial/circular RQ, FR-without-task, gutted requirement, fabricated data, nonexistent citation, plan↔tasks contradiction)
│   ├── differential.py          # run clean vs injected, diff verdicts, surface extra findings for manual adjudication
│   └── domains.py               # per-field anchor-paper registry (9 LIBRARIAN_DEFAULT_FIELDS) + held-out marker
├── agents/
│   ├── prompts/
│   │   ├── panels/              # NEW per-lens panel prompts (idea_*, spec_*, plan_*, tasks_* + paper twins) + analyze prompts (research + paper)
│   │   ├── implementer_research.md   # NEW real research-code implementer prompt (replaces mis-pointed LaTeX prompt)
│   │   └── _shared/rereview_block.md # reused by engine R3
│   ├── research_reviewer.py     # reuse; panel feeds engine; fix _produced_by stub (advancement.py:177)
│   ├── paper_reviewer.py        # reuse; summarizer call → tools/summarize.py; panel feeds engine
│   ├── advancement.py           # thin reader of ConvergenceResult + kickback router; remove point scoring/thresholds
│   ├── publisher.py             # wire into graph; manual DOI sign-off gate (FR-054); living-document recompile
│   ├── status_reporter.py       # convergence-based status; projects.json regen; issue comment/close
│   └── personality.py           # cron emits review-intake input (triage producer)
├── speckit/
│   ├── tasks_cmd.py             # Mode-A/B refactored INTO engine; honest reporting; per-round budget; constitution input
│   ├── analyze_cmd.py           # real prompt file (kill dead ANALYZE_SYSTEM_PROMPT_PATH); paper-appropriate analyze; pass project_dir (comments)
│   ├── implement_cmd.py         # research implementer uses implementer_research.md; in-loop revise + filesystem re-verify (#49)
│   ├── clarify_cmd.py / paper_clarify_cmd.py   # fix dead escalation paths
│   └── paper_specify_cmd.py     # resolve code_summary/data_summary prompt input drift
├── pipeline/
│   ├── graph.py                 # wire publisher (paper_accepted→publisher→posted); route via engine; collapse transient-stage scheme
│   └── zenodo.py                # reused by publisher (+ version DOI for living-document)
├── librarian/theoremsearch*.py  # arXiv graceful degradation on 429/503
└── config.py                    # remove point thresholds; per-round budget constant

tests/
├── unit/            # summarizer edge cases, engine round logic, triage filter/mapping, kickback routing, injectors
├── contract/        # schema validation for new pydantic models + contract docs
├── integration/     # per-step convergence on real projects; advancement/graph collapse; living-document
├── real_call/       # real qwen calls: summarizer fidelity, panel reviews, differential calibration (LLMXIVE_REAL_TESTS=1)
└── e2e/             # 9-domain end-to-end traversal to posted; weak-project rejection

.specify/memory/constitution.md  # amend point-based Review-thresholds clause
README.md, web/ (about page)     # re-express Backlog→Ready→Done in convergence terms
```

**Structure Decision**: Single Python package (`src/llmxive`). Two NEW top-level modules/packages (`tools/summarize.py`, `convergence/`) house the SSoT primitives; `calibration/` houses the validation harness; everything else is in-place extension/fix of existing modules. New per-lens panel prompts live under `agents/prompts/panels/`. A living `STATUS.md` (FR-052) tracks per-workstream progress with direct file references so any agent/sub-agent can read current status.

## Implementation sequencing (drives `/speckit-tasks`)

Ordered by the design's dependency chain (summarizer validated FIRST; calibration/e2e last):

0. **Constitution amendment + bug-fix groundwork** — amend the point-based clause; quick standalone fixes (dead constant, prompt drift, arXiv resilience) that unblock later real runs.
1. **`summarize`/`desummarize` primitive** (TDD on real over-budget artifacts; 7 edge cases; inode-table; re-point `paper_reviewer`). **First.**
2. **Convergence engine + types + kickback** (TDD; generalize panel/rereview machinery; honest reporting; per-round budget; inspection trail).
3. **Review-intake triage** (quality filter + stage-aware aspect-mapping; personality cron → triage producer).
4. **Per-step ReviewSpec adapters** (idea, spec [specifier+clarifier collapsed], plan, tasks [Mode-A/B→engine], research-unit [implement↔review loop, #49], paper twins, publisher wiring) + constitution-as-input + advancement/graph collapse (#51) + point removal.
5. **Remaining audit bug fixes** (research-implementer prompt, analyze prompt, self-review stub, stage-header drift) wired through the engine.
6. **Status-model re-expression** (README/about/`status_reporter`; migrate in-flight projects).
7. **Living-document discussion board** (post-`posted` triaged comments → log → batched recompile → version DOI w/ sign-off).
8. **Calibration** (differential clean-vs-injected per panel, all 9 domains, held-out generality; manual adjudication).
9. **End-to-end traversal** (real high-quality project → `posted` in all 9 domains, manual DOI sign-off; weak-project rejection; direct artifact inspection).

Cross-cutting throughout: inspection hook for non-speckit Agent steps (close §9 gap); run-log per convergence round; schema validation on every written artifact; `STATUS.md` kept current.

## Complexity Tracking

|Violation|Why Needed|Simpler Alternative Rejected Because|
|-|-|-|
| Constitution "Review thresholds" point system removed (governance change) | Spec FR-019/020/024 + clarified user decision: unanimous-panel acceptance replaces points everywhere; points and the unanimous gate are mutually exclusive | Keeping points leaves a split-brain gate (engine vs points) and contradicts the spec's core review-model overhaul; the user explicitly authorized removal |
| No global kickback cap (tension with Const. V "no retry-forever loops") | Spec FR-017 + clarified user decision: each kickback is a completed, provenance-carrying cycle expected to improve the artifact until convergence | A hard cap forces "give up on good work" — the dead-end the goal property forbids; genuine failures still fail fast via `human_input_needed`/`*_blocked`, so V's intent (no silent continuation past a *failed precondition*) is preserved |

## Notes

- **Constitution amendment** is a real task (Workstream 0): edit `.specify/memory/constitution.md`, bump version (MINOR — material change to a governance gate), add a Sync Impact Report, update README cross-links.
- **SSoT discipline**: after generalizing the summarizer and panels, grep to confirm the old forked implementations are deleted/re-pointed (Const. I).
- **Real-call cost/time**: 9-domain e2e + per-panel differential calibration are large real-compute efforts on the free model; runs are repeated for noise-robustness. The manual DOI sign-off (FR-054) is a deliberate human checkpoint that WILL pause the e2e/publish work.
