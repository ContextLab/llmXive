# Implementation Plan: llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-17 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project will (1) download the open‑access TIDE evaluation CSV from a verified HuggingFace URL and verify its checksum; (2) generate a deterministic synthetic code corpus (≥ 200 instances) that systematically varies dependency depth, semantic scope, and syntactic complexity, capping depth at 5 (FR‑009); (3) parse every code snippet to compute structural metrics (AST depth, import count, cyclomatic complexity, etc.) producing a feature matrix; (4) run two detection pipelines on the unified matrix – a deterministic static heuristic (“TIDE‑Lite”) and a CPU‑native quantized generative LLM (“TIDE‑Original”) – logging binary outcomes and per‑instance latency; (5) merge all artefacts into a single SSoT (`merged_results.csv`) that conforms to a JSON‑Schema contract; (6) fit logistic regression with 5‑fold CV on the training split, verify Events‑Per‑Variable ≥ 15, and identify the predictor value where predicted static‑detection probability = 0.5 via Partial Dependence Plots (PDP) with bootstrap confidence intervals; (7) conduct stratified exact McNemar’s tests across low/medium/high complexity bins and apply Holm‑Bonferroni correction; (8) perform a sensitivity sweep over probability cut‑offs {0.01, 0.05, 0.10} to assess threshold stability; (9) aggregate latency statistics to confirm wall‑clock ≤ 6 h and average CPU utilisation ≤ 80 %; (10) generate figures and tables that directly trace back to rows in `merged_results.csv`. All steps are **CPU‑first** and fully reproducible on a GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `datasets==2.20.0` (download TIDE CSV)  
  - `transformers==4.41.2` (CPU‑native `distilgpt2`)  
  - `torch==2.2.2` (CPU wheel)  
  - `radon==6.0.1` (cyclomatic complexity)  
  - `scikit-learn==1.5.0` (logistic regression, CV, PDP)  
  - `statsmodels==0.14.2` (McNemar, Holm‑Bonferroni)  
  - `pandas==2.2.2`, `numpy==1.26.4`, `matplotlib==3.9.0`, `psutil==5.9.8`  
- **Storage**: Files under `data/` (raw CSV, synthetic `.py` files, derived CSVs, checksums)  
- **Testing**: `pytest` with contract validation (`tests/contract`)  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only)  
- **Constraints**: Total wall‑clock ≤ 6 h, peak RAM ≤ 7 GB, average CPU utilisation ≤ 80 % (SC‑004)  
- **Scale/Scope**: ≥ 200 real TIDE instances + ≥ 200 synthetic edge‑case instances (FR‑001, SC‑005)

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed seeds (`seed=42`, `torch.manual_seed(42)`); data fetched from the verified URL; all scripts deterministic. |
| II. Verified Accuracy | Only the URL listed in the “Verified datasets” block is cited for the real dataset. |
| III. Data Hygiene | Raw CSV checksum recorded (`sha256`); every transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | `data/merged_results.csv` is the sole source for every downstream figure/table. |
| V. Versioning Discipline | All artefacts are content‑hashed and referenced in `state/projects/PROJ-889-…yaml`. |
| VI. Computational Efficiency Boundary Analysis | Implements TIDE‑Lite (deterministic static rules) and TIDE‑Original (CPU‑native `distilgpt2`), logs latency, models detection probability vs. three intrinsic properties. |
| VII. Statistical Validation of Method Efficacy | Performs stratified McNemar’s tests, Holm‑Bonferroni correction, logistic regression with CV, EPV check, and PDP threshold estimation. |

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
│   ├── acquire_real.py          # download TIDE CSV, verify SHA‑256, map ground_truth_label
│   ├── generate_synthetic.py    # deterministic synthetic generator (depth 1‑5, scope, complexity)
│   └── split_data.py            # train/validation split (seed=42)
├── features/
│   └── extract.py               # AST, radon, import‑graph analysis → feature CSV
├── pipelines/
│   ├── tide_lite.py             # static heuristic, latency logging
│   ├── tide_original.py         # CPU‑native `distilgpt2` inference, deterministic decoding
│   └── consolidate.py           # join features + both pipeline results
├── analysis/
│   ├── logistic.py              # logistic regression, EPV check, PDP threshold, bootstrap CI
│   ├── mcnemar.py               # stratified exact McNemar + Holm‑Bonferroni
│   ├── sensitivity.py           # probability‑cutoff sweep, variance reporting
│   ├── efficiency.py            # latency aggregation, CPU utilisation check
│   └── visualize.py             # ROC, PDP, significance bar plots
└── run_all.py                   # orchestrates all phases in order
```

## Phase‑by‑Phase Task List (covers all FR/SC)

| Phase | Description | FRs addressed | SCs addressed |
|-------|-------------|---------------|----------------|
| **0. Data Acquisition** | • Use `datasets.load_dataset` to fetch `Team10_chat_anonymized.csv` from the verified URL.<br>• Compute SHA‑256 of the downloaded file; abort if mismatch.<br>• Map the provided annotation to binary `ground_truth_label`.<br>• Run `src/data/generate_synthetic.py` to create ≥ 200 deterministic `.py` files; each file’s metadata (depth, scope, complexity) is recorded in `synthetic_manifest.csv`.<br>• Enforce FR‑009: any generated instance with `dependency_depth` > 5 is capped to 5 and a warning logged. | FR‑001, FR‑009 | SC‑005 |
| **1. Feature Extraction** | Parse every `.py` (real + synthetic). Compute:<br>• `dependency_depth` (import‑graph depth, capped at 5)<br>• `semantic_scope` (`local`/`cross_module`)<br>• `syntactic_complexity` (custom score based on nesting & token count)<br>• `ast_depth` (max AST node depth)<br>• `import_count` (distinct imports)<br>• `cyclomatic_complexity` (radon).<br>Write `data/features.csv` with a `sha256` checksum per row. | FR‑001 | – |
| **2. Static Pipeline (TIDE‑Lite)** | Apply deterministic heuristic rules (e.g., flag if `ast_depth > 3` or `cyclomatic_complexity > 10`). Record binary `prediction`, per‑instance `latency_ms`, and row checksum. Output `data/tide_lite_enriched.csv` conforming to the contract schema. | FR‑002, FR‑004 | – |
| **3. Generative Pipeline (TIDE‑Original)** | Load the CPU‑only `distilgpt2` model (≈ 82 M params). Prompt each snippet: *“Does the following code contain a hidden problem? Answer Yes/No.”* Use deterministic decoding (`temperature=0.0`, `top_k=1`). Record `prediction`, `latency_ms`, and checksum. Output `data/tide_original_enriched.csv` (schema‑compliant). | FR‑003, FR‑004 | – |
| **4. Consolidation** | Merge `features.csv`, `tide_lite_enriched.csv`, and `tide_original_enriched.csv` on `instance_id` → `data/merged_results.csv`. The merged file is the **Single Source of Truth** for all downstream analysis. | FR‑001, FR‑002, FR‑003 | – |
| **5. Train/Validation Split** | Deterministically split `merged_results.csv` into training and hold‑out validation using `seed=42`. Persist index files (`train_ids.txt`, `val_ids.txt`). | FR‑010 | – |
| **6. Logistic Regression & Thresholds** | • Fit `LogisticRegression(solver='lbfgs')` on the training set: `static_success ~ dependency_depth + semantic_scope + syntactic_complexity + ast_depth + import_count + cyclomatic_complexity`.<br>• Perform 5‑fold CV; report mean AUC and standard deviation.<br>• **Power validation**: compute Events‑Per‑Variable (EPV) = `events / predictors`; assert EPV ≥ 15 (FR‑010).<br>• Compute VIF for each predictor; if any VIF > 5, orthogonalize and note in `analysis_summary.json`.<br>• **Threshold estimation**: generate Partial Dependence Plots for each predictor; locate the predictor value where predicted probability = 0.5 using a binary search (tolerance 0.01).<br>• Bootstrap the hold‑out set 1 000 times to obtain 95 % CI for each threshold.<br>Save results to `analysis/logistic_summary.json`. | FR‑005, FR‑010 | SC‑001 |
| **7. Stratified McNemar’s Tests** | Bin instances into Low/Medium/High based on tertiles of `syntactic_complexity`. For each bin, construct a 2×2 contingency table of static vs. generative outcomes (TP/FP/FN/TN) and run `statsmodels.stats.contingency_tables.mcnemar` (exact). Record raw p‑values in `analysis/mcnemar_results.csv`. | FR‑006 | SC‑002 |
| **8. Multiple‑Comparison Correction** | Apply Holm‑Bonferroni (`statsmodels.stats.multitest.multipletests`) to the three bin p‑values; store corrected p‑values alongside raw values in `analysis/mcnemar_results.csv`. | FR‑008 | SC‑002 |
| **9. Sensitivity Analysis** | Sweep probability cut‑offs `{0.01, 0.05, 0.10}`. For each cut‑off, recompute PDP thresholds and aggregate FP/FN counts; compute variance across cut‑offs. Save `analysis/sensitivity_summary.csv`. | FR‑007 | SC‑003 |
| **10. Efficiency Reporting** | Sum `latency_ms` per pipeline, compute total wall‑clock time via `time.perf_counter()`, and measure average CPU utilisation with `psutil.cpu_percent(interval=1, percpu=False)`. Verify ≤ 6 h and ≤ 80 % utilisation; write `analysis/efficiency_report.json`. | – | SC‑004 |
| **11. Figure & Table Generation** | Generate: (a) ROC curve for static pipeline; (b) PDP plots for each predictor with the 0.5‑probability threshold marked; (c) bar plot of Holm‑Bonferroni‑corrected McNemar p‑values. All figures read directly from `merged_results.csv` (SSoT) and are saved under `outputs/`. | – | SC‑001, SC‑002, SC‑003 |

All phases are ordered so that data acquisition precedes any consumption, model inference precedes statistical analysis, and visualisation follows analysis. The plan satisfies every FR‑NNN and SC‑NNN listed in the specification without adding any un‑specified constraints.  

---
