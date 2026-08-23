# Data Model: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Entity Definitions

### StudyRecord
Represents a single entry from the literature.
-   `author_year`: string (e.g., "Smith2023") - Unique identifier for the study.
-   `tract_name`: string (e.g., "Arcuate Fasciculus")
-   `metric_type`: string (e.g., "FA", "MD")
-   `effect_size`: float (Correlation coefficient `r`, or converted from t/F)
-   `sample_size`: int (`n`)
-   `source`: string (e.g., "PubMed", "Manual")

### MetaAnalysisResult
Aggregated output of the statistical synthesis.
-   `pooled_effect_size`: float (Weighted mean `r`)
-   `ci_lower`: float
-   `ci_upper`: float
-   `heterogeneity_i2`: float
-   `publication_bias_p`: float (or null if skipped)
-   `study_count`: int
-   `synthesis_mode`: string ("quantitative" or "narrative")
-   `bonferroni_threshold`: float (or null if not applicable)
-   `tract_count`: int (Number of distinct tracts, k)

### NarrativeSummary
Output for the fallback mode.
-   `summary_text`: string
-   `key_findings`: list of strings
-   `limitations`: list of strings
-   `qualitative_descriptors`: list of strings (Text snippets about neural circuitry)

## File Formats

### Input: `data/raw/studies.csv`
CSV file with headers: `author_year, tract_name, metric_type, effect_size, sample_size`.

### Output: `data/processed/study_count.json`
**Single Source of Truth for Gate Logic**.
```json
{
  "count": 12,
  "tract_count": 5,
  "mode": "quantitative",
  "timestamp": "2026-07-02T12:00:00Z"
}
```
*Note: This file replaces the previously proposed `real_data_status.json` to consolidate the gate logic into a single artifact.*

### Output: `data/derived/meta_result.json`
```json
{
  "pooled_r": 0.25,
  "ci_95": [0.10, 0.40],
  "i2": 45.5,
  "egger_p": 0.12,
  "bonferroni_threshold": 0.01,
  "tract_count": 5,
  "mode": "quantitative"
}
```

### Output: `data/derived/narrative_summary.json`
```json
{
  "summary_text": "The literature suggests a link between...",
  "key_findings": ["Tract A is associated with...", "Tract B shows no correlation..."],
  "limitations": ["Small sample size", "Heterogeneous methods"],
  "qualitative_descriptors": ["Auditory cortex activation", "Reward pathway connectivity"]
}
```

## Data Flow

1.  **Ingestion**: `extract.py` reads `data/raw/studies.csv` (or generates mock data).
2.  **Validation**: `real_data_validator.py` counts unique `author_year` pairs and distinct `tract_name` values. Writes `data/processed/study_count.json`.
3.  **Gate**: If `count < 10`, `pivot_narrative.py` reads `study_count.json` and generates `data/derived/narrative_summary.json`.
4.  **Analysis**: If `count >= 10`, `meta_analysis.py` runs statistical models.
5.  **Correction**: If `count >= 10` and `tract_count >= 2`, Bonferroni correction is applied.
6.  **Visualization**: `visualize.py` generates PNGs based on the result.