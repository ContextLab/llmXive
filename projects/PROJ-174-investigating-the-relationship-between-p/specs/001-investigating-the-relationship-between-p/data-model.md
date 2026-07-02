# Data Model: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

## 1. Overview

This document defines the data schemas for the project, ensuring strict adherence to the "Single Source of Truth" principle. All data artifacts are versioned and checksummed.

## 2. Entity Definitions

### 2.1 Raw Dataset Entity
Represents the unaltered eye‑tracking data from the source.
- **Source**: OpenNeuro (Parquet/CSV)
- **Location**: `data/raw/`
- **Integrity**: Checksummed; no modifications.

### 2.2 Processed Trial Entity
Represents a single valid trial after preprocessing (interpolation, filtering, validation).
- **Location**: `data/processed/trials.csv`
- **Key Attributes**:
  - `subject_id`: Unique identifier for the participant.
  - `trial_id`: Unique identifier for the trial.
  - `timestamp`: Monotonic timestamp (ms).
  - `pupil_diameter`: Interpolated and filtered pupil size (mm).
  - `search_time`: Reaction time or search duration (ms).
  - `target_salience`: *Nullable*. If missing in source metadata, this column is **omitted** and a warning is logged (FR‑003 “skip if missing” policy).  
  - `fixation_count`: Total number of fixations in the trial.

### 2.3 Analysis Result Entity
Aggregated results for correlation and modeling.
- **Location**: `data/results/`
- **Types**:
  - `correlation_summary.csv`: Pearson r, p‑value, Holm‑Bonferroni‑adjusted p‑value, significance flag.
  - `model_summary.csv`: LME coefficients, SE, p‑value, model type (Full, Reduced (Collinearity Handled)), and likelihood‑ratio test.
  - `classification_metrics.csv`: Accuracy, precision, recall, ROC‑AUC, `relative_decrease`, decision threshold, and ground‑truth limitation note.
  - `quality_report.csv`: Primary exclusion report summarizing counts per exclusion type (blink loss, timestamp errors, insufficient trials). This file is the **primary** artifact for FR‑008.

## 3. Data Flow Diagram

```mermaid
graph TD
    A[Raw Data (OpenNeuro)] -->|Ingest| B(Preprocessing)
    B -->|Filter/Interpolate| C{Validation}
    C -->|Fail: >30% missing| D[Exclude Trial]
    C -->|Pass| E[Processed Trials]
    E -->|Check Salience| F{Salience Present?}
    F -->|No| G[Log WARNING; omit Salience column]
    F -->|Yes| H[Use Salience]
    G & H --> I[Feature Extraction]
    I --> J[Correlation Analysis]
    I --> K[LME Modeling (only if Salience present & VIF OK)]
    I --> L[Classification Prototype]
    J --> M[Correlation CSV]
    K --> N[Model CSV]
    L --> O[Classification CSV]
```

## 4. Constraints & Invariants

1. **No On‑the‑Fly Salience Computation**: The `target_salience` column must exist in the source or be omitted; it is never derived from fixation data (FR‑003).  
2. **Monotonic Timestamps**: All trials in `data/processed` must have strictly increasing timestamps.  
3. **Exclusion Logging**: Every excluded trial must be recorded in `quality_report.csv` with the reason (primary artifact for FR‑008). A supplementary log file may also be written.  
4. **Ground Truth Limitation**: If the classifier uses the median‑split label, `ground_truth_limitation.txt` must state “Ground truth derived from search‑time median split; independent load measure unavailable.”  
