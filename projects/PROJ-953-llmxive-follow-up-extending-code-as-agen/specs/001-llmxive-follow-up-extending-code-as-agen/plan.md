# Implementation Plan: llmXive follow-up: extending "Code as Agent Harness"

**Branch**: `001-llmxive-harness-extension` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-follow-up-extending-code-as-agen/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-code-as-agen/spec.md`

## Summary

This project investigates the correlation between code structural complexity and the necessity of dynamic verification (operationalized as test suite failure) in agent harnesses. The technical approach involves ingesting SWE-bench Verified and AgentBench OS datasets, generating ground-truth execution outcomes (Pass/Fail) via CPU-only re-execution, extracting structural metrics (dependency depth, cyclomatic complexity) via `tree-sitter`, and training a CPU-only logistic regression or Random Forest model.

**Critical Methodological Note**: The goal is to identify decision thresholds that minimize dynamic execution while maintaining a false-negative rate (FNR) ≤ 0.1%. However, given the expected low base-rate of failures and sample size constraints, achieving a statistically stable [deferred] FNR estimate is challenging. The study is structured as a **Pilot -> Feasibility Test**:
1.  **Pilot**: Estimate the base failure rate.
2.  **Feasibility**: If the base rate is too low, the study reports the minimum achievable FNR with confidence intervals and explicitly concludes that static analysis may be insufficient for the 0.1% safety threshold.
3.  **Outcome**: A valid finding is either a viable threshold OR a robust demonstration of the limits of static analysis for this specific safety constraint.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (HuggingFace), `tree-sitter` (and language bindings), `scikit-learn`, `pandas`, `networkx`, `radon`, `pyyaml`, `pytest`, `jsonschema`  
**Storage**: Local filesystem (`data/` for raw/derived CSVs/JSONs, `models/` for pickled models)  
**Testing**: `pytest` with contract validation against `contracts/task_artifact.schema.yaml`, `contracts/structural_metric.schema.yaml`, and `contracts/model_outcome.schema.yaml`.  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ~7GB RAM)  
**Project Type**: Research/Data Pipeline  
**Performance Goals**: Complete full pipeline (ingest → analyze → model) within 6 hours on CPU-only runner.  
**Constraints**: No GPU/CUDA. No large LLM inference. Memory usage must stay < 7GB (requires sampling if necessary).  
**Scale/Scope**: Representative subset of SWE-bench/AgentBench (target ~500 tasks for pilot, up to 1000 if feasible).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinning random seeds in `code/`, fetching datasets from canonical HuggingFace URLs (verified list provided), and ensuring `requirements.txt` is used. All scripts will be runnable end-to-end on a fresh runner.
- **II. Verified Accuracy**: All dataset citations in `research.md` will strictly use the provided verified URLs. No external URLs will be invented. The `Reference-Validator` logic will be simulated in the testing phase to ensure citation integrity.
- **III. Data Hygiene**: Raw data downloads will be checksummed. Derived datasets (with features) will be written to new files with documented derivation steps. No in-place modification of raw files.
- **IV. Single Source of Truth**: All figures and statistics in the final report will be generated programmatically from the `data/` artifacts. No hand-typed numbers.
- **V. Versioning Discipline**: Artifacts will carry content hashes. The pipeline includes a `scripts/update_state.py` script that runs at the end of each major phase to update the `state/projects/...yaml` file, satisfying the blocking gate requirement.
- **VI. Structural Verification Fidelity**: The core methodology explicitly compares static structural metrics against a full-environment re-execution baseline (FR-003, FR-005). The false-negative rate constraint (≤ 0.1%) is a hard gate for "safe" classification, but the study is designed to validly report "unsafe" if the threshold cannot be met.
- **VII. Graph-Based Traceability**: `tree-sitter` will be used to generate dependency graphs. The mapping between raw code and graph structures will be preserved in the `data/` artifacts (serialized as JSON) to ensure metric consistency.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-harness-extension/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── raw/             # Downloaded parquet files (checksummed)
│   ├── processed/       # Derived CSVs with features and labels
│   └── graphs/          # Serialized dependency graphs (JSON)
├── scripts/
│   ├── ingest.py        # Dataset download and ground truth extraction
│   ├── extract_features.py # tree-sitter parsing and metric calculation
│   ├── train_model.py   # Model training and threshold analysis
│   ├── evaluate.py      # Sensitivity analysis and reporting
│   └── update_state.py  # Updates project state file (Constitution Principle V)
├── models/
│   └── [model_name].pkl # Trained models
├── tests/
│   ├── contract/        # Schema validation tests (task_artifact, structural_metric, model_outcome)
│   ├── unit/            # Feature extraction unit tests
│   └── integration/     # Pipeline integration tests
├── requirements.txt
└── main.py              # Orchestration entry point
```

**Structure Decision**: A single `code/` directory is selected to simplify the CPU-only pipeline. Data is separated into `raw` (immutable) and `processed` (derived). This aligns with Constitution Principle III (Data Hygiene) and Principle VII (Graph-Based Traceability).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Full Environment Re-execution | Required by FR-003 and Constitution Principle VI to establish ground truth for "verification necessity". | Static-only baselines cannot validate the "need for dynamic execution" hypothesis. |
| `tree-sitter` + `networkx` | Required by Constitution Principle VII to generate consistent dependency graphs for metric calculation. | Regex-based parsing is insufficient for accurate dependency depth and semantic complexity. |
| Sensitivity Analysis Sweep | Required by FR-005 to verify safety constraints across thresholds. | A single threshold point does not prove robustness or identify the optimal trade-off. |
| Pilot Phase for Base-Rate | Required to address statistical power concerns for rare events ([deferred] FNR). | Jumping straight to modeling without knowing the failure rate risks a statistically invalid conclusion. |