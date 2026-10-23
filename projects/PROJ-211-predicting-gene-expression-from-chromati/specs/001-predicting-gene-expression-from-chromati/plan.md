# Implementation Plan: Predicting Gene Expression from Chromatin Accessibility

**Branch**: `211-predicting-gene-expression` | **Date**: 2026-10-23 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/001-predicting-gene-expression-from-chromati/spec.md`

## Summary
Create a fully reproducible, CPU‑only pipeline that (1) programmatically downloads paired ENCODE RNA‑seq and ATAC/DNase‑seq files for five human cell lines, (2) streams and preprocesses the data (CPM normalisation, log‑pseudocount, median imputation, aggregation into 200 fixed‑width bins within ±50 kb of each gene TSS while excluding the promoter ±2 kb), (3) trains an Elastic Net regression model per cell line (α = 0.5, l1_ratio tuned via LOOCV), (4) evaluates performance (Pearson r, R², Bonferroni‑corrected p‑values), (5) extracts bin‑level feature importance, (6) quantifies the proportion of top‑100 bins within ±10 kb and performs a permutation‑based enrichment test (SC‑003), (7) computes R² for housekeeping genes, (8) calculates the performance gap ΔR² between housekeeping and cell‑type‑specific genes, and (9) conducts cross‑cell‑line external validation (train on four lines, test on the held‑out line). All artifacts are checksum‑verified and validated against JSON‑Schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `pybedtools==0.9.*`, `requests==2.32.*`, `tqdm==4.66.*`, `jsonschema==4.22.*`  
- **Storage**: Local filesystem under `data/` (raw, processed, models)  
- **Testing**: `pytest==8.2.*` (unit, integration, contract)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≤7 GiB RAM, ≤6 h wall‑time)  
- **Performance Goals**: Peak RAM < 7 GiB, total runtime ≤ 6 h  
- **Constraints**: CPU‑only (SC‑002), interpretability (SC‑001), reproducibility (Constitution I)  

## Constitution Check
| Principle | Verification |
|-----------|--------------|
| **I. Reproducibility** | Fixed random seeds (`np.random.seed(42)`, `random_state=42`). All downloads use deterministic ENCODE REST URLs; SHA‑256 checksums recorded in `state/projects/...yaml`. |
| **II. Verified Accuracy** | Citations limited to ENCODE, GENCODE v44, Elastic Net (Zou & Hastie 2005), Bonferroni, LOOCV (ArXiv 2507.20048). |
| **III. Data Hygiene** | Raw files stored under `data/raw/` with checksums; every transformation writes a new file; no in‑place edits. |
| **IV. Single Source of Truth** | All figures/tables generated from schema‑validated artifacts; no manual transcription. |
| **V. Versioning Discipline** | Each artifact’s SHA‑256 hash stored in `state/projects/...yaml`; updates bump `updated_at`. |
| **VI. Computational Resource Efficiency** | Streaming I/O, gene‑wise loops, and `n_jobs=1` keep RAM < 7 GiB and CPU usage ≤ 2 cores. |
| **VII. Biological Interpretability** | Feature importance reported per 200‑bin window; promoter excluded; covariate‑adjusted partial‑R² provided. |

## Project Structure
```
specs/001-predicting-gene-expression-from-chromati/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── model_output.schema.yaml
    └── output_schema.schema.yaml

code/
├── download_encode.py       # FR‑001 – robust streaming download with retries, checksum, chromosome‑1 subset option
├── preprocess.py            # FR‑002‑006 – normalisation, aggregation, imputation
├── train.py                 # FR‑007‑011 – Elastic Net training, LOOCV, Bonferroni, external validation
├── analyze.py               # FR‑008‑010 – feature importance, TSS mapping, enrichment, performance gap
├── generate_report.py       # FR‑011 – markdown summary
└── utils.py                 # checksum utilities, logging, constants (random seed, bin params)

data/
├── raw/
│   ├── rna_counts.tsv
│   ├── atac_peaks.bed
│   └── gene_tss.bed
├── processed/
│   ├── filtered_expression.csv
│   ├── imputed_expression.csv
│   ├── normalized_counts.csv
│   ├── normalized_peaks.csv
│   ├── selected_bins.txt
│   ├── binned_matrix.csv
│   ├── housekeeping_genes.csv
│   ├── cell_type_specific_genes.csv
│   └── housekeeping_matrix.csv
└── models/
    └── elastic_net_{cell_line}.pkl
    └── cv_scores.json

tests/
├── unit/
│   └── test_utils.py
├── integration/
│   └── test_end_to_end.py   # runs full pipeline on a tiny synthetic subset (seed = 42)
└── contract/
    └── test_contracts.py    # validates all files against contracts/*.schema.yaml
```

## Mapping of Functional & Non‑Functional Requirements to Plan Phases

| Phase | Tasks | FR / SC addressed |
|-------|-------|-------------------|
| **Phase 1 – Setup** | Create virtualenv, pin `requirements.txt` | — |
| **Phase 2 – Contracts** | Write JSON‑Schema contracts (`dataset.schema.yaml`, `model_output.schema.yaml`, `output_schema.schema.yaml`) | Constitution III, V |
| **Phase 3 – Data Ingestion (US 1)** | `download_encode.py` streams **exact** ENCODE URLs for each cell line (see Research.md). Implements retry (max 3) and SHA‑256 verification. If a file exceeds 2 GB, streams only chromosome 1 (still ≥ 5 % of genome, sufficient for proof‑of‑concept). | FR‑001, Constitution I & III |
| **Phase 4 – Preprocessing (US 1 continued)** | `preprocess.py` performs: (a) CPM normalisation of RNA‑seq counts; (b) CPM normalisation of ATAC/DNase scores; (c) aggregation into 200 fixed‑width bins within ±50 kb of each TSS, promoter ±2 kb set to 0 (FR‑002, FR‑008); (d) removal of genes with zero expression across all samples (FR‑003); (e) log1p transformation (FR‑004); (f) median imputation per bin (FR‑005). All outputs written to `data/processed/` and checksummed. | FR‑002‑006, SC‑001 |
| **Phase 5 – Modeling (US 2)** | `train.py` runs Elastic Net per cell line (α = 0.5, l1_ratio tuned via LOOCV). Variance‑based filter retains ≤ N‑1 bins (N = #samples) and zero‑pads coefficients to maintain 200‑length vectors (FR‑007). Computes Pearson r, R², raw two‑sided p‑values; applies Bonferroni correction across the 5 cell lines (FR‑006). Stores model pickle and `cv_scores.json`. | FR‑007‑011, SC‑001, SC‑006 |
| **Phase 6 – Cross‑Cell‑Line Validation** | Same script with `--hold-out` flag trains on four cell lines, tests on the fifth, writes `external_validation.json`. | SC‑006 |
| **Phase 7 – Analysis (US 3)** | `analyze.py` extracts non‑zero coefficients, maps each bin to distance from TSS (FR‑008), ranks bins by |coefficient|, computes percentage of top‑100 bins within ±10 kb, and runs a permutation‑based enrichment test (1 000 permutations) yielding an empirical p‑value (SC‑003). Adjusts for gene length, GC content, baseline expression (covariate adjustment). Calculates R² for housekeeping genes (FR‑009) and ΔR² between housekeeping and cell‑type‑specific genes (FR‑010). | FR‑008‑010, SC‑003, SC‑004 |
| **Phase 8 – Reporting** | `generate_report.py` creates `paper/results.md` and `paper/limitations.md`, referencing only schema‑validated CSV/JSON files (Constitution IV). | FR‑011, Constitution I‑IV, VII |
| **Phase 9 – Testing** | Unit, integration, and contract tests (`pytest`). Integration test runs the full pipeline on a deterministic synthetic subset (seed = 42) to guarantee CI passes even if ENCODE is temporarily unavailable. | All FR/SC, Constitution III‑V |

## Compute Feasibility (CPU‑First)
All steps use scikit‑learn (CPU‑only) and stream data; no GPU libraries are imported. Memory usage stays < 1 GB per gene; total RAM < 5 GB. Estimated runtime ≈ 4.5 h on the free GitHub Actions runner.

## Decision Rationale
| Decision | Reason |
|----------|--------|
| **Robust ENCODE streaming download** | Guarantees deterministic files; retry + checksum prevents silent failures that caused T002. |
| **Chromosome‑1 subset fallback** | Keeps file size < 2 GB while preserving real biological signal; still satisfies FR‑001 because the subset is a genuine ENCODE-derived slice. |
| **Variance filter ≤ N‑1 predictors** | Avoids p ≫ n over‑fitting; zero‑padding preserves the 200‑bin schema required by contracts. |
| **LOOCV (5 folds)** | Matches verified source (ArXiv 2507.20048) and works with the small N per cell line. |
| **Permutation enrichment for SC‑003** | Provides an empirical test independent of the model ranking, satisfying the non‑tautological requirement. |
| **Cross‑cell‑line external validation** | Meets SC‑006 and demonstrates generalisability. |
| **Synthetic integration test** | Guarantees CI can always run; synthetic data are only a fallback for CI, not a replacement for real ENCODE data in the scientific analysis. |

## Limitations & Caveats
- **Bulk vs. Single‑Cell**: Results reflect population averages; single‑cell heterogeneity is not captured.  
- **Correlation ≠ Causation**: All statements are associative; no causal inference is performed.  
- **Genomic Scope**: Only ±50 kb windows; distal enhancers beyond this range are omitted.  
- **Sample‑Size**: N ≤ 5 per cell line yields wide confidence intervals; bootstrapped CIs reported only when N ≥ 4.  
- **Collinearity**: Adjacent bins remain correlated; coefficients should be interpreted as regional effects.  
- **Feature‑selection bias**: Variance filter may preferentially retain highly variable regions; permutation test mitigates over‑interpretation.  

## Reproducibility Checklist
- Fixed seeds (`np.random.seed(42)`, `random_state=42`).  
- All downloads via `download_encode.py` with SHA‑256 verification.  
- Checksums recorded in `state/projects/…yaml`.  
- Deterministic pipelines; re‑run `python -m pytest` to confirm all tests pass.

---
