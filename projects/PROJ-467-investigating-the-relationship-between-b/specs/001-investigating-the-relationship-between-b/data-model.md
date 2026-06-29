# Data Model: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Tactile Discrimination

## Overview
The data model defines the schema for raw, intermediate, and final artifacts used throughout the pipeline. All schemas are expressed in JSON‑compatible YAML and are validated against the contracts in `contracts/`.

## 1. Raw Dataset Schema (`raw_dataset.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Raw Multimodal Dataset"
type: object
required:
  - subject_id
  - fmri_path
  - tactile_score
  - age
  - sex
  - mean_framewise_displacement
  - scanner_id
properties:
  subject_id:
    type: string
    description: "Unique identifier (e.g., HCP01, ABCD_12345)"
  fmri_path:
    type: string
    format: uri
    description: "Local path or HF URI to the pre‑processed 4‑D NIfTI file"
  tactile_score:
    type: number
    description: "Two‑point discrimination threshold in mm"
  age:
    type: integer
    minimum: 5
    description: "Age in years at scan"
  sex:
    type: string
    enum: [M, F, O, U]
    description: "Self‑reported sex"
  mean_framewise_displacement:
    type: number
    description: "Average FD (mm) across the run"
  scanner_id:
    type: string
    description: "Site or scanner identifier (e.g., 'HCP_3T_1')"
```

## 2. Static Network Metric Schema (`static_metric.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Static Network Metric"
type: object
required:
  - subject_id
  - metric_name
  - value
  - parameters
properties:
  subject_id:
    type: string
  metric_name:
    type: string
    enum: [modularity, segregation]
  value:
    type: number
  parameters:
    type: object
    required: [threshold, atlas, algorithm_version]
    properties:
      threshold:
        type: number
        description: "Absolute correlation threshold used to binarize graph"
      atlas:
        type: string
        description: "Parcellation used (e.g., 'schaefer-200')"
      algorithm_version:
        type: string
        description: "Version tag of Louvain implementation"
```

## 3. Dynamic Metric Schema (`dynamic_metric.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Dynamic Network Metric"
type: object
required:
  - subject_id
  - metric_name
  - time_series
  - window_length_sec
  - step_sec
  - parameters
properties:
  subject_id:
    type: string
  metric_name:
    type: string
    enum: [dynamic_modularity, flexibility]
  time_series:
    type: array
    items:
      type: number
    description: "Metric value for each sliding window"
  window_length_sec:
    type: number
  step_sec:
    type: number
  parameters:
    type: object
    required: [threshold, atlas, algorithm_version]
    properties:
      threshold:
        type: number
      atlas:
        type: string
      algorithm_version:
        type: string
```

## 4. Analysis Result Schema (`analysis_result.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Correlation Analysis Result"
type: object
required:
  - predictor
  - outcome
  - raw_r
  - raw_p
  - adjusted_r
  - adjusted_p
  - ci_95
  - corrected_p
  - power_estimate
properties:
  predictor:
    type: string
    description: "Name of the network metric (e.g., 'static_modularity')"
  outcome:
    type: string
    enum: [tactile_score]
  raw_r:
    type: number
  raw_p:
    type: number
  adjusted_r:
    type: number
  adjusted_p:
    type: number
  ci_95:
    type: array
    items:
      type: number
    description: "95% confidence interval for the adjusted correlation"
  corrected_p:
    type: number
    description: "p‑value after FDR correction"
  power_estimate:
    type: number
    description: "Post‑hoc power for this test (or `[deferred]` if under‑powered)"
```

## 5. Provenance Metadata (`metadata.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Provenance Metadata"
type: object
required:
  - file_hash
  - created_at
  - git_commit
  - parameters
properties:
  file_hash:
    type: string
    description: "SHA‑256 checksum of the artifact"
  created_at:
    type: string
    format: date-time
  git_commit:
    type: string
    description: "Full 40‑char commit hash of the code used"
  parameters:
    type: object
    description: "Arbitrary key‑value mapping of pipeline parameters"
```

## 6. Flexibility Metric Definition
**Flexibility** quantifies the temporal re‑configuration of a node’s community affiliation across sliding windows. For each node, count the number of times its community label changes from one window to the next; the per‑subject flexibility score is the mean (or sum) of these counts across all nodes. This metric is stored using the `dynamic_metric.schema.yaml` with `metric_name: flexibility` and follows the same parameter metadata as dynamic modularity.

All generated files (`*.parquet`, `*.npz`, `*.csv`) must have an accompanying `metadata/*.json` that conforms to `metadata.schema.yaml`. Contract validation will be performed in CI.

---

