# Implementation Plan: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Branch**: `001-circadian-metabolic-correlation` | **Date**: 2026-09-10 | **Spec**: [spec.md](./specs/001-investigating-the-correlation-between-ci/spec.md)  
**Input**: Feature specification from `/specs/001-investigating-the-correlation-between-ci/spec.md`

## Summary
The project will (1) download the **MESA** open cohort (RNA‑seq TPM matrices and full ATP‑III clinical variables) as the primary dataset for MetS classification, (2) optionally download GTEx v8 TPM matrices for exploratory tissue‑level expression (without MetS labels), (3) classify donors into MetS vs. Control using ATP‑III criteria **only on MESA**, (4) perform a **hierarchical mixed‑effects ANCOVA** comparing each core circadian gene between MetS and Control groups across tissues, (5) apply a **global** Benjamini‑Hochberg False Discovery Rate correction across **all** gene‑tissue tests, (6) compute gene‑trait correlations using permutation‑based significance testing, (7) fit a multivariate logistic regression model **excluding metabolic traits as predictors** (genes + demographics) with regularization and optional feature selection, (8) evaluate performance via 5‑fold cross‑validation and compare against a random‑classifier baseline (AUC = 0.5) using a DeLong test, (9) perform **comprehensive power analyses** for logistic regression, differential expression, and correlation pipelines, (10) run batch‑effect sensitivity analysis, (11) validate findings **in MESA blood** (the only tissue shared with GTEx) and report replication metrics, and (12) generate diagnostic figures. All steps are CPU‑first, reproducible on GitHub Actions free tier; a CI workflow will enforce `torch.cuda.is_available() == False`. The plan respects every FR and SC, references all contracts, and includes a Constitution Check.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pingouin`, `matplotlib`, `seaborn`, `datasets`, `pyarrow`, `tqdm`  
- **Storage**: `data/raw/` for downloads, `data/processed/` for derived tables (CSV/Parquet).  
- **Testing**: `pytest` + contract validation via YAML schemas in `contracts/`.  
- **Target Platform**: Linux (GitHub Actions runner, 2 CPU cores, ~7 GB RAM).  
- **Compute Strategy**: All statistical models are CPU‑tractable; no GPU is required. A CI step will assert `torch.cuda.is_available() == False` before any script runs.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts are deterministic (`numpy.random.seed(42)`, `sklearn.utils.check_random_state`). External datasets are fetched from the exact HuggingFace URLs listed in the Verified Datasets section. |
| II. Verified Accuracy | Every citation (ATP‑III guideline, Brown et al. 2020) will be validated by the Reference‑Validator Agent before inclusion. Title‑token‑overlap with the cited source ≥ 0.7. |
| III. Data Hygiene | Datasets are checksum‑verified on download; every transformation writes a new file with a provenance log. |
| IV. Single Source of Truth | All processed artifacts live under `data/processed/`; figures/tables trace back to these files. |
| V. Versioning Discipline | `requirements.txt` pins exact package versions; Git hashes of all artifacts are recorded in `state/projects/PROJ-110-...yaml`. |
| VI. Clinical Criteria and Gene Panel Integrity | MetS classification follows ATP‑III thresholds **only on MESA** (GTEx used exploratory only). Core circadian gene list is fixed; any expansion is logged as a sensitivity analysis. |
| VII. Statistical Correction and Validation | Global Benjamini‑Hochberg FDR applied to DE, correlation, and model coefficient tests. 5‑fold CV for logistic regression with baseline AUC comparison (DeLong test). |

## Phase Mapping (FR → Plan Phase)

| Phase | Description | FRs addressed |
|-------|-------------|----------------|
| **Phase 0 – Data Acquisition** | Download MESA RNA‑seq TPM + phenotype (open HF dataset) and GTEx TPM (exploratory). Verify SHA‑256 checksums. **Validate raw files against `contracts/dataset.schema.yaml`.** | FR‑001, FR‑011 |
| **Phase 1 – Phenotype Processing (MESA)** | Clean clinical variables, handle missingness, apply ATP‑III thresholds, compute MetS label and severity score, log exclusions. Perform **±5 % threshold sensitivity analysis**; require ≥ 90 % label stability (SC‑005). **Validate classification output against `contracts/classification.schema.yaml`.** | FR‑001, FR‑002, FR‑005, SC‑005 |
| **Phase 1a – GTEx Phenotype Check** | Verify presence/absence of ATP‑III variables; if absent, flag GTEx as exploratory only (no MetS label). | FR‑001 |
| **Phase 2 – Differential Expression (Hierarchical ANCOVA)** | For each tissue with ≥ 10 MetS and ≥ 10 Control donors (after exclusions), fit a **hierarchical mixed‑effects ANCOVA** (`statsmodels.MixedLM`) with random intercept for tissue and covariates (age, sex, PMI, TOD). Extract β, 95 % CI, raw p‑value. | FR‑003, FR‑013 |
| **Phase 3 – Global DE FDR** | Concatenate all raw p‑values across gene‑tissue tests; apply Benjamini‑Hochberg (q < 0.05). **Validate DE table against `contracts/de_results.schema.yaml`.** | FR‑004 |
| **Phase 4 – Gene‑Trait Correlation** | For each (gene, trait) pair test normality (Shapiro‑Wilk). Use Spearman unless both normal → Pearson. Fit mixed‑effects model (`statsmodels.MixedLM`) with tissue random intercept. Compute empirical p‑values via a sufficiently large number of permutations; apply global BH (FR‑012). **Validate correlation outputs against `contracts/output.schema.yaml`.** |
| **Phase 5 – Power Analysis** | Perform a priori power calculations for (a) logistic regression (binary MetS) using `statsmodels.stats.power.NormalIndPower`; (b) DE (ANCOVA) using Bonferroni‑adjusted α across all tests; (c) correlation tests using effect‑size estimates. Flag `study_status=exploratory` if any required N exceeds available N. | FR‑011 |
| **Phase 6 – Predictive Modeling (Primary)** | Assemble feature matrix: core gene log‑TPM + age + sex + tissue (one‑hot) + PMI + TOD + batch. Compute VIF; if VIF > 5, switch to ridge (`C=1.0`). Optionally select top 5 genes by variance to keep predictor‑to‑sample ratio safe. Fit `LogisticRegression(penalty='none', solver='lbfgs')` (or ridge). Compute odds ratios, 95 % CI (Wald). **Validate model coefficients against `contracts/logistic_regression.schema.yaml`, `contracts/model.schema.yaml`, and `contracts/output.schema.yaml`.** |
| **Phase 6a – Auxiliary Traits‑Only Model** | Fit a logistic model with only the five ATP‑III clinical traits to report their odds ratios (FR‑009) for comparison (no gene predictors). |
| **Phase 7 – Cross‑Validation & Baseline** | Stratified k‑fold CV (preserve MetS proportion). Compute AUC per fold, aggregate mean AUC, 95 % CI (bootstrapped). **Compute ΔAUC vs random (0.5) and perform DeLong two‑sided test** (SC‑003). |
| **Phase 8 – Batch‑Effect Sensitivity** | Re‑fit the primary logistic model with and without sequencing batch; compute Pearson correlation of coefficient vectors; require stability ≥ 0.90 (FR‑015). |
| **Phase 9 – External Validation (MESA Blood)** | Replicate DE (Phase 2–3) **on MESA whole‑blood samples only**, compute gene‑overlap proportion (≥ 30 % required) and AUC difference (ΔAUC ≤ 0.05, DeLong test). **Validate validation table against `contracts/output.schema.yaml`.** | FR‑010 |
| **Phase 10 – Reporting & Visualization** | Generate heatmaps of DE β values, ROC curves (with baseline), scatter plots for significant correlations, and summary tables. Compute **SC‑002** (proportion of significant circadian genes) and **SC‑004** (report ρ, p‑value against null). | FR‑008, FR‑009 |

## Milestones & Timeline (CPU‑only)

| Milestone | Approx. Duration | Success Metric |
|-----------|------------------|----------------|
| Data download & checksum | brief duration | All files present, checksums match |
| Phenotype cleaning, MetS labeling & sensitivity analysis (MESA) | a brief period | ≥ 95 % of MESA donors classified, ≥ 90 % label stability |
| Hierarchical DE (ANCOVA) | ~1 h (mixed‑effects) | ≥ 80 % of eligible tissues processed |
| Global FDR correction | a few minutes | Adjusted p‑values generated |
| Gene‑Trait correlation & permutation test | ~1 h | All gene‑trait pairs evaluated, BH‑adjusted p‑values |
| Power analysis (logistic, DE, correlation) | short duration | `study_status` flag set correctly |
| Logistic regression & auxiliary model | brief session | Coefficients, odds ratios, VIFs reported |
| Cross‑validation & baseline AUC | short duration | Mean AUC, 95 % CI, ΔAUC vs 0.5 reported, DeLong p‑value |
| Batch‑effect sensitivity | brief duration | Stability ≥ 0.90 logged |
| MESA blood validation | short duration | Gene overlap ≥ 30 %, ΔAUC ≤ 0.05 |
| Figure generation & report | brief duration | All PNG/SVG files saved in `figures/` |

Total ≤ 5 h on a 2‑core GitHub Actions runner.

## CI Workflow (T060)
A GitHub Actions workflow (`.github/workflows/ci.yml`) will:
1. Install dependencies from `requirements.txt`.
2. Run `python -c "import torch; assert not torch.cuda.is_available()"` to enforce CPU‑only execution.
3. Execute the full pipeline scripts in the order defined above.
4. Run `pytest -v` with contract validation.

All steps will abort if a GPU is detected.

---

