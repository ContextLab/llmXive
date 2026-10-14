# Data Model: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Improvisation Skill

## Overview
Schemas below define the structure of every artifact produced by the pipeline. Contract tests in `tests/contract/` validate conformity to these schemas.

## Schemas

### 1. Raw OpenNeuro Parquet Dataset (`raw_dataset.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Raw OpenNeuro Parquet Dataset"
type: object
required:
  - subject_id
  - run_label
  - age
  - years_training
  - fd
  - roi_1
properties:
  subject_id:
    type: string
    description: "Unique participant identifier."
  run_label:
    type: string
    enum: ["Improv", "Scripted"]
    description: "Task condition."
  age:
    type: number
    description: "Age in years."
  years_training:
    type: number
    description: "Self‑reported years of musical training."
  fd:
    type: number
    description: "Mean frame‑wise displacement (mm)."
  roi_1:
    type: number
  roi_2:
    type: number
  # ...
  roi_100:
    type: number
  instrument_type:
    type: string
    description: "Instrument played by the participant (optional)."
  genre:
    type: string
    description: "Musical genre preference (optional)."
  practice_intensity:
    type: number
    description: "Average weekly practice hours (optional)."
  education:
    type: string
    description: "Highest education level (optional)."
  improv_rating:
    type: number
    description: "Post‑scan improvisation rating (0‑10 scale, optional)."
additionalProperties: false
```

### 2. Preprocessed ROI Time‑Series (`preprocessed_timeseries.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Preprocessed ROI Time‑Series"
type: object
required:
  - subject_id
  - timepoint
properties:
  subject_id:
    type: string
  timepoint:
    type: integer
    description: "Index of the time point within the run."
  roi_1:
    type: number
  roi_2:
    type: number
  # ...
  roi_100:
    type: number
additionalProperties: false
```

### 3. Network Metrics (`network_metrics.schema.yaml`) – **Primary contract**
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Dynamic Network Metrics per Window"
type: object
required:
  - subject_id
  - window_id
  - global_efficiency
  - modularity
  - participation_coefficient
properties:
  subject_id:
    type: string
    description: "Identifier of the participant."
  window_id:
    type: integer
    description: "Sliding‑window index (starting at 0)."
  global_efficiency:
    type: number
    description: "Weighted global efficiency of the functional graph."
  modularity:
    type: number
    description: "Louvain modularity score of the graph."
  participation_coefficient:
    type: number
    description: "Mean participation coefficient across all nodes."
additionalProperties: false
```

### 4. PCA Scores (`pca_scores.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Principal Component Scores per Subject"
type: object
required:
  - subject_id
  - pc_1
  - pc_2
  - pc_3
properties:
  subject_id:
    type: string
  pc_1:
    type: number
  pc_2:
    type: number
  pc_3:
    type: number
additionalProperties: false
```

### 5. Regression Results (`regression_results.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Regression and Permutation Test Results"
type: object
required:
  - pc
  - coefficient
  - raw_p
  - fdr_p
  - significance
properties:
  pc:
    type: string
    description: "Principal component identifier (e.g., pc_1)."
  coefficient:
    type: number
    description: "Regression coefficient for years_training."
  raw_p:
    type: number
    description: "Permutation‑derived p‑value before correction."
  fdr_p:
    type: number
    description: "Benjamini‑Hochberg FDR‑corrected p‑value."
  significance:
    type: boolean
    description: "True if fdr_p < 0.05."
additionalProperties: false
```

## Relationships
- Each **subject** appears in the raw dataset, the preprocessed time‑series, the network‑metrics file, and the PCA‑scores file.  
- **Window IDs** link metrics to the corresponding time‑window.  
- **PC identifiers** link regression results to the PCA‑scores.  

All files reside under `data/` with clear naming (`raw.parquet`, `timeseries_<sub>.csv`, `metrics_<sub>.csv`, `pca_scores.csv`, `regression_results.csv`).

---


