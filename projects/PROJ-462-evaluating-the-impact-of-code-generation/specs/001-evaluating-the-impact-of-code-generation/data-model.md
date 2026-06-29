# Data Model: 001-code-generation-performance-outcomes

## 1. Entity Definitions

### 1.1 DatasetRecord

Represents a single developer observation.

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| tool_usage | boolean | Yes | Whether LLM code generation was used |
| task_time | float | Yes | Task completion time (minutes) |
| defect_rate | float | Yes | Code quality metric (defects per KLOC) |
| experience_years | integer | Yes | Developer experience (years) |
| task_complexity | float | No | Task complexity score (if available) |
| project_type | string | No | Project type category (if available) |
| team_size | integer | No | Team size (if available) |

**Validation Rules**:  
- `tool_usage` must be `True`/`False`.  
- `task_time` > 0.  
- `defect_rate` ≥ 0.  
- `experience_years` ≥ 0.  

**Experience Level Derivation** (used for stratification):  
`experience_level` is **computed** from `experience_years` using the following **documented thresholds** (version‑controlled in `code/analysis/experience.py`):

- **Novice**: `experience_years` < 2  
- **Intermediate**: 2 ≤ `experience_years` ≤ 5  
- **Expert**: `experience_years` > 5  

These thresholds are the default; the sensitivity analysis sweeps alternative boundaries (1, 2, 3 years).

> **Spec-Root Flag**: The spec.md Assumptions section describes "Experience level classification algorithm: Combines repository contribution history and tenure metrics using weighted score (contributions × relative_weight + tenure_years × relative_weight)". This approach requires `contribution_count` and `tenure_years` fields that do NOT exist in the DatasetRecord schema above. The data-model.md definition (raw `experience_years` integer with simple threshold derivation) is correct for available data; the weighted-score approach in spec.md is incompatible and requires spec.md revision.

### 1.2 AnalysisResult

Statistical output from the ANCOVA analysis.

| Attribute | Type | Description |
|-----------|------|-------------|
| anova_results | dict | F‑statistics, p‑values, and (optional) covariate statistics |
| effect_sizes | dict | Cohen's d per experience stratum |
| adjusted_p_values | dict | Holm‑Bonferroni corrected p‑values |
| associational_framing | boolean | Must be `true` (FR‑006) |
| confounding_controls | dict | Coefficient estimates for each covariate actually included |
| power_flag | boolean | `true` if any stratum has < 30 observations |
| vif_scores | dict | VIF for each predictor (tool_usage, experience_level) |
| visualizations | array[object] *(optional)* | Metadata for generated plots (see VisualizationOutput) |
| sensitivity_results | array[object] *(optional)* | Rows of the threshold‑sweep CSV/JSON (see SensitivityResult) |

#### Example `anova_results` JSON fragment

```json
{
  "tool_usage": {"f_stat": 4.12, "p_value": 0.043},
  "experience_level": {"f_stat": 3.57, "p_value": 0.032},
  "interaction": {"f_stat": 2.89, "p_value": 0.058},
  "covariates": {
    "task_complexity": {"f_stat": 1.21, "p_value": 0.274},
    "team_size": {"f_stat": 0.87, "p_value": 0.354}
  }
}
```

### 1.3 VisualizationOutput

Metadata for each generated plot.

| Attribute | Type | Description |
|-----------|------|-------------|
| plot_type | string | e.g., `"boxplot"` |
| stratification_variable | string | Variable used for grouping (e.g., `"experience_level"` ) |
| interaction_lines | boolean | `true` if interaction lines are drawn |
| file_path | string | Relative path to the PNG/SVG file |

### 1.4 SensitivityResult

Results of the experience‑threshold sweep.

| Attribute | Type | Description |
|-----------|------|-------------|
| threshold_set | list[int] | Experience boundaries used (e.g., `[1,2,3]`) |
| completion_time_rates | dict[string, float] | Mean `task_time` per stratum |
| defect_rates | dict[string, float] | Mean `defect_rate` per stratum |
| effect_sizes | dict[string, float] | Cohen's d per stratum |
| variation_summary | dict[string, float] | Range/SD of each metric across thresholds |

## 2. Data Flow Diagram

```
raw/ (downloaded) → validate (FR‑001/FR‑002) → processed/ (filtered, complete cases) → analysis/ (ANCOVA, effect sizes, VIF, power flag) → output/
   ├─> visualizations/ (boxplots) → output/
   └─> sensitivity/ (threshold sweep) → output/
```

## 3. File Schemas

### 3.1 Input Dataset Schema (CSV/Parquet)

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| tool_usage | bool | Yes | 1 = assisted, 0 = unassisted |
| task_time | float | Yes | Minutes |
| defect_rate | float | Yes | Defects per KLOC |
| experience_years | int | Yes | Years of experience |
| task_complexity | float | No | Optional |
| project_type | string | No | Optional |
| team_size | int | No | Optional |

### 3.2 Analysis Output Schema (JSON)

See `contracts/analysis.schema.yaml` for the full JSON‑Schema definition, which mirrors the fields above (including optional `visualizations` and `sensitivity_results`).

### 3.3 Sensitivity Output Schema (CSV)

| threshold | stratum | completion_time | defect_rate | cohen_d |
|-----------|---------|-----------------|-------------|---------|
| 1 | novice | 45.2 | 1.8 | 0.34 |
| 1 | intermediate | 38.7 | 1.2 | 0.41 |
| … | … | … | … | … |

## 4. Versioning & Checksums

All files under `data/` are listed in `state/projects/PROJ-462.../artifacts.yaml` with SHA‑256 hashes, satisfying Constitution Principle III.

```yaml
artifact_hashes:
  data/raw/developer_productivity.parquet: sha256:abc123...
  data/processed/cleaned.parquet: sha256:def456...
  data/output/analysis.json: sha256:ghi789...
```

---

# Quickstart: 001-code-generation-performance-outcomes

## Prerequisites

- Python 3.11+
- Git
- **Verified developer‑productivity dataset** (see *Dataset Acquisition Strategy* in `plan.md`)

## ⚠️ DATASET AVAILABILITY

The pipeline **cannot run** until a verified dataset containing the required variables is added to the project's "# Verified datasets" block. Follow the steps in `plan.md` → *Dataset Acquisition Strategy* to supply such a dataset.

## Installation

```bash
# Clone repository
git clone <repo-url>
cd projects/PROJ-462-evaluating-the-impact-of-code-generation

# Virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Directory Layout

```
code/
  ├── ingest/
  ├── analysis/
  ├── viz/
  ├── export/
  └── main.py
data/
  ├── raw/
  ├── processed/
  └── output/
```

## Running the Full Pipeline

```bash
# 1️⃣ Download & verify dataset (FR‑001)
python code/ingest/download.py --url <verified-dataset-url>

# 2️⃣ Validate required columns (FR‑002)
python code/ingest/validate.py --input data/raw/dataset.parquet

# 3️⃣ Run ANCOVA analysis, effect sizes, FWE correction (FR‑003‑FR‑005)
python code/main.py --input data/processed/cleaned.parquet --output data/output/

# 4️⃣ Generate publication‑ready plots (FR‑007)
python code/viz/plots.py --analysis data/output/analysis.json --out-dir data/output/plots/

# 5️⃣ Sensitivity analysis on experience thresholds (FR‑009)
python code/analysis/sensitivity.py --input data/processed/cleaned.parquet \
    --thresholds 1 2 3 --output data/output/sensitivity.csv

# 6️⃣ Export final results (FR‑008)
python code/export/results.py --analysis data/output/analysis.json \
    --plots data/output/plots/ --sensitivity data/output/sensitivity.csv \
    --out-dir data/output/final/
```

Each step writes intermediate files to `data/` and logs progress. The pipeline aborts with a clear error if any required variable is missing or if a stratum contains < 30 observations (power flag).

## Testing

```bash
# Contract validation (datasets & analysis output)
pytest tests/contract/

# Integration test of the full pipeline (requires a small verified test dataset)
pytest tests/integration/

# Unit tests for core modules
pytest tests/unit/
```

## Reproducibility Guarantees

- Random seed `42` is hard‑coded in `code/main.py`.  
- All dependencies are pinned in `code/requirements.txt`.  
- Dataset checksums are stored in `state/projects/.../artifacts.yaml`.  
- No in‑place data modifications; each transformation creates a new file.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| Variable‑presence report lists missing columns | Wrong dataset or outdated URL | Verify dataset URL and checksum; obtain a dataset that includes all required variables. |
| > 20 % of rows removed due to missing experience | Incomplete records | Consider data imputation (outside scope) or obtain a cleaner dataset. |
| Power flag `true` | < 30 observations in a stratum | Collect more data or note limitation in the final report. |
| VIF > 5 warning | Collinearity between `tool_usage` and `experience_level` | Report as limitation; do not claim independent effects. |
| Covariate columns absent | Dataset does not contain them | Model runs without covariates; warning logged. |
| Runtime > 6 h | Very large raw dataset | Use the sampling option in `download.py` to limit size (documented). |

--- 

# References

(Only URLs from the verified‑datasets block are cited; none currently satisfy the variable requirements, reinforcing the need for dataset acquisition.)