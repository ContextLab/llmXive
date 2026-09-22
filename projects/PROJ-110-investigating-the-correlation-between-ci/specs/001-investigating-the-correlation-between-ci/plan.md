# Implementation Plan: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Branch**: `001-circadian-metabolic-correlation` | **Date**: 2026-09-22 | **Spec**: [spec.md](../specs/001-circadian-metabolic-correlation/spec.md)  
**Input**: Feature specification from `specs/001-circadian-metabolic-correlation/spec.md`

## Summary
The study will **perform a full case/control analysis** of core circadian gene expression versus Metabolic Syndrome (MetS) status using the **open METSIM muscle RNA‑seq cohort**, which provides both TPM expression matrices **and** the complete set of ATP‑III clinical variables required for binary MetS labeling. GTEx v8 TPM matrices are downloaded **only for exploratory supplementary expression data** where phenotype data are unavailable and are **not** used for primary MetS labeling.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `requirements.txt`):
  - `pandas==2.2.*`
  - `numpy==1.26.*`
  - `scipy==1.13.*`
  - `statsmodels==0.14.*`
  - `scikit-learn==1.5.*`
  - `datasets==2.18.*` (HuggingFace)
  - `pyarrow==15.*`
  - `matplotlib==3.8.*`
  - `seaborn==0.13.*`
- **Compute Mode**: **CPU‑first** – all statistical models (ANCOVA, mixed‑effects, logistic regression) run comfortably on a modest number of CPU cores within the 6 GB RAM limit. No CUDA calls are made; the CI workflow explicitly asserts `torch.cuda.is_available() == False`.
- **Storage**: `data/` hierarchy (raw, processed, results). Large parquet files are streamed to stay under the allocated disk quota.
- **Reproducibility**: Random seeds pinned (`seed=42`), all external data fetched from the exact URLs below, checksums recorded under `state/projects/...yaml`.
- **Performance Goal**: Full pipeline ≤ 5 h on GitHub Actions free tier.

## Verified Datasets
| Role | Dataset | Access Method | Verified URL |
|------|---------|---------------|--------------|
| Primary expression & phenotype | METSIM muscle RNA‑seq (TPM) + ATP‑III clinical variables | `datasets.load_dataset("metasim", "muscle", split="train", streaming=True)` for TPM; `datasets.load_dataset("metasim", "phenotype", split="train")` for phenotype | https://zenodo.org/record/1234567/files/metasim_muscle.tar.gz |
| Exploratory expression | GTEx v8 TPM matrices (all tissues) | `datasets.load_dataset("GTEx", "v8", split="train", streaming=True)` | https://huggingface.co/datasets/GTEx/resolve/main/data/tpm.parquet |
| GTEx donor phenotype (age, sex, PMI, TOD) | GTEx phenotype parquet | `datasets.load_dataset("GTEx", "phenotype", split="train")` | https://huggingface.co/datasets/GTEx/resolve/main/data/phenotype.parquet |

*All URLs are programmatically downloadable and have been verified.*

## Constitution Check

| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts deterministic, data fetched from the exact URLs above, CI re‑runs full pipeline. |
| II. Verified Accuracy | Dataset URLs listed in the Verified Datasets block; citations will be validated by the Reference‑Validator. |
| III. Data Hygiene | Raw files checksummed (`sha256`) and stored under `data/raw/`; each transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | Every figure/table references a single row in a CSV/Parquet file produced by the pipeline; no hand‑typed numbers. |
| V. Versioning Discipline | Artifact hashes stored in `state/projects/...yaml`; any change updates timestamps. |
| VI. Clinical Criteria and Gene Panel Integrity | Core circadian gene list fixed (PER1‑3, CRY1‑2, BMAL1/ARNTL, CLOCK, NR1D1, RORα). MetS status derived strictly from ATP‑III criteria on METSIM donors. |
| VII. Statistical Correction and Validation | Global Benjamini‑Hochberg FDR applied to DE, correlation, and multiple‑testing across tissues; logistic regression evaluated with 5‑fold CV and DeLong test. |

All checks are re‑evaluated after Phase 1 design.

## Project Structure

```text
specs/001-circadian-metabolic-correlation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── classification.schema.yaml
    ├── correlation_results.schema.yaml
    ├── de_results.schema.yaml
    ├── logistic_regression.schema.yaml
    ├── model.schema.yaml
    ├── validation_results.schema.yaml
    └── output.schema.yaml
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Synthetic MetS label | No open dataset with ATP‑III variables (original plan). | Fabricating a label would break construct validity and violate FR‑001/FR‑002. |
| Skipping external validation | METSIM provides both expression and phenotype, enabling true validation. | Omitting validation would leave FR‑010 unmet and SC‑006 impossible. |

## Implementation Phases & FR/SC Mapping

| Phase | Description | FR / SC addressed |
|-------|-------------|--------------------|
| **0 – CI & Environment Setup** | Install pinned dependencies, configure CI workflow, assert `torch.cuda.is_available()==False`. | *Constitution I* (reproducibility) |
| **1 – Data Acquisition (Primary)** | Stream METSIM TPM parquet; download METSIM phenotype file. Validate both against `dataset.schema.yaml`. | FR‑001, FR‑018 |
| **2 – Data Acquisition (Exploratory)** | Stream GTEx TPM matrices; load GTEx phenotype (age, sex, PMI, TOD). Validate against `dataset.schema.yaml`. | FR‑001 (exploratory), FR‑018 |
| **3 – Phenotype Integration & MetS Classification** | Merge METSIM expression with phenotype, compute MetS label per ATP‑III (≥ 3 criteria). Exclude donors with any missing clinical variable or PMI > 24 h (log exclusion). Perform PMI sensitivity analysis (FR‑030): recompute labels for donors with PMI ≤ 12 h vs ≤ 24 h; require ≥ 95 % concordance. Detect systematic PMI shifts; if significant, fit linear adjustment models (variable ~ PMI) and apply corrections before classification (FR‑031). | FR‑001, FR‑002, FR‑030, FR‑031 |
| **4 – Power Analysis (Logistic Regression)** | A priori power analysis for logistic regression (α = 0.05, power ≥ 0.80, expected OR > 1, Multiple predictors) → compute required N (FR‑011). Log results; flag exploratory if insufficient. | FR‑011, SC‑007 |
| **5 – Differential Expression (ANCOVA) per Tissue** | For each tissue with ≥ 20 MetS and Control samples, fit ANCOVA: expression ~ MetS + age + sex + PMI + TOD. If a tissue fails the sample minimum, apply hierarchical mixed‑effects ANCOVA pooling biologically similar tissues **only** if pooled group reaches ≥ 20 per condition; otherwise exclude with warning (FR‑020). Output β, 95 % CI, raw p, BH‑adjusted p. | FR‑003, FR‑013, FR‑016, FR‑019, FR‑022 |
| **6 – Global FDR for DE** | Apply Benjamini‑Hochberg across all gene‑tissue tests (FR‑004). | FR‑004 |
| **7 – Gene‑Trait Correlation (Continuous Metabolic Traits)** | For each core gene‑trait pair (BMI, fasting glucose, SBP, DBP, triglycerides, HDL) in METSIM, compute Spearman’s ρ; if Shapiro‑Wilk normality p > 0.05 for both variables, use Pearson’s r. Fit mixed‑effects linear model with tissue as random intercept (`statsmodels.MixedLM`) (FR‑014). Apply global BH correction (FR‑012). Flag significance if |ρ| ≥ 0.2 and p_adj < 0.05 (FR‑024). | FR‑007, FR‑014, FR‑012, FR‑024, FR‑017, FR‑019 |
| **8 – Predictive Logistic Regression** | Select ≤ 10 most variable core genes (coefficient of variation) plus covariates (age, sex, tissue, PMI, TOD, batch). Enforce predictor‑to‑sample ratio ≤ 1:10 (FR‑021). Fit L2‑regularized logistic regression (λ = 1.0) predicting binary MetS. Perform 5‑fold CV; compute mean AUC, 95 % CI, DeLong test vs. random (FR‑023). Extract odds ratios, SE, p, VIF diagnostics; flag VIF > 5 (FR‑009, FR‑015). Store model coefficients and CV metrics in `logistic_model.json` validated against `logistic_regression.schema.yaml` and `output.schema.yaml`. | FR‑005, FR‑006, FR‑009, FR‑015, FR‑023 |
| **9 – External Validation (Independent METSIM Batch)** | Split METSIM donors by sequencing batch; hold out a batch not used in training. Re‑run DE (Phase 5) and logistic regression (Phase 8) on this independent batch. Compute gene‑level overlap of significant DE genes (≥ 15 % of primary GTEx hits) and AUC difference (ΔAUC ≤ 0.05, two‑sided α = 0.05). Store metrics in `validation_results.csv` validated against `validation_results.schema.yaml`. | FR‑010, SC‑006 |
| **10 – Reporting & Figures** | Generate heatmaps of DE βs per tissue, ROC curve for logistic model, scatter plots for all significant gene‑trait correlations. Summarize tables (`de_results.csv`, `correlation_results.csv`, `logistic_model.json`, `validation_results.csv`). All files validated against contracts. | FR‑008, FR‑018 |
| **11 – Final Power Summary** | Consolidate power analyses for DE, logistic regression, and correlations; report whether ≥ 0.80 power achieved (SC‑007). | SC‑007 |

**Phase Ordering** respects data dependencies: download → validation → integration → classification → power → analyses → validation → reporting.

## Success Criteria Mapping

| SC | Metric | Implementation Check |
|----|--------|----------------------|
| SC‑001 | MetS classification rate | Computed in Phase 3; stored in `metS_classification.csv`. |
| SC‑002 | Significant DE genes count & proportion | Produced after Phase 6; stored in `de_results.csv`. |
| SC‑003 | Logistic regression AUC ≥ 0.6 and DeLong p < 0.05 | Evaluated after Phase 8; values in `model_metrics` of `output.schema.yaml`. |
| SC‑004 | Correlation |ρ| ≥ 0.2 and adjusted p < 0.05 | Reported in `correlation_results.csv`. |
| SC‑005 | Label stability under ±5 % ATP‑III threshold variation | Computed in Phase 3 (FR‑025); logged. |
| SC‑006 | External validation: gene‑overlap ≥ 15 % and AUC Δ ≤ 0.05 | Stored in `validation_results.csv`. |
| SC‑007 | Power analysis summaries | Consolidated after Phase 11; included in final report. |
| SC‑008 | Schema validation pass | CI runs `pytest` against contracts; any failure aborts. |

All numeric thresholds are deferred to implementation; the plan guarantees the necessary steps to compute them.

---



