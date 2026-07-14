# Implementation Plan: Low-Rank RL for Foresight in LLM Training

**Branch**: `001-low-rank-rl-foresight` | **Date**: 2026-07-12 | **Spec**: `specs/001-low-rank-rl-foresight/spec.md`
**Input**: Feature specification from `/specs/001-low-rank-rl-foresight/spec.md`

## Summary

This project investigates whether the "foresight" phenomenon in LLM reasoning stems from the geometric stability of parameter update subspaces or the supervised distillation objective. The plan executes six experimental variants to isolate the geometric signal: (1) On-Policy Distillation (OPD) to define a stable subspace via SVD of early updates; (2) Low-Rank RL (Hybrid), which projects PPO gradients onto this OPD subspace; (3) Random Projection Baseline, which projects PPO gradients onto a random subspace of the same rank; (4) Random Walk Prior Baseline, which projects onto a subspace derived from a random walk (noise) to control for geometry learned from supervision; (5) Standard RL as a baseline; and (6) **OPD-Initialized RL**, which initializes the RL agent with OPD weights but does *not* project gradients, isolating the effect of the constraint from the initialization. The implementation strictly adheres to CPU-only constraints (limited RAM, bounded runtime) by utilizing a compact parameter model (TinyLlama variant, pruned from a large-scale base model), layer-wise SVD (attention projections only), and mixed-precision (FP16) arithmetic.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `torch` (CPU-only build), `transformers`, `datasets`, `peft`, `scikit-learn` (for SVD/stats), `pandas`, `numpy`, `matplotlib`.  
**Storage**: Local filesystem. `data/` is for raw datasets **only**. `results/` is for **all** derived artifacts including checkpoints, logs, matrices, and plots.  
**Testing**: `pytest` for unit tests on projection logic; integration tests via GitHub Actions workflow.  
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple vCPUs, 7GB RAM).  
**Project Type**: Computational research / ML Experimentation.  
**Performance Goals**: Complete full pipeline (OPD + 6 RL variants + analysis) within 6 hours; memory peak < 7GB.  
**Constraints**: No GPU; no full-model SVD (must be layer-wise or randomized); FP16 precision mandatory; strict seed pinning for reproducibility.  
**Scale/Scope**: GSM8K subset (representative sample); Multiple independent seeds per variant; ~M parameter model.

> **Dataset Note**: The GSMK dataset is sourced from the verified HuggingFace repository (main split). The The TinyLlama model architecture is derived from the TinyLlama Chat series. by reducing hidden size to a parameter count in the hundreds of millions (e.g., hidden_size=512) to fit memory constraints. The base weights are verified; the pruning is performed programmatically.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan mandates pinned seeds in `code/`, deterministic data loading from verified URLs, and isolated virtualenv execution.
- **II. Verified Accuracy**: All dataset citations (GSM8K, TinyLlama weights) reference only the verified URLs provided in the project context. No external unverified sources will be used.
- **III. Data Hygiene**: Raw GSM8K data will be downloaded and checksummed. Derived data (e.g., update matrices) will be stored as new files with documented derivation steps.
- **IV. Single Source of Truth**: All figures and statistics in the final report will be generated programmatically from `results/` logs, not hand-calculated.
- **V. Versioning Discipline**: Plan mandates a specific step `src/utils/hasher.py` to compute SHA-256 hashes of all derived artifacts (logs, metrics, small matrices) in `results/` and store them in `state/`. This explicitly satisfies Principle V.
- **VI. Geometric Constraint Validation**: The plan explicitly includes a validation step (FR-003, FR-005) to verify that Low-Rank RL updates lie within the subspace (cosine similarity ≥ 0.99). Failure here invalidates the variant.
- **VII. Statistical Convergence Rigor**: The plan mandates Multiple independent runs (seeds) per variant and a Wilcoxon signed-rank test (FR-006, SC-003) to validate convergence differences. Power analysis is included.

## Project Structure

### Documentation (this feature)

```text
specs/001-low-rank-rl-foresight/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── loader.py           # GSM8K loading and preprocessing
│   └── checksums.py        # Data integrity verification
├── models/
│   ├── config.py           # TinyLlama-300M config generation (pruning logic)
│   └── backbone.py         # Model definition (attention projection hooks)
├── training/
│   ├── opd_baseline.py     # On-Policy Distillation runner
│   ├── rl_baseline.py      # Standard PPO runner
│   ├── low_rank_rl.py      # Low-Rank RL runner (with projection)
│   ├── random_projection.py # Random Projection Baseline runner
│   ├── random_walk_prior.py # Random Walk Prior Baseline runner
│   ├── opd_initialized_rl.py # OPD-Initialized RL (no projection)
│   └── projection_utils.py # SVD and gradient projection logic
├── analysis/
│   ├── metrics.py          # Convergence, alignment, stats
│   ├── plots.py            # Visualization generation
│   └── power_analysis.py   # Statistical power calculation
├── utils/
│   ├── seeds.py            # Seed pinning
│   ├── memory_monitor.py   # RAM usage tracking
│   └── hasher.py           # SHA-256 hashing for Versioning Discipline
└── cli/
    └── run_experiment.py   # Main entry point (orchestrates ALL scripts)

tests/
├── unit/
│   ├── test_projection.py  # Verify projection math
│   └── test_svd.py         # Verify SVD on small matrices
└── integration/
    └── test_full_pipeline.py # End-to-end run (subset)

requirements.txt
```

**Structure Decision**: A modular `src/` structure is selected to separate data loading, model definition, training variants, and analysis. This facilitates unit testing of the critical projection logic (Constitution Principle VI) and allows independent execution of the six training variants. The `run_experiment.py` CLI is the **single entry point**, orchestrating the data loading, training, and analysis steps. No other entry points are permitted. All scripts are imported and run via this CLI.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Layer-wise SVD instead of full-model SVD | Full-model SVD on a large-scale model exceeds available CPU memory resources.. | A full-model SVD would cause OOM errors, making the experiment impossible on the target hardware. |
| M parameter model instead of 1.1B | 1.1B model + FP16 + optimizer states > 7GB RAM. | Larger models would prevent training within the limited time and memory constraint, even with CPU optimization. |
| Multiple independent seeds per variant | Statistical rigor (Principle VII) requires sufficient power (N=10) to detect medium effect sizes with Wilcoxon test. | A single run or N=3 cannot distinguish "foresight" effects from random stochasticity in RL. |
| Random Walk Prior Baseline (Variant E) | Needed to isolate the effect of *specific* OPD geometry from general low-rank constraints and geometry learned from supervision. | Without this control, any improvement from Low-Rank RL could be attributed to the constraint itself, not the OPD geometry. |
| OPD-Initialized RL Baseline (Variant F) | Needed to isolate the effect of the *projection constraint* from the *initialization* with OPD weights. | Without this, we cannot distinguish if success is due to the geometry constraint or simply starting from a better point. |
| Pruning TinyLlamaB to 300M | No verified M TinyLlama artifact exists; must derive from verified 1.1B source. | Using an unverified or generic 300M model would violate Constitution Principle II (Verified Accuracy). |