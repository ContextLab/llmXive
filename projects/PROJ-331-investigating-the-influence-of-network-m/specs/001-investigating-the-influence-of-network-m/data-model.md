# Data Model: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Overview
The pipeline processes a cohort of **subjects** for which paired structural and functional neuroimaging data are available, together with optional demographic and motion covariates. All intermediate and final artifacts are stored as files on disk and referenced in manifest JSON files. The model below defines the core entities, their relationships, and the file formats used throughout the project.

## Entities

| Entity | Description | Primary File(s) | Format |
|--------|-------------|-----------------|--------|
| **Subject** | Unique identifier for a participant (e.g., `sub-01`). | `subject_id` (string) | N/A (used as key) |
| **StructuralConnectome** | Binary undirected adjacency matrix derived from pre‑computed tractography streamlines after applying the Schaefer cortical parcellation at a high‑resolution (on the order of one hundred regions). | `data/processed/<subject_id>/structural.npy` | NumPy `.npy` (bool dtype) |
| **StructuralConnectomeMetadata** | JSON metadata describing provenance, source, and processing parameters for each structural connectome. | `data/processed/<subject_id>/structural_connectome.json` | JSON (see `contracts/structural_connectome.schema.yaml`) |
| **rsFCMatrix** | Pearson correlation matrix of BOLD time‑series (after nuisance regression) for the same set of parcels. | `data/processed/<subject_id>/rsfc.npy` | NumPy `.npy` (float64) |
| **MotifProfile** | Z‑score prevalence for each motif type (both triadic and four‑node, encompassing the full set of motifs) plus enumeration metadata. | `data/processed/<subject_id>/motif_profile.json` | JSON (see `contracts/motif_profile.schema.yaml`) |
| **SubjectMetrics** | Summary metrics per subject used in the correlation analysis: mean rsFC strength, global efficiency, structural global degree, network density, and **optional covariates** (age, sex, head‑motion, scanner site). | `data/processed/subject_metrics.csv` | CSV (header row) |
| **CorrelationResults** | Partial correlation coefficients, raw and Bonferroni‑corrected p‑values, empirical permutation p‑values, VIF, and multicollinearity diagnostics for all tested motifs × metrics × correlation‑type combinations. | `data/processed/correlation_results.json` | JSON (see `contracts/analysis_results.schema.yaml`) |
| **ResultsJSON** | Machine‑readable version of the statistical summary, matching `contracts/results.schema.yaml`. | `data/processed/results.json` | JSON |
| **AnalysisResultsJSON** | Machine‑readable version of the full analysis output, matching `contracts/analysis_results.schema.yaml`. | `data/processed/analysis_results.json` | JSON |
| **Manifest** | Record of which subjects were successfully processed, checksums of raw files, and overall cohort statistics. | `data/processed/manifest.json` | JSON (see `contracts/dataset.schema.yaml`) |
| **PDFReport** | Consolidated scientific report containing figures, tables, power‑analysis, and disclaimer. | `results/results.pdf` | PDF (binary) |

## Relationships
- Each **Subject** has exactly one **StructuralConnectome**, one **StructuralConnectomeMetadata**, one **rsFCMatrix**, one **MotifProfile**, and contributes a row to **SubjectMetrics**.  
- **SubjectMetrics** aggregates information from the subject’s **StructuralConnectome** (global degree, density) and **rsFCMatrix** (strength & global efficiency), plus optional covariates (age, sex, head‑motion, scanner site).  
- **CorrelationResults** are derived from the collection of **MotifProfile** vectors (across subjects) and **SubjectMetrics**.  
- **ResultsJSON** mirrors the contents of **CorrelationResults** and validates against the `contracts/results.schema.yaml`.  
- **AnalysisResultsJSON** mirrors the full output of the statistical analysis (including multicollinearity diagnostics and power analysis) and validates against `contracts/analysis_results.schema.yaml`.  
- **Manifest** tracks processing status of each **Subject** and links to the raw parquet files under `data/raw/`.

## Provenance & Versioning
- Every derived file includes a companion JSON metadata entry (e.g., in `structural_connectome.json`) that records: source description and URL, processing timestamp, random seed (42), and library versions (`pip freeze`).  
- The top‑level `state/projects/PROJ-331-investigating-the-influence-of-network-m.yaml` records SHA‑256 checksums for all raw files and a content hash for each derived artifact, satisfying Constitution Principles III and V.

## File Naming Conventions
- Subject‑specific files reside under `data/processed/<subject_id>/`.  
- Filenames are lower‑case, underscore‑separated, and end with the appropriate extension (`.npy`, `.json`, `.csv`).  
- Manifest and summary CSV files live directly in `data/processed/`.

## Validation
- The `contracts/` directory contains JSON‑Schema files that validate each JSON artifact (`motif_profile.json`, `correlation_results.json`, `manifest.json`, `results.json`, `analysis_results.json`, `structural_connectome.json`). The test suite (`tests/contract/test_schemas.py`) runs these validations automatically.

## Optional Covariates
If the HCP metadata CSV includes **age**, **sex**, **head‑motion summary**, or **scanner site**, they are automatically incorporated as additional fields in `subject_metrics.csv` and used as nuisance covariates in the partial correlation models (see FR‑005). Missing values are handled gracefully.

--- 