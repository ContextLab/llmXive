# Implementation Plan: llmXive follow-up: extending "AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents"

**Branch**: `001-llmxive-agenticsts-followup` | **Date**: 2026-07-05 | **Spec**: `spec.md`
**Input**: Feature specification for dynamic memory policy execution, baseline comparison, and statistical reporting.

## Summary

This feature extends the AgenticSTS testbed by implementing a **Dynamic Memory Policy** that adapts memory retrieval based on real-time game-state entropy. The core technical approach involves:
1.  **Data Ingestion & Ablation**: Parsing the existing AgenticSTS trajectories

The research question is to evaluate the effectiveness of current agentic workflows. The method involves qualitative analysis of trajectory data. References include Smith et al. (year). and performing a **full ablation study** on the training set to generate ground-truth "layer utility" labels (removing layers and re-running the game engine).
2.  **Proxy Validation**: Testing the correlation between static-log-derived utility and ablation-derived utility on a stratified hold-out set. If correlation < 0.7, the proxy is rejected.
3.  **Classifier Training**: Training a lightweight, CPU-tractable classifier (Decision Tree or Logistic Regression) on the **ablation-derived** utility labels (or the validated proxy if correlation is high).
4.  **Re-Simulation**: Re-executing the game engine from the initial states of the test set for three conditions: Dynamic Policy, Static "All-Layers" Baseline, and "No-Store" Random Baseline. This ensures valid comparisons on the same initial state distribution, even if trajectories diverge.
5.  **Statistical Analysis**: Performing significance testing (McNemar's test for paired outcomes if deterministic; Permutation Test or Z-test for non-deterministic diverging trajectories) with Bonferroni correction.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn` (for classifier and stats), `pytest`, `pyyaml`, `agenticsts-engine` (cited source)  
**Storage**: Local CSV/JSON files under `data/` (derived from raw trajectory logs)  
**Testing**: `pytest` (unit tests for entropy calc, integration tests for simulation loops)  
**Target Platform**: Linux (GitHub Actions free-tier: limited CPU resources, ~7GB RAM, no GPU)  
**Project Type**: Computational Research / Data Analysis Pipeline  
**Performance Goals**: Complete simulation of 298 trajectories + statistical analysis within 6 hours on CPU-only runner.  
**Constraints**:
-   **No GPU**: All models must be CPU-tractable (scikit-learn).
-   **Token Budget**: Hard limit on the maximum number of tokens per prompt.
-   **Data Volume**: Must fit within standard workstation RAM; dataset is small.
-   **Statistical Rigor**: Must handle edge cases (NaN entropy, insufficient samples) and trajectory divergence.
-   **Engine Dependency**: Requires the AgenticSTS game engine to be available and runnable from the `code/` directory.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | Random seeds pinned in `code/`. Game engine version pinned. All external data fetched from canonical source. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **COMPLIANT** | Citations in `research.md` validated. Ablation study performed on engine, not logs. |
| **III. Data Hygiene** | **COMPLIANT** | Raw data preserved in `data/raw/`. Derived metrics (entropy, utility) written to `data/processed/` with checksums. |
| **IV. Single Source of Truth** | **COMPLIANT** | All statistics in `paper/` generated from `data/processed/statistical_results.json`. This file conforms to `contracts/result.schema.yaml` (see `data-model.md`). |
| **V. Versioning Discipline** | **COMPLIANT** | Artifacts carry content hashes. `updated_at` timestamps updated on artifact change. |
| **VI. Adaptive Memory Utility Validation** | **COMPLIANT** | Classifier trained on **ablation-derived** utility. Proxy validation (FR-006) is a mandatory gate before training. |
| **VII. Token Budget Independence** | **COMPLIANT** | Win rate measured via game engine ground-truth, independent of predictor features. |

## Project Structure

### Documentation (this feature)
```text
specs/001-llmxive-agenticsts-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── trajectory.schema.yaml
    ├── metric.schema.yaml
    └── result.schema.yaml
```

### Source Code (repository root)
```text
projects/PROJ-990-llmxive-follow-up-extending-agenticsts-a/
├── data/
│   ├── raw/                 # A set of immutable trajectory logs.
│   ├── processed/           # Derived metrics, training splits, simulation results
│   └── engine/              # Cited game engine source (if local) or loader script
├── code/
│   ├── __init__.py
│   ├── config.py            # Paths, seeds, hyperparameters
│   ├── parser.py            # Extract metrics from raw logs
│   ├── ablation.py          # Perform full ablation study (re-run engine)
│   ├── classifier.py        # Train/predict utility (sklearn)
│   ├── entropy.py           # Shannon entropy calculation
│   ├── simulator.py         # Dynamic, Static, Random agents (re-run engine)
│   ├── stats.py             # McNemar, Permutation Test, Bonferroni
│   └── main.py              # Orchestration script
├── tests/
│   ├── unit/                # Unit tests for entropy, parser
│   └── integration/         # End-to-end simulation tests
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (Option 1) is selected. The scope is a data analysis pipeline. Separating `data/` and `code/` ensures strict adherence to Data Hygiene (Constitution Principle III).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Full Ablation Study** | Required to generate ground-truth labels (FR-001) and avoid circularity. | Using static logs as ground truth creates a tautology (predicting frequency of retrieval based on retrieval logs). |
| **Proxy Validation Gate** | Required to ensure the proxy is valid before training (FR-006). | Training on a potentially invalid proxy risks learning spurious relationships. |
| **Statistical Validity Check** | Required to handle trajectory divergence (Methodology Concern). | McNemar's test is invalid for non-paired diverging trajectories; a fallback test is required. |
| **Engine Re-Simulation** | Required to generate new outcomes for Dynamic policy (Methodology Concern). | Logs alone cannot generate new outcomes for a different memory policy. |
