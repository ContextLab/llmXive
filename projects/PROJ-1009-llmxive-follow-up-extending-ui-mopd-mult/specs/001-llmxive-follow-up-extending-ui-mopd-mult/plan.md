# Implementation Plan: llmXive follow-up: extending "UI-MOPD: Multi-Platform On-Policy Distillation for Continual GUI Agent"

**Branch**: `001-gui-topology-transfer` | **Date**: 2026-10-20 | **Spec**: [spec.md]
**Input**: Feature specification from `/specs/001-llmxive-transfer/spec.md`

## Spec Scope Mismatch (flagged for kickback)

FR-001, US-1, and SC-000 require extracting structural metadata **from Uni-GUI logs**, and the assumptions require reproducible UI-MOPD baseline metrics. **No open, directly-downloadable source of Uni-GUI logs exists** (no verified dataset URL is available), and no open dataset pairs widget-tree/navigation-graph structure with GUI-agent execution success in the UI-MOPD sense. This plan therefore executes a clearly-labeled **simulation study** that validates the analysis pipeline end-to-end; it does NOT claim to answer the real-data research question. The spec must be revised to either (a) sanction a simulation/pipeline-validation scope, or (b) name an obtainable dataset. This mismatch is surfaced for spec correction rather than silently substituted. All results below are reported as applying to the simulated setting only.

## Summary
The project must (1) generate a **reproducible simulated UI-topology dataset** ([deferred] records per SC-000) containing widget tree depth, branching factor, navigation-graph connectivity, platform labels, and a binary task-success outcome whose label carries substantial independent noise (see anti-circularity design below), (2) train a lightweight CPU adapter and produce feature-importance scores evaluated against an explicit null control, (3) simulate policy-head selection and benchmark latency/memory against a simulated UI-MOPD baseline, including FR-009 synthetic-variation evaluation, and (4) perform rigorous statistical validation (Bonferroni correction, McNemar's test, sensitivity sweeps).

### Anti-circularity design
Because the simulated outcome is generated from a logistic function of the topology features plus noise, it **cannot test the real research question**; it can only validate the pipeline. To keep the evaluation informative rather than trivially satisfied:
- **Noise calibration sweep**: label noise ε is swept so the Bayes-optimal AUC spans ≈ 0.55 (near-uninformative) to ≈ 0.85; results are reported across the sweep, including regimes where FR-002 thresholds are NOT met.
- **Null control**: a shuffled-label run (labels permuted, destroying all predictor–outcome association) provides the empirical null reference; FR-002's AUC-ROC ≥ 0.80 / Brier ≤ 0.20 are reported **relative to** this control, not as absolute evidence.
- **Uninformative-feature control**: a random noise feature is added to the feature set; its importance must be near zero, verifying the importance machinery.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas==2.2.*`, `networkx==3.2.*`, `torch==2.3.*` (CPU-only), `torch-geometric==2.5.*`, `scikit-learn==1.5.*`, `shap==0.45.*`, `matplotlib==3.9.*`, `statsmodels==0.14.*`, `psutil==5.9.*`
- **Storage**: File-based CSV/Parquet under `data/` (raw simulated data, derived under `data/derived/`)
- **Testing**: `pytest==8.2.*` with contract validation (`jsonschema`)
- **Target Platform**: Linux CI runner (GitHub Actions, 2 CPU cores, ~7 GB RAM)
- **Constraints**: CPU-only; memory ≤ 7 GB; no GPU usage; no external downloads required (simulated generation).

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | All scripts deterministic (seeded RNG); simulated generation scripted; outputs version-hashed. |
| II. Verified Accuracy | No external citations beyond verified URLs; simulation documented internally. |
| III. Data Hygiene | Raw simulated file checksummed; every transformation writes a new file with provenance. |
| IV. Single Source of Truth | Every figure/table traces to one row in `data/derived/structural_records.csv` and one script call. |
| V. Versioning Discipline | Artifact hashes stored in `state/projects/...yaml`; changes update the timestamp. |
| VI. Structural Topology Grounding | Only widget_depth, branching_factor, graph_connectivity are used as real predictors (plus one declared control feature); all claims qualified as simulation-only pending spec revision. |
| VII. Edge-Deployment Efficiency Verification | Latency/memory measured on CI CPU runner; success tolerance ≤ 5 % and ≥ 5× latency reduction reported against the simulated baseline, with the baseline-validity caveat stated. |

## Project Structure
```text
specs/001-gui-topology-transfer/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── structural_record.schema.yaml
src/
├── generate/
│   └── synthetic_dataset.py            # creates structural_records.csv (10,000 records)
├── extract/
│   └── structural_extractor.py          # applies FR-008 cleaning rules
├── model/
│   ├── adapter_gnn.py
│   ├── adapter_linear.py
│   └── train.py
├── evaluate/
│   ├── feature_importance.py
│   ├── sensitivity.py
│   ├── variations.py                    # FR-009 synthetic-variation evaluation
│   ├── benchmark.py
│   └── statistical_tests.py
└── utils/
    ├── data_io.py
    └── logger.py
tests/
├── contract/
│   └── test_structural_record_schema.py
└── unit/
    ├── test_extractor.py
    ├── test_training.py
    └── test_evaluation.py
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Simulation substitutes for Uni-GUI logs | Uni-GUI logs have no verified open source; CI cannot fetch them | Fabricating a mirror or pretending the data is real would violate the fabrication gate; flagged for spec kickback instead |

## Phase Mapping (Coverage of FRs & SCs)

| Phase | Tasks | FR addressed | SC addressed |
|-------|-------|--------------|--------------|
| **0 – Simulated Data Generation & Cleaning** | run `synthetic_dataset.py` to create `structural_records.csv` with **[deferred] records**; apply FR-008 cleaning (missing-data flagging, cycle truncation at depth 10, structural-ambiguity flag); verify ≥ 95 % non-null predictor fields | FR-001 (simulated analog; real-data scope flagged for kickback), FR-008 | SC-000 (≥ 95 % non-null, N ≥ 10,000) |
| **1 – Noise Calibration & Power Analysis** | sweep label-noise ε so Bayes-optimal AUC spans ≈ 0.55–0.85; run shuffled-label null control; a-priori power note for detecting ΔAUC = 0.05 with three predictors under Bonferroni correction | – (supports FR-002 interpretability) | – |
| **2 – Adapter Training** | train GNN (or linear fallback) on structural features with platform_id one-hot covariate; stratified train/val/test split; if memory > 7 GB, stratified sample + linear fallback (FR-008); report AUC-ROC, Brier, and R² **per noise level and vs. the shuffled-label null** | FR-002, FR-008 | SC-001 |
| **3 – Feature Importance** | SHAP (KernelExplainer) + permutation importance for the three topology features **plus the random control feature**; Bonferroni correction; Spearman rank correlation between the two rankings; emit `feature_importance.csv` and importance figure | FR-003, FR-007 | SC-004 |
| **4 – Sensitivity Analysis** | sweep depth ∈ {3,4,5}, branching_factor ∈ {1.0,1.5,2.0}, graph_connectivity ∈ {0.3,0.5,0.7}; report variance of overall success rate; emit sweep figures | FR-006 | SC-006 |
| **5 – Policy Simulation, Benchmark & Variation Evaluation** | (a) generate simulated policy heads under `data/artifacts/policy_heads/`; run adapter-driven head selection on held-out test set; log per-step inference latency, peak RSS, success; write `outputs/adapter_output.csv`; compute McNemar's test vs simulated baseline and latency/memory comparison; (b) **FR-009**: evaluate adapter on synthetic navigation-graph variations (shuffled widget order, altered screen resolution) and report degradation vs the original test set; emit benchmark table and latency/memory figures | FR-004, FR-005, FR-009 | SC-002, SC-003, SC-005, SC-007 |

Each phase includes unit-test checkpoints and contract validation against `contracts/structural_record.schema.yaml`. Result tables/figures are generated within the phase that produces them; no standalone reporting phase is added beyond what the FRs/SCs require.