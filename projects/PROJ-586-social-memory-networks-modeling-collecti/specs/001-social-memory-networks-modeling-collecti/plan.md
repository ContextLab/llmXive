# Implementation Plan: Social Memory Networks: Modeling Collective Remembering in Multi‑Agent LLMs

**Branch**: `001-social-memory-networks` | **Date**: 2026-06-25 | **Spec**: `specs/001-social-memory-networks/spec.md`
**Input**: Feature specification from `/specs/001-social-memory-networks/spec.md`

## Summary

This project implements a multi-agent LLM simulation framework to test transactive-memory dynamics (specialization and cue-driven retrieval) and their robustness to context-window truncation. The technical approach uses decoder-only LLMs via `transformers` with a shared external memory buffer, computing specialization index and cue-retrieval efficiency metrics across full vs. limited context conditions.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `torch` (CPU-only), `scikit-learn`, `pandas`, `pytest`, `numpy`, `matplotlib`  
**Storage**: File-based memory buffer (JSON/Parquet), CSV output logs  
**Testing**: pytest with contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: CLI research experiment  
**Performance Goals**: ≤6 h total runtime, ≤7 GB RAM peak, ≤14 GB disk usage  
**Constraints**: CPU-only inference, no CUDA, default float32 precision, sampled dataset subsets  
**Scale/Scope**: 500 games per context condition (reduced from a higher baseline for CPU feasibility), multiple agent population sizes, multiple truncation thresholds (varying token lengths)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Implementation Note |
|------------------------|-------------------|---------------------|
| I. Reproducibility | PASS | Random seed pinned (42); `requirements.txt` at `code/`; isolated venv per task |
| II. Verified Accuracy | PASS | All dataset URLs from verified block only; Reference-Validator gate at research_review→research_accepted |
| III. Data Hygiene | PASS | Raw data checksummed under `data/`; derivations written to new files with documented derivation |
| IV. Single Source of Truth | PASS | All figures/statistics trace to one row in `data/` and one block in `code/`; no hand-typed numbers |
| V. Versioning Discipline | PASS | Content hash for all artifacts stored in `state/projects/PROJ-586-social-memory-networks-modeling-collecti.yaml` `artifact_hashes` map; `state/*.yaml` updated on artifact change |
| VI. Transactive‑Memory Evaluation | PASS | Specialization index and cue-retrieval efficiency computed from interaction logs; code version-controlled and referenced in manuscript |
| VII. Context‑Window Robustness | PASS | Systematic window-size sweep (128, 256, 512 tokens); raw logs stored unchanged; truncated variants saved as derived files with checksums |

## Project Structure

### Documentation (this feature)

```text
specs/001-social-memory-networks/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── game-result.schema.yaml
│   ├── memory-action.schema.yaml
│   └── analysis-output.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-586-social-memory-networks-modeling-collecti/code/
├── run_experiment.py          # CLI entry point (FR-001)
├── agent/
│   ├── __init__.py
│   ├── base_agent.py          # Agent abstraction (FR-002)
│   └── memory_actions.py      # <MEMORY_ACTION> token handling (FR-003)
├── memory/
│   ├── __init__.py
│   └── buffer.py              # Shared external memory buffer (FR-003, FR-012)
├── metrics/
│   ├── __init__.py
│   ├── specialization.py      # Specialization index computation (FR-004)
│   └── retrieval.py           # Cue-retrieval efficiency (FR-005)
├── analysis/
│   ├── __init__.py
│   ├── anova.py               # Separate ANOVAs per metric (FR-006, FR-007)
│   ├── sensitivity.py         # Token threshold sweep (FR-008)
│   ├── power.py               # Power analysis (FR-009)
│   └── scaling.py             # Power-law fitting (US-3)
├── data/
│   ├── loaders.py             # Dataset loading with verified URLs only
│   └── synthetic.py           # Synthetic cue generator fallback (FR-011)
├── utils/
│   ├── __init__.py
│   ├── logging.py             # Error logging to experiment.log (FR-010)
│   └── serialization.py       # Queue-based conflict handling (FR-012)
├── contracts/
│   ├── game-result.schema.yaml
│   ├── memory-action.schema.yaml
│   └── analysis-output.schema.yaml
└── tests/
    ├── contract/
    ├── integration/
    └── unit/

projects/PROJ-586-social-memory-networks-modeling-collecti/data/
├── raw/                        # Raw dataset downloads (checksummed)
├── derived/                    # Transformed data (documented derivation)
└── logs/                       # Interaction logs, experiment.log

projects/PROJ-586-social-memory-networks-modeling-collecti/results/
├── results_full.csv            # US-1 output
├── results_limited.csv         # US-2 output
├── scaling_plot.pdf            # US-3 output
└── power_analysis_report.md    # FR-009 output
```

**Structure Decision**: Single project structure under `code/` with modular subpackages for agent logic, memory management, metrics computation, and analysis. This minimizes overhead while supporting clear separation of concerns for the Implementer Agent.

## Phase Schedule (Computational Task Ordering)

| Phase | Task | Dependency | Output | FR/SC Coverage |
|-------|------|------------|--------|----------------|
| 0 | Dataset verification & download | None | `data/raw/` | FR-001, FR-011 |
| 1 | Memory buffer & agent instantiation | Phase 0 | Agent instances, buffer | FR-002, FR-003 |
| 2 | Game simulation (full context) | Phase 1 | `results_full.csv` | US-1, FR-004, FR-005, SC-001 |
| 3 | Game simulation (limited context) | Phase 1 | `results_limited.csv` | US-2, FR-004, FR-005, SC-001 |
| 4 | Separate ANOVA per metric (Context × Metric) | Phase 2, 3 | ANOVA tables, p-values | FR-006, FR-007, SC-002 |
| 5 | Sensitivity analysis (token sweep) | Phase 2, 3 | Trend report | FR-008, SC-003 |
| 6 | Power analysis report | Phase 4 | `power_analysis_report.md` | FR-009, SC-004 |
| 7 | Scaling analysis (3, 5, 7 agents) - exploratory trend | Phase 0 | `scaling_plot.pdf` | US-3, FR-004, FR-005, SC-005 |
| 8 | Error handling & logging validation | All phases | `experiment.log` | FR-010, FR-012 |

## FR/SC Coverage Matrix

| ID | Description | Plan Phase(s) | Implementation Artifact |
|----|-------------|---------------|------------------------|
| FR-001 | CLI `run_experiment.py` with flags | Phase 0 | `code/run_experiment.py` |
| FR-002 | Multiple decoder-only LLMs via `transformers` | Phase 1 | `code/agent/base_agent.py` |
| FR-003 | Shared external memory buffer with `<MEMORY_ACTION>` tokens | Phase 1 | `code/memory/buffer.py`, `code/agent/memory_actions.py` |
| FR-004 | Specialization index (0 to log₂(N_agents)) | Phase 2, 3, 7 | `code/metrics/specialization.py` |
| FR-005 | Cue-retrieval efficiency (proportion vs. 1/N_agents baseline) | Phase 2, 3, 7 | `code/metrics/retrieval.py` |
| FR-006 | Separate ANOVAs per metric (Context) with p-values | Phase 4 | `code/analysis/anova.py` |
| FR-007 | Bonferroni correction for family-wise tests | Phase 4 | `code/analysis/anova.py` |
| FR-008 | Sensitivity analysis (128, 256, 512 tokens) | Phase 5 | `code/analysis/sensitivity.py` |
| FR-009 | Power analysis report (N=500-1000, α=0.05, power=0.80; flag if <0.70) | Phase 6 | `code/analysis/power.py` |
| FR-010 | Error logging to `experiment.log` with timestamps | Phase 8 | `code/utils/logging.py` |
| FR-011 | Synthetic cue generator fallback | Phase 0 | `code/data/synthetic.py` |
| FR-012 | Queue-based serialization for write-conflicts | Phase 8 | `code/utils/serialization.py` |
| SC-001 | Baseline metrics computed for ≥95% of games | Phase 2, 3 | `results_full.csv`, `results_limited.csv`; validation computes success_rate = (games with metrics / total games) and compares to 0.95 threshold |
| SC-002 | ANOVA interaction p-value reported with significance flag | Phase 4 | ANOVA table output |
| SC-003 | Sensitivity trend report with max absolute change [deferred] | Phase 5 | Sensitivity report |
| SC-004 | Power analysis with [deferred] power or "Power limitation" flag | Phase 6 | `power_analysis_report.md` |
| SC-005 | Scaling plot with fitted power-law curves, 95% CI, sublinearity note | Phase 7 | `scaling_plot.pdf` |

## Compute Feasibility Assessment

| Constraint | Plan Mitigation |
|------------|-----------------|
| No GPU / CUDA | All `transformers` calls use CPU inference, default float32 precision |
| ≤7 GB RAM peak | Sample dataset to a representative subset of rows; load models sequentially per turn; use a distilled GPT model as default model |
| ≤14 GB disk | Raw data checksummed; derived files compressed; logs rotated |
| ≤6 h runtime | 500 games per condition × 3 agent counts × 3 truncation thresholds = 4,500 game simulations (reduced from 9,000); batched with parallelization where safe |
| Library compatibility | Pin `torch` CPU wheel, `transformers` 4.35+, `scikit-learn` 1.3+ |

## Dataset Constraint Acknowledgement

The spec requires `--dataset {hanabi,coqa}` (FR-001), but the verified datasets block contains NO verified source for Hanabi or CoQA. Per the planning rules, I MUST state this mismatch explicitly rather than fabricate URLs. The implementation will:
1. Attempt to load from verified URLs in the block (US-1, US-2, US-3 parquet/CSV/jsonl sources)
2. For any dataset lacking explicit cue annotations or game-state facts, invoke the synthetic cue generator (FR-011) with minimum 10 synthetic cues per game
3. Document the dataset-variable fit gap in `research.md`
4. Validate synthetic-generated metrics against any available real multi-agent interaction data from verified datasets (US-100K, WINNIE-US2) as sensitivity analysis to assess construct validity

## Reviewer Feedback Integration

| Reviewer | Comment | Integration Decision |
|----------|---------|---------------------|
| geoffrey-west-simulated | Scaling analysis for memory accuracy/retrieval speed vs. agent count | Phase 7 implements scaling analysis (US-3) with power-law fitting as descriptive only; acknowledges 3 data points limit power-law reliability and reframes as exploratory trend analysis (per methodology concern fd007e52) |
| david-krakauer-simulated | Memory as adaptation mechanism; forgetting critical | Note added to `research.md` on forgetting as potential future work; current scope focuses on remembering fidelity |
| eric-kandel-simulated | Computational equivalent of CREB-mediated transcription | Note added to `research.md` on memory consolidation mechanisms as future work; current scope focuses on transactive-memory metrics |