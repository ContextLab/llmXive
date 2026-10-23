# Research: llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

## Objective
Quantify how intrinsic code properties (dependency depth, semantic scope, syntactic complexity) influence the success probability of a deterministic static detector (TIDE‑Lite) **which uses only `ast_depth` and `cyclomatic_complexity`**, and assess the performance gap between static and generative pipelines (TIDE‑Original) across complexity bins. Identify the “complexity threshold” where static detection probability falls below 0.5, and verify statistical significance using stratified McNemar’s tests with Holm‑Bonferroni correction. Control for the `origin` (real vs. synthetic) to avoid confounding.

## Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Real code instances | **TIDE evaluation parquet** (verified) | Direct HTTP download (`urllib.request`) → SHA‑256 verification → CSV (`data/raw/tide.csv`) | URL: <https://huggingface.co/datasets/deeplearning-tide/actresses/resolve/main/data/test-00000-of-00001-9189dc62872204f7.parquet> |
| Synthetic edge‑cases | Local deterministic generator (`src/data/generate_synthetic.py`) | `python -m src.data.generate_synthetic` | Systematically varies **dependency depth** (1‑5), **semantic scope** (local vs. cross‑module), and **syntactic complexity** (simple vs. nested). Caps depth at 5 per FR‑009. |

Both datasets are fully reproducible and stored under `data/` with SHA‑256 checksums (Principle III). The `origin` column (`real`/`synthetic`) is retained throughout.

## Methods

| Step | Method | Library | CPU / GPU | Rationale |
|------|--------|---------|-----------|-----------|
| Feature extraction | Python `ast` + `radon` + custom import‑graph analysis → `dependency_depth`, `semantic_scope`, `syntactic_complexity`, `ast_depth`, `import_count`, `cyclomatic_complexity`; retain `origin`. | `ast`, `radon` | CPU | Pure‑Python, negligible resource use, fits CI limits. |
| Static heuristic (TIDE‑Lite) | Deterministic rule: **positive if `ast_depth > 3` OR `cyclomatic_complexity > 10`**. | Custom Python | CPU | Uses metrics **not** employed as predictors in the logistic model, avoiding circularity. |
| Generative inference (TIDE‑Original) | CPU‑native `distilgpt2` with deterministic decoding (`temperature=0.0`, `top_k=1`). | `transformers`, `torch` (CPU) | CPU | Small model fits within ~2 GB RAM; deterministic for reproducibility (Principle I). |
| Logistic regression | Predict **static_success** using predictors **excluding** the static‑heuristic metrics: `dependency_depth`, `semantic_scope`, `syntactic_complexity`, plus `origin` as a control and interaction terms (`dependency_depth*semantic_scope`). Perform 5‑fold CV; compute EPV; if EPV < 15 switch to penalized (Firth) regression; compute VIF and orthogonalize if needed. | `scikit-learn`, `statsmodels` | CPU | Guarantees non‑circular predictor set; EPV check ensures sufficient power (SC‑001). |
| Power validation | Events‑Per‑Variable (EPV ≥ 15) computed from training positives; fallback to Firth regression noted if EPV insufficient. | Custom Python | CPU | Addresses methodology‑7c58e512 concern. |
| Boundary estimation | Evaluate full model surface on a fine grid over the three intrinsic predictors (holding `origin` constant) and locate region where predicted probability = 0.5 via binary search (tolerance 0.01). Bootstrap 1 000 resamples for 95 % CI. | `scikit-learn` | CPU | Provides interaction‑aware threshold (methodology‑f7be6975). |
| Stratified McNemar’s test | Create a **3×3 grid** of bins (tertiles of `syntactic_complexity` × tertiles of `dependency_depth`). For each bin, construct a 2×2 contingency table of static vs. generative outcomes and run exact McNemar (`statsmodels.stats.contingency_tables.mcnemar`). | `statsmodels` | CPU | Uses full 9‑bin design; Holm‑Bonferroni applied across nine tests (methodology‑b028ea41). |
| Multiple‑comparison correction | Holm‑Bonferroni (`statsmodels.stats.multitest.multipletests`) applied to all nine p‑values. | `statsmodels` | CPU | Controls family‑wise error (FR‑008). |
| Sensitivity sweep | Vary (a) probability cut‑offs `{0.01,0.05,0.10}`, (b) synthetic depth‑distribution parameters (uniform vs. skewed toward depth 5), and (c) binning schemes (quantile vs. equal‑width). Recompute thresholds and aggregate FP/FN variance. | Custom loop | CPU | Expands robustness checks (methodology‑85dcd8af). |
| Efficiency reporting | Aggregate `latency_ms`; wall‑clock via `time.perf_counter`; CPU utilisation via `psutil`. | `time`, `psutil` | CPU | Verifies SC‑004. |
| Visualization | Matplotlib ROC, PDP, and bar plot of corrected p‑values. | `matplotlib` | CPU | Figures directly derived from `merged_results.csv` (SSoT). |

### Decision / Rationale
All computation is **CPU‑first**. The generative baseline uses `distilgpt2`, a model small enough to run on the free GitHub Actions CPU runner without quantization libraries. Deterministic decoding guarantees reproducibility (Principle I). No GPU is required; therefore the plan avoids any off‑load.

## Statistical Rigor Checklist
- **Multiple‑comparison correction** – Holm‑Bonferroni applied to nine McNemar p‑values (FR‑008).  
- **Power / Sample‑size** – EPV ≥ 15 validated; fallback to penalized regression if not met (FR‑010).  
- **Causal assumptions** – Analyses are purely correlational; no causal claims are made.  
- **Measurement validity** – Ground‑truth labels are human‑annotated in the TIDE dataset; synthetic labels are generated consistently by the script.  
- **Collinearity** – VIF computed; predictors with VIF > 5 are orthogonalized; interaction terms are included.  

## Expected Deliverables
- `data/features.csv` (structural metrics + `origin` + checksum)  
- `data/tide_lite_enriched.csv` & `data/tide_original_enriched.csv` (binary outcomes, latency, `origin`, checksum)  
- `data/merged_results.csv` (SSoT, conforms to `contracts/detection_results.schema.yaml`)  
- `analysis/logistic_summary.json` (coefficients, mean AUC, interaction‑aware threshold region with 95 % CI, VIF, EPV status)  
- `analysis/mcnemar_results.csv` (raw and Holm‑Bonferroni‑corrected p‑values for each of the nine bins)  
- `analysis/sensitivity_summary.csv` (threshold variance across cut‑offs, synthetic parameters, binning schemes)  
- `analysis/efficiency_report.json` (total runtime, CPU utilisation)  
- Figures under `outputs/`: ROC curve, PDP boundary plots, McNemar significance bar plot.  

All artifacts will be validated against the contract schema via `pytest -q tests/contract`.  

---


