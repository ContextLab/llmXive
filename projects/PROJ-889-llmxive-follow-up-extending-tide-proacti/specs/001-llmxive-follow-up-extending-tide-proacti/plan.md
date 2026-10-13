# Implementation Plan: llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

**Branch**: `001-llmxive-follow-up-extending-tide-proacti` | **Date**: 2026-10-13 | **Spec**: [spec.md](../specs/001-llmxive-follow-up-extending-tide-proacti/spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-tide-proacti/spec.md`

## Summary
The project must (1) ingest a real code dataset (CodeXGLUE defect‑detection) and a synthetic generation script, (2) extract structural code features, (3) run two detection pipelines (deterministic static “TIDE‑Lite” and generative “TIDE‑Original” using a CPU‑quantized LLM), (4) consolidate results into a single joined table that satisfies the contract schema, (5) perform statistical analyses (logistic regression with marginal threshold estimation, stratified McNemar’s tests, sensitivity analysis, and multiple‑comparison correction) to identify the intrinsic “complexity threshold” where static detection drops below 0.5 probability, and (6) report efficiency metrics.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers==4.41.2`, `torch==2.2.2` (CPU build), `datasets==2.20.0`, `radon==6.0.1`, `scikit‑learn==1.5.0`, `statsmodels==0.14.2`, `pandas==2.2.2`, `numpy==1.26.4`, `matplotlib==3.9.0`  
- **Storage**: File‑system under `data/` (raw, derived CSVs, model checkpoints)  
- **Testing**: `pytest` (unit tests for parsers, pipeline runners, contracts)  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only)  
- **Constraints**: Total wall‑clock ≤ 6 h, average CPU ≤ 80 % (SC‑004)  
- **Scale/Scope**: ≥ 200 real instances (CodeXGLUE) + A substantial set of synthetic edge‑case instances (FR‑005)

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are pinned (`seed=42`), data fetched from canonical URLs or generated deterministically, scripts are deterministic. |
| II. Verified Accuracy | All external citations limited to the two verified URLs listed in the spec. |
| III. Data Hygiene | Raw files checksummed, each transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | **`data/merged_results.csv` is designated as the authoritative Single Source of Truth (SSoT) for all downstream figures and tables.** Every figure, statistic, and table is generated directly from this file, satisfying Principle IV. |
| V. Versioning Discipline | All artefacts (datasets, models, results) are content‑hashed and referenced in `state/projects/...yaml`. |
| VI. Computational Efficiency Boundary Analysis | The plan implements TIDE‑Lite static rules, a quantized GPT‑2 model of comparable scale (on the order of hundreds of millions of parameters) in 8‑bit on CPU, logs latency, and models detection probability vs. three intrinsic properties. |
| VII. Statistical Validation of Method Efficacy | Stratified McNemar’s tests, Holm‑Bonferroni correction, logistic regression with marginal threshold estimation, and bootstrap validation are explicitly scheduled. |

## Project Structure
```text
specs/001-llmxive-follow-up-extending-tide-proacti/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── detection_results.schema.yaml
├── tasks.md          # generated later by /speckit-tasks
```

```text
src/
├── data/                 # download scripts, raw & derived CSVs
├── features/             # AST, cyclomatic complexity extraction
├── pipelines/
│   ├── tide_lite.py      # static heuristic
│   └── tide_original.py  # generative LLM inference
├── analysis/
│   ├── logistic.py
│   ├── mcnemar.py
│   ├── sensitivity.py
│   └── efficiency.py
└── run_all.py            # orchestrates all phases
```

## Phase‑by‑Phase Task List (covers all FR/SC)

| Phase | Description | FRs addressed | SCs addressed |
|-------|-------------|---------------|----------------|
| **0. Data Acquisition** | • Download CodeXGLUE defect‑detection dataset via `datasets.load_dataset("code_x_glue", "defect_detection")` (open, no verified URL).<br>• Run provided synthetic generation script to produce a sizable collection of edge‑case `.py` files.<br>• For real instances, run a lightweight manual labeling script that maps defect‑detection labels to the required hidden‑problem binary (`ground_truth_label`).<br>• Verify checksum, cap `dependency_depth ≤ 5` (FR‑009). | FR‑001, FR‑009 | SC‑005 |
| **1. Feature Extraction** | Parse every code file with Python `ast` and `radon` to compute:<br>• `ast_depth`<br>• `import_count`<br>• `cyclomatic_complexity`<br>Store in `features.csv` (includes `origin` field). | FR‑001 | – |
| **2. Static Pipeline (TIDE‑Lite) – Enriched Results** | Apply deterministic rule‑set (e.g., depth > 3 → flag, import > 2 → flag). Record binary outcome, `latency_ms`, **and join the feature fields** (`dependency_depth`, `semantic_scope`, `syntactic_complexity`, `ast_depth`, `import_count`, `cyclomatic_complexity`, `sha256`). Write `tide_lite_enriched.csv`. **Each row conforms to `contracts/detection_results.schema.yaml`.** | FR‑002, FR‑004 | – |
| **3. Generative Pipeline (TIDE‑Original) – Enriched Results** | Load quantized `gpt2` (8‑bit, CPU) via `transformers` and `bitsandbytes`. Prompt with code snippet and ask for hidden‑problem detection. Use deterministic decoding (`temperature=0.0`, `top_k=1`). Record binary outcome, `latency_ms`, **and join the feature fields** as above. Write `tide_original_enriched.csv`. **Each row conforms to `contracts/detection_results.schema.yaml`.** | FR‑003, FR‑004 | – |
| **4. Consolidation** | Merge `features.csv`, `tide_lite_enriched.csv`, and `tide_original_enriched.csv` on `instance_id` → `merged_results.csv`. This file contains **all** columns required by `contracts/detection_results.schema.yaml` (including `sha256`). | FR‑001, FR‑002, FR‑003 | – |
| **5. Train/Validation Split** | Randomly split (seed = 42) into training ([deferred]) and hold‑out validation ([deferred]). Persist split indices. | FR‑010 | – |
| **6. Logistic Regression** | • Fit logistic model on training set: `static_success ~ dependency_depth + semantic_scope + syntactic_complexity + origin` (origin as categorical covariate).<br>• Perform 5‑fold CV, report mean AUC.<br>• **Power analysis** using `statsmodels.stats.power` to confirm ≥ 80 % power for the 3‑predictor model.<br>• **Threshold estimation**: for each predictor, fix the other predictors at their training‑set mean, then binary‑search the predictor value where predicted probability = 0.5 (tolerance 0.01).<br>• **Bootstrap validation**: repeat threshold search on 1000 bootstrap resamples of the validation set; report mean threshold and 95 % CI.<br>Output `logistic_summary.json`. | FR‑005, FR‑010 | SC‑001 |
| **7. Stratified McNemar’s Tests** | Bin instances into Low/Medium/High complexity based on `syntactic_complexity` quantiles. For each bin, build 2×2 contingency table (static vs. generative TP/FP) and run `statsmodels.stats.contingency_tables.mcnemar`. Store p‑values in `mcnemar_results.csv`. | FR‑006 | SC‑002 |
| **8. Multiple‑Comparison Correction** | Apply Holm‑Bonferroni to the three bin p‑values, store corrected p‑values in the same CSV. | FR‑008 | SC‑002 |
| **9. Sensitivity Analysis** | Sweep the probability cutoff used to define the “operating point” (`{0.01, 0.05, 0.10}`) and recompute marginal thresholds for each predictor. Compute variance of FP/FN rates across cutoffs; store in `sensitivity_summary.csv`. | FR‑007 | SC‑003 |
| **10. Efficiency Reporting** | Sum all `latency_ms` per pipeline, compute total wall‑clock time, and verify ≤ 6 h & CPU ≤ 80 % (record in `efficiency_report.json`). | – | SC‑004 |
| **11. Figure & Table Generation** | Produce final visualisations (ROC curve, threshold heatmap per predictor, McNemar significance bar plot) under `outputs/`. All figures are generated directly from `merged_results.csv`, satisfying the SSoT requirement. | – | – |

All phases are ordered so that data is downloaded before any consumption, models are fitted before evaluation, and figures are generated after analyses.
