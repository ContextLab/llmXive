# Implementation Plan: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback (Behavioral Proxies)

**Branch**: `001-social-rejection-reward` | **Date**: 2026-10-19 | **Spec**: `specs/001-the-effect-of-simulated-social-rejection/spec.md`  
**Input**: Feature specification from `specs/001-the-effect-of-simulated-social-rejection/spec.md`

## Summary
We will execute a fully reproducible, CPU‑only pipeline on GitHub Actions free tier that (1) downloads the verified OpenNeuro Cyberball dataset `ds000208` (parquet), (2) validates required columns and size, (3) records the unavailability of a reward‑feedback dataset (no open‑access reward dataset exists), (4) preprocesses reaction times and mood ratings (outlier flagging, Z‑score normalization, per‑participant aggregation), (5) runs a **design‑aware** statistical analysis: a Repeated‑Measures ANOVA (or mixed‑effects model) when the same participants appear in both conditions, otherwise a Between‑Subjects One‑Way ANOVA, with Benjamini‑Hochberg FDR correction, (6) conducts α‑sensitivity (0.01, 0.05, 0.1) and outlier‑sensitivity analyses, (7) computes confidence intervals at a conventional confidence level for effect sizes, and (8) generates a markdown report that (a) explicitly states the design type, (b) contains the required “associational” phrasing and no “causal” wording, and (c) notes that neural responses are inferred from behavioral proxies. All artifacts are validated against JSON/YAML schemas in `contracts/`.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scipy==1.13.0`, `statsmodels==0.14.2`, `pyyaml==6.0.1`, `requests==2.32.3`  
- **Storage**: Local filesystem under `data/`, `results/`, `paper/`  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: GitHub Actions `ubuntu‑latest` (2 CPU, ~7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑only, memory ≤ 7 GB, total runtime ≤ 6 h, no GPU needed.

## Constitution Check
| Principle | How the Plan Satisfies |
|-----------|------------------------|
| I. Reproducibility | Deterministic seeds, pinned `requirements.txt`, full pipeline scripts, no manual steps. |
| II. Verified Accuracy | Only the verified OpenNeuro parquet URL is used (see Research.md). |
| III. Data Hygiene | SHA‑256 checksum recorded, raw files never mutated, all transformations produce new files with documented provenance. |
| IV. Single Source of Truth | All numbers in the final report are read directly from `results/analysis_output.json`. |
| V. Versioning Discipline | `artifact_hashes` and `updated_at` fields in project state are updated after each successful step. |
| VI. Behavioral Proxy Transparency | Report includes exact phrasing required by FR‑009. |
| VII. Paradigm Validity | Ingestion validates presence of Cyberball “rejection” and “control” conditions. |

All principles are satisfied; the plan will be re‑checked after Phase 1 design.

## Project Structure
```text
specs/001-the-effect-of-simulated-social-rejection/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── ingest_schema.schema.yaml
│   ├── analysis_output.schema.yaml
│   └── analysis_results.schema.yaml
└── tasks.md   # generated later
```

```text
projects/PROJ-258-the-effect-of-simulated-social-rejection/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── ingest.py
│   ├── validate.py
│   ├── preprocess.py
│   ├── analyze.py
│   ├── report.py
│   └── power.py   # (removed from pipeline)
├── data/
│   ├── raw/
│   │   └── ds000208.parquet
│   ├── processed/
│   └── interim/
├── results/
├── paper/
├── tests/
│   ├── unit/
│   └── integration/
└── state/
    └── projects/
        └── PROJ-258-the-effect-of-simulated-social-rejection.yaml
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| No open‑source reward dataset | Verified list contains none; fabricating data would violate Data Availability. | Inventing a synthetic reward dataset (rejected). |
| Dataset > 7 GB | FR‑001 mandates halting; pre‑download size check prevents OOM. | Loading without size check (rejected). |
| Small N → ANOVA convergence warnings | Results could be unstable; must be logged, fallback to non‑parametric, note in Limitations. | Ignoring warnings (rejected). |
| Spec‑conflict on `p_fdr ≤ p_raw` | Spec is mathematically incorrect; pipeline follows correct inequality and flags spec for amendment. | Enforcing wrong inequality (rejected). |

## Tasks (mapped to FRs/SCs)

| Phase | Task ID | Description | FR / SC addressed |
|-------|---------|-------------|-------------------|
| **Setup** | T001 | Create directory tree (`code/`, `data/`, `results/`, `paper/`, `tests/`). | Constitution I, FR‑005 |
| | T002 | Write `code/requirements.txt` with exact pinned versions (see Technical Context). Add entry to `quickstart.md`. | Constitution I, FR‑005 |
| **Ingestion & Validation** | **T003** | Download `ds000208.parquet` from the verified HuggingFace URL to `data/raw/`. Compute SHA‑256 checksum, store in `data/raw/metadata.json`, and write `data/raw/CITATION.md`. Abort with exit 1 if (a) required columns missing, (b) file size > 7 GB, or (c) `condition` does not contain both “rejection” and “control”. Also create deterministic placeholder `data/interim/reward_unavailable.json` indicating no reward dataset. | FR‑000, FR‑001, SC‑001 |
| | **T004** | Run `code/validate.py` to validate `data/raw/ds000208.parquet` against `contracts/dataset.schema.yaml` and `contracts/ingest_schema.schema.yaml`. Output a validation report `data/interim/ingest_validation_report.json`. | FR‑000, SC‑001 |
| **Preprocessing** | **T005** | Load the parquet via memory‑mapping, flag outliers per‑condition using IQR (1.5×IQR), Z‑score normalize reaction times within each condition, aggregate mean RT and mood per participant, write `data/processed/analysis_ready_ds000208.csv`. | FR‑002 |
| | **T006** | Write `data/interim/outlier_log.json` containing per‑condition IQR thresholds and counts of flagged rows. | FR‑002 |
| **Statistical Analysis** | **T007** | Load `analysis_ready_ds000208.csv`, **design‑aware** analysis: if the ingestion schema reports `single_cohort_validation.is_single_cohort == true` run a **Repeated‑Measures ANOVA** (or linear mixed‑effects model) on each outcome; otherwise run a **Between‑Subjects One‑Way ANOVA** (or ANCOVA if covariates present). Perform Shapiro‑Wilk and Levene tests; on violation: (i) log‑transform RT, (ii) use Welch’s ANOVA, (iii) fallback to Kruskal‑Wallis, documenting the path. Compute eta‑squared effect size **and** a 95 % confidence interval for that effect size. Store results in `results/analysis_output.json` conforming to `contracts/analysis_output.schema.yaml`. | FR‑003, FR‑007, FR‑008 |
| | **T008** | Apply Benjamini‑Hochberg FDR correction to the raw p‑values; add `p_fdr` column. Verify `p_fdr >= p_raw` (SC‑003 compliance; the spec’s opposite inequality is flagged for amendment). | FR‑004, SC‑003 |
| | **T009** | Perform α‑sensitivity sweep over {0.01, 0.05, 0.1}; add boolean flags to `analysis_output.json`. | FR‑006, SC‑004 |
| | **T010** | Conduct outlier‑sensitivity analysis: re‑run the analysis with outliers retained vs. removed; store differences in `results/outlier_sensitivity.json`. | FR‑006 (linked via updated FR/SC for T011) |
| **Reporting** | **T011** | Render `paper/report.md` containing (a) design type (“Between‑Subjects” or “Repeated‑Measures”) as stored in `data/interim/design_branch.json`, (b) ANOVA (or fallback) tables with 95 % CI for effect sizes, (c) FDR‑corrected p‑values, (d) Limitations paragraph with exact word **“associational”**, (e) no occurrence of **“causal”** in Results, and (f) statement that neural responses are inferred from behavioral proxies (FR‑009). **FR‑003, FR‑006, FR‑009** |
| | **T012** | Consolidate `analysis_output.json`, `design_branch.json`, and phrasing‑check flags into `results/analysis_results.json` validated against `contracts/analysis_results.schema.yaml`. **FR‑009, SC‑003, SC‑004** |
| | **T013** | Log total wall‑clock time from the GitHub Actions run; fail if > 6 h (FR‑005, SC‑002). | FR‑005, SC‑002 |
| **Testing & Validation** | **T014** | Run `pytest` suite. Tests enforce: (i) schema compliance, (ii) FDR inequality, (iii) presence of required phrasing, (iv) runtime ≤ 6 h, (v) **confidence_interval** field present and valid in `analysis_results.json` (SC‑003). **FR‑005, SC‑002, SC‑003** |

All functional requirements (FR‑000 – FR‑009) and success criteria (SC‑001 – SC‑004) are explicitly addressed.

## Compute Feasibility
- **CPU**: Pure Python (pandas, scipy, statsmodels) → runs on GitHub Actions free tier.  
- **RAM**: ≤ 7 GB enforced by pre‑download size check and memory‑mapped parquet loading.  
- **Time**: ≤ 6 h total; expected < 30 min; CI step T013 enforces via runtime log.  
- **GPU**: Not needed | No GPU escape hatch required.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Required columns missing | Pipeline aborts (FR‑001) | Validation in T003/T004 with exit 1. |
| Dataset larger than RAM | OOM failure | Size check before download; abort if > 7 GB. |
| Small N causing ANOVA convergence warnings | Unstable results | Log warnings; fallback to non‑parametric test; note in Limitations. |
| No reward dataset | Cannot test modulation by reward | Produce explicit placeholder JSON (`reward_unavailable.json`) and note limitation (FR‑009, Constitution VI). |
| API endpoint unavailable | No data download | T003 aborts with informative message; CI reports failure. |
| Assumption violations | Invalid inference | Automatic switch to appropriate test; report in Results. |
| Outlier handling bias | Result sensitivity | Outlier‑sensitivity analysis (T010) reports impact. |

---



## projects/PROJ-258-the-effect-of-simulated-social-rejection/specs/001-the-effect-of-simulated-social-rejection/research.md

# Research: The Effect of Simulated Social Rejection on Behavioral Proxies (Reaction Time and Mood)

## Executive Summary
We will conduct a secondary analysis of the open‑access OpenNeuro Cyberball dataset **ds000208** (rejection vs. control). No verified reward‑feedback dataset exists, so the investigation is limited to a **design‑aware** analysis: when the same participants appear in both conditions we will run a **Repeated‑Measures ANOVA** (or linear mixed‑effects model) preserving within‑subject information; otherwise we fall back to a **Between‑Subjects One‑Way ANOVA** (or ANCOVA when covariates are present). The pipeline includes rigorous outlier handling, Z‑score normalization, Benjamini‑Hochberg FDR correction, α‑sensitivity (0.01, 0.05, 0.1), and outlier‑sensitivity analyses. The final report will explicitly state that the neural inference is **associational** and will avoid any causal language, satisfying Constitution VI.

### Construct Validity Justification
Reaction time and mood ratings have been demonstrated as reliable behavioral proxies for neural activity in social‑pain and reward circuits (e.g., Eisenberger et al.; Kragel et al., 2020). These peer‑reviewed studies report convergent validity between RT/mood measures and fMRI activation in the anterior cingulate cortex and ventral striatum during Cyberball exclusion and subsequent reward tasks. Accordingly, our claim that “neural responses are inferred from behavioral proxies” is grounded in this validated literature, satisfying Constitution VI.

## Dataset Strategy

| Role | Source | Verified URL | Variables Required |
|------|--------|--------------|---------------------|
| **Primary (Rejection & Control)** | OpenNeuro (mirrored on HuggingFace) | ` | `participant_id`, `condition` (values *rejection* and *control*), `reaction_time`, `mood_rating` |
| **Reward Feedback** | *None available* (no open‑access dataset with verified URL) | – | – |

*No open‑access reward‑feedback dataset meeting the specification exists; therefore the scope is limited to examining how rejection influences the behavioral proxies themselves.*

### Verification
- The ingestion script computes a SHA‑256 checksum for the parquet file and records it in `state/projects/PROJ-258-the-effect-of-simulated-social-rejection.yaml`.  
- Schema validation against `contracts/dataset.schema.yaml` and `contracts/ingest_schema.schema.yaml` confirms the presence of all required columns.  
- A pre‑download size estimate guarantees the file fits within the RAM limit mandated by FR‑001.  
- The ingestion schema also reports whether the dataset is a **single cohort** (each participant has both rejection and control rows). This flag drives the design‑selection logic described below.

## Statistical Methodology

### Design Selection Logic
- **Single‑cohort (within‑subject) data**: If the ingestion validation reports `single_cohort_validation.is_single_cohort == true`, the pipeline runs a **Repeated‑Measures ANOVA** (or linear mixed‑effects model) on each outcome (RT, mood). This preserves the paired nature of the data and maximizes statistical power.  
- **Between‑subjects data**: If the flag is false (or participants differ across conditions), the pipeline runs a **Between‑Subjects One‑Way ANOVA** (or ANCOVA when covariates are present). The chosen design type (“Repeated‑Measures” or “Between‑Subjects”) is stored in `data/interim/design_branch.json` and reported in the final markdown.

### Primary Model
- **Test**: One‑Way ANOVA (or ANCOVA) for Between‑Subjects; Repeated‑Measures ANOVA (or mixed‑effects) for Within‑Subjects, for each outcome (RT, mood) separately.  
- **Covariates**: Age and gender are included if present.  
- **Assumption Checks**: Shapiro‑Wilk normality and Levene’s homogeneity of variances. If violated, the pipeline (i) log‑transforms RT, (ii) uses Welch’s ANOVA, and (iii) falls back to Kruskal‑Wallis, documenting the decision.

### Multiple‑Comparison Control
- Benjamini‑Hochberg FDR correction applied to the two raw p‑values (RT and mood). The corrected column `p_fdr` is **≥** the raw `p_raw` (SC‑003 compliance; the spec’s opposite inequality is flagged for amendment).

### Sensitivity Analyses
- **α‑sweep**: thresholds {0.01, 0.05, 0.1} – for each α the pipeline records whether the FDR‑corrected p‑value meets significance (SC‑004).  
- **Outlier Sensitivity**: the analysis is repeated with outliers retained vs. removed; differences in effect sizes, confidence intervals, and p‑values are logged in `results/outlier_sensitivity.json`.

### Post‑hoc Effect Size Confidence Intervals
- For each effect size (eta‑squared) a 95 % confidence interval is computed (using non‑parametric bootstrap) and stored in the analysis output. This satisfies the schema requirement for `confidence_interval`.

## Compute Feasibility

| Resource | Requirement | Plan |
|----------|-------------|------|
| CPU | Pure Python (pandas, scipy, statsmodels) | CPU‑first on GitHub Actions free tier |
| RAM | ≤ 7 GB | Pre‑download size check; memory‑mapped parquet loading |
| Time | ≤ 6 h total | Expected < 30 min; CI enforces via T013 |
| GPU | Not needed | No GPU escape hatch required |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Required columns missing | Pipeline aborts (FR‑001) | Validation in T003/T004 with exit 1. |
| Dataset larger than RAM | OOM failure | Size check before download; abort if > 7 GB. |
| Small N causing ANOVA convergence warnings | Unstable results | Log warnings; fallback to non‑parametric test; note in Limitations. |
| No reward dataset | Cannot test modulation by reward | Produce explicit placeholder JSON (`reward_unavailable.json`) and note limitation (FR‑009, Constitution VI). |
| API endpoint unavailable | No data download | T003 aborts with informative message; CI reports failure. |
| Assumption violations | Invalid inference | Automatic switch to appropriate test; report in Results. |
| Outlier handling bias | Result sensitivity | Outlier‑sensitivity analysis (T010) reports impact. |

## Decision Rationale
- **Dataset Choice**: The verified OpenNeuro parquet file is the only open source meeting the variable requirements; no reward dataset exists, so we document the limitation rather than fabricate data.  
- **Statistical Approach**: Design‑aware analysis (Between‑Subjects or Repeated‑Measures) with FDR and sensitivity analyses satisfies FR‑004, FR‑006, and stays within CPU constraints.  
- **Design Flexibility**: Automatic design‑selection logic ensures compliance with FR‑007/FR‑008 regardless of participant ID overlap.  
- **Scope Discipline**: No unverified data or synthetic stand‑ins are introduced; all required phrasing and proxy transparency are enforced programmatically.

---



## projects/PROJ-258-the-effect-of-simulated-social-rejection/specs/001-the-effect-of-simulated-social-rejection/data-model.md

# Data Model: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

## Overview
The pipeline manipulates five logical data layers, each validated against a JSON/YAML schema in `contracts/`.

| Layer | Description | File Location | Schema |
|-------|-------------|---------------|--------|
| **Raw Dataset** | Unmodified download from OpenNeuro (Parquet) | `data/raw/ds000208.parquet` | `contracts/dataset.schema.yaml` |
| **Reward Availability Stub** | JSON indicating no reward dataset is available | `data/interim/reward_unavailable.json` | *inline schema validated by `validate.py`* |
| **Preprocessed Dataset** | Cleaned, outlier‑flagged, Z‑score normalized, aggregated per participant/condition | `data/processed/analysis_ready_ds000208.csv` | `contracts/dataset.schema.yaml` (extended) |
| **Outlier Log** | Per‑condition IQR thresholds and counts of flagged rows | `data/interim/outlier_log.json` | *description only* |
| **Design Branch** | Stores the chosen design type (`Between-Subjects`, `Repeated-Measures`) | `data/interim/design_branch.json` | *description only* |
| **Analysis Output** | Statistical results, FDR‑corrected p‑values, effect sizes, α‑sensitivity flags, **95 % confidence intervals** for effect size | `results/analysis_output.json` | `contracts/analysis_output.schema.yaml` |
| **Full Results Package** | Combines `analysis_output.json` with design metadata, phrasing checks, and outlier‑sensitivity summary | `results/analysis_results.json` | `contracts/analysis_results.schema.yaml` |
| **Metadata** | Checksum, download timestamp, citation for the raw dataset | `data/raw/metadata.json` | *description only* |
| **Citation File** | Human‑readable citation for the dataset | `data/raw/CITATION.md` | – |

## Entity Definitions

### 1. Raw Dataset Record
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | Anonymized participant identifier. |
| `task` | string | Task name (e.g., `"cyberball"` or `"reward"`). **Optional**; present when the dataset includes multiple tasks. |
| `condition` | string | `"rejection"` or `"control"` (both must be present). |
| `reaction_time` | number (≥ 0) | RT in milliseconds. |
| `mood_rating` | number (1 – 7) | Self‑reported mood. |
| `age` | number (optional) | Age in years. |
| `gender` | string (optional) | `"male"`, `"female"` or `"other"`. |

### 2. Reward Availability Stub
```json
{
  "reward_dataset_available": false,
  "reason": "No open-access reward dataset with verified URL."
}
```
Used by downstream steps to skip reward‑related processing.

### 3. Preprocessed Record
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | Same as raw. |
| `condition` | string | Same as raw. |
| `rt_normalized` | number | Z‑score of `reaction_time` within the condition. |
| `is_outlier` | boolean | `true` if flagged by IQR rule. |
| `rt_mean` | number | Mean of `rt_normalized` for the participant‑condition pair. |
| `mood_mean` | number | Mean of `mood_rating` for the participant‑condition pair. |
| `age` | number (optional) | Propagated from raw. |
| `gender` | string (optional) | Propagated from raw. |

### 4. Outlier Log (JSON)
```json
{
  "condition": "rejection",
  "iqr_lower": <number>,
  "iqr_upper": <number>,
  "flagged_count": <int>
}
```
One object per condition; stored in `data/interim/outlier_log.json`.

### 5. Design Branch (JSON)
```json
{
  "design_type": "Between-Subjects"  // or "Repeated-Measures"
}
```
Reflects the automatic selection (FR‑007).

### 6. Analysis Output – conforms to `contracts/analysis_output.schema.yaml`
| Field | Type | Description |
|-------|------|-------------|
| `test_type` | string | `"One_Way_ANOVA"` (or `"Repeated_Measures_ANOVA"` when applicable). |
| `design_type` | string | `"Between-Subjects"` or `"Repeated-Measures"`. |
| `f_value` | number | F‑statistic. |
| `p_raw` | number (0‑1) | Unadjusted p‑value. |
| `p_fdr` | number (0‑1) | Benjamini‑Hochberg corrected p‑value (≥ `p_raw`). |
| `effect_size` | number | Eta‑squared. |
| `confidence_interval` | array[2] | 95 % CI for `effect_size`. |
| `alpha_sensitivity` | object | Keys `"0.01"`, `"0.05"`, `"0.1"` → booleans indicating significance. |

### 7. Full Results Package – conforms to `contracts/analysis_results.schema.yaml`
| Field | Type | Description |
|-------|------|-------------|
| `design_type` | string | `"Between-Subjects"` or `"Repeated-Measures"` or `"Unavailable"`. |
| `main_test` | object | Mirrors `analysis_output.json` (F, p_raw, p_fdr, effect size, CI). |
| `sensitivity_analysis` | array | Results of α sweep (α = 0.01, 0.05, 0.1). |
| `outlier_sensitivity` | object | Differences in statistics with vs. without outliers (from T010). |
| `limitations` | object | Flags for required phrasing constraints. |

## Data Flow
1. **Ingestion** (`code/ingest.py`) → `data/raw/ds000208.parquet`, `metadata.json`, `CITATION.md`.  
2. **Reward stub** (`code/ingest.py`) → `data/interim/reward_unavailable.json`.  
3. **Validation** (`code/validate.py`) → `data/interim/ingest_validation_report.json`.  
4. **Preprocessing** (`code/preprocess.py`) → `data/processed/analysis_ready_ds000208.csv`, `outlier_log.json`.  
5. **Analysis** (`code/analyze.py`) → `results/analysis_output.json`.  
6. **Packaging** (`code/report.py`) → `results/analysis_results.json` & `paper/report.md`.  

All intermediate files are immutable; any transformation writes a new file with documented provenance.

## Constraints
- **Memory**: Files must fit within 7 GB RAM; raw parquet is streamed/memory‑mapped.  
- **PII**: `participant_id` is anonymized; no personal data stored.  
- **Immutability**: Raw files never overwritten; checksums guarantee integrity.

---



## projects/PROJ-258-the-effect-of-simulated-social-rejection/specs/001-the-effect-of-simulated-social-rejection/quickstart.md

# Quickstart: Simulated Social Rejection → Behavioral Proxies

## Prerequisites
- Python 3.11+  
- Git  
- Access to GitHub Actions (or a local runner with ≥ 7 GB RAM)

## Installation

```bash
# 1️⃣ Clone the repository
git clone 
cd PROJ-258-the-effect-of-simulated-social-rejection

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

### Step 1 – Ingest the Cyberball dataset
```bash
python code/ingest.py \
  --url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet" \
  --out-dir data/raw \
  --dataset-id ds000208
```
*Outputs*:
- `data/raw/ds000208.parquet`
- `data/raw/metadata.json` (SHA‑256 checksum, download timestamp)
- `data/raw/CITATION.md`
- `data/interim/reward_unavailable.json` (placeholder indicating no reward data)

*Failure*: Exit code 1 if required columns are missing, file > 7 GB, or `condition` lacks both “rejection” and “control”.

### Step 2 – Validate the download
```bash
python code/validate.py \
  --raw data/raw/ds000208.parquet \
  --schema contracts/dataset.schema.yaml \
  --output data/interim/ingest_validation_report.json
```
*Outputs*: JSON validation report. The script exits 1 on any schema violation.

### Step 3 – Preprocess
```bash
python code/preprocess.py \
  --input data/raw/ds000208.parquet \
  --output data/processed/analysis_ready_ds000208.csv
```
*Outputs*:
- `data/processed/analysis_ready_ds000208.csv` (cleaned, outlier‑flagged, Z‑score normalized)
- `data/interim/outlier_log.json` (per‑condition IQR thresholds & counts)

*Failure*: Exit code 1 if memory usage exceeds 7 GB.

### Step 4 – Statistical Analysis
```bash
python code/analyze.py \
  --data data/processed/analysis_ready_ds000208.csv \
  --output results/analysis_output.json
```
*Outputs*: `results/analysis_output.json` containing **design‑aware** ANOVA results (Between‑Subjects or Repeated‑Measures), FDR‑corrected p‑values, effect sizes, **95 % confidence intervals**, and α‑sensitivity flags.

### Step 5 – Outlier Sensitivity Check
```bash
python code/analyze.py \
  --data data/processed/analysis_ready_ds000208.csv \
  --outlier-sensitivity results/outlier_sensitivity.json
```
*Outputs*: Comparison of statistics with vs. removed outliers.

### Step 6 – Generate Report
```bash
python code/report.py \
  --analysis results/analysis_output.json \
  --outlier-sensitivity results/outlier_sensitivity.json \
  --design data/interim/design_branch.json \
  --output paper/report.md
```
*Outputs*: `paper/report.md` with:
- Design type (“Between‑Subjects” or “Repeated‑Measures”)  
- ANOVA tables (or non‑parametric equivalents) with 95 % CI for effect sizes  
- FDR‑corrected p‑values  
- Limitations paragraph containing **“associational”**  
- No occurrence of **“causal”** in the Results section  
- Statement that neural responses are inferred from behavioral proxies.

### Step 7 – Verify Everything (CI style)
```bash
pytest tests/
```
All tests must pass. They enforce:
- Schema compliance for raw, processed, and analysis files.  
- Correct FDR inequality (`p_fdr >= p_raw`).  
- Presence of required phrasing constraints in the final report.  
- Execution time ≤ 6 h (enforced by task T013).  

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **Missing columns** (`participant_id`, `condition`, `reaction_time`, `mood_rating`) | Dataset version mismatch | Verify the URL points to the verified parquet file; re‑run `ingest.py`. |
| **Memory overflow** | Dataset larger than RAM budget | `ingest.py` will halt; you cannot proceed until a smaller dataset is used. |
| **Design not selected** | Unexpected condition values | Ensure both “rejection” and “control” appear in the `condition` column; the script will auto‑select the appropriate design. |
| **Assumption violations** | Normality or homogeneity failures | Pipeline will automatically switch to Welch’s ANOVA or Kruskal‑Wallis and note this in the report. |
| **“causal” appears in report** | Manual edit of `paper/report.md` | Regenerate the report; the script enforces the phrasing rule. |
| **CITATION.md missing** | Ingestion step skipped | Re‑run `ingest.py`; it creates `CITATION.md`. |
| **Outlier impact unclear** | Need to assess sensitivity | Run Step 5 to produce the outlier‑sensitivity summary. |
| **Reward dataset needed** | No open‑access reward data exists | The pipeline creates `reward_unavailable.json` and proceeds with the Between‑Subjects analysis; limitation is documented in the final report. |

---



## projects/PROJ-258-the-effect-of-simulated-social-rejection/specs/001-the-effect-of-simulated-social-rejection/contracts/analysis_output.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Analysis Output Schema"
description: "Schema for the statistical analysis results produced by the pipeline."
type: "object"
properties:
  test_type:
    type: "string"
    description: "Type of statistical test performed."
    enum:
      - "One_Way_ANOVA"
      - "Repeated_Measures_ANOVA"
  design_type:
    type: "string"
    description: "Design type based on data structure."
    enum:
      - "Between-Subjects"
      - "Repeated-Measures"
  f_value:
    type: "number"
    description: "F-statistic value."
  p_raw:
    type: "number"
    description: "Raw p-value."
    minimum: 0
    maximum: 1
  p_fdr:
    type: "number"
    description: "Benjamini-Hochberg FDR corrected p-value (must be >= p_raw)."
    minimum: 0
    maximum: 1
  effect_size:
    type: "number"
    description: "Effect size (eta-squared)."
  confidence_interval:
    type: "array"
    description: "95% confidence interval for effect size."
    items:
      type: "number"
    minItems: 2
    maxItems: 2
  alpha_sensitivity:
    type: "object"
    description: "Sensitivity analysis results for different alpha levels."
    properties:
      "0.01":
        type: "boolean"
        description: "Significant at alpha = 0.01?"
      "0.05":
        type: "boolean"
        description: "Significant at alpha = 0.05?"
      "0.1":
        type: "boolean"
        description: "Significant at alpha = 0.1?"
    required:
      - "0.01"
      - "0.05"
      - "0.1"
required:
  - test_type
  - design_type
  - f_value
  - p_raw
  - p_fdr
  - effect_size
  - confidence_interval
  - alpha_sensitivity
additionalProperties: false



## projects/PROJ-258-the-effect-of-simulated-social-rejection/specs/001-the-effect-of-simulated-social-rejection/contracts/analysis_results.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Analysis Results Schema"
description: "Schema for the final statistical output. Ensures FDR correction, sensitivity analysis, and phrasing constraints."
type: "object"
properties:
  design_type:
    type: "string"
    description: "Statistical design used based on data structure."
    enum:
      - "Within-Subjects"
      - "Between-Subjects"
      - "Repeated-Measures"
      - "Unavailable"
  main_test:
    type: "object"
    description: "Primary ANOVA (or fallback) results."
    properties:
      f_statistic:
        type: "number"
      p_raw:
        type: "number"
        minimum: 0
        maximum: 1
      p_fdr:
        type: "number"
        minimum: 0
        maximum: 1
        description: "Benjamini-Hochberg corrected p-value."
      effect_size:
        type: "number"
      confidence_interval:
        type: "array"
        description: "95% CI for the effect size."
        items:
          type: "number"
        minItems: 2
        maxItems: 2
    required:
      - f_statistic
      - p_raw
      - p_fdr
      - effect_size
  sensitivity_analysis:
    type: "array"
    description: "Results for alpha sweep {0.01, 0.05, 0.1}"
    items:
      type: "object"
      properties:
        alpha:
          type: "number"
          enum:
            - 0.01
            - 0.05
            - 0.1
        power_at_alpha:
          type: "number"
          minimum: 0
          maximum: 1
      required:
        - alpha
        - power_at_alpha
  limitations:
    type: "object"
    description: "Must contain specific phrasing flags."
    properties:
      contains_associational:
        type: "boolean"
        const: true
        description: "True if the word 'associational' appears in the Limitations section."
      modulation_claim_valid:
        type: "boolean"
        description: "False when design is Within-Subjects but cannot test modulation."
    required:
      - contains_associational
      - modulation_claim_valid
required:
  - design_type
  - main_test
  - sensitivity_analysis
  - limitations
additionalProperties: false



## projects/PROJ-258-the-effect-of-simulated-social-rejection/specs/001-the-effect-of-simulated-social-rejection/contracts/dataset.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Dataset Schema"
description: "Schema for raw and preprocessed dataset records."
type: "object"
properties:
  participant_id:
    type: "string"
    description: "Unique anonymized participant identifier."
  task:
    type: "string"
    description: "Task name (e.g., 'cyberball' or 'reward')."
    enum:
      - "cyberball"
      - "reward"
  condition:
    type: "string"
    description: "Experimental condition."
    enum:
      - "rejection"
      - "control"
      - "reward"
  reaction_time:
    type: "number"
    description: "Reaction time in milliseconds."
    minimum: 0
  mood_rating:
    type: "number"
    description: "Self-reported mood rating."
    minimum: 1
    maximum: 7
  is_outlier:
    type: "boolean"
    description: "Flag indicating whether the record is flagged as outlier."
    default: false
  age:
    type: "number"
    description: "Age in years (optional)."
    minimum: 0
  gender:
    type: "string"
    description: "Gender (optional)."
    enum:
      - "male"
      - "female"
      - "other"
required:
  - participant_id
  - condition
  - reaction_time
  - mood_rating
additionalProperties: false



## projects/PROJ-258-the-effect-of-simulated-social-rejection/specs/001-the-effect-of-simulated-social-rejection/contracts/ingest_schema.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Ingested Dataset Schema"
description: "Schema for raw data ingestion validation. Ensure required columns exist for Cyberball analysis and validates single‑cohort structure."
type: "object"
properties:
  required_columns:
    type: "array"
    description: "List of mandatory column names. Must include participant_id, condition, reaction_time, mood_rating."
    items:
      type: "string"
    minItems: 4
    contains:
      const: "participant_id"
  data_types:
    type: "object"
    description: "Expected data types for each column."
    properties:
      participant_id:
        type: "string"
      condition:
        type: "string"
      reaction_time:
        type: "number"
      mood_rating:
        type: "number"
  constraints:
    type: "object"
    description: "Value constraints for numeric columns "
    properties:
      reaction_time:
        type: "object"
        properties:
          min:
            type: "number"
            description: "Minimum valid reaction time (ms)."
          max:
            type: "number"
            description: "Maximum valid reaction time (ms)."
      mood_rating:
        type: "object"
        description: "Valid range for mood rating."
        properties:
          min:
            type: "number"
            minimum: 1
          max:
            type: "number"
            maximum: 7
required:
  - required_columns
  - data_types
additionalProperties: false