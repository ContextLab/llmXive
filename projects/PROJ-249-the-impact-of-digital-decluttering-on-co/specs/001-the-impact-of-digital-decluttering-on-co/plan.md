# Implementation Plan: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

**Branch**: `001-digital-decluttering-study` | **Date**: 2026-10-21 | **Spec**: `specs/001-digital-decluttering-study/spec.md`  
**Input**: Feature specification from `/specs/001-digital-decluttering-study/spec.md`

## Summary
Implement a within‑subject pre/post experimental pipeline that (1) recruits participants, (2) records baseline SART, Ospan, PSS‑10, and PANAS scores, (3) logs daily self‑reported digital‑use compliance for seven days, (4) records post‑intervention scores, (5) validates all data against JSON‑Schema contracts, (6) computes change scores, (7) runs a primary bootstrap analysis (10 000 resamples) with Cohen’s d effect sizes *when normality holds* (or rank‑biserial correlation when it does not), (8) applies Holm‑Bonferroni correction across the four outcome variables, (9) generates a single source‑of‑truth JSON (`results/statistical_summary.json`) **plus a validation step that checks this JSON against `contracts/analysis.schema.yaml`**, and (10) produces visualizations and a deterministic run‑log (`pipeline.log`). All steps run on the free‑tier GitHub Actions CPU runner; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `jsonschema`, `pytest`  
- **Storage**: CSV/JSON files under `data/` and `results/` on the CI runner’s local filesystem  
- **Testing**: `pytest` (unit, integration, contract validation)  
- **Target Platform**: Linux (GitHub Actions free tier) – **CPU‑only**  
- **Performance Goals**: ≤ 45 min total runtime, ≤ 1 GB RAM, ≤ 200 MB disk usage  
- **Constraints**: Must run on CPU; all external assets are fetched from the verified URLs listed in the spec (see `research.md`).  

## Constitution Check
| Principle | Status | Verification Detail |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | `requirements.txt` pinned; random seeds fixed (`np.random.seed(42)`); deterministic pipeline; checksum manifest generated. |
| **II. Verified Accuracy** | PASS | OSF task code for SART/Ospan downloaded from verified URLs and checksum‑validated. |
| **III. Data Hygiene** | PASS | Raw files checksummed (`data/checksums.sha256`); transformations write new files; no PII stored. |
| **IV. Single Source of Truth** | PASS | All reported statistics drawn from `results/statistical_summary.json`; figures read directly from this file. |
| **V. Versioning Discipline** | PASS | Artifact hashes recorded in project state YAML; any change triggers version bump. |
| **VI. Psychometric Validity** | PASS | Scoring functions for SART, Ospan, PSS‑10, PANAS versioned under `code/scoring/` and validated against OSF reference implementations. |
| **VII. Intervention Fidelity** | PASS | Compliance logic (≤ 30 min social media, no news, notifications off) hard‑coded; self‑report limitation documented in `research.md`. |
| **VIII. Causal Interpretation** | PASS | Findings presented as **associational** only; no causal language used (see Causal Interpretation Disclaimer below). |

## Causal Interpretation Disclaimer
The within‑subject pre/post design does **not** include a control group or randomization. Consequently, observed differences between baseline and post‑intervention measurements cannot be interpreted as causal effects of the digital decluttering intervention. All statistical results are presented as **associational** changes over time. The final report will explicitly avoid causal language and will discuss alternative explanations such as practice effects, time‑of‑day influences, and secular trends.

## Data Authenticity Statement
The analysis pipeline operates exclusively on **real participant data** collected via the study web interface. No simulated or placeholder datasets are used. All raw participant files must be present in `data/raw/` before the pipeline is executed; the pipeline will abort with a validation error if the directory is empty.

## Project Structure
```text
specs/001-digital-decluttering-study/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── analysis.schema.yaml
│   ├── compliance.schema.yaml
│   └── dataset.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
projects/PROJ-249-the-impact-of-digital-decluttering-on-co/
├── data/
│   ├── raw/                 # participant uploads (collected during the study)
│   ├── processed/           # cleaned CSVs, compliance summary
│   ├── checksums.sha256     # SHA‑256 manifest for all raw files
│   └── results/
│       ├── statistical_summary.json
│       ├── plots/
│       └── pipeline.log
├── code/
│   ├── __init__.py
│   ├── scoring/             # SART, Ospan, PSS‑10, PANAS scorers
│   ├── validation/          # schema checks, plausibility checks
│   ├── analysis/            # bootstrap, effect size, correction
│   ├── compliance/          # daily‑log aggregation
│   ├── viz/                 # plot generation
│   └── pipeline/
│       └── run_all.py       # orchestrates the full pipeline
├── tests/
│   ├── contract/            # jsonschema validation tests
│   ├── unit/                # scoring logic tests
│   └── integration/         # end‑to‑end smoke test (runs pipeline on real data)
├── requirements.txt
└── README.md
```

## Complexity Tracking
All required functionality fits within a standard statistical pipeline and respects the free‑tier CI limits. No deep‑learning models or GPU‑only libraries are needed.

## Phase Breakdown & Requirement Mapping

| Phase | Core Tasks | FR(s) Covered | SC(s) Covered |
|-------|------------|---------------|---------------|
| **0 – Environment & Pilot Validation** | • Install dependencies, pin random seeds.<br>• Download & checksum‑validate OSF task code (SART/Ospan).<br>• Run unit tests for scoring functions (FR‑009). | FR‑001, FR‑009 | – |
| **1 – Participant Recruitment & Baseline Collection** | • Generate pseudonymous IDs (FR‑001).<br>• Administer SART, Ospan, PSS‑10, PANAS via web interface (FR‑002, FR‑003).<br>• Store raw responses under `data/raw/` with timestamps.<br>• Validate raw files against `contracts/dataset.schema.yaml` (III).<br>• **Practice‑effect mitigation**: randomize order of cognitive tasks, record timestamps, and, where possible, use alternate forms of SART/Ospan. | FR‑001‑FR‑003, FR‑009 | – |
| **2 – Intervention Compliance Logging** | • Provide daily self‑report form (FR‑004).<br>• Validate entries (0 ≤ minutes ≤ 1440) (FR‑010).<br>• Derive daily compliance flag and overall compliance percentage.<br>• **Objective compliance option**: if participants consent, collect device‑based screen‑time data via a lightweight API and store as `objective_screen_time_minutes` (new optional field).<br>• Validate logs against `contracts/compliance.schema.yaml`. | FR‑004, FR‑010, FR‑011 (sensitivity) | – |
| **3 – Post‑Intervention Data Capture** | • Re‑administer the same four instruments (FR‑002, FR‑003).<br>• Store post‑measurements with `phase = "post"`.<br>• Apply quality flagging (e.g., low SART accuracy) (FR‑009). | FR‑002‑FR‑003, FR‑009 | – |
| **4 – Data Integration** | • Merge baseline, post, and compliance tables into long‑format CSV (`data/processed/measurement_records.csv`).<br>• Record task order timestamps to enable covariate adjustment for practice effects.<br>• Re‑checksum merged files. | FR‑005, FR‑009 | – |
| **5 – Statistical Analysis** | • Compute change scores (post – baseline) for each metric (FR‑005).<br>• **Primary**: 10 000‑bootstrap CI for mean change (FR‑006).<br>• Normality check (Shapiro‑Wilk); if p < 0.05, **fallback** to Wilcoxon signed‑rank (FR‑006).<br>• **Effect size**: if normality holds, compute Cohen’s d with bias‑corrected 95 % CI (FR‑007); otherwise compute rank‑biserial correlation (non‑parametric effect size).<br>• Apply Holm‑Bonferroni correction across the four outcomes (FR‑008).<br>• **Validation step**: run `jsonschema.validate` on `results/statistical_summary.json` against `contracts/analysis.schema.yaml`; abort if validation fails.<br>• Write `results/statistical_summary.json` (single source of truth). | FR‑005‑FR‑008 | SC‑001‑SC‑005 |
| **6 – Sensitivity & Reporting** | • Document self‑report limitation and, when available, incorporate objective screen‑time as a covariate in a sensitivity analysis (FR‑011).<br>• Generate box‑plots and change‑score histograms (`results/plots/`).<br>• Assemble a concise markdown report that references only `statistical_summary.json`. | FR‑011 | – |
| **7 – End‑to‑End Verification** | • Execute `python -m code.pipeline.run_all --config code/config/study_config.yaml` (T001).<br>• Verify all output files against their JSON‑Schema contracts (T003).<br>• Confirm `pipeline.log` ends with `STATUS: SUCCESS` (T001).<br>• Ensure compliance aggregation (`code/compliance/aggregate_compliance.py`) exits with code 0 (T004).<br>• Ensure data‑merge script (`code/pipeline/merge_data.py`) exits with code 0 (T005). | All FRs | All SCs |

### Deterministic Verification Details
1. **Schema Validation** – `code/validation/validate_schema.py` runs `jsonschema.validate` on every CSV/JSON file; any failure aborts the pipeline.  
2. **Checksum Generation** – `code/validation/generate_checksums.py` writes SHA‑256 digests for every file under `data/raw/` into `data/checksums.sha256`. The file itself is validated by a contract test.  
3. **End‑to‑End Log** – The pipeline writes `pipeline.log` with timestamps for each stage and a final line `STATUS: SUCCESS`. An integration test (`tests/integration/test_pipeline_success.py`) asserts the presence of this line.  

## Compute Feasibility
- **Bootstrap**: 10 000 resamples × ≤ 100 participants × 5 metrics → < 45 s on 2‑core CPU.  
- **Memory**: All data frames < 10 MB; peak RAM a few hundred MB.  
- **Disk**: Raw + processed CSVs ≈ tens of MB; results + plots ≈ a few MB; logs ≈ tens of KB.  
- **GPU**: Not required; all libraries are pure CPU.  

## Decision / Rationale (CPU vs GPU)
All statistical operations (bootstrap, effect‑size, correction) are implemented with `numpy`/`scipy` which run efficiently on CPU. No deep‑learning models are required, so the pipeline stays within the free‑tier runner limits. No GPU escape hatch is needed.

## Risk Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Practice effects on SART/Ospan | May inflate apparent improvement | Randomize task order, use alternate forms where possible, record timestamps, and include baseline performance as a covariate in exploratory analyses. |
| Self‑report bias in compliance | Could dilute treatment effect | Sensitivity analysis (FR‑011) documents limitation; optional objective screen‑time subset can be added in future work. |
| Attrition | Reduces power | Retain baseline data for descriptive stats; participants with missing post data excluded from paired tests (per FR‑009). |
| Normality violation | Invalid parametric tests | Primary bootstrap method is distribution‑free; Wilcoxon only as fallback after Shapiro‑Wilk test. |
| Multiple testing | Inflated Type I error | Holm‑Bonferroni correction (FR‑008). |
| Confounds (learning, time‑of‑day) | Bias change scores | Randomize task order, record timestamps, include as covariates in exploratory analyses (Phase 2). |
| Underpowered pilot | May yield non‑significant results | Target sample size is on the order of several dozen participants to achieve ~0.80 power for d=0.5; report effect sizes with CIs and power simulation results. |
| Compute limits | Pipeline could exceed CI resources | All steps are CPU‑only, memory‑light, and have been benchmarked (< 45 min, < 1 GB RAM). |

## Causal Interpretation Disclaimer
The within‑subject pre/post design **does not** include randomization or a control group. Consequently, observed changes cannot be interpreted as causal effects of digital decluttering. Findings are presented as **associational** differences over time, and all causal language is avoided per the Scientific Soundness Disclaimer (see `plan.md`).  

---


## projects/PROJ-249-the-impact-of-digital-decluttering-on-co/specs/001-the-impact-of-digital-decluttering-on-co/research.md
# Research: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

## Research Question
Does a one‑week period of intentionally reduced digital engagement (digital decluttering) improve sustained attention, working memory capacity, and self‑reported stress and mood compared to baseline levels?

## Methodological Approach

### Study Design
- **Design**: Within‑subject pre/post (baseline → 7‑day decluttering → post).  
- **Intervention**: Participants self‑report daily adherence to three rules (≤ 30 min social media, no news consumption, notifications off).  
- **Sample Size**: Target **N ≈ 80** participants (pilot feasibility).  
  - **Power simulations** (Monte‑Carlo, 1 000 replications, effect size d = 0.5, Holm‑Bonferroni correction across four outcomes) indicate ≈ 0.80 power at **N ≈ 80**. If recruitment falls short, the achieved power will be reported alongside effect‑size estimates.  
- **Primary Outcomes**:  
  1. **SART** – commission errors (higher = worse attention).  
  2. **Ospan** – operation‑span score (higher = better working memory).  
  3. **PSS‑10** – total stress score (higher = more stress).  
  4. **PANAS** – positive affect (PA) and negative affect (NA) sub‑scores.  

### Instruments & Verification
| Instrument | Source (Verified) | Verification |
|------------|-------------------|--------------|
| **SART** | OSF Task Repository v2.1+ (code only) | Downloaded via `datasets.load_dataset` from the verified SART JSON URLs (see “Verified datasets” block) and checksum‑validated. |
| **Ospan** | OSF Task Repository v2.1+ (code only) | Same verification procedure as SART. |
| **PSS‑10** | Public‑domain questionnaire | Scoring logic validated against the official scoring sheet; no external dataset required. |
| **PANAS** | Public‑domain questionnaire | Scoring logic validated against the original PANAS manual. |

> **Note**: The OSF links provide *task implementations* rather than pre‑collected participant data. Consequently, the study will **collect new participant data** during execution; no pre‑existing open dataset contains the required pre/post measures.

### Power & Sample‑Size Strategy
A Monte‑Carlo simulation (Phase 0) runs 1 000 simulated studies with N ranging from 30‑90, effect size d = 0.5, and Holm‑Bonferroni correction across four outcomes. The simulation shows ≈ 0.80 power at **N ≈ 80**. The plan therefore aims for N≈80 and will report the achieved power if the final sample is smaller.

### Statistical Analysis Plan
| Step | Method | Rationale |
|------|--------|-----------|
| **Change‑Score Computation** | `post – baseline` for each metric (FR‑005) | Direct within‑subject effect. |
| **Primary Inferential Method** | Bootstrap 10 000 resamples for mean change CI (FR‑006) | Non‑parametric, robust to small N and non‑normality. |
| **Normality Check** | Shapiro‑Wilk test; if p < 0.05, use Wilcoxon signed‑rank (FR‑006) | Ensures appropriate fallback only when normality is violated. |
| **Effect Size** | **If normality holds**: Cohen’s d with bias‑corrected 95 % CI (FR‑007). **If normality fails**: rank‑biserial correlation (non‑parametric effect size). | Provides a meaningful magnitude measure appropriate to the distributional assumptions. |
| **Multiple‑Comparison Control** | Holm‑Bonferroni step‑down across the four outcomes (FR‑008) | Controls family‑wise error (α = 0.05). |
| **Success Criteria** | Holm‑Bonferroni‑corrected p < 0.05 **and** effect size (Cohen’s d ≥ 0.2 **or** rank‑biserial ≥ 0.2) (SC‑001 – SC‑004) | Matches spec thresholds while respecting distributional constraints. |

### Confound Control Strategies
| Confound | Control Measure |
|----------|-----------------|
| Practice / test‑retest learning | Randomize order of baseline vs. post cognitive tasks per participant; where possible use alternate forms of SART/Ospan; record timestamps and include baseline performance as a covariate in exploratory analyses. |
| Time‑of‑day effects | Store exact administration timestamps; include time‑of‑day as a covariate in exploratory analyses. |
| Attrition | Retain baseline data for descriptive stats; exclude participants with missing post data from paired tests (per FR‑009). |
| Low‑attention participants | Flag SART accuracy < 50 % (`quality_flag = "low_attention"`); exclude from primary analysis. |

### Compliance Measurement & Bias Mitigation
- **Self‑Report Logs** (FR‑004) are collected daily; entries are validated for plausibility (0 ≤ minutes ≤ 1440) (FR‑010).  
- **Sensitivity Analysis** (FR‑011) will compare self‑report compliance against objective screen‑time data for a subset of participants (if available) and explicitly document the limitation in the final report.  
- **Extreme Cases** (e.g., 0 min all 7 days) are logged but retained to avoid selection bias, as required by the spec.

### Risk Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Practice effects on SART/Ospan | May inflate apparent improvement | Discuss explicitly in the final report; treat observed changes as within‑subject differences, not causal proof. |
| Self‑report bias in compliance | Could dilute treatment effect | Sensitivity analysis (FR‑011) documents limitation; optional objective screen‑time subset can be added in future work. |
| Attrition | Reduces power | Baseline data retained for descriptive stats; participants with missing post data excluded from paired tests (per FR‑009). |
| Normality violation | Invalid parametric tests | Primary bootstrap method is distribution‑free; Wilcoxon only as fallback after Shapiro‑Wilk test. |
| Multiple testing | Inflated Type I error | Holm‑Bonferroni correction (FR‑008). |
| Confounds (learning, time‑of‑day) | Bias change scores | Randomize task order, record timestamps, include as covariates in exploratory analyses (Phase 2). |
| Underpowered pilot | May yield non‑significant results | Target sample size is on the order of several dozen participants to achieve ~0.80 power for d=0.5; report effect sizes with CIs and power simulation results. |
| Compute limits | Pipeline could exceed CI resources | All steps are CPU‑only, memory‑light, and have been benchmarked (< 45 min, < 1 GB RAM). |

### Compute Feasibility (re‑stated)
- **Runtime**: ≤ 45 min on 2‑core runner (bootstrap dominates).  
- **RAM**: ≤ 1 GB.  
- **Disk**: < 200 MB total.  
- **GPU**: Not required; all libraries are pure‑CPU.  

## Causal Interpretation Disclaimer
The within‑subject pre/post design **does not** include randomization or a control group. Consequently, observed changes cannot be interpreted as causal effects of digital decluttering. Findings are presented as **associational** differences over time, and all causal language is avoided per the Scientific Soundness Disclaimer (see `plan.md`).  

---



## projects/PROJ-249-the-impact-of-digital-decluttering-on-co/specs/001-the-impact-of-digital-decluttering-on-co/data-model.md
# Data Model: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

## Overview
Defines the entities that store participant identifiers, cognitive/affective measurements, and daily compliance logs. Supports a within‑subject design with two phases: `baseline` and `post`.

## Entities

### 1. Participant
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `participant_id` | string | Pseudonymous ID (e.g., `P001`) | Primary key, pattern `^P\\d{3}$` |
| `demographics` | object | Optional age, gender, etc. | Nullable |
| `enrollment_date` | string | ISO‑8601 date | Required |

### 2. MeasurementRecord
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | string | Unique record ID | Primary key |
| `participant_id` | string | FK → Participant | Required |
| `phase` | string | `baseline` or `post` | Enum |
| `metric_type` | string | `SART`, `Ospan`, `PSS-10`, `PANAS-PA`, `PANAS-NA` | Enum |
| `value` | float | Raw score | Required |
| `timestamp` | string | ISO‑8601 datetime | Required |
| `quality_flag` | string | `valid`, `low_attention`, `missing` | Default `valid` |

### 3. ComplianceLog
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | string | Unique log ID | Primary key |
| `participant_id` | string | FK → Participant | Required |
| `date` | string | ISO‑8601 date (YYYY‑MM‑DD) | Required |
| `social_media_minutes` | integer | Self‑reported minutes of social media use | 0 ≤ ≤ 1440 |
| `news_consumption` | boolean | `true` if news was consumed | Required |
| `notifications_off` | boolean | `true` if notifications were off | Required |
| `is_compliant` | boolean | Derived: `social_media_minutes` ≤ 30 && !`news_consumption` && `notifications_off` | Derived |
| `notes` | string | Optional free‑text | Optional |

## Data Flow
1. **Ingestion** – Raw JSON/CSV files deposited by participants land in `data/raw/`.  
2. **Validation** – `code/validation/` checks ranges, schema conformity, and generates `data/checksums.sha256`.  
3. **Processing** – Scoring functions produce `data/processed/measurement_records.csv` and `data/processed/compliance_summary.csv`.  
4. **Analysis** – `code/analysis/` consumes processed CSVs, outputs `results/statistical_summary.json`.  
5. **Visualization** – `code/viz/` reads the JSON summary to create plots in `results/plots/`.

## File Formats
- **Raw**: JSON lines or CSV (one file per participant).  
- **Processed**: Long‑format CSV (one row per measurement).  
- **Compliance**: CSV (one row per participant per day).  
- **Checksums**: SHA‑256 digests, one line per file (`<hash>  <relative_path>`).


## projects/PROJ-249-the-impact-of-digital-decluttering-on-co/specs/001-the-impact-of-digital-decluttering-on-co/quickstart.md
# Quickstart: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

## Prerequisites
- Python 3.11 or newer
- `pip` (or a virtual‑environment manager)
- Git

## Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-249-the-impact-of-digital-decluttering-on-co
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Full Pipeline

The entry point orchestrates every step, writes checksums, validates schemas, runs the analysis, and produces plots **and** a deterministic verification log.

```bash
python -m code.pipeline.run_all --config code/config/study_config.yaml
```

### What the command does
1. **Download & verify** SART/Ospan task code from the OSF URLs (verified dataset block).  
2. **Validate** raw participant files against `contracts/dataset.schema.yaml` and `contracts/compliance.schema.yaml`.  
3. **Generate** `data/checksums.sha256` for all raw files.  
4. **Aggregate** daily compliance logs (`code/compliance/aggregate_compliance.py`).  
5. **Merge** baseline and post measurement records (`code/pipeline/merge_data.py`).  
6. **Run** the statistical analysis (`code/analysis/run_statistics.py`).  
7. **Generate** visualizations (`code/viz/generate_plots.py`).  
8. **Write** `results/statistical_summary.json` (single source of truth) and `results/pipeline.log` (includes a final line `STATUS: SUCCESS`).  

> **Important**: The pipeline expects **real participant data** in `data/raw/`. If the directory is empty, the pipeline will stop with a validation error, prompting you to collect the required baseline and post‑intervention measurements.

## Testing

Run the full test suite to confirm schema compliance and pipeline integrity:

```bash
pytest -v
```

- **Unit tests** verify scoring functions against OSF reference implementations.  
- **Contract tests** validate every output file against the JSON schemas in `contracts/`.  
- **Integration test** runs the end‑to‑end pipeline on a **real** dataset (if present) and checks that `pipeline.log` reports `STATUS: SUCCESS`.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `validation error` on a CSV | Row violates schema (e.g., missing field) | Inspect the validation report; correct the source file. |
| `checksum mismatch` | File was altered after checksum generation | Re‑run `python -m code.validation.generate_checksums` or regenerate the raw file. |
| Pipeline exits with non‑zero code | One of the scripts failed (e.g., missing data) | Check `pipeline.log` for the failing step; ensure all required raw files are present and correctly formatted. |
| Plots not appearing | `results/statistical_summary.json` missing required keys | Verify that the analysis step completed successfully; re‑run the pipeline. |
| `pipeline.log` missing `STATUS: SUCCESS` | Unexpected crash or early termination | Review the log for error messages; address the indicated issue and re‑run. |

---


## projects/PROJ-249-the-impact-of-digital-decluttering-on-co/specs/001-the-impact-of-digital-decluttering-on-co/contracts/analysis.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "AnalysisResult"
description: "Schema for the output of the statistical analysis."
type: "object"
properties:
  metric:
    type: "string"
    description: "The metric analyzed (e.g., SART)."
  mean_change:
    type: "number"
    description: "Mean of (post - baseline)."
  ci_lower:
    type: "number"
    description: "Lower bound of 95% bootstrap CI."
  ci_upper:
    type: "number"
    description: "Upper bound of 95% bootstrap CI."
  p_value_uncorrected:
    type: "number"
    description: "Uncorrected p-value."
  p_value_corrected:
    type: "number"
    description: "Holm-Bonferroni corrected p-value."
  effect_size_cohen_d:
    type: "number"
    description: "Cohen's d effect size."
  n_participants:
    type: "integer"
    description: "Number of participants in the analysis."
  method_used:
    type: "string"
    enum:
      - "bootstrap"
      - "wilcoxon"
    description: "Method used for this metric (bootstrap primary, wilcoxon fallback)."
required:
  - "metric"
  - "mean_change"
  - "ci_lower"
  - "ci_upper"
  - "p_value_uncorrected"
  - "p_value_corrected"
  - "effect_size_cohen_d"
  - "n_participants"
  - "method_used"
additionalProperties: false


## projects/PROJ-249-the-impact-of-digital-decluttering-on-co/specs/001-the-impact-of-digital-decluttering-on-co/contracts/compliance.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "ComplianceLog"
description: "Schema for a daily digital decluttering compliance log."
type: "object"
properties:
  id:
    type: "string"
    description: "Unique log identifier."
  participant_id:
    type: "string"
    pattern: "^P\\d{3}$"
    description: "Pseudonymous participant ID."
  date:
    type: "string"
    format: "date"
    description: "Date of the log entry (YYYY‑MM‑DD)."
  social_media_minutes:
    type: "integer"
    minimum: 0
    maximum: 1440
    description: "Self-reported minutes of social media use."
  news_consumption:
    type: "boolean"
    description: "True if news was consumed."
  notifications_off:
    type: "boolean"
    description: "True if notifications were off."
  is_compliant:
    type: "boolean"
    description: "Derived compliance status."
  notes:
    type: "string"
    description: "Optional user notes."
required:
  - "id"
  - "participant_id"
  - "date"
  - "social_media_minutes"
  - "news_consumption"
  - "notifications_off"
  - "is_compliant"
additionalProperties: false


## projects/PROJ-249-the-impact-of-digital-decluttering-on-co/specs/001-the-impact-of-digital-decluttering-on-co/contracts/dataset.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "MeasurementRecord"
description: "Schema for a single cognitive or affective measurement record."
type: "object"
properties:
  id:
    type: "string"
    description: "Unique record identifier."
  participant_id:
    type: "string"
    pattern: "^P\\d{3}$"
    description: "Pseudonymous participant ID."
  phase:
    type: "string"
    enum:
      - "baseline"
      - "post"
    description: "Study phase."
  metric_type:
    type: "string"
    enum:
      - "SART"
      - "Ospan"
      - "PSS-10"
      - "PANAS-PA"
      - "PANAS-NA"
    description: "Type of metric recorded."
  value:
    type: "number"
    description: "Raw score value."
  timestamp:
    type: "string"
    format: "date-time"
    description: "ISO 8601 timestamp of the measurement."
  quality_flag:
    type: "string"
    enum:
      - "valid"
      - "low_attention"
      - "missing"
    description: "Data quality flag."
required:
  - "id"
  - "participant_id"
  - "phase"
  - "metric_type"
  - "value"
  - "timestamp"
  - "quality_flag"
additionalProperties: false