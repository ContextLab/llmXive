# Implementation Plan: llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-16 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project will (1) download the open‑access TIDE evaluation CSV and generate a synthetic edge‑case code corpus; (2) parse every code snippet to compute structural metrics, estimating dependency depth and semantic scope for real instances via import analysis; (3) run two detection pipelines – a deterministic static heuristic (“TIDE‑Lite”) and a native CPU generative LLM (“TIDE‑Original”) – logging binary outcomes, latency, and row checksums; (4) merge all artefacts into a single `merged_results.csv` (SSoT); (5) model the association between intrinsic properties and static detection success using logistic regression with 5‑fold CV, validating sample size via Events Per Variable (EPV), and estimating thresholds using Partial Dependence Plots (PDP); (6) conduct stratified McNemar’s tests across complexity bins with Holm‑Bonferroni correction; (7) run a sensitivity sweep over probability cut‑offs; (8) report total execution efficiency; and (9) generate figures/tables mapping to SC-001 through SC-003.

All steps are CPU‑first, deterministic, and fully reproducible on a GitHub Actions free‑tier runner.

## Verified Datasets
- **TIDE Evaluation Dataset**: `

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `datasets==2.20.0` (for HuggingFace download)  
  - `transformers==4.41.2` (using `distilgpt2` for CPU-native inference)  
  - `torch==2.2.2` (CPU build)  
  - `radon==6.0.1` (cyclomatic complexity)  
  - `scikit-learn==1.5.0` (logistic regression, CV, PDP)  
  - `statsmodels==0.14.2` (McNemar, multiple‑comparison)  
  - `pandas==2.2.2`, `numpy==1.26.4`, `matplotlib==3.9.0`  
- **Storage**: File‑system under `data/` (raw CSVs, derived CSVs, checksums, model checkpoint)  
- **Testing**: `pytest` (contract validation, unit tests)  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only)  
- **Constraints**: Wall‑clock ≤ 6 h, average CPU utilisation ≤ 80 % (SC‑004)  
- **Scale/Scope**: ≥ 200 real TIDE instances + ≥ 200 synthetic edge‑case instances (FR‑001, SC‑005)

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are fixed (`seed=42`). Data is fetched from the canonical TIDE URL (verified) and generated deterministically. |
| II. Verified Accuracy | Only the URL listed in the “Verified Datasets” block above is cited. |
| III. Data Hygiene | Raw CSV is checksummed (`sha256`). Every transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | `data/merged_results.csv` is designated as the SSoT for every downstream figure/table. |
| V. Versioning Discipline | All artefacts are content‑hashed and referenced in `state/projects/PROJ-889-…yaml`. |
| VI. Computational Efficiency Boundary Analysis | Implements TIDE‑Lite (deterministic rules) and TIDE‑Original (CPU-native LLM) on TIDE + synthetic data, logs latency, and models detection probability vs. three intrinsic properties. |
| VII. Statistical Validation of Method Efficacy | Stratified McNemar’s tests, Holm‑Bonferroni correction, logistic regression with CV, EPV validation, and PDP threshold estimation are scheduled. |

## Project Structure
```text
specs/001-gene-regulation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── detection_results.schema.yaml
└── tasks.md          # generated later by /speckit-tasks
```

```text
src/
├── data/
│   ├── acquire_real.py          # download TIDE CSV, checksum, map labels
│   ├── generate_synthetic.py    # deterministic synthetic generator
│   └── split_data.py            # train/validation split (seed=42)
├── features/
│   └── extract.py               # AST, radon, import-graph depth/scope analysis
├── pipelines/
│   ├── tide_lite.py             # static heuristic, latency logging
│   ├── tide_original.py         # CPU-native LLM inference, deterministic decoding
│   └── consolidate.py           # join features + both pipeline results
├── analysis/
│   ├── logistic.py              # logistic regression, EPV check, PDP threshold, origin-stratification
│   ├── mcnemar.py               # stratified McNemar + Holm‑Bonferroni
│   ├── sensitivity.py           # probability‑cutoff sweep
│   ├── efficiency.py            # latency aggregation, CPU utilisation check
│   └── visualize.py             # ROC, PDP plots, significance bar plot
└── run_all.py                   # orchestrates all phases
```

## Phase‑by‑Phase Task List (covers all FR/SC)

| Phase | Description | FRs addressed | SCs addressed |
|-------|-------------|---------------|----------------|
| **0. Data Acquisition** | • Download TIDE CSV from verified URL using `datasets.load_dataset`. Verify SHA‑256 checksum.<br>• Run `src/data/generate_synthetic.py` to create ≥ 200 synthetic `.py` files with systematic variation of dependency depth (1‑5), semantic scope, and syntactic complexity.<br>• Map TIDE’s existing annotation to binary `ground_truth_label`.<br>• Enforce FR‑009: cap `dependency_depth` at 5; log a warning if exceeded. | FR‑001, FR‑009 | SC‑005 |
| **1. Feature Extraction** | Parse every `.py` file. For synthetic data, use metadata. For real data, estimate `dependency_depth` by the depth of the import tree within the dataset and `semantic_scope` by identifying relative vs. absolute imports. Compute `ast_depth`, `import_count`, `cyclomatic_complexity`. Write `data/features.csv` with `sha256` checksum. | FR‑001 | – |
| **2. Static Pipeline (TIDE‑Lite)** | Apply deterministic heuristic rules. Record binary `prediction`, per‑instance `latency_ms`, and `sha256` checksum for each row. Join all feature fields. Output `data/tide_lite_enriched.csv` conforming to `contracts/detection_results.schema.yaml`. | FR‑002, FR‑004 | – |
| **3. Generative Pipeline (TIDE‑Original)** | Load `distilgpt2` (CPU-native). Prompt: *“Does the following code contain a hidden problem? Answer Yes/No.”* Use deterministic decoding (`temperature=0.0`). Record `prediction`, `latency_ms`, and `sha256` checksum for each row. Output `data/tide_original_enriched.csv` (schema‑compliant). | FR‑003, FR‑004 | – |
| **4. Consolidation** | Merge `features.csv`, `tide_lite_enriched.csv`, and `tide_original_enriched.csv` on `instance_id` → `data/merged_results.csv` (SSoT). | FR‑001, FR‑002, FR‑003 | – |
| **5. Train/Validation Split** | Deterministically split `merged_results.csv` into training ([deferred]) and hold‑out validation ([deferred]) using `seed=42`. Persist split indices. | FR‑010 | – |
| **6. Logistic Regression & Thresholds** | • Fit `LogisticRegression` on training set: `static_success ~ predictors`. Perform 5‑fold CV; report mean AUC.<br>• **Power Validation**: Verify sample size satisfies EPV ≥ 15 (Events Per Variable) for the 6 predictors (FR‑010).<br>• **Distribution Check**: Fit separate models for `origin==real` and `origin==synthetic` to report coefficients shift.<br>• **Threshold Estimation**: Use Partial Dependence Plots (PDP) to identify the predictor value where predicted probability = 0.5. Bootstrap validation set 1 000 times for 95 % CI.<br>• Save results to `data/analysis_summary.json` (AnalysisSummary entity). | FR‑005, FR‑010 | SC‑001 |
| **7. Stratified McNemar’s Tests** | Bin instances into Low/Medium/High based on `syntactic_complexity` quantiles. Run `statsmodels.stats.contingency_tables.mcnemar` (exact) for each bin. Update `data/analysis_summary.json` with raw p‑values. | FR‑006 | SC‑002 |
| **8. Multiple‑Comparison Correction** | Apply Holm‑Bonferroni (`statsmodels.stats.multitest.multipletests`) to the three bin p‑values; update `data/analysis_summary.json` with corrected p‑values. | FR‑008 | SC‑002 |
| **9. Sensitivity Analysis** | Sweep operating probability cut‑offs `{0.01, 0.05, 0.10}`. Recompute PDP thresholds and compute FP/FN variance. Save `analysis/sensitivity_summary.csv`. | FR‑007 | SC‑003 |
| **10. Efficiency Reporting** | Aggregate `latency_ms` per pipeline, compute total wall‑clock time and verify ≤ 6 h and ≤ 80 % CPU utilisation. Save `analysis/efficiency_report.json`. | – | SC‑004 |
| **11. Figure & Table Generation** | Generate: (a) ROC curve for static pipeline, (b) PDP plots for marginal thresholds, (c) bar plot of corrected McNemar p‑values. All figures read from `merged_results.csv` (SSoT) to satisfy SC-001, SC-002, and SC-003. | – | SC-001, SC-002, SC-003 |

All phases are ordered so that data acquisition precedes any consumption, model inference precedes statistical analysis, and visualisation follows analysis.
