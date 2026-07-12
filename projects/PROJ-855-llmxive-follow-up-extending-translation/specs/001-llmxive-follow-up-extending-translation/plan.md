# Implementation Plan: llmXive follow-up: extending "Translation as a Bridging Action"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-13 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This feature implements a synthetic data generation and lightweight sequence modeling pipeline to test the hypothesis that "translation-only" wrist trajectories *probabilistically* encode physical stability constraints in bi-manual manipulation under controlled noise. The system generates ≥5,000 episodes using PyBullet on CPU, injects Gaussian noise into trajectories and physics parameters to break deterministic mappings, labels them based on tipping/slippage physics, trains a <10M parameter Transformer, and validates performance against a geometry-only baseline and a shuffled-translation control using McNemar's test. All components are constrained to run on a 2-core CPU, 7GB RAM GitHub Actions runner within 6 hours.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pybullet` (physics engine), `torch` (CPU-only), `pandas`, `numpy`, `scikit-learn`, `pyyaml`  
**Storage**: Local CSV/Parquet files in `data/` (no external database)  
**Testing**: `pytest` (contract tests against schema, unit tests for labeling logic)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational research pipeline (data gen -> model train -> eval)  
**Performance Goals**: <6h total runtime, <7GB RAM peak, <10M model params  
**Constraints**: No GPU/CUDA, no force/torque data, strict translation-only input  
**Scale/Scope**: A large set of synthetic episodes, 4-layer Transformer, 2 baseline comparisons (geometry, shuffled)  

> *Note: All dataset generation is synthetic; no external real-world dataset URLs are cited for training data.*

## Constitution Check

**GATE: Must pass before Phase 0 research.**

| Principle | Status | Compliance Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | Random seeds pinned in `code/`; PyBullet deterministic mode enabled; `requirements.txt` pins all deps. |
| **II. Verified Accuracy** | ✅ N/A | No external citations for data or methodology used; all methods (McNemar, PyBullet) implemented via standard libraries without external theoretical claims requiring citation verification. |
| **III. Data Hygiene** | ✅ Pass | Raw generated data checksummed; derivation scripts produce new files; no PII (synthetic). |
| **IV. Single Source of Truth** | ✅ Pass | Results stored in `data/processed/metrics_report.json` linked to `data/checksums.json`; no hand-typed stats in paper. |
| **V. Versioning Discipline** | ✅ Pass | `state/projects/...yaml` is the authoritative record for hashes; `code/utils/data_utils.py` validates `checksums.json` against state before execution. |
| **VI. CPU-Tractability** | ✅ Pass | <10M params; PyBullet CPU; no GPU libs; batch size tuned for 7GB RAM. |
| **VII. Translation-Only Signal Integrity** | ✅ Pass | Runtime validation in `code/utils/data_utils.py` enforces schema exclusion of rotation/force; script exits fatally if violated. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
projects/PROJ-855-llmxive-follow-up-extending-translation/
├── data/
│   ├── raw/                  # Generated synthetic episodes (parquet)
│   ├── processed/            # Prepped for training & metrics_report.json
│   ├── checksums.json        # Data integrity hashes
│   └── metrics_report.json   # Final statistics linked to data checksums
├── code/
│   ├── requirements.txt      # Pinned dependencies
│   ├── generate_data.py      # PyBullet simulation, noise injection & labeling
│   ├── train_model.py        # Lightweight Transformer training
│   ├── evaluate.py           # Baseline comparison, McNemar's test & metrics report
│   ├── models/
│   │   └── transformer.py    # <10M param architecture
│   └── utils/
│       ├── physics_metrics.py # Tipping/slippage logic
│       └── data_utils.py      # Schema validation, checksum verification & filtering
├── tests/
│   ├── contract/
│   │   └── test_schemas.py   # Validates output against contracts
│   ├── unit/
│   │   └── test_labeling.py  # Physics metric unit tests
│   └── integration/
│       └── test_pipeline.py  # End-to-end CPU feasibility
└── state/
    └── projects/PROJ-855-llmxive-follow-up-extending-translation.yaml
```

**Structure Decision**: Single-project structure chosen to minimize overhead. `data/` is split into `raw` (immutable generation output) and `processed` (model-ready). `code/` is modularized by pipeline stage (gen, train, eval) to ensure strict separation of concerns and reproducibility. `metrics_report.json` ensures traceability for Principle IV.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Synthetic Data Generation** | Real-world bi-manual manipulation data with ground-truth stability labels is unavailable; simulation is required to control variables (tipping/slippage) and ensure "translation-only" input. | Using existing datasets (e.g., MixSub) fails to provide the specific physics labels and translation-only constraint needed for the hypothesis. |
| **Lightweight Transformer** | Must capture temporal dependencies in translation sequences; simple MLPs may miss trajectory dynamics. | Larger models (e.g., with tens of millions of parameters) would exceed 6h/7GB RAM constraints on CPU. |
| **McNemar's Test** | Required to statistically compare paired predictions (model vs. baseline) on the same test set. | Standard t-tests assume independence, which is violated here as both models predict on identical samples. |
| **Noise Injection** | Required to break deterministic simulation mappings and test probabilistic signal sufficiency. | A deterministic simulation would result in a tautological validation where the model simply learns the physics engine's rules. |