# Research: llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

## Objective
Identify the intrinsic code‑property boundaries (dependency depth, semantic scope, syntactic complexity) that separate successful static detection (TIDE‑Lite) from generative detection (TIDE‑Original), and quantify the statistical significance of the performance gap.

## Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Real code instances | CodeXGLUE defect‑detection dataset (open) | `datasets.load_dataset("code_x_glue", "defect_detection")` | Provides source code and defect labels; a lightweight manual mapping script converts defect labels to the required binary *hidden‑problem* ground‑truth (`ground_truth_label`). |
| Synthetic edge‑cases | Local generation script (included in repo) | Executed via `python src/data/generate_synthetic.py` | Systematically varies dependency depth (1‑5), semantic scope (local vs. cross‑module), and syntactic complexity (simple vs. nested). Caps depth at 5 per FR‑009. |
| Feature extraction reference | AST (hdf5) model file (verified) | Not directly used; retained for provenance only. | No direct relevance to feature values but cited for compliance with verified‑dataset rule. |

> No verified URL is available for the CodeXGLUE dataset; it is referenced by name per the “no verified source” policy.

## Methods

| Step | Method | Library | CPU / GPU | Rationale |
|------|--------|---------|-----------|-----------|
| Feature extraction | AST parsing (`ast`), import count, cyclomatic complexity (`radon`) | `ast`, `radon` | CPU | Pure Python, lightweight, fits CI limits. |
| Static heuristic (TIDE‑Lite) | Rule‑based thresholds on extracted metrics | Custom Python | CPU | Deterministic, no model loading. |
| Generative inference (TIDE‑Original) | Quantized GPT-family model loaded with `transformers` and `bitsandbytes` 8‑bit mode | `transformers`, `torch` (CPU) | CPU (quantized) | Small enough to run on CI CPU; deterministic decoding ensures reproducibility. |
| Logistic regression | `LogisticRegression(solver='lbfgs')` with 5‑fold CV | `scikit-learn` | CPU | Classical statistical model, satisfies FR‑005 & FR‑010. |
| Power analysis | `statsmodels.stats.power.GofPower` (logistic regression) | `statsmodels` | CPU | Justifies sample size for 3‑predictor model. |
| Threshold estimation | Marginal analysis: fix other predictors at mean, binary‑search predictor value where predicted probability = 0.5 (tolerance 0.01). Bootstrap 1000 resamples for CI. | Custom loop | CPU | Provides reproducible, univariate “complexity threshold”. |
| McNemar’s test | `statsmodels.stats.contingency_tables.mcnemar` | `statsmodels` | CPU | Provides exact test for paired binary outcomes. |
| Multiple‑comparison correction | Holm‑Bonferroni (`statsmodels.stats.multitest.multipletests`) | `statsmodels` | CPU | Meets FR‑008. |
| Sensitivity sweep | Vary probability cutoff `{0.01,0.05,0.10}` used to define the operating point; recompute marginal thresholds and FP/FN variance. | Custom loop | CPU | Addresses FR‑007. |
| Efficiency reporting | Summation of latency columns; wall‑clock measurement via `time` module. | Standard library | CPU | Verifies SC‑004. |

### Decision / Rationale
All computations are CPU‑first. The generative baseline uses a quantized small LLM that comfortably fits within the typical RAM budget of a CI runner. No GPU is required, satisfying the compute feasibility rule.

## Statistical Rigor Checklist
- **Multiple‑comparison correction** – Holm‑Bonferroni applied to three McNemar p‑values (see FR‑reference).  
- **Power / Sample‑size** – Power analysis confirms ≥ 80 % power for detecting an odds‑ratio of 1.5 with α = 0.05 given ~400 instances (FR‑010).  
- **Causal assumptions** – Analyses are purely associative; no causal claims are made.  
- **Measurement validity** – CodeXGLUE defect labels are human‑annotated independent of any detection pipeline; manual mapping to hidden‑problem labels is documented (SC‑001 & SC‑002).  
- **Collinearity** – Variance Inflation Factor (VIF) will be computed; if any predictor exceeds VIF > 5, the model will be refit with orthogonalized features (recorded in `logistic_summary.json`).  

## Expected Deliverables
- `features.csv` (code‑level structural metrics, includes `origin`)  
- `tide_lite_enriched.csv` & `tide_original_enriched.csv` (binary outcomes + latency + all feature fields + checksum)  
- `merged_results.csv` (joined table satisfying the contract schema)  
- `logistic_summary.json` (coefficients, AUC, marginal thresholds with bootstrap CI)  
- `mcnemar_results.csv` (raw & corrected p‑values per bin)  
- `sensitivity_summary.csv` (threshold variance across cutoffs)  
- `efficiency_report.json` (total runtime, CPU utilization)  
- Figures: ROC curve, marginal‑threshold heatmaps, McNemar significance bar plot (saved under `outputs/`).  

All files will be validated against the contract schema in `contracts/detection_results.schema.yaml`.

---


