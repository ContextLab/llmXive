# Implementation Plan: Dendritic Computation in Transformers: Beyond Point Neurons

**Branch**: `001-dendritic-computation-in-transformers` | **Date**: 2026-06-25 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-dendritic-computation-in-transformers/spec.md`

## Summary

This project investigates whether artificial neurons with biologically realistic dendritic compartmentalization enable more efficient hierarchical feature detection in transformer architectures compared to standard point-neuron designs. The technical approach involves implementing a matched-parameter dendritic transformer variant (replacing standard feedforward layers with compartmentalized units featuring **local nonlinearities**, **plateau potential gating**, and **calcium modulation**) and a baseline point-neuron transformer. To ensure strict parameter and FLOP matching (tolerances: **<0.1% parameters**, **<1% FLOPs**), the plan explicitly compensates for the dendritic overhead by reducing the hidden dimension of the baseline's main trunk. Both models will be trained on the GLUE SST-2 benchmark under strict CPU-only constraints (**2 cores, 7GB RAM**, **6-hour wall-clock limit**). The plan includes rigorous statistical analysis (**paired Wilcoxon tests** on **sample efficiency** (steps to reach **[deferred] fixed accuracy**) and **probing accuracy**, **Benjamini-Hochberg correction** for per-layer tests, and **AUC of accuracy-vs-depth curve**) across **3-5 random seeds**. A **sensitivity analysis** sweeps the `dendritic_threshold` parameter over values **0.1, 0.5, and 0.9** to validate robustness (FR-007).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch (CPU-only wheel), scikit-learn, pandas, datasets (HuggingFace), pytest, torchinfo  
**Storage**: Local file system (`data/` for datasets/checkpoints, `data/experiments/` for logs)  
**Testing**: `pytest` with unit tests for model architecture matching and integration tests for training pipelines  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM, no GPU)  
**Project Type**: Research library/experimental pipeline  
**Performance Goals**: Train both models to stable state or hard stop within 6 hours on CPU; parameter match <0.1%; FLOP match <1%  
**Constraints**: No GPU/CUDA; memory footprint <7GB; disk usage <14GB; reproducibility via pinned seeds (stored in `config.yaml`) and checksummed data  
**Scale/Scope**: Single benchmark task (SST-2); 3-5 random seeds; sensitivity sweep over 3 threshold values (0.1, 0.5, 0.9)

> Empirical specifics (exact dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan mandates pinned random seeds (persisted in `config.yaml`), checksummed datasets, and isolated virtualenv execution. All results traceable to `code/` and `data/`.
- **II. Verified Accuracy**: Dataset references in `research.md` are restricted to the verified list provided in the prompt (no invented URLs). Citations in analysis will be validated by the Reference-Validator Agent.
- **III. Data Hygiene**: Raw data preserved; derivations written to new files with checksums. No PII in data.
- **IV. Single Source of Truth**: All figures/stats in final paper trace to `data/` rows and `code/` blocks.
- **V. Versioning Discipline**: Artifacts carry content hashes; state file updated on changes.
- **VI. Dendritic Model Documentation**: Plan explicitly requires logging of dendritic parameters (local nonlinearities, plateau gating, calcium modulation) in `data/experiments/` via `dendritic_parameters` schema.
- **VII. Benchmark Parity and Compute Consistency**: Plan enforces matched parameters/FLOPs (via hidden dimension compensation), **identical optimization schedules**, **identical batch sizes**, and a **6-hour wall-clock limit** on the same runner config (2 cores, 7GB RAM), as required by Constitution Principle VII.

## Project Structure

### Documentation (this feature)

```text
specs/001-dendritic-computation-in-transformers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schema files)
│   ├── experiment_log.schema.yaml
│   ├── probe_result.schema.yaml
│   ├── stat_test.schema.yaml
│   └── transformer_config.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-585-dendritic-computation-in-transformers-be/
├── code/
│   ├── models/
│   │   ├── transformer_baseline.py
│   │   └── transformer_dendritic.py
│   ├── experiments/
│   │   ├── train.py
│   │   ├── probe.py
│   │   └── analyze.py
│   ├── utils/
│   │   ├── flops.py
│   │   └── config.py
│   └── tests/
│       ├── test_architecture_match.py
│       └── test_training_pipeline.py
├── data/
│   ├── raw/
│   │   └── glue_sst2/
│   ├── processed/
│   └── experiments/
│       └── [seed_001]/
└── docs/
    ├── research_notes.md
    └── quickstart.md
```

**Structure Decision**: Single-project structure with clear separation of models, experiments, and utilities. Directories align with Constitution Principle I (Reproducibility) and Principle VII (Benchmark Parity). Contract files (Phase 1 outputs) are explicitly listed to ensure traceability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Constitution Check passed without violations. | N/A |