# Research: llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

## Objective
Quantify how intrinsic code properties (dependency depth, semantic scope, syntactic complexity) influence the success probability of a deterministic static detector (TIDE‑Lite) and assess the performance gap between static and generative pipelines (TIDE‑Original) across complexity bins. Identify the “complexity threshold” where static detection probability falls below 0.5, and verify statistical significance using stratified McNemar’s tests with multiple‑comparison correction.

## Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Real code instances | **TIDE evaluation CSV** (verified) | `datasets.load_dataset("hclee99/TIDES", "Team10_chat_anonymized", streaming=False)` | Provides source code strings and human‑annotated hidden‑problem labels. Dependency depth is estimated via import‑graph analysis; semantic scope inferred from import style. |
| Synthetic edge‑cases | Local deterministic generator (`src/data/generate_synthetic.py`) | `python -m src.data.generate_synthetic` | Systematically varies **dependency depth** (1‑5), **semantic scope** (local vs. cross‑module), and **syntactic complexity** (simple vs. nested). Caps depth at 5 per FR‑009. |

Both datasets are fully reproducible and stored under `data/` with SHA‑256 checksums (Principle III).

## Methods

| Step | Method | Library | CPU / GPU | Rationale |
|------|--------|---------|-----------|-----------|
| Feature extraction | Python `ast` + `radon` + custom import‑graph analysis → `dependency_depth`, `semantic_scope`, `syntactic_complexity`, `ast_depth`, `import_count`, `cyclomatic_complexity` | `ast`, `radon` | CPU | Pure‑Python, negligible memory/CPU, fits CI limits. |
| Static heuristic (TIDE‑Lite) | Rule‑based thresholds on extracted metrics (e.g., `ast_depth > 3` → flag) | Custom Python | CPU | Deterministic, no model loading, fully reproducible. |
| Generative inference (TIDE‑Original) | CPU‑native `distilgpt2` with deterministic decoding (`temperature=0.0`, `top_k=1`) | `transformers`, `torch` (CPU) | CPU | Small (≈ 82 M) model fits within ~2 GB RAM; deterministic for reproducibility (Principle I). |
| Logistic regression | `LogisticRegression(solver='lbfgs')` with 5‑fold CV; EPV check; PDP for 0.5‑probability threshold; bootstrap 1 000 resamples for CI | `scikit-learn` | CPU | Classical statistical model; meets FR‑005 & FR‑010. |
| Power validation | Events‑Per‑Variable (EPV ≥ 15) computed from training data | Custom Python | CPU | Ensures adequate sample size for logistic regression (SC‑001). |
| Threshold estimation | Partial Dependence Plots (PDP) + binary search (tolerance 0.01) to locate predictor value where `P(static_success)=0.5`; bootstrap CI | `scikit-learn` | CPU | Provides interpretable “complexity threshold”. |
| McNemar’s test | Exact paired test per complexity bin (low/med/high) | `statsmodels.stats.contingency_tables.mcnemar` | CPU | Validates performance gap (SC‑002). |
| Multiple‑comparison correction | Holm‑Bonferroni (`statsmodels.stats.multitest.multipletests`) | `statsmodels` | CPU | Controls family‑wise error (FR‑008). |
| Sensitivity sweep | Evaluate cut‑offs `{0.01,0.05,0.10}`; recompute PDP thresholds; compute FP/FN variance | Custom loop | CPU | Checks stability of identified boundary (FR‑007). |
| Efficiency reporting | Aggregate `latency_ms`; wall‑clock via `time.perf_counter`; CPU utilisation via `psutil` | `time`, `psutil` | CPU | Verifies SC‑004. |
| Visualization | Matplotlib ROC, PDP, and bar plot of corrected p‑values | `matplotlib` | CPU | Figures directly derived from `merged_results.csv` (SSoT). |

### Decision / Rationale
All computation is **CPU‑first**. The generative baseline uses `distilgpt2`, a model small enough to run on the free GitHub Actions CPU runner without quantization libraries. Deterministic decoding guarantees reproducibility (Principle I). No GPU is required; therefore the plan avoids any off‑load to a GPU escape hatch.

## Statistical Rigor Checklist
- **Multiple‑comparison correction** – Holm‑Bonferroni applied to three McNemar p‑values (FR‑008).  
- **Power / Sample‑size** – EPV ≥ 15 verified before logistic regression (FR‑010).  
- **Causal assumptions** – Analyses are purely correlational; no causal claims are made.  
- **Measurement validity** – Ground‑truth labels are human‑annotated in the TIDE dataset; synthetic labels are generated consistently by the script.  
- **Collinearity** – Variance Inflation Factor (VIF) computed; predictors with VIF > 5 are orthogonalized and documented.  

## Expected Deliverables
- `data/features.csv` (structural metrics + checksum)  
- `data/tide_lite_enriched.csv` & `data/tide_original_enriched.csv` (binary outcomes, latency, checksum)  
- `data/merged_results.csv` (SSoT, conforms to `contracts/detection_results.schema.yaml`)  
- `analysis/logistic_summary.json` (coefficients, mean AUC, PDP thresholds with 95 % CI, VIF, EPV status)  
- `analysis/mcnemar_results.csv` (raw and Holm‑Bonferroni‑corrected p‑values per bin)  
- `analysis/sensitivity_summary.csv` (threshold variance across cut‑offs)  
- `analysis/efficiency_report.json` (total runtime, CPU utilisation)  
- Figures under `outputs/`: ROC curve, PDP threshold plots, McNemar significance bar plot.  

All artifacts will be validated against the contract schema via `pytest -q tests/contract`.  

---
