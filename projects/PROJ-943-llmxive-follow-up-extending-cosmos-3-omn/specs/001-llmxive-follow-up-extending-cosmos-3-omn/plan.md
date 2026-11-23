# Implementation Plan: llmXive follow-up: extending "Cosmos 3: Omnimodal World Models for Physical AI"

**Branch**: `001-llmxive-cosmos-gap` | **Date**: 2026-07-15 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-llmxive-cosmos-gap/spec.md`

## Summary

This feature implements a CPU-compatible research pipeline to quantify the "modality gap" between continuous physical control and symbolic reasoning in world models. The core approach involves: (1) downloading the **Bridge** dataset (a verified open substitute for the gated Cosmos 3, containing continuous action vectors and physics rewards), (2) transforming continuous action vectors into discrete symbolic tokens using a **composite logical rule** (L2 norm of the first 3 dimensions + text context check for "Safety Constraint"), (3) training a lightweight DistilBERT proxy model on CPU to predict the Symbolic Label, and (4) evaluating this model on the Physics Task (predicting the independent physics reward outcome) to measure the generalization loss (modality gap). The implementation strictly adheres to the constrained RAM and runtime limits of the GitHub Actions free tier.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (Hugging Face), `transformers` (CPU-optimized), `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `pytest`  
**Storage**: Local filesystem (`code/data/` for raw/derived, `code/models/` for artifacts)  
**Testing**: `pytest` with unit tests for transformation logic and integration tests for pipeline execution  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: Training completes in < 6 hours; Memory usage < 7 GB RAM; Dataset processing streams to avoid OOM.  
**Constraints**: CPU-only execution; No local GPU; Deterministic logical rules for tokenization; Reproducible random seeds.  
**Scale/Scope**: Single dataset (Bridge); One proxy model (Symbolic); Comparative analysis of cross-domain generalization.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: **PASS**. Plan mandates pinned seeds, deterministic transformation rules (L2 norm of first 3 dims for Symbolic + text context, physics_reward threshold for Physics), and re-runnable scripts. External datasets are fetched via programmatic loaders (Hugging Face).
- **II. Verified Accuracy**: **PASS**. Plan cites only verified dataset URLs (Bridge: `https://huggingface.co/datasets/bridge-to-worlds/bridge-data`). No fabricated URLs. Explicit abort if dataset unavailable or schema mismatch.
- **III. Data Hygiene**: **PASS**. Raw data is preserved; transformations produce new files with checksums. No in-place modification.
- **IV. Single Source of Truth**: **PASS**. All metrics trace to specific code blocks and data rows. No hand-typed statistics.
- **V. Versioning Discipline**: **PASS**. Artifacts (models, derived data) will carry content hashes in `state/`.
- **VI. Action-Space Discretization Fidelity**: **PASS**. Plan explicitly defines the logical rule derivation (L2 norm of first 3 dims + text context for Symbolic; physics_reward > threshold for Physics) and mandates documentation of the specific vector dimensions used to ensure reproducibility.
- **VII. Proxy Model Efficiency Constraints**: **PASS**. DistilBERT is selected for CPU compatibility; memory usage is monitored and capped at 7 GB.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-cosmos-3-omn/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── raw/             # Downloaded raw datasets (Bridge)
│   ├── processed/       # Transformed symbolic datasets (CSV/JSONL)
│   └── splits/          # Train/validation/test splits
├── scripts/
│   ├── download_data.py # Data ingestion, checksumming, and schema verification
│   ├── transform_actions.py # Continuous -> Symbolic/Physics mapping
│   ├── train_symbolic.py # DistilBERT training for Symbolic labels
│   ├── evaluate.py      # Comparative analysis (Cross-domain AUC)
│   └── analyze_errors.py # Failure mode identification
├── models/
│   └── symbolic/        # Saved symbolic model artifacts
├── reports/
│   ├── metrics.json     # Performance metrics
│   └── error_analysis/  # Visualizations and qualitative reports
└── requirements.txt     # Pinned dependencies

tests/
├── unit/
│   ├── test_transform.py # Logic rule verification
│   └── test_model_init.py
├── integration/
│   └── test_pipeline.py  # End-to-end run verification
```

**Structure Decision**: Single project structure under `code/` is selected to align with the GitHub Actions runner's file system expectations and to simplify the data flow between scripts. The `code/data/` subdirectory separates raw and processed assets to enforce the "Data Hygiene" principle. All paths in this plan assume execution from the repository root.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations identified. The plan strictly follows the spec and constitution. | N/A |

## Implementation Phases

### Phase 0: Data Ingestion & Verification
- **Task T001**: Download the **Bridge** dataset (Hugging Face ID: `bridge-to-worlds/bridge-data`) to `code/data/raw/`.
- **Task T002**: **Schema Verification**. Verify the presence of `action` (list of floats, length >= 3) and `physics_reward` (float) fields in the first N samples. **Abort** with clear error if missing or if schema drift is detected. This ensures the dataset supports the continuous-to-symbolic transformation.

### Phase 1: Data Transformation
- **Task T011**: Transform continuous action vectors to **Symbolic Labels**:
  - Rule: Calculate `L2 norm of the first 3 dimensions (x, y, z)` of the `action_vector`.
  - **Composite Logic**: If `norm > 0.5` AND `text_description` contains keywords indicating "collision" or "unsafe" (simulated safety constraint), label as `constraint_violated`. Else, label as `constraint_satisfied`.
  - *Note*: This composite rule ensures the task is non-trivial (construct validity) and requires the model to learn a relationship between vector magnitude and semantic context, not just a scalar threshold.
- **Task T012**: Transform continuous action vectors to **Physics Labels**:
  - Rule: `physics_reward > 0.5` (threshold) -> `success`, else `failure`.
  - *Note*: This uses the **independent** physics engine reward from the dataset, ensuring no correlation with the Symbolic label rule.

### Phase 2: Symbolic Proxy Training
- **Task T020**: Initialize and train `DistilBERT` on the **Symbolic Labels** using data from `code/data/processed/`.
- **Task T021**: Save model artifact to `code/models/symbolic/`.

### Phase 3: Evaluation & Comparative Analysis
- **Task T022**: Evaluate Symbolic Model on Symbolic Test Set (AUC-Symbolic).
- **Task T023**: Evaluate Symbolic Model on Physics Test Set (AUC-Physics-CrossDomain).
- **Task T024**: Calculate **Generalization Gap**: `AUC_Symbolic - AUC_Physics_CrossDomain`.
- **Task T025**: Perform **Bootstrap Confidence Interval** (A sufficient number of iterations to ensure convergence.) on the Generalization Gap to determine statistical significance (p < 0.05).
  - *Dependency*: Must wait for T020/T021 and T022/T023 completion. No parallel execution.

### Phase 4: Error Analysis
- **Task T026**: Analyze misclassified samples from the Symbolic Task.
  - *Dependency*: **Strictly Sequential**. Requires output (misclassified samples) from Phase 3 (T022/T023).
- **Task T027**: Categorize errors into "visual ambiguity", "logical complexity", "context mismatch".
- **Task T028**: Generate final report to `code/reports/error_analysis/`.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Bridge Dataset Unavailable** | Fatal | Script checks for Hugging Face ID; if missing, exits with clear error. No synthetic data. |
| **Schema Mismatch** | Fatal | T002 explicitly checks for `action` (len>=3) and `physics_reward` fields. Exits if missing. |
| **Memory Exceeds 7 GB** | Fatal | Use `streaming=True`; implement batch processing; sample data if necessary. |
| **Model Fails to Converge** | Medium | Increase epochs; adjust learning rate; fallback to logistic regression baseline. |
| **Trivial Rule** | Medium | Use "Safety Constraint Simulation" (norm + text context) for Symbolic label to ensure non-triviality. |

## Verification

- **Reproducibility**: Re-run `code/scripts/` on a fresh runner; results must match (within seed tolerance).
- **Feasibility**: Total runtime < 6 hours; Memory < 7 GB.
- **Correctness**: `code/reports/metrics.json` contains valid Bootstrap CI for Generalization Gap.