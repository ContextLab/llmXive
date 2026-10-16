# Research: llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

## Objective
Model the association between intrinsic code properties (dependency depth, semantic scope, syntactic complexity) and the probability of successful detection by a deterministic static detector (TIDE‑Lite), identifying the complexity thresholds where detection probability drops below 0.5, and statistically assess the performance gap between static and generative pipelines across complexity bins.

## Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Real code instances | **TIDE evaluation CSV** (verified) | `datasets.load_dataset("hclee99/TIDES", "Team10_chat_anonymized", streaming=False)` | Provides source code strings and human‑annotated hidden‑problem labels. Dependency depth is estimated by the depth of the import tree reachable within the dataset; semantic scope is inferred from relative vs. absolute imports. |
| Synthetic edge‑cases | Local generation script (`src/data/generate_synthetic.py`) | Executed locally (`python -m src.data.generate_synthetic`) | Systematically varies **dependency depth** (1‑5), **semantic scope** (local vs. cross‑module), and **syntactic complexity** (simple vs. nested). Caps depth at 5 per FR‑009. |

## Methods

| Step | Method | Library | CPU / GPU | Rationale |
|------|--------|---------|-----------|-----------|
| Feature extraction | Python `ast` + `radon` + import graph analysis → `ast_depth`, `import_count`, `cyclomatic_complexity`, `dependency_depth`, `semantic_scope`, `syntactic_complexity` | `ast`, `radon` | CPU | Pure‑Python, negligible memory/CPU, fits CI limits. |
| Static heuristic (TIDE‑Lite) | Rule‑based thresholds on extracted metrics (e.g., `ast_depth > 3` → flag) | Custom Python | CPU | Deterministic, no model loading, reproducible. |
| Generative inference (TIDE‑Original) | Native CPU-compatible `distilgpt2` with deterministic decoding (`temperature=0.0`, `top_k=1`) | `transformers`, `torch` (CPU) | CPU | Small enough to run on CI CPU without quantization libraries, deterministic for reproducibility. |
| Logistic regression | `LogisticRegression(solver='lbfgs')` with 5‑fold CV and origin-stratified models | `scikit-learn` | CPU | Classical statistical model; meets FR‑005 & FR‑010. |
| Power validation | Events Per Variable (EPV) check: ensure $\text{events} / \text{predictors} \geq 15$ | Custom calculation | CPU | Standard heuristic for logistic regression stability (SC-001). |
| Threshold estimation | Partial Dependence Plots (PDP) to find predictor value where $P(\text{success})=0.5$; bootstrap 1 000 resamples for CI | `scikit-learn` | CPU | Accounts for predictor interactions; provides interpretable “complexity threshold”. |
| McNemar’s test | Paired exact test per complexity bin | `statsmodels.stats.contingency_tables.mcnemar` | CPU | Validates performance gap (SC‑002). |
| Multiple‑comparison correction | Holm‑Bonferroni (`statsmodels.stats.multitest.multipletests`) | `statsmodels` | CPU | Controls family‑wise error (FR‑008). |
| Sensitivity sweep | Evaluate logistic operating cut‑offs `{0.01,0.05,0.10}`; recompute thresholds and FP/FN variance | Custom loop | CPU | Checks stability of boundary (FR‑007). |
| Efficiency reporting | Sum `latency_ms`; wall‑clock via `time.perf_counter`; CPU utilisation via `psutil` | `time`, `psutil` | CPU | Verifies SC‑004. |
| Visualization | Matplotlib ROC, PDP plots, bar plot | `matplotlib` | CPU | Figures derive directly from `merged_results.csv` (SSoT). |

### Decision / Rationale
All computation is **CPU‑first**. The generative baseline uses `distilgpt2` (~82M parameters) which fits comfortably within the ≤ 7 GB RAM budget of a free GitHub Actions runner without needing `bitsandbytes`. Deterministic seeds (`seed=42`, `torch.manual_seed(42)`) guarantee reproducibility (Principle I).

## Statistical Rigor Checklist
- **Multiple‑comparison correction** – Holm‑Bonferroni applied to three McNemar p‑values (FR‑008).  
- **Power / Sample‑size** – Validated via EPV $\geq 15$ for the logistic model to ensure stability given the combined ~several hundred instances (FR‑010).  
- **Causal assumptions** – All analyses are correlational; no causal claims are made regarding the "cause" of detection failure.  
- **Measurement validity** – Ground‑truth labels are human‑annotated in the TIDE dataset; synthetic labels are internally consistent.  
- **Collinearity** – VIF will be computed; if any predictor exceeds VIF > 5, the model will be refit with orthogonalized features (recorded in `analysis_summary.json`).  

## Expected Deliverables
- `data/features.csv` (structural metrics + checksum)  
- `data/tide_lite_enriched.csv` & `data/tide_original_enriched.csv` (binary outcomes, latency, full feature set, checksum)  
- `data/merged_results.csv` (SSoT, conforms to `contracts/detection_results.schema.yaml`)  
- `data/analysis_summary.json` (AnalysisSummary entity: coefficients, mean AUC, PDP thresholds with 95 % CI, VIF, corrected p-values)  
- `analysis/sensitivity_summary.csv` (threshold variance across cut‑offs)  
- `analysis/efficiency_report.json` (total runtime, CPU utilisation)  
- Figures under `outputs/`: ROC curve, PDP threshold plots, McNemar significance bar plot.  

All artifacts will be validated against the contract schema via `pytest -q tests/contract`.
