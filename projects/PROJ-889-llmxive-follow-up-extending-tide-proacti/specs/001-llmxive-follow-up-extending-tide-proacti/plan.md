# Implementation Plan: llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-23 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project will (1) download the verified TIDE evaluation dataset via the HuggingFace `datasets` library (with SHA‑256 verification), (2) generate a deterministic synthetic corpus of ≥ 200 Python files that systematically vary dependency depth, semantic scope, and syntactic complexity (capped at a limited depth per FR‑009) **and whose marginal distributions are matched to the real data** (distribution‑matching step described below), (3) extract structural metrics (AST depth, import‑graph depth, cyclomatic complexity, plus the three intrinsic properties) producing a feature matrix, (4) run two detection pipelines – a deterministic static heuristic (“TIDE‑Lite”) and a CPU‑only quantized **7B** language model (“TIDE‑Original”) – logging binary outcomes and per‑instance latency, (5) merge all artifacts into a **long‑format** “single source of truth” CSV that conforms to a JSON‑Schema contract, (6) fit logistic regression **including `ast_depth` and `cyclomatic_complexity` as predictors (in addition to the intrinsic properties)** to model static‑detection probability, (7) conduct stratified McNemar’s tests across **adaptive bins** that guarantee ≥ 30 instances **and ≥ 10 discordant pairs** per bin, apply Holm‑Bonferroni correction, (8) perform a sensitivity sweep over probability cut‑offs, synthetic depth‑distribution, binning schemes, **and inclusion/exclusion of `ast_depth` & `cyclomatic_complexity`**, (9) report execution efficiency (wall‑clock ≤ 6 h, CPU ≤ 80 % avg), and (10) generate figures and tables that directly trace back to rows in the merged CSV. All steps are **CPU‑first** and fully reproducible on a GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `datasets==2.20.0` (download & streaming, checksum helper)  
  - `huggingface_hub==0.23.0` (checksum utilities)  
  - `pandas==2.2.2` (CSV handling)  
  - `torch==2.2.2` (CPU wheel)  
  - `transformers==4.41.2` (CPU‑native inference)  
  - `bitsandbytes==0.43.1` (8‑bit quantization for 7B model)  
  - `radon==6.0.1` (cyclomatic complexity)  
  - `scikit-learn==1.5.0` (logistic regression, CV)  
  - `statsmodels==0.14.2` (McNemar, Holm‑Bonferroni, Firth fallback)  
  - `matplotlib==3.9.0`, `psutil==5.9.8`, `numpy==1.26.4`  
- **Storage**: Files under `data/` (raw parquet/CSV, synthetic `.py` files, derived CSVs, checksums)  
- **Testing**: `pytest` with contract validation (`tests/contract`) and lightweight CLI‑style smoke tests for each phase.  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only)  
- **Constraints**: Total wall‑clock ≤ 6 h, peak RAM ≤ 7 GB, average CPU utilisation ≤ 80 % (SC‑004)  
- **Scale/Scope**: ≥ 200 real TIDE instances + ≥ 200 synthetic edge‑case instances (FR‑001, SC‑005)

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed seeds (`seed=42`, `torch.manual_seed(42)`). All data fetched via a deterministic HuggingFace loader; every script is deterministic. |
| II. Verified Accuracy | Only the verified TIDE parquet URL (see research.md) is used. |
| III. Data Hygiene | Raw parquet checksum recorded (`data/raw/tide.sha256`). Every transformation writes a new file with its own checksum column (`sha256`). |
| IV. Single Source of Truth | `data/merged_results.csv` is the **sole** source for all downstream figures/tables (long‑format). |
| V. Versioning Discipline | All artefacts are content‑hashed; hashes stored in `state/projects/PROJ-889-…yaml`. |
| VI. Computational Efficiency Boundary Analysis | Implements TIDE‑Lite (static heuristic) and TIDE‑Original (CPU‑native quantized 7B LLM), logs latency, models detection probability vs. three intrinsic properties. |
| VII. Statistical Validation of Method Efficacy | Stratified McNemar’s tests (adaptive bins) with Holm‑Bonferroni correction, logistic regression with EPV check and control covariates, sensitivity sweeps. |

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
│   ├── acquire_real.py          # HuggingFace download, SHA‑256 verification, CSV conversion
│   ├── generate_synthetic.py    # Deterministic generator (depth 1‑5, scope, complexity) **distribution‑matched** to real data
│   ├── split_data.py            # Train/validation split (seed=42)
│   └── test_acquire_real.py     # pytest: asserts exit 0 and checksum match
│   └── test_generate_synthetic.py # pytest: asserts manifest has exactly 200 rows
├── features/
│   ├── extract.py               # AST + radon + import‑graph → feature CSV (includes `origin`)
│   └── test_extract.py          # pytest: asserts non‑empty CSV and row count ≥ 400
├── pipelines/
│   ├── tide_lite.py             # Static heuristic using `ast_depth` & `cyclomatic_complexity`
│   ├── tide_original.py         # CPU‑native 8‑bit quantized 7B LLM (`bigcode/starcoderbase-7b`) inference
│   └── consolidate.py           # Join features + both pipeline results in **long‑format**
└── analysis/
│   ├── logistic.py              # Logistic regression (predictors: dependency_depth, semantic_scope,
│   │                               syntactic_complexity, ast_depth, cyclomatic_complexity, origin,
│   │                               interaction terms); EPV check, VIF, Firth fallback,
│   │                               bootstrap CI, 0.5‑probability boundary search)
│   ├── mcnemar.py               # Adaptive binning (≥ 30 instances & ≥ 10 discordant pairs per bin) → exact McNemar + Holm‑Bonferroni
│   ├── sensitivity.py           # Sweep over cut‑offs, synthetic depth distribution, binning schemes,
│   │                               **and inclusion/exclusion of `ast_depth` & `cyclomatic_complexity`**
│   ├── efficiency.py            # Latency aggregation, wall‑clock & CPU utilisation check
│   └── visualize.py             # ROC, PDP with boundary region, McNemar significance bar plots
└── run_all.py                   # Orchestrates all phases in order
```

## Phase‑by‑Phase Task List (covers all FR/SC)

| Phase | Description | FRs addressed | SCs addressed |
|-------|-------------|---------------|----------------|
| **0. Data Acquisition** | • Use `datasets.load_dataset("deeplearning-tide/tide", split="test", streaming=True)` to stream the verified parquet. <br>• Compute SHA‑256 of each streamed row; compare against a pre‑computed checksum file (`data/raw/tide.sha256`). <br>• Convert streamed rows to CSV `data/raw/tide.csv` preserving `instance_id` and `ground_truth_label`. <br>• Run `src/data/test_acquire_real.py` (pytest) to assert exit 0 and checksum match. <br>• Run `src/data/generate_synthetic.py --seed 42` → creates ≥ 200 `.py` files under `data/synthetic/` and `synthetic_manifest.csv`. Caps `dependency_depth` at 5; logs a warning for any cap event. **Additionally**, the generator samples synthetic instances to **match the marginal distributions** of `dependency_depth`, `semantic_scope`, and `syntactic_complexity` observed in the real TIDE data (distribution‑matching step). A Kolmogorov‑Smirnov test is performed and logged; if p < 0.05 a warning is issued. <br>• Run `src/data/test_generate_synthetic.py` to assert a successful exit and **exactly 200 rows** in the manifest. <br>**Note**: `features.csv` (produced later) does **not** undergo validation against `detection_results.schema.yaml` because it lacks pipeline‑specific columns; only the enriched result files and the long‑format merge are validated. | FR‑001, FR‑009 | SC‑005 |
| **1. Feature Extraction** | Parse **all** `.py` files (real + synthetic). Compute: <br>• `dependency_depth` (import‑graph depth, capped 5) <br>• `semantic_scope` (`local`/`cross_module`) <br>• `syntactic_complexity` (nesting + token count) <br>• `ast_depth` (max AST node depth) <br>• `import_count` (distinct imports) <br>• `cyclomatic_complexity` (radon). <br>Include `origin` column. Write `data/features.csv` with a per‑row `sha256` checksum. Run `src/features/test_extract.py` to assert ≥ 400 rows and non‑null metrics. | FR‑001 | – |
| **2. Static Pipeline (TIDE‑Lite)** | Deterministic rule: **positive if `ast_depth > 3` OR `cyclomatic_complexity > 10`**. Record binary `prediction`, per‑instance `latency_ms`, and checksum. Output `data/tide_lite_enriched.csv` conforming to the contract schema (includes `origin`). | FR‑002, FR‑004 | – |
| **3. Generative Pipeline (TIDE‑Original)** | Load CPU‑only **8‑bit quantized 7B** model `bigcode/starcoderbase-7b` via `bitsandbytes` (`device='cpu'`). Prompt each snippet with *“Does the following code contain a hidden problem? Answer Yes/No.”* Use deterministic decoding (`temperature=0.0`, `top_k=1`). To respect CI limits, inference is performed on a **sampled subset of 200 instances** (selected uniformly). Record `prediction`, `latency_ms`, and checksum. Output `data/tide_original_enriched.csv` (schema‑compliant). | FR‑003, FR‑004 | – |
| **4. Consolidation** | Merge `features.csv`, `tide_lite_enriched.csv`, and `tide_original_enriched.csv` **in long‑format** (two rows per instance, one per pipeline) → `data/merged_results.csv`. Retain `origin`. This file is the **Single Source of Truth** for all downstream analysis and satisfies `detection_results.schema.yaml`. | FR‑001, FR‑002, FR‑003 | – |
| **5. Train/Validation Split** | Deterministically split `merged_results.csv` into training and hold‑out validation using `seed=42`. Persist `train_ids.txt` & `val_ids.txt`. | FR‑010 | – |
| **6. Logistic Regression & Thresholds** | • Fit `LogisticRegression(penalty='l2', solver='lbfgs')` on the training set with predictors **including** `dependency_depth`, `semantic_scope`, `syntactic_complexity`, **and** `ast_depth` & `cyclomatic_complexity` (as control covariates), plus `origin` (categorical) and interaction terms (`dependency_depth*semantic_scope`). <br>• Perform 5‑fold cross‑validation; report mean AUC and standard deviation. <br>• **Power validation**: expecting [deferred] static‑positive rate → ≈ 120 positives for 8 predictors (EPV ≈ 15 > 15). If observed EPV drops below 15, automatically switch to penalized (Firth) logistic regression via `statsmodels` and note the limitation. <br>• Compute VIF; orthogonalize predictors with VIF > 5 via PCA. <br>• **Boundary estimation**: evaluate the fitted model surface on a fine grid over the three intrinsic predictors (holding `origin` constant) and locate where predicted probability = 0.5 using binary search (tolerance 0.01). Bootstrap a sufficiently large number of resamples for a 95 % confidence interval. Save `analysis/logistic_summary.json`. | FR‑005, FR‑010 | SC‑001 |
| **7. Stratified McNemar’s Tests** | Bin instances using **adaptive binning**: start with tertiles of `syntactic_complexity` and `dependency_depth`; merge adjacent bins until each bin contains **≥ 30 instances** **and** at least **10 discordant pairs** for the static vs. generative outcomes. For each resulting bin, build a 2×2 contingency table and run exact McNemar (`statsmodels.stats.contingency_tables.mcnemar`). Record raw p‑values in `analysis/mcnemar_results.csv`. | FR‑006 | SC‑002 |
| **8. Multiple‑Comparison Correction** | Apply Holm‑Bonferroni (`statsmodels.stats.multitest.multipletests`) to the set of McNemar raw p‑values; store corrected p‑values alongside raw values in `analysis/mcnemar_results.csv`. | FR‑008 | SC‑002 |
| **9. Sensitivity Analysis** | Sweep: <br>(a) probability cut‑offs `{0.01,0.05,0.10}`, <br>(b) synthetic depth‑distribution parameters (uniform vs. skewed toward depth 5), <br>(c) binning schemes (quantile vs. equal‑width with adaptive merging), **(d) inclusion/exclusion of `ast_depth` & `cyclomatic_complexity`** in the logistic model. For each configuration recompute the PDP‑based threshold and aggregate FP/FN variance. Save `analysis/sensitivity_summary.csv`. | FR‑007 | SC‑003 |
| **10. Efficiency Reporting** | Sum `latency_ms` per pipeline, compute total wall‑clock time via `time.perf_counter()`, and measure average CPU utilisation with `psutil.cpu_percent(interval=1, percpu=False)`. Verify ≤ 6 h and ≤ 80 % utilisation; write `analysis/efficiency_report.json`. | – | SC‑004 |
| **11. Figure & Table Generation** | Generate: (a) ROC curve for static pipeline; (b) PDP plots for each predictor with the 0.5‑probability boundary region marked; (c) bar plot of Holm‑Bonferroni‑corrected McNemar p‑values. All figures read directly from `merged_results.csv` (SSoT) and are saved under `outputs/`. | – | SC‑001, SC‑002, SC‑003 |

All phases are ordered so that data acquisition precedes any consumption, model inference precedes statistical analysis, and visualisation follows analysis. The plan satisfies every FR‑NNN and SC‑NNN listed in the specification without adding any un‑specified constraints.  

---



