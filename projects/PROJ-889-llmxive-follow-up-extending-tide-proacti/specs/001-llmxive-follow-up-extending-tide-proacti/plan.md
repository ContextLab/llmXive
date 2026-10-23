# Implementation Plan: llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-22 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project will (1) acquire a **verified** TIDE evaluation dataset via a direct HTTP download (with SHA‑256 checksum verification), (2) generate a deterministic synthetic code corpus (≥ 200 instances) that systematically varies dependency depth, semantic scope, and syntactic complexity, capping depth at 5 per FR‑009, (3) parse every code snippet to compute structural metrics (AST depth, import counts, cyclomatic complexity) **including the `origin` flag**, producing a feature matrix, (4) execute two detection pipelines – a deterministic static heuristic (“TIDE‑Lite”) that uses *only* `ast_depth` and `cyclomatic_complexity`, and a generative “TIDE‑Original” engine (CPU‑only quantized `distilgpt2`) – logging binary outcomes and per‑instance latency, (5) merge all artefacts into a single SSoT (`merged_results.csv`) that conforms to a JSON‑Schema contract and retains `origin`, (6) fit logistic regression **using only intrinsic properties not used by the static heuristic** (`dependency_depth`, `semantic_scope`, `syntactic_complexity`, plus `origin` as a control) with interaction terms, performing an EPV‑based power check and falling back to penalized (Firth) regression if EPV < 15, (7) conduct stratified McNemar’s tests across a **3×3 grid** of bins defined by tertiles of `syntactic_complexity` and `dependency_depth`, applying Holm‑Bonferroni correction across the nine tests, (8) perform a sensitivity analysis that sweeps (a) probability cut‑offs `{0.01, 0.05, 0.10}`, (b) synthetic depth‑distribution parameters (uniform vs. skewed toward depth 5), and (c) alternative binning schemes (quantile vs. equal‑width), reporting variance of identified thresholds, (9) aggregate latency statistics to confirm wall‑clock ≤ 6 h and average CPU utilisation ≤ 80 % (SC‑004), and (10) generate figures and tables that directly trace back to rows in `merged_results.csv`. All steps are **CPU‑first** and fully reproducible on a GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `datasets==2.20.0` (used only for checksum utilities)  
  - `huggingface_hub==0.23.0` (checksum helpers)  
  - `pandas==2.2.2` (CSV handling)  
  - `torch==2.2.2` (CPU wheel)  
  - `transformers==4.41.2` (CPU‑native `distilgpt2`)  
  - `radon==6.0.1` (cyclomatic complexity)  
  - `scikit-learn==1.5.0` (logistic regression, CV)  
  - `statsmodels==0.14.2` (McNemar, Holm‑Bonferroni, Firth fallback)  
  - `matplotlib==3.9.0`, `psutil==5.9.8`, `numpy==1.26.4`  
- **Storage**: Files under `data/` (raw parquet/CSV, synthetic `.py` files, derived CSVs, checksums)  
- **Testing**: `pytest` with contract validation (`tests/contract`)  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only)  
- **Constraints**: Total wall‑clock ≤ 6 h, peak RAM ≤ 7 GB, average CPU utilisation ≤ 80 % (SC‑004)  
- **Scale/Scope**: ≥ 200 real TIDE instances + ≥ 200 synthetic edge‑case instances (FR‑001, SC‑005)

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed seeds (`seed=42`, `torch.manual_seed(42)`); data fetched via verified URL; all scripts deterministic. |
| II. Verified Accuracy | Only URLs listed in the “Verified datasets” block are cited for the real dataset. |
| III. Data Hygiene | Raw parquet checksum recorded (`sha256` per shard); every transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | `data/merged_results.csv` is the sole source for every downstream figure/table. |
| V. Versioning Discipline | All artefacts are content‑hashed and referenced in `state/projects/PROJ-889-…yaml`. |
| VI. Computational Efficiency Boundary Analysis | Implements TIDE‑Lite (deterministic static analysis using `ast_depth` & `cyclomatic_complexity`) and TIDE‑Original (CPU‑native `distilgpt2`), logs latency, models detection probability vs. three intrinsic properties. |
| VII. Statistical Validation of Method Efficacy | Performs stratified McNemar’s tests across a 3×3 bin grid, Holm‑Bonferroni correction, logistic regression with EPV check, interaction handling, and sensitivity sweeps. |

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
│   ├── acquire_real.py          # direct HTTP download, SHA‑256 verification, CSV conversion
│   ├── generate_synthetic.py    # deterministic generator (depth 1‑5, scope, complexity)
│   └── split_data.py            # train/validation split (seed=42)
├── features/
│   └── extract.py               # AST, radon, import‑graph analysis → feature CSV (includes `origin`)
├── pipelines/
│   ├── tide_lite.py             # static heuristic using `ast_depth` & `cyclomatic_complexity`
│   ├── tide_original.py         # CPU‑native `distilgpt2` inference, deterministic decoding
│   └── consolidate.py           # join features + both pipeline results, preserve `origin`
├── analysis/
│   ├── logistic.py              # logistic regression (predictors: dependency_depth, semantic_scope,
│   │                               syntactic_complexity, origin), EPV check, VIF, fallback Firth,
│   │                               interaction terms, multivariate boundary search
│   ├── mcnemar.py               # 3×3 stratified exact McNemar + Holm‑Bonferroni (9 tests)
│   ├── sensitivity.py           # cut‑off sweep, synthetic depth‑distribution sweep, binning‑scheme sweep
│   ├── efficiency.py            # latency aggregation, wall‑clock & CPU utilisation check
│   └── visualize.py             # ROC, PDP, McNemar significance bar plots
└── run_all.py                   # orchestrates all phases in order
```

## Phase‑by‑Phase Task List (covers all FR/SC)

| Phase | Description | FRs addressed | SCs addressed |
|-------|-------------|---------------|----------------|
| **0. Data Acquisition** | • **Direct download** of the verified TIDE parquet from `<https://huggingface.co/datasets/deeplearning-tide/actresses/resolve/main/data/test-00000-of-00001-9189dc62872204f7.parquet>` using `urllib.request`. <br>• Compute SHA‑256 checksum (`sha256` stored in `data/raw/tide.sha256`). Abort on mismatch. <br>• Convert streamed rows to CSV `data/raw/tide.csv`, preserving `instance_id` and `ground_truth_label`. <br>• Run `src/data/generate_synthetic.py` to create ≥ 200 deterministic `.py` files; each file’s metadata (depth, scope, complexity) is recorded in `synthetic_manifest.csv`. <br>• Enforce FR‑009: any generated instance with `dependency_depth` > 5 is capped to 5 and a warning logged. | FR‑001, FR‑009 | SC‑005 |
| **1. Feature Extraction** | Parse every `.py` (real + synthetic). Compute: <br>• `dependency_depth` (import‑graph depth, capped at 5) <br>• `semantic_scope` (`local`/`cross_module`) <br>• `syntactic_complexity` (custom score based on nesting & token count) <br>• `ast_depth` (max AST node depth) <br>• `import_count` (distinct imports) <br>• `cyclomatic_complexity` (radon). <br>• **Preserve `origin`** (`real`/`synthetic`). <br>Write `data/features.csv` with a per‑row `sha256` checksum. | FR‑001 | – |
| **2. Static Pipeline (TIDE‑Lite)** | Apply deterministic heuristic: flag as positive if **`ast_depth > 3` OR `cyclomatic_complexity > 10`**. Record binary `prediction`, per‑instance `latency_ms`, and row checksum. Output `data/tide_lite_enriched.csv` conforming to the contract schema (now includes `origin`). | FR‑002, FR‑004 | – |
| **3. Generative Pipeline (TIDE‑Original)** | Load the CPU‑only `distilgpt2` model (≈ 82 M params). Prompt each snippet: *“Does the following code contain a hidden problem? Answer Yes/No.”* Use deterministic decoding (`temperature=0.0`, `top_k=1`). Record `prediction`, `latency_ms`, and checksum. Output `data/tide_original_enriched.csv` (schema‑compliant). | FR‑003, FR‑004 | – |
| **4. Consolidation** | Merge `features.csv`, `tide_lite_enriched.csv`, and `tide_original_enriched.csv` on `instance_id` → `data/merged_results.csv`. The merged file **retains the `origin` column** and is the **Single Source of Truth** for all downstream analysis. | FR‑001, FR‑002, FR‑003 | – |
| **5. Train/Validation Split** | Deterministically split `merged_results.csv` into training and hold‑out validation using `seed=42`. Persist index files (`train_ids.txt`, `val_ids.txt`). | FR‑010 | – |
| **6. Logistic Regression & Thresholds** | • Fit `LogisticRegression(penalty='l2', solver='lbfgs')` on the training set with predictors **excluding** the static‑heuristic metrics: `dependency_depth`, `semantic_scope`, `syntactic_complexity`, plus `origin` as a categorical control and interaction terms (e.g., `dependency_depth*semantic_scope`). <br>• Perform 5‑fold CV; report mean AUC and std. <br>• **Power validation**: compute Events‑Per‑Variable (EPV = positives / num_predictors). If EPV ≥ 15, proceed; otherwise switch to penalized (Firth) logistic regression via `statsmodels` and note the limitation. <br>• Compute VIF; orthogonalize predictors with VIF > 5 via PCA. <br>• **Boundary estimation**: evaluate the full model surface on a fine grid over the three intrinsic predictors (holding `origin` constant) and locate the region where predicted static‑success probability = 0.5 (binary search tolerance 0.01). Bootstrap 1 000 resamples of the hold‑out set to obtain 95 % CI for the threshold region. Save results to `analysis/logistic_summary.json`. | FR‑005, FR‑010 | SC‑001 |
| **7. Stratified McNemar’s Tests** | Bin instances into a **3×3 grid** based on tertiles of `syntactic_complexity` **and** tertiles of `dependency_depth`. For each of the nine bins, construct a 2×2 contingency table of static vs. generative outcomes and run `statsmodels.stats.contingency_tables.mcnemar` (exact). Record raw p‑values in `analysis/mcnemar_results.csv`. | FR‑006 | SC‑002 |
| **8. Multiple‑Comparison Correction** | Apply Holm‑Bonferroni (`statsmodels.stats.multitest.multipletests`) to the nine McNemar raw p‑values; store corrected p‑values alongside raw values in `analysis/mcnemar_results.csv`. | FR‑008 | SC‑002 |
| **9. Sensitivity Analysis** | Sweep: <br>(a) probability cut‑offs `{0.01, 0.05, 0.10}`; <br>(b) synthetic depth‑distribution parameters (uniform vs. skewed toward depth 5); <br>(c) binning schemes (quantile vs. equal‑width). For each configuration recompute PDP‑based thresholds and aggregate FP/FN variance. Save `analysis/sensitivity_summary.csv`. | FR‑007 | SC‑003 |
| **10. Efficiency Reporting** | Sum `latency_ms` per pipeline, compute total wall‑clock time via `time.perf_counter()`, and measure average CPU utilisation with `psutil.cpu_percent(interval=1, percpu=False)`. Verify ≤ 6 h and ≤ 80 % utilisation; write `analysis/efficiency_report.json`. | – | SC‑004 |
| **11. Figure & Table Generation** | Generate: (a) ROC curve for static pipeline; (b) PDP plots for each predictor with the 0.5‑probability boundary region marked; (c) bar plot of Holm‑Bonferroni‑corrected McNemar p‑values. All figures read directly from `merged_results.csv` (SSoT) and are saved under `outputs/`. | – | SC‑001, SC‑002, SC‑003 |

All phases are ordered so that data acquisition precedes any consumption, model inference precedes statistical analysis, and visualisation follows analysis. The plan satisfies every FR‑NNN and SC‑NNN listed in the specification without adding any un‑specified constraints.  

---


