# STATUS — Pipeline Convergence Protocol (spec 015 / #239)

**Living progress doc (FR-052).** Any agent/sub-agent can determine current status by reading this file. Updated as work proceeds. Design SSoT: [the design doc](../../docs/superpowers/specs/2026-05-27-pipeline-convergence-protocol.md); requirements: [spec.md](./spec.md); tasks: [tasks.md](./tasks.md).

**Branch**: `015-pipeline-convergence-protocol`. **Pipeline**: plan ✅ · tasks ✅ · analyze ✅ (0 findings) · implement 🟡 in progress · verify ⬜.

## Workstream status

|WS|Tasks|Status|Notes / file refs|
|-|-|-|-|
| Setup | T001–T003 | 🟡 | T001 dirs ✅ (`src/llmxive/convergence/`, `calibration/`, `agents/prompts/panels/`); T003 ✅ (`types.py` Stage.AWAITING_PUBLICATION_SIGNOFF; `config.py` CONVERGENCE_MAX_ROUNDS=3, CONVERGENCE_PER_ROUND_BUDGET_SECONDS=600); T002 (this file) ✅ |
| Foundational | T004–T007 | ⬜ | T004 `convergence/types.py` models; T005/T006 Severity; T007 constitution amendment + FR-053 principle |
| US1 Summarizer | T008–T018 | 🟡 | `src/llmxive/tools/summarize.py` + tests; re-point `paper_reviewer` (T017). **Validated FIRST.** |
| US2 Engine | T019–T028 | ⬜ | `convergence/engine.py`, `kickback.py`; refactor tasker Mode-A/B into engine |
| US8 Bug fixes | T029–T036 | ⬜ | research-implementer prompt, analyze prompt, escalations, prompt drift, arXiv, DOI sign-off gate |
| US3 Review model | T037–T045 | ⬜ | triage, point removal, status re-expression, migration |
| US4 Per-step panels | T046–T062 | ⬜ | reviewspecs registry + panel prompts + per-step wiring + publisher graph wiring |
| US5 Calibration | T063–T070 | ⬜ | injectors, differential harness, 9 domains, held-out. **Manual adjudication gate.** |
| US6 E2E | T071–T075 | ⬜ | 9-domain traversal to `posted`. **Manual DOI sign-off gate (FR-054).** |
| US7 Living-doc | T076–T079 | ⬜ | post-`posted` comments → recompile → version DOI |
| Polish | T080–T085 | ⬜ | non-speckit inspection hook, invariants, SSoT grep audit, docs, full suite, final QC |

Legend: ✅ done · 🟡 in progress · ⬜ not started.

## Human gates (cannot be bypassed autonomously)
- **FR-054 / T035, T073, T078**: maintainer must run `llmxive publish-approve <PROJ-ID>` before any real Zenodo DOI mints (initial + version).
- **FR-046 / T068, T075**: maintainer co-evaluates calibration adjudication reports + e2e outputs against the anchor papers.

## Decisions that supersede the design doc (from /speckit-clarify, 2026-05-27)
Overflow floor = on-disk inode-table pointers + recursive desummarize (NOT truncate-with-notice) · NO global kickback cap (per-step 3-round cap kept) · all 9 domains e2e to `posted` · real public DOIs gated by manual sign-off · calibration = differential clean-vs-injected + manual adjudication (no fixed over-flag %) · no `posted`/`done` projects exist → migrate in-flight only.
