# Data Model: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## 1. Entities & Relationships

### 1.1 Subject
Represents a single participant in the study.
-   **ID**: Unique HCP Subject ID (string).
-   **Status**: `processed`, `skipped`, `error`.
-   **Dependencies**: Structural Matrix, RSFC Matrix, Motif Profile.
-   **Skip Logic**: If data is missing, status is `skipped` and a warning is logged. The subject is excluded from downstream calculations.

### 1.2 Structural Connectome
Binary adjacency matrix derived from diffusion data.
-   **Format**: NumPy `.npy` (100x100 float32).
-   **Origin**: HCP Diffusion Data + Schaefer-100 Parcellation.
-   **Properties**: Symmetric (undirected), binary (0/1).

### 1.3 Functional Connectome (RSFC)
Correlation matrix derived from BOLD time-series.
-   **Format**: NumPy `.npy` (100x100 float32).
-   **Properties**: Symmetric, values in [-1, 1].

### 1.4 Motif Profile
Summary of 3-node motif z-scores for a subject.
-   **Format**: JSON.
-   **Keys**: Motif type ID (e.g., "isolated", "edge", "path", "triangle"), Z-score (float).
-   **Null Model Params**: Iterations, seed.

### 1.5 Correlation Result
Statistical output linking motifs to functional metrics.
-   **Format**: JSON / CSV.
-   **Fields**: Motif ID, Metric (Strength/Efficiency), Partial Correlation (r), P-value (raw), P-value (Bonferroni), Significant (bool), Empirical P-value (from permutation), VIF.

### 1.6 Manifest
Cohort-level summary of processing status.
-   **Format**: JSON.
-   **Fields**: `cohort_target`, `cohort_actual`, `cohort_skipped`, `subjects` (list of records), `checksums`.

## 2. File Formats & Schemas

### 2.1 Raw Data
-   `data/raw/<subject_id>/structural.nii.gz` (HCP original)
-   `data/raw/<subject_id>/rsfmri.nii.gz` (HCP original)

### 2.2 Processed Data
-   `data/processed/<subject_id>/structural.npy`: Binary adjacency matrix.
-   `data/processed/<subject_id>/rsfc.npy`: Correlation matrix.
-   `data/processed/<subject_id>/motif_profile.json`: Z-scores.
-   `data/processed/manifest.json`: List of processed subjects, skipped count, and checksums.

### 2.3 Output
-   `results/results.pdf`: Final report.
-   `data/logs/pipeline.log`: Machine-readable log.
-   `data/processed/correlation_results.json`: Statistical outputs.

## 3. Data Flow

1.  **Ingest**: HCP Data -> `data/raw/`
2.  **Process**: `data/raw/` -> `code/data_loader.py` -> `data/processed/structural.npy`, `rsfc.npy`. *Logic*: Skip missing subjects, log warnings, update manifest.
3.  **Analyze**: `structural.npy` -> `code/motif_analysis.py` -> `data/processed/motif_profile.json`
4.  **Correlate**: `motif_profile.json`, `rsfc.npy` -> `code/correlation_analysis.py` -> `data/processed/correlation_results.json` (includes VIF check).
5.  **Report**: `correlation_results.json` -> `code/report_generator.py` -> `results/results.pdf`

## 4. Validation & Logging (Task T017)

-   **utils.py**: Validates `seed=42`, `bonferroni_alpha` (calculated as 0.05/num_motifs), `permutation_count=1000`, and `vif_threshold=5` at startup.
-   **pipeline.log**: Records all processing steps, warnings (e.g., "Subject X skipped: missing diffusion"), and errors.
-   **Manifest**: Tracks `actual_count` vs `target` to satisfy SC-001 (>= 95% success).

## 5. Manifest Schema Details

The `manifest.json` file (referenced in `dataset.schema.yaml`) contains:
-   `cohort_target`: Integer (50).
-   `cohort_actual`: Integer (number of subjects successfully processed).
-   `cohort_skipped`: Integer (number of subjects skipped).
-   `subjects`: Array of objects, each containing:
    -   `subject_id`: String.
    -   `status`: Enum ["processed", "skipped", "error"].
    -   `structural_path`: String or null.
    -   `rsfc_path`: String or null.
    -   `error_message`: String or null.
-   `checksums`: Object mapping filenames to SHA256 hashes.

The `data_loader.py` logic ensures that if a subject is missing data, the `status` is set to "skipped", the `error_message` is logged, and the subject is **not** included in the `cohort_actual` count for statistical analysis, but **is** included in the manifest to track the success rate against SC-001.