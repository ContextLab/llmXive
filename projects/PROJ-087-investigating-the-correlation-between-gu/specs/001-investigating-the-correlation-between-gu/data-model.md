# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

## Overview

This document defines the data structures for the microbiome-sleep correlation pipeline. It covers the input schema (if data were available), the intermediate processed schema, and the output schema for both "Happy Path" and "Blocked Path" scenarios.

## Entities

### 1. MicrobiomeSample (Input/Intermediate)

Represents a single participant's data.

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `sample_id` | string | Unique identifier for the sample | Yes |
| `otu_counts` | object | Dictionary of OTU ID -> count | Yes |
| `age` | integer | Age of participant | No |
| `bmi` | float | Body Mass Index | No |
| `antibiotic_use_last_3m` | boolean | True if antibiotics used in last 3 months | **Yes** |
| `sleep_efficiency` | float | Percentage (0-100) | **Yes** |
| `sleep_duration_hours` | float | Total hours slept | **Yes** |
| `sleep_latency` | float | Time to fall asleep (minutes) | No |

### 2. AlphaDiversityResult

Computed diversity indices for a sample.

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `sample_id` | string | Link to sample | Yes |
| `shannon` | float | Shannon diversity index | Yes |
| `simpson` | float | Simpson diversity index | Yes |
| `observed_otus` | float | Count of observed OTUs | Yes |

### 3. CorrelationResult

Statistical output of a single test.

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `diversity_metric` | string | Name of diversity metric (e.g., "shannon") | Yes |
| `sleep_metric` | string | Name of sleep metric (e.g., "efficiency") | Yes |
| `r_value` | float | Spearman correlation coefficient | Yes |
| `p_value` | float | Raw p-value | Yes |
| `q_value` | float | Benjamini-Hochberg adjusted p-value | Yes |
| `is_significant` | boolean | True if q_value < 0.05 | Yes |
| `is_moderate` | boolean | True if |r| > 0.3 | Yes |

### 4. FeasibilityReport (Blocked State)

Structure for "Feasibility Report" (generated when data is unavailable).

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `status` | string | Value: "blocked" | Yes |
| `reason` | string | Explanation (e.g., "No verified URL for AGP") | Yes |
| `timestamp` | string | ISO 8601 timestamp (static, derived from plan.md) | Yes |
| `measurement_status` | string | Value: "unmeasurable" | Yes |
| `diversity_computation_status` | string | Value: "blocked" | Yes |
| `correlation_analysis_status` | string | Value: "blocked" | Yes |
| `visualization_status` | string | Value: "blocked" | Yes |
| `exclusion_rates_status` | string | Value: "unmeasurable" | Yes |
| `correlation_metrics_status` | string | Value: "unmeasurable" | Yes |

## File Schemas

### Input: `data/raw/agp_otu.tsv` (Expected)
- **Format**: TSV
- **Columns**: `SampleID`, `OTU_1`, `OTU_2`, ... (OTU counts), `antibiotic_use_last_3m`, `sleep_efficiency`, `sleep_duration_hours`.
- **Note**: This file is **NOT** available in the current `# Verified datasets` block.

### Output: `data/processed/feasibility_report.json` (Blocked)
- **Format**: JSON
- **Content**:
  ```json
  {
    "status": "blocked",
    "reason": "No verified URL for American Gut Project with sleep metadata",
    "timestamp": "2026-06-26T00:00:00Z",
    "measurement_status": "unmeasurable",
    "diversity_computation_status": "blocked",
    "correlation_analysis_status": "blocked",
    "visualization_status": "blocked",
    "exclusion_rates_status": "unmeasurable",
    "correlation_metrics_status": "unmeasurable"
  }
  ```
  *Note: The timestamp is static (derived from plan.md) to ensure deterministic hashing.*

### Output: `outputs/reports/feasibility_report.md`
- **Format**: Markdown
- **Content**: A human-readable report stating the analysis was not performed due to data unavailability, citing the specific missing variables and the lack of a verified URL.