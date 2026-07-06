# Data Model: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## 1. Overview

This document defines the data structures and schemas used throughout the pipeline. All data is derived from the raw OpenNeuro source and transformed through the QC and analysis stages. The pipeline uses memory-mapped loading for raw NIfTI data to respect RAM constraints.

## 2. Entity Definitions

### Subject
Represents a single participant.
- `subject_id`: Unique string identifier.
- `motion_displacement`: Float (mm), maximum displacement.
- `qc_status`: Enum ["passed", "failed"].
- `has_inclusion`: Boolean.
- `has_exclusion`: Boolean.
- `inclusion_time_series`: 2D Array (Time x Nodes) or `null`. (Stored in memory/intermediate file).
- `exclusion_time_series`: 2D Array (Time x Nodes) or `null`. (Stored in memory/intermediate file).
- `raw_nifti_path`: String (Path to memory-mapped source file).

### ConnectivityMatrix
Represents the correlation matrix for a specific condition.
- `subject_id`: String.
- `condition`: Enum ["inclusion", "exclusion"].
- `nodes`: List of strings ["PCC", "mPFC", "Angular"].
- `matrix`: 2D Array (Nodes x Nodes) of correlation coefficients.
- `mean_absolute_correlation`: Float.

### Result
Aggregated statistical results.
- `metric`: String (e.g., "mean_absolute_correlation").
- `condition_comparison`: String ("inclusion vs exclusion").
- `p_value`: Float.
- `effect_size`: Float (e.g., Cohen's d or permutation-based).
- `confidence_interval`: Tuple (lower, upper).
- `is_associational`: Boolean.
- `edge_p_values`: Dict {edge_name: p_value}.
- `edge_p_values_fdr`: Dict {edge_name: adjusted_p_value}.
- `n_subjects`: Integer.
- `motion_threshold`: Float (mm).
- `sensitivity_curve`: List of {threshold: float, p_value: float} (Optional, for SC-005).

## 3. File Formats

### Input: Raw Data (BIDS)
Source: OpenNeuro dataset.
- Files: `sub-<id>/func/sub-<id>_task-cyberball_run-<id>_space-MNI_desc-preproc_bold.nii.gz`, `events.tsv`.
- Format: NIfTI-1 (4D), JSON sidecars, TSV events.

### Intermediate: QC Report (JSON)
- List of subjects with `qc_status` and `motion_displacement`.

### Intermediate: Time-Series (NPY/PKL)
- Memory-mapped or temporary files storing extracted 1D/2D arrays per subject.

### Output: Results (JSON/YAML)
- Final statistical findings, including p-values, effect sizes, and framing.

## 4. Constraints

- **Motion Threshold**: `motion_displacement` > 3.0 → `qc_status` = "failed".
- **Condition Completeness**: Both `has_inclusion` and `has_exclusion` must be true for inclusion in paired analysis.
- **Subject Count**: Valid subjects < 10 → Halt.
- **Memory**: Raw 4D data is never fully loaded into RAM; only time-series (1D/2D) are held in memory.