# Implementation Plan: Predicting Plant Stress Response from Publicly Available Transcriptomic Data

**Branch**: `001-predicting-plant-stress-response-from-pu` | **Date**: 2026-10-25 | **Spec**: `specs/001-predicting-plant-stress-response-from-pu/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-plant-stress-response-from-pu/spec.md`

## Summary
The pipeline will (1) discover public plant RNA‑seq GEO series that contain at least two of the four abiotic stresses (drought, salinity, heat, cold); (2) download raw count matrices, harmonize gene identifiers, filter low‑expressed genes, and TMM‑normalize; (3) retain only the intersection of genes present in all included series (≥ 1,500 genes); (4) perform Leave‑One‑Dataset‑Out (LODO) cross‑dataset classification with an L2‑regularized Logistic Regression using the top K most variable genes (K ∈ {50, 100, 150}); (5) evaluate accuracy, macro‑F1, and permutation‑test significance; (6) conduct bootstrap stability analysis of coefficients; (7) generate UMAP embeddings of held‑out test samples and compute Silhouette scores; (8) run a post‑hoc power/MDES analysis for any null result; (9) write all artefacts, update the project state file, and produce an associational report.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `requirements.txt`): `scikit-learn==1.5.0`, `pandas==2.2.2`, `numpy==1.26.4`, `GEOparse==2.2.0`, `mygene==3.2.2`, `biomart==0.9.2`, `umap-learn==0.5.6`, `statsmodels==0.14.2`, `pyyaml==6.0.2`, `matplotlib==3.8.4`, `seaborn==0.13.2` (all CPU‑only wheels).  
- **Storage**: Local file system under `data/` (raw, processed, results).  
- **Testing**: `pytest` for loader, preprocessing, model training, and schema validation.  
- **Target Platform**: Linux (Ubuntu 22.04) on GitHub Actions free‑tier runner (2 CPU, ≈ 7 GB RAM, ≤ 6 h).  
- **Constraints**: No GPU is required; all methods run on CPU.  

## Constitution Check
| Principle | Reference |
|------------|-----------|
| I. Reproducibility | All random seeds are fixed (`seed=42`), dependencies are pinned, and raw GEO files are checksum‑verified. |
| II. Verified Accuracy | Dataset discovery uses NCBI GEO (primary source) programmatically; no third‑party URLs are introduced. |
| III. Data Hygiene | Raw archives are immutable; every transformation writes a new file with a recorded SHA‑256 hash. |
| IV. Single Source of Truth | All numeric results are stored in JSON artefacts; the report pulls values directly from these files. |
| V. Versioning Discipline | `state/projects/PROJ-042-predicting-plant-stress-response-from-pu.yaml` records artifact hashes and timestamps after each stage. |
| VI. Cross‑Dataset Generalization Validation | LODO CV with no batch correction in the primary evaluation ensures genuine cross‑dataset testing. |
| VII. Transcriptomic Data Harmonization and Feature Consistency | Gene‑ID mapping to a common namespace and strict intersection across *included* datasets is enforced before any modelling. |

All principles are satisfied; any violation would abort the run.

## Project Structure
```text
specs/001-predicting-plant-stress-response-from-pu/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── model_output.schema.yaml

code/
├── __init__.py
├── main.py                # orchestrates pipeline stages
├── config.py              # seeds, hyper‑parameters, paths
├── data/
│   ├── __init__.py
│   ├── loader.py          # GEO discovery & download (GEOparse)
│   ├── preprocess.py      # CPM filter, TMM normalization, ID mapping
│   └── utils.py           # checksum, logging helpers
├── models/
│   ├── __init__.py
│   ├── logistic.py        # training, coefficient extraction
│   └── stability.py       # bootstrap coefficient variance
├── analysis/
│   ├── __init__.py
│   ├── permutation.py     # label‑permutation tests
│   ├── power.py           # MDES & post‑hoc power
│   └── unsupervised.py    # UMAP + Silhouette
├── viz/
│   ├── __init__.py
│   └── plots.py           # confusion matrix, UMAP scatter
└── tests/
    ├── test_loader.py
    ├── test_preprocess.py
    ├── test_models.py
    └── test_analysis.py
```

## Complexity Tracking
No constitution violations; the plan follows the specification directly.

## Detailed Phase Mapping (FR / SC Coverage)

| Phase | FR / SC | Description |
|-------|----------|-------------|
| 0 – Dataset Discovery & Verification | FR‑001, FR‑002, FR‑018, FR‑017 | `loader.py` queries NCBI GEO via Entrez/E‑utilities, filters for plant species and ≥2 stress types, ensures ≥ 7 distinct series. If fewer than 7 pass, abort with clear message (covers FR‑017). |
| 1 – Raw Pre‑processing | FR‑003, FR‑004, FR‑012, FR‑013 | CPM filter (≥1 CPM in ≥3 samples), TMM normalization (edgeR via `rpy2` avoided – use `scipy` implementation), gene‑ID harmonization with `mygene`/`biomart`. Invalid samples written to `invalid_samples.csv`. |
| 1.5 – Feature Space Construction | FR‑005, FR‑019 | Compute variance across all samples, select top K (K = 50, 100, 150). Abort if gene intersection < 1,500 (Edge Case). |
| 2 – LODO Model Training | FR‑006, FR‑007, FR‑008, FR‑012 | For each held‑out dataset: train L2‑regularized Logistic Regression (liblinear), evaluate stratified accuracy, macro‑F1, precision, recall. Perform two permutation tests (within‑held‑out & across‑datasets) with 1,000 iterations each; apply Benjamini‑Hochberg FDR (FR‑012). |
| 3 – Bootstrap Stability | FR‑010, FR‑012 | 100 bootstrap resamples of the training data; compute coefficient variance and selection frequency. Genes with variance ≤ 0.30 **and** frequency ≥ 0.70 are reported as robust biomarkers. |
| 4 – Unsupervised Validation | FR‑011 | UMAP (n_neighbors = 15, min_dist = 0.1) on held‑out test matrix (no batch correction). Compute Silhouette scores for stress‑type and dataset‑ID; report Δ ≥ 0.10 significance via permutation. |
| 5 – Post‑hoc Power & MDES | FR‑009 | For any null result (accuracy ≤ random baseline), compute MDES using normal approximation for difference in proportions, α = 0.05, and estimate power to detect an effect size of 0.15 (Cohen’s h). |
| 6 – Reporting & State Update | FR‑014, FR‑015, SC‑001‑SC‑008 | Assemble PDF/HTML report with associational framing, confidence intervals, power analysis, biomarker tables, and reproducibility metadata. Update `state/projects/PROJ-042-…yaml` with `research_complete: true`, UTC timestamp, and SHA‑256 hashes of all result artefacts. |
| 7 – Resource Guardrails | FR‑016 | Prior to each heavy step, estimate RAM usage (via `psutil`) and abort with informative error if projected > 7 GB or if total runtime exceeds 6 h (GitHub Actions timeout). |

All functional requirements (FR‑001 – FR‑019) and success criteria (SC‑001 – SC‑008) are covered.

## Decision Log (excerpt)

| Decision | Rationale |
|----------|-----------|
| Use GEOparse loader (verified recipe) | Meets Constitution Principle II; no fabricated URLs. |
| Abort if < 7 plant stress GEO series found | Directly follows FR‑017; avoids fabricating data. |
| Strict gene‑intersection (≥ 1,500) | Enforces Principle VII; prevents spurious batch effects. |
| LODO CV without batch correction (primary) | Satisfies Principle VI – genuine cross‑dataset validation. |
| Intra‑fold ComBat only for optional sensitivity analysis (not required) | Keeps primary analysis simple and CPU‑friendly. |
| Bootstrap (100) for coefficient stability | Provides quantitative robustness metric required by US‑2. |
| Permutation tests (1,000) with FDR | Controls family‑wise error as mandated by FR‑012. |
| Post‑hoc MDES & power | Enables interpretation of null outcomes per SC‑005. |
| All random seeds fixed (`seed=42`) | Guarantees reproducibility (Principle I). |
