# Implementation Plan: Impact of Environmental Factors on Fungal Community Structure in Soil

**Branch**: `001-impact-of-environmental-factors` | **Date**: 2026-07-03 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-impact-of-environmental-factors/spec.md`

## Summary
The core scientific goal is to quantify how abiotic soil variables (pH, nutrient concentrations, temperature, moisture) predict fungal community composition (ITS amplicon ASVs) and how the ranking of these drivers varies across biomes or soil types.  
We will build a fully reproducible, CPU‑only workflow that (1) verifies the availability of ≥ 3 public ITS studies containing **all** required abiotic columns, (2) downloads raw ITS FASTQ files and associated metadata, (3) denoises sequences to an ASV table with DADA2, (4) computes beta‑diversity (Bray‑Curtis) and alpha‑diversity metrics, (5) builds environmental distance matrices, (6) runs PERMANOVA (adonis2) and variance partitioning (varpart), (7) stratifies analyses by biome, (8) conducts a sensitivity sweep over significance thresholds, and (9) generates standardized reports and figures. All steps respect the functional requirements (FR‑001 – FR‑009) and success criteria (SC‑001 – SC‑006).

> **Critical Note:** The scientific analysis **cannot proceed** without at least three verified public ITS datasets that contain **all** required abiotic columns (pH, nitrogen, phosphorus, potassium, temperature, moisture, biome).  
> *Dataset Availability Check*: the pipeline first validates that each candidate study includes every required column. Studies missing any column are **excluded** with a structured WARN log entry (`{"level":"WARN","msg":"Dataset excluded: missing variable <VAR>","dataset_id":"<ID>"}`). After exclusion, if **fewer than three qualifying studies remain**, the pipeline logs a **CRITICAL** error and **exits with return code 2**, aborting downstream scientific steps. Users may optionally invoke `--placeholder` to run a synthetic stub workflow that writes empty result files and a log entry `No scientific data available`; this path is intended solely for CI sanity checks and does **not** produce ecological conclusions.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**:  
  - `pandas==2.2.*`  
  - `numpy==1.26.*`  
  - `scikit-bio==0.6.*` (beta‑diversity, PERMANOVA)  
  - `scikit-learn==1.5.*` (VIF, PCA)  
  - `statsmodels==0.14.*` (variance partitioning)  
  - `dada2==0.2.*` (via `rpy2` – CPU‑only)  
  - `miceforest==5.4.*` (MICE imputation)  
  - `click==8.1.*` (CLI)  
- **Storage**: File‑based artefacts under `data/` and `results/`; no external DB.  
- **Testing**: `pytest` with fixtures for each pipeline stage.  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Project Type**: CLI‑driven analysis library.  
- **Performance Goals**: Entire pipeline ≤ 6 h wall‑clock, ≤ 7 GB RAM.  
- **Constraints**: CPU‑only, no GPU, no large‑model inference, strict memory ceiling.  
- **Scale/Scope**: Anticipated several public ITS studies (≥2) with a substantial total sample size after subsampling.

> All quantitative thresholds (e.g., p‑value < 0.05, 999 permutations) are taken directly from the spec; no additional thresholds are introduced.

## Constitution Check
| Principle | Compliance Statement | Example Check |
|-----------|----------------------|---------------|
| I. Reproducibility | All external datasets are fetched via deterministic URLs; random seeds are pinned in `code/seed.py`. | Checksums of downloaded files are recorded; `seed.set_seed(42)` is called at pipeline start. |
| II. Verified Accuracy | No external citation is introduced beyond those in the spec; dataset URLs are limited to the verified list. | Reference‑Validator runs on every citation before CI passes. |
| III. Data Hygiene | Every transformation writes a new file; checksums recorded in `state/projects/...yaml`. | Post‑process script verifies that each output file has a matching checksum entry. |
| IV. Single Source of Truth | All figures and tables are generated directly from the CSV/Parquet artefacts produced by the pipeline. | CI asserts that each figure’s metadata (source file path) matches a row in a results CSV. |
| V. Versioning Discipline | All artefacts are content‑hashed; updates trigger hash changes recorded in the project state file. | GitHub Action compares stored hashes before and after a run and fails on mismatch without version bump. |
| VI. Wet‑lab Data Integrity | Raw FASTQ files are stored under `data/raw-seq/` unchanged; QC reports under `data/qc/`. | A pre‑commit hook verifies that files in `data/raw-seq/` have no modifications since download. |
| VII. Environmental Metadata Standardization | Metadata files follow the `contracts/metadata_schema.yaml` schema, with explicit units and biome labels. | `jsonschema` validation step runs on `data/metadata/harmonized.csv` before downstream analysis. |

*Each principle is verified by the corresponding automated check described above.*

## Project Structure
```text
specs/001-impact-of-environmental-factors/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── metadata_schema.yaml

code/
├── cli/
│   └── run_analysis.py          # entry point
├── pipelines/
│   ├── download.py
│   ├── dada2_process.py
│   ├── diversity.py
│   ├── env_matrix.py
│   ├── collinearity.py
│   ├── permanova_varpart.py
│   ├── stratified.py
│   └── sensitivity.py
├── utils/
│   ├── io.py
│   └── logging.py
└── seed.py                     # random seed centralization

data/
├── raw-seq/                    # downloaded FASTQ files (read‑only)
├── qc/                         # QC reports (fastqc, trim stats)
├── metadata/                   # harmonized metadata CSVs
├── asv/                        # ASV tables (biom format)
└── processed/                  # intermediate artefacts (distance matrices, sampling_report.csv)
    ├── sampling_report.csv     # records any subsampling ratios applied
    ├── bray_curtis.parquet
    ├── env_euclidean.parquet
    ├── shannon.csv
    ├── observed_asv.csv
    └── imputed_env.parquet

results/
├── permanova_summary.csv
├── varpart_summary.csv
├── db_rda_biome_*.csv
├── sensitivity_analysis.csv
├── robustness_summary.md
└── figures/
    ├── db_rda_triplot.png
    └── driver_ranking_by_biome.png
```

## Phase‑by‑Phase Plan (covers every FR/SC)

| Phase | Description | FR/SC Addressed | Key Outputs |
|-------|-------------|------------------|--------------|
| **0 – Research & Design** | Draft methodology, confirm dataset availability, define file‑naming conventions. **If fewer than three qualifying ITS studies are available, the pipeline logs a CRITICAL error, exits with return code 2, and aborts scientific analysis** (or runs a synthetic placeholder with `--placeholder`). | – | `research.md`, `data-model.md`, `contracts/metadata_schema.yaml` |
| **1 – Dataset Acquisition & Harmonization** | Download ≥ 3 public ITS studies via `pysradb` or `requests`. Validate presence of required columns (`pH`, `nitrogen`, `phosphorus`, `potassium`, `temperature`, `moisture`, `biome`). **Studies missing any required column are excluded**; a structured WARN is logged. After processing all candidates, if < 3 studies remain, trigger the abort described in Phase 0. | FR‑001, Edge‑Case “Dataset‑Variable Fit”, spec_coverage‑69fa5ea9 | `data/metadata/harmonized.csv`, `data/raw-seq/` |
| **2 – Sequence Denoising (DADA2)** | Run DADA2 (via `rpy2`) on each study’s FASTQs → ASV table (BIOM). Preserve raw reads. | FR‑001 | `data/asv/{study_id}_asv.biom` |
| **3 – Diversity Calculations** | Compute Bray‑Curtis (beta) and Shannon/Observed (alpha) using `scikit‑bio`. | FR‑002 | `data/processed/bray_curtis.parquet`, `data/processed/shannon.csv` |
| **4 – Environmental Matrix Prep** | Scale abiotic variables (z‑score) and one‑hot encode `biome`. Save as Parquet. | FR‑001 (metadata), FR‑007 (collinearity prep) | `data/processed/env_matrix.parquet` |
| **5 – Missing‑Data Imputation & Collinearity Handling** | • Apply MICE (`miceforest`) per study. **If MICE fails for a sample, the sample is excluded** (rather than median imputation) because median substitution would shrink variance and bias effect estimates, whereas exclusion preserves the multivariate structure. Optionally, a secondary KNN imputation can be run for sensitivity testing. <br>• Compute VIF for all predictors (`statsmodels`). Flag VIF > 5 (a common ecological rule‑of‑thumb). For flagged pairs, either drop the lower‑priority variable (priority: pH > temperature > moisture > nitrogen > phosphorus > potassium) **or** combine via PCA, logging the decision. | FR‑007, FR‑008, Edge‑Case “Collinearity”, scientific_soundness‑c4f297d3 | `data/processed/imputed_env.parquet`, `data/processed/vif_report.csv` |
| **6 – Global PERMANOVA & Variance Partitioning** | • PERMANOVA (`scikit-bio.adonis`) with ≥ 999 permutations. <br>• Apply Benjamini‑Hochberg FDR correction (controls expected proportion of false discoveries while retaining power in the presence of correlated predictors, preferable to the overly conservative Bonferroni). <br>• Variance partitioning (`statsmodels` `varpart`) to obtain unique/shared variance per predictor. | FR‑003, FR‑004, SC‑001, SC‑002, scientific_soundness‑3a1282e5 | `results/permanova_summary.csv`, `results/varpart_summary.csv` |
| **7 – Biome‑Specific Analyses** | Split dataset by `biome`. For each stratum with **≥ 10 samples** (derived from a power analysis: medium effect size f = 0.25, α = 0.05, power = 0.80 → ≈ 10 samples needed for PERMANOVA), repeat Phase 6. **If a biome has < 10 samples, the test is skipped** and an ERROR is logged, with the power justification, rather than crashing or producing unreliable p‑values. | FR‑005, SC‑003, methodology‑99467f0c | `results/db_rda_biome_<NAME>.csv`, `results/permanova_biome_<NAME>.csv` |
| **8 – Sensitivity & Robustness Sweep** | Loop over p‑value thresholds {0.01, 0.05, 0.10} and R² cutoffs {0.05, 0.10, 0.15}. Record top driver per combination. Compute stability metric (percentage of combos where same driver is top). Flag “Low Confidence” if stability < 80 %. | FR‑006, SC‑004 | `results/sensitivity_analysis.csv`, `results/robustness_summary.md` |
| **9 – Reporting & Figures** | Generate: <br>• PERMANOVA/varpart tables (CSV) <br>• db‑RDA triplot (PNG) with dominant vector highlighted <br>• Driver‑ranking bar plots per biome <br>• Sensitivity heatmap. <br>All figures saved under `results/figures/`. <br>All reports explicitly note if **no significant abiotic driver** was detected (edge‑case). | All SC, Edge‑Case “Null Results” | CSV/PNG files, `paper/figures/` placeholders |
| **10 – Runtime & Memory Safeguards** | Prior to Phase 2, estimate RAM usage; if a study’s raw FASTQ exceeds 4 GB, randomly subsample reads to ≤ 2 M per sample (record ratio in `data/processed/sampling_report.csv`). Use streaming parsers where possible. Monitor memory via `psutil`; abort with clear message if > 7 GB. | FR‑009, Edge‑Case “Computational Limits” | Log entries, `sampling_report.csv` |

### Milestones & Deliverables
| Milestone | Expected Completion | Artefacts |
|-----------|---------------------|-----------|
| M0 – Research Design | Day 1 | `research.md`, `data-model.md`, `contracts/metadata_schema.yaml` |
| M1 – Data Ingestion & QC | Day 2‑3 | Harmonized metadata, raw‑seq logs |
| M2 – ASV Generation | Day 4‑5 | ASV BIOM files |
| M3 – Diversity & Env Matrices | Day 6 | Distance matrices, imputed env matrix |
| M4 – Global PERMANOVA/Varpart | Day 7 | `permanova_summary.csv`, `varpart_summary.csv` |
| M5 – Stratified Analyses | Day 8‑9 | Biome‑specific CSVs |
| M6 – Sensitivity Sweep | Day 10 | `sensitivity_analysis.csv`, `robustness_summary.md` |
| M7 – Reporting & Figures | Day 11‑12 | All CSV/PNG outputs |
| M8 – CI Validation | Day 13 | GitHub Actions run < 6 h, < 7 GB |

## Risk & Mitigation
- **Dataset Availability**: If no verified ITS dataset with all required columns is supplied, the pipeline aborts scientific analysis with a CRITICAL error (return code 2). Users may run `--placeholder` for CI sanity checks. This satisfies the spec‑driven exclusion policy.
- **Memory Overrun**: Subsampling step (Phase 10) guarantees RAM stays ≤ 7 GB.
- **Collinearity**: Automated VIF check + rule‑based dropping prevents unstable coefficient interpretation.
- **Insufficient Biome Samples**: Power analysis justification (f = 0.25, α = 0.05, 80 % power) underpins the ≥ 10 sample threshold.
- **Null Results**: Even if no predictor reaches significance, a report stating “No significant abiotic drivers detected” is generated.

---


