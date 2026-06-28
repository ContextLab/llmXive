# Data Model: Assessing the Impact of Mindfulness Training on Default Mode Network Activity

## Entity Relationship Diagram

```
┌─────────────────┐       ┌──────────────────┐       ┌─────────────────────┐
│   Dataset       │──────▶│  Subject         │──────▶│  Preprocessing      │
│                 │       │                  │       │  Output             │
│ - dataset_id    │       │ - subject_id     │       │ - bold_path         │
│ - source_url    │       │ - pre_scan_path  │       │ - motion_params     │
│ - scan_count    │       │ - post_scan_path │       │ - qc_report_path    │
│ - subject_count │       │ - motion_flags   │       │                     │
│ - design_status │       │ - exclusion_flag │       │                     │
└─────────────────┘       └──────────────────┘       └─────────────────────┘
                                    │
                                    │
                                    ▼
┌─────────────────┐       ┌──────────────────┐       ┌─────────────────────┐
│  Meta Analysis  │◀──────│  Effect Size     │◀──────│  Connectivity       │
│                 │       │                  │       │  Matrix             │
│ - pooled_effect │       │ - node_pair      │       │ - node_pair         │
│ - ci_lower      │       │ - pre_corr       │       │ - pre_fisher_z      │
│ - ci_upper      │       │ - post_corr      │       │ - post_fisher_z     │
│ - i_squared     │       │ - cohen_d        │       │ - nbs_p_value       │
│ - q_test        │       │ - ci_lower       │       │ - effect_size       │
│ - dataset_count │       │ - ci_upper       │       │ - boot_ci_lower     │
│ - sensitivity   │       │ - dataset_id     │       │ - boot_ci_upper     │
└─────────────────┘       └──────────────────┘       └─────────────────────┘
```

## Dataset Entity

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| dataset_id | string | OpenNeuro dataset identifier | pattern: `^ds[0-9]{6}$`, required |
| source_url | string | Canonical download URL | format: `uri`, required |
| scan_count | integer | Total number of fMRI scans | minimum: 2 |
| subject_count | integer | Total number of subjects | minimum: 1 |
| design_status | string | Pre/post design verification status | enum: {verified, failed, missing} |
| mindfulness_metadata | object | Intervention details | optional |
| checksum | string | SHA256 checksum of dataset bundle | pattern: `^[a-f0-9]{64}$` |
| download_timestamp | string | ISO‑8601 timestamp of download | format: `date-time` |

## Subject Entity

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| subject_id | string | Subject identifier within dataset | required |
| dataset_id | string | Parent dataset reference | required |
| pre_scan_path | string | Path to pre‑intervention BOLD file | required if paired |
| post_scan_path | string | Path to post‑intervention BOLD file | required if paired |
| motion_params | object | Translation/rotation from fMRIPrep | required |
| motion_exclusion | boolean | Flag for >3 mm / >3° motion | derived |
| exclusion_reason | string | Reason for exclusion (if any) | nullable |
| paired_status | string | Pre/post availability | enum: {complete, missing_pre, missing_post} |

## Preprocessing Output Entity

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| subject_id | string | Subject identifier | required |
| bold_path | string | Path to preprocessed BOLD (MNI152) | pattern: `^data/processed/fmriprep_outputs/` |
| motion_params_file | string | Path to motion parameters file | required |
| confound_file | string | Path to confound regressors file | required |
| qc_report_path | string | Path to fMRIPrep HTML QC report | pattern: `\.html$` |
| preprocessing_status | string | Execution status | enum: {success, failed, timeout} |
| preprocessing_timestamp | string | ISO‑8601 timestamp | format: `date-time` |
| mni_space | string | Normalization space | const: `MNI152` |
| smoothing_mm | number | Smoothing kernel size | const: 6.0 |
| bandpass_low | number | Low‑frequency cutoff | const: 0.01 |
| bandpass_high | number | High‑frequency cutoff | const: 0.1 |
| motion_exclusion_flag | boolean | True if motion >3 mm/3° | required |
| exclusion_reason | string | Optional reason for exclusion | nullable |

## Connectivity Matrix Entity

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| subject_id | string | Subject identifier | required |
| scan_type | string | Pre or post scan | enum: {pre, post} |
| node_pair | string | Identifier `node1-node2` | pattern: `^[A-Za-z_]+-[A-Za-z_]+$` |
| node1 | string | First DMN node | enum: {PCC, mPFC, IPL, angular_gyrus} |
| node2 | string | Second DMN node | enum: {PCC, mPFC, IPL, angular_gyrus} |
| pearson_corr | number | Raw Pearson correlation | min: -1.0, max: 1.0 |
| fisher_z | number | Fisher‑transformed correlation | required |
| ar1_residual | number | AR(1) prewhitening residual | nullable |
| time_series_length | integer | Length of extracted time series | min: 1 |

## Effect Size Entity (new)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| node_pair | string | Node pair identifier | required |
| dataset_id | string | Source dataset | required |
| cohen_d | number | Effect size point estimate | required |
| ci_lower | number | Bootstrapped 95 % CI lower | required |
| ci_upper | number | Bootstrapped 95 % CI upper | required |
| nbs_p_value | number | NBS‑corrected p‑value | min: 0.0, max: 1.0 |
| nbs_significant | boolean | Significance at α = 0.05 | required |
| permutation_count | integer | Permutations used | const: 10000 |
| bootstrap_count | integer | Bootstraps used | const: 10000 |

## Meta‑Analysis Result Entity (new)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| analysis_id | string | Unique identifier | required |
| node_pair | string | Node pair meta‑analyzed | required |
| pooled_effect | number | Random‑effects pooled Cohen’s d | required |
| pooled_ci_lower | number | Pooled 95 % CI lower | required |
| pooled_ci_upper | number | Pooled 95 % CI upper | required |
| i_squared | number | Heterogeneity (0‑[deferred]) | min: 0, max: 100 |
| q_test_p_value | number | Q‑test heterogeneity p‑value | min: 0, max: 1 |
| dataset_count | integer | Number of datasets included | min: 1 |
| sensitivity_results | object | Leave‑one‑out analysis per dataset | nullable |
