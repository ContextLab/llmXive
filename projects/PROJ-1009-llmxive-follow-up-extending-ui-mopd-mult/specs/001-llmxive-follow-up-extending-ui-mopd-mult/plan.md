# Implementation Plan: llmXive follow‑up: extending "UI‑MOPD: Multi‑Platform On‑Policy Distillation for Continual GUI Agent"

**Branch**: `001-gui-topology-transfer` | **Date**: 2026-10-24 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-gui-topology-transfer/spec.md`

## Summary
The project must (1) extract non‑visual structural metadata (widget tree depth, branching factor, navigation‑graph connectivity) from the **Uni‑GUI** logs (or an approved synthetic substitute), (2) train a lightweight CPU‑only adapter to predict task‑success probability, (3) compute rigorous feature importance, (4) simulate policy‑head selection and benchmark efficiency against the UI‑MOPD baseline, and (5) run sensitivity and synthetic‑variation analyses.  

### Spec Amendment Required
The current specification mandates the use of **real** Uni‑GUI logs and **real** UI‑MOPD policy heads, neither of which are openly downloadable. Until the spec is amended to permit synthetic substitutes or an open repository is provided, the following phases are **blocked** and will remain pending:
- **Phase 0 – Data Acquisition & Extraction** (FR‑001, FR‑008, SC‑000)  
- **Phase 4 – Policy‑Head Simulation & Benchmark** (FR‑004, FR‑005, SC‑002, SC‑003, SC‑005)

**Synthetic Data Design (if spec amendment is granted)**  
When allowed, a synthetic Uni‑GUI‑style dataset will be generated using a latent variable‑driven label model (see Research section). The latent variable accounts for the majority of variance in `task_success`, while the three topology features contribute only modestly. This anti‑circularity design prevents the outcome from being a deterministic function of the predictors, ensuring a genuine test of topology‑only predictive power.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas==2.2.*`, `networkx==3.2.*`, `torch==2.3.*` (CPU‑only), `torch-geometric==2.5.*`, `scikit-learn==1.5.*`, `shap==0.45.*`, `matplotlib==3.9.*`, `statsmodels==0.14.*`, `psutil==5.9.*`
- **Storage**: File‑based CSV/Parquet under `data/` (raw, derived) and `outputs/`.
- **Testing**: `pytest==8.2.*` with JSON‑Schema contract validation.
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ~7 GB RAM, no GPU).
- **Constraints**: CPU‑only; memory ≤ 7 GB; all scripts deterministic (seeded RNG).

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | All scripts deterministic; seeds recorded; outputs hashed. |
| II. Verified Accuracy | No external citations beyond verified URLs. |
| III. Data Hygiene | Raw and derived files checksummed; transformations write new files with provenance. |
| IV. Single Source of Truth | Every figure/statistic traced to a single CSV row and script call. |
| V. Versioning Discipline | Artifact hashes stored in `state/projects/...yaml`; timestamps updated on change. |
| VI. Structural Topology Grounding | Only `widget_depth`, `branching_factor`, `graph_connectivity` used as predictors. |
| VII. Edge‑Deployment Efficiency Verification | Latency and memory measured on CI CPU runner; performance gains reported only after spec amendment. |

## Project Structure
```text
specs/001-gui-topology-transfer/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── structural_record.schema.yaml
    ├── policy_head.schema.yaml
    └── adapter_output.schema.yaml

src/
├── generate/
│   └── synthetic_dataset.py            # realistic label generator (latent variable)
├── extract/
│   └── structural_extractor.py        # implements FR‑001 & FR‑008 cleaning
├── model/
│   ├── adapter_gnn.py
│   ├── adapter_linear.py
│   └── train.py
├── evaluate/
│   ├── feature_importance.py
│   ├── sensitivity.py
│   ├── variations.py
│   ├── benchmark.py
│   └── statistical_tests.py
└── utils/
    ├── data_io.py
    └── logger.py

tests/
├── contract/
│   ├── test_structural_record_schema.py
│   ├── test_policy_head_schema.py
│   └── test_adapter_output_schema.py
└── unit/
    ├── test_extractor.py
    ├── test_training.py
    └── test_evaluation.py
```

## Phase Mapping (Coverage of FRs & SCs)

| Phase | Tasks (script) | FR addressed | SC addressed | Notes / Blockers |
|-------|----------------|--------------|--------------|------------------|
| **0 – Data Acquisition & Extraction** | `src/extract/structural_extractor.py` on **real Uni‑GUI logs** or **approved synthetic substitute** | FR‑001, FR‑008 | SC‑000 | **Blocked** until spec amendment authorises synthetic data or provides open logs. |
| **1 – Adapter Training** | `src/model/train.py` (GNN *or* linear fallback) | FR‑002 (including fallback handling) | SC‑001 | Enforces **absolute** thresholds AUC‑ROC ≥ 0.80 and Brier ≤ 0.20; aborts if not met. |
| **2 – Feature Importance** | `src/evaluate/feature_importance.py` (SHAP + permutation) | FR‑003, FR‑007 | SC‑004 | Bonferroni correction across three topology features. |
| **2b – Platform‑Masking Control** | `src/model/train.py` with `--mask-platform` flag | FR‑003 (control) | SC‑004 | Randomises `platform_id` each epoch to isolate structural effect. |
| **3 – Sensitivity Analysis** | `src/evaluate/sensitivity.py` (depth ∈ {3, 4, 5} etc.) | FR‑006 | SC‑006 | Variance of overall success rate must be ≤ 0.02. |
| **4 – Policy‑Head Simulation & Benchmark** | `src/evaluate/benchmark.py` (lookup table, latency & memory logging) | FR‑004, FR‑005 | SC‑002, SC‑003, SC‑005 | **Blocked**: requires spec amendment to permit simulated policy‑head artifacts. |
| **5 – Synthetic‑Variation Evaluation** | `src/evaluate/variations.py` (graph shuffle, resolution change) | FR‑009 | SC‑007 | Runs on the test split produced in Phase 1. |
| **6 – Contract Validation** | `tests/contract/*` | FR‑001 (data‑hygiene), FR‑004 (adapter output) | – | Validates CSV outputs against schemas in `contracts/`. |

All phases are ordered so that data is obtained before extraction, extraction before training, training before importance/sensitivity/benchmark, and benchmark before final reporting.

## Required Spec Amendments (to unblock the pipeline)

1. **Data Source Amendment** – Add an explicit permission to use a *synthetic* Uni‑GUI‑style dataset (or point to an open dataset that contains equivalent structural metadata and success outcomes).  
2. **Baseline Amendment** – Permit the use of *simulated* UI‑MOPD policy‑head artifacts for benchmarking, or provide a public repository of such artifacts.  
3. **Performance Threshold Clarification** – Confirm that FR‑002’s absolute thresholds are mandatory; the pipeline now aborts if they are not met.

Once these amendments are incorporated, the blocked phases (0 and 4) can be executed on the CI runner without violating any MUST.

---



## Additional Anti‑Circularity Note
When the synthetic dataset generator is authorized, it will follow the design described in the **Research** document: a dominant latent variable `z` (sampled from `N(0,1)`) determines `task_success`, while the topology term `h` (a modest function of `widget_depth`, `branching_factor`, `graph_connectivity`) contributes only a small noisy component. This ensures that any predictive performance of the lightweight adapter reflects genuine explanatory power of the structural features beyond what is explained by `z`. The absolute performance thresholds in FR‑002 therefore serve as a stringent test of this explanatory power.
