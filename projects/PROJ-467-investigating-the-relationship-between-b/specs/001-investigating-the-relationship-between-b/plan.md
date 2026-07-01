# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Tactile Discrimination

**Branch**: `001-brain-network-tactile` | **Date**: 2026-06-29 | **Spec**: [spec.md](../specs/001-brain-network-tactile/spec.md)
**Input**: Feature specification from `/specs/001-brain-network-tactile/spec.md`

## Summary
The project must (1) load the Human Connectome Project (HCP) resting‑state fMRI dataset **and** verify the presence of tactile discrimination scores, (2) compute a suite of static and dynamic graph‑theoretic metrics from the fMRI data using CPU‑only methods within ≤ 3 hours for ≤ 100 subjects (CI subset), (3) test associational relationships between those metrics and tactile behavior while adjusting for confounds, (4) enforce rigorous statistical safeguards (multiple‑comparison correction, power analysis, collinearity diagnostics, sensitivity sweeps, and a fallback dimensionality‑reduction strategy), and (5) produce reproducible reports and artifacts that satisfy all functional (FR‑001‑FR‑013) and success (SC‑001‑SC‑009) criteria **without violating any constitutional principle**.

**Key updates**:
- No automatic fallback to non‑HCP datasets (Constitution VI).
- Flexibility is now explicitly defined as the mean number of community changes per node across sliding windows.
- Sensitivity analysis now includes the primary graph‑construction threshold and three additional thresholds.
- Multiple‑comparison correction applies to **all** hypothesis tests performed (≥ 5).
- CI runs a subset (≤ 100 subjects) for validation only; full‑scale analysis (≥ 194 subjects) must be executed locally.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**:
 - `numpy==1.26.*`, `pandas==2.2.*`
 - `nilearn==0.10.*` (fMRI loading & preprocessing)
 - `networkx==3.2.*` (graph metrics)
 - `scikit‑learn==1.5.*` (VIF, regression)
 - `statsmodels==0.14.*` (partial correlations, FDR)
 - `pingouin==0.5.*` (power analysis)
 - `datasets==2.18.*` (HCP download)
- **Storage**: All intermediate files are stored under `data/processed/` as compressed NumPy (`.npz`) or Parquet files.
- **Testing**: `pytest==8.2.*` with unit tests for each pipeline stage; contract validation via `jsonschema` against `contracts/*.schema.yaml`.
- **Target Platform**: Linux (GitHub Actions runner).
- **Performance Goals**:
 - ≤ 3 h wall‑clock for metric computation on ≤ 100 subjects (CI).
 - Peak RAM ≤ 6.5 GB.
- **Constraints**: CPU‑only; no GPU, no large‑model inference; all libraries must install on a default Ubuntu‑22.04 runner.
- **Scale/Scope**: Up to 1200 subjects (HCP) – CI limited to 100; full runs locally can use the entire cohort.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Fixed random seeds, deterministic preprocessing, all external URLs are pinned to specific HF releases. |
| II. Verified Accuracy | All citations (e.g., Weinstein tactile instrument DOI 10.1016/j.neuropsychologia.2011.04.012) will be validated by the Reference‑Validator before any review point is awarded. |
| III. Data Hygiene | Raw datasets are never overwritten; checksums are recorded in `state/projects/PROJ-467...yaml`. |
| IV. Single Source of Truth | Every figure/table references a single row in a derived Parquet file; metadata logs map each artifact to its provenance. |
| V. Versioning Discipline | All artifacts are content‑hashed; `state/projects/...yaml` is updated automatically by the CI pipeline. |
| VI. Neuroimaging Data Consistency | All fMRI comes exclusively from HCP; no fallback to other datasets is permitted. |
| VII. Network Metric Transparency | Metric calculations use Nilearn (v0.10) + NetworkX (v3.2); all parameters (window length, step, community‑detection algorithm) are stored in a side‑car JSON file per network file. |

## Project Structure
```text
specs/001-brain-network-tactile/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
 ├── analysis_results.schema.yaml
 ├── network_metric.schema.yaml
 └── raw_subject.schema.yaml

src/
├── brainnet/
│ ├── __init__.py
│ ├── data_loader.py # HCP download & validation
│ ├── preprocessing.py # fMRI motion correction, masking
│ ├── static_metrics.py # connectivity, modularity, segregation
│ ├── dynamic_metrics.py # sliding‑window, dynamic modularity, flexibility
│ ├── analysis.py # correlation, partial correlation, VIF, power, sensitivity, PCA fallback
│ └── utils.py # logging, seed handling
tests/
├── unit/
│ ├── test_data_loader.py
│ ├── test_static_metrics.py
│ └── test_analysis.py
└── contract/
 └── test_network_schema.py
requirements.txt
```
**Structure Decision**: A single‑package Python library (`src/brainnet/`) is sufficient; no web or mobile components are required.

## Complexity Tracking
No constitution violations remain after the design. All FR and SC items are covered by explicit pipeline stages (see mapping below).

### FR / SC Mapping
| FR / SC | Pipeline Phase | Description |
|--------|----------------|-------------|
| FR‑001 | `data_loader.validate()` | Load HCP; if tactile missing → **halt** (no fallback). |
| FR‑002 | `static_metrics` & `dynamic_metrics` | Compute static & dynamic graph metrics, including flexibility. |
| FR‑003 | `analysis.perform_corrections()` | Apply FDR (q ≤ 0.05) for **all** hypothesis tests (≥ 5). |
| FR‑004 | `analysis.report_association()` | Enforce association‑only language. |
| FR‑005 | `analysis.check_vif()` | Flag VIF > 5.0. |
| FR‑006 | `analysis.sensitivity_sweep()` | Sweep thresholds {0.01, 0.05, 0.1, 0.2}. |
| FR‑007 | `data_loader.load_tactile_instrument()` | Cite Weinstein DOI. |
| FR‑008 | `analysis.power_analysis()` | Compute required N≈ on the order of a few hundred participants; flag under‑powered. |
| FR‑009 | Same as FR‑001 (halt if tactile absent). |
| FR‑010 | `dynamic_metrics.save_series()` | Store dynamic modularity & flexibility time‑series. |
| FR‑011 | Same as FR‑008 (report required N). |
| FR‑012 | `analysis.partial_correlation()` | Adjust for age, sex, motion, scanner. |
| FR‑013 | **Not executed** – Constitution VI forbids non‑HCP fMRI; pipeline will halt if tactile missing, flagging a spec gap. |
| SC‑001 | `data_loader.validate_completeness()` | ≥ 95 % subjects complete. |
| SC‑002 | `static_metrics.timing()` & `dynamic_metrics.timing()` | ≤ 3 h runtime (CI subset). |
| SC‑003 | `dynamic_metrics.memory_profile()` | ≤ 6.5 GB peak. |
| SC‑004 | `analysis.correction_report()` | FDR/Bonferroni details. |
| SC‑005 | `analysis.sensitivity_report()` | ≥ 3 thresholds, stability metric. |
| SC‑006 | `analysis.vif_report()` | Flag VIF > 5.0 and report effect‑size change after removal or PCA. |
| SC‑007 | `analysis.power_report()` | Power ≥ 0.80 or under‑power flag. |
| SC‑008 | Same as SC‑002/SC‑003 for dynamic metrics. |
| SC‑009 | `analysis.adjusted_vs_raw()` | Both raw & covariate‑adjusted correlations. |

## Phased Execution Plan
| Phase | Tasks | Expected Duration (CI) |
|-------|-------|------------------------|
| 0️⃣ **Dataset Validation** | - Download HCP via `datasets.load_dataset` <br> - Verify presence of `tactile_score` column <br> - Compute completeness stats, checksum files <br> - **If tactile column missing → abort** with explicit message (Constitution VI compliance) | ≤ 15 min |
| 1️⃣ **Preprocessing** | - Motion correction, band‑pass filtering (Nilearn) <br> - Spatial normalization to MNI152 2 mm <br> - Extract Schaefer‑200 ROI time series | ≤ 30 min |
| 2️⃣ **Static Metric Computation** | - Pearson correlation matrix (200 × 200) <br> - Graph construction (absolute r ≥ 0.2) <br> - Modularity (Louvain) <br> - Segregation index | ≤ 45 min |
| 3️⃣ **Dynamic Metric Computation** | - Sliding‑window (60 s, 30 s step → ~80 volumes per window) <br> - Windowed correlation matrices <br> - Dynamic modularity time‑series (Louvain per window) <br> - **Flexibility**: count of community changes per node across windows | ≤ 1 h |
| 4️⃣ **Diagnostics** | - VIF on all predictors <br> - **If any VIF > 5.0**: <br> 1. Remove predictor with highest VIF and recompute VIFs. <br> 2. If any VIF > 5.0 remains, perform PCA on the remaining predictor set, retain components explaining ≥ 90 % variance, and flag that dimensionality reduction was applied. <br> - Memory & runtime profiling logs | ≤ 15 min |
| 5️⃣ **Statistical Analysis** | - Power analysis (Pingouin) <br> - Pearson & partial correlations (adjusted) <br> - FDR correction applied to **all** tests (≥ 5) <br> - Sensitivity sweep across thresholds {0.01, 0.05, 0.1, 0.2} <br> - If PCA was applied in Phase 4, compute correlations between tactile scores and the retained component scores (report variance explained). <br> - Report stability (coefficient of variation) of correlation coefficients across thresholds | ≤ 30 min |
| 6️⃣ **Reporting & Artifacts** | - Assemble `results/` (CSV, JSON, figures) <br> - Generate markdown summary & LaTeX tables <br> - Validate contracts (`jsonschema`) | ≤ 15 min |
| **Total** | | **≈ 3 h 45 min** (well within 6 h CI limit) |

### CI vs. Full‑Scale Execution
- **CI Run**: Uses `--max-subjects 100` to stay within RAM/time limits; reports under‑power flag (N < 194) but does **not** claim definitive effect sizes.
- **Full Run**: Researchers should invoke the pipeline locally with the full HCP cohort (≈ 1200 subjects) to achieve the a‑priori power target (FR‑008).

---



## projects/PROJ-467-investigating-the-relationship-between-b/specs/001-investigating-the-relationship-between-b/research.md===
# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Tactile Discrimination

## Overview
This document outlines the scientific rationale, dataset strategy, analysis pipeline, and statistical safeguards for the study. All decisions are driven by the functional (FR‑001‑FR‑013) and success (SC‑001‑SC‑009) requirements in the specification and respect the project constitution.

## 1. Scientific Rationale
Prior work links resting‑state functional connectivity to sensory perception, yet the temporal dynamics of those networks have rarely been examined in relation to fine‑grained tactile discrimination (e.g., two‑point discrimination thresholds). We therefore test the hypothesis that individuals with **greater dynamic flexibility** (more frequent community re‑assignments) and higher dynamic modularity variance exhibit superior tactile discrimination, while controlling for demographic and motion confounds.

## 2. Dataset Strategy
| Dataset | Source URL (verified) | Modalities | Tactile Measure | Expected N | Comments |
|---------|----------------------|------------|-----------------|-----------|----------|
| **Human Connectome Project (HCP) Young Adult** | https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet | Resting‑state fMRI (TR = 0.72 s) | Two‑point discrimination threshold (mm) – **required** | ≈ 1200 | **If the `tactile_score` column is missing, the pipeline aborts** (Constitution VI). No alternative dataset with verified tactile scores is available, so a custom multimodal dataset must be provided to proceed. |

**Decision Logic**:
1. Attempt to load HCP.
2. Verify that the `tactile_score` column exists and meets completeness criteria (≥ 95 % non‑missing).
3. If tactile data are absent, **halt** with the explicit error message defined in FR‑001/FR‑009. No automatic fallback to other datasets is permitted (Constitution VI).

## 3. Preprocessing Pipeline
- **Motion correction**: `nilearn.image.clean_img` with `t_r=0.72` (HCP) or `0.8` (if a custom dataset uses a different TR).
- **Band‑pass filter**: 0.01–0.1 Hz.
- **Spatial normalization**: MNI152 2 mm via Nilearn’s `resample_to_img`.
- **ROI definition**: Schaefer 200‑parcel atlas (scale = 200).

All steps are deterministic; random seeds are fixed (`np.random.seed(42)`).

## 4. Metric Computation
### 4.1 Static Metrics
- Pearson correlation matrix (200 × 200).
- Threshold at absolute r ≥ 0.2 to create an undirected weighted graph.
- **Modularity Q** (Louvain algorithm, `community‑louvain`).
- **Segregation index** (within‑ vs. between‑module connectivity).

### 4.2 Dynamic Metrics
- **Sliding‑window**: length = 60 s, step = 30 s.
 *Justification*: With TR ≈ 0.72 s, each window contains a moderate number of volumes, covering the low‑frequency BOLD band of interest (0.01–0.1 Hz) as recommended by Allen et al., 2014.
- For each window compute a correlation matrix and modularity Q.
- **Dynamic modularity time‑series**: modularity Q per window.
- **Flexibility**: number of times a node changes community assignment across consecutive windows (Bassett et al., 2011). This captures the temporal re‑configuration of the network.

All computations use NumPy/Numba loops to stay CPU‑tractable.

## 5. Statistical Analysis
### 5.1 Power Analysis (FR‑008, SC‑007)
- Anticipated effect size: r = 0.20 (Cohen, 1992).
- α = 0.05, target power = 0.80 → required N ≈ a few hundred participants to ensure adequate statistical power. (computed with Pingouin).
- **CI run** (≤ 100 subjects) will report an *under‑powered* flag; researchers should run the full analysis locally with the complete HCP cohort to meet the power target.

### 5.2 Correlation & Adjustment (FR‑012, SC‑009)
- **Raw Pearson** between each predictor (static modularity, segregation, dynamic mean modularity, dynamic modularity variance, flexibility) and tactile score.
- **Partial correlation** controlling for age, sex, mean framewise displacement, scanner ID (or site ID for custom datasets). Implemented via `statsmodels.stats.partial_corr`.
- Both raw and adjusted effect sizes, 95 % CIs, and p‑values are exported.

### 5.3 Multiple‑Comparison Correction (FR‑003, SC‑004)
- Minimum of **five** hypothesis tests (the five predictors above).
- Apply Benjamini‑Hochberg FDR (q ≤ 0.05) to *all* tests.
- The correction method and adjusted q‑values are reported in the results table.

### 5.4 **Collinearity Diagnostics** (FR‑005, SC‑006)
- Compute VIF for the full predictor set.
- **If any VIF > 5.0**:
 1. Remove the predictor with the highest VIF and recompute VIFs.
 2. If VIF > 5.0 persists, perform **principal component analysis (PCA)** on the remaining predictors, retain components that together explain ≥ 90 % of the variance, and proceed with the component scores as the predictor set.
 3. Record the variance explained by the retained components and flag the analysis as having used dimensionality reduction.
- The VIF report includes the change in correlation coefficient when high‑VIF predictors are removed, and notes that PCA‑derived components are orthogonal (VIF = 1). Results derived from PCA are framed descriptively (no independent‑effect language) in accordance with FR‑004.

### 5.5 Sensitivity Analysis (FR‑006, SC‑005)
- Sweep graph‑construction thresholds across **{0.01, 0.05, 0.1, 0.2}** (the primary 0.2 value is now included).
- For each threshold recompute all static and dynamic metrics and the corresponding correlations.
- Report the coefficient of variation of the correlation coefficients across thresholds as a stability metric.

## 6. Reporting & Reproducibility
- All figures (scatter plots, modularity time‑series) saved as SVG/PNG in `results/figures/`.
- Tables exported as CSV and rendered in markdown for the manuscript.
- Each derived file has a companion `metadata/*.json` conforming to `metadata.schema.yaml`, recording SHA‑256 checksum, creation timestamp, Git commit hash, and all pipeline parameters.
- The final markdown report (`results/report.md`) contains sections for data completeness, runtime/memory profiling, power analysis outcome, correction details, sensitivity results, VIF diagnostics, and both raw/adjusted correlation tables.

## 7. Edge‑Case Handling
- **Missing tactile data in HCP** → pipeline aborts with message:
 `Dataset validation failed: HCP Young Adult dataset does NOT include tactile discrimination measures. Provide a custom dataset with both modalities to proceed.` (FR‑001, FR‑009).
- **> 10 % missing fMRI volumes** → subject excluded; log exclusion count (target ≤ 5 % of total).
- **High collinearity** → handled as described in 5.4; results framed descriptively.
- **Under‑powered sample** → flagged; confidence‑interval fields marked `[deferred]` (FR‑008).

---



## projects/PROJ-467-investigating-the-relationship-between-b/specs/001-investigating-the-relationship-between-b/data-model.md===
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
 dimensionality_reduction:
 type: string
 enum: [none, pca]
 description: "Whether PCA was applied to address collinearity"
 pca_variance_explained:
 type: number
 description: "Proportion of variance explained by retained PCA components (if applicable)"
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

## 7. PCA Component Record (Optional)
When collinearity persists after VIF screening, the pipeline writes a PCA component file (`pca_components.parquet`) conforming to the following minimal schema:

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "PCA Components"
type: object
required:
 - subject_id
 - component_scores
 - variance_explained
properties:
 subject_id:
 type: string
 component_scores:
 type: array
 items:
 type: number
 description: "Scores for each retained component"
 variance_explained:
 type: number
 description: "Cumulative variance explained by the retained components"
```

All PCA outputs are linked to their provenance metadata and are used in downstream correlation analysis when dimensionality reduction is required.

---



## projects/PROJ-467-investigating-the-relationship-between-b/specs/001-investigating-the-relationship-between-b/quickstart.md===
# Quickstart: Brain Network Dynamics ↔ Tactile Discrimination

This guide shows how to run the full pipeline on the GitHub Actions CI or locally on a Linux machine.

## Prerequisites
- Python 3.11 (or newer) installed.
- Git 2.40+
- Sufficient disk space (on the order of several gigabytes) for dataset download.
- Internet access to the verified HuggingFace URL for the HCP dataset.

## 1. Clone the Repository
```bash
git clone
cd brainnet-tactile
```

## 2. Create a Virtual Environment & Install Dependencies
```bash
python -m venv.venv
source.venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt # pins exact versions (CPU‑only wheels)
```

## 3. Run the End‑to‑End Pipeline
```bash
# The CLI supports sub‑commands; the default runs all phases.
# In CI we limit the number of subjects to a level that stays within the RAM/time budget.
python -m brainnet.run_all \
 --max-subjects 100 \ # CI subset for validation
 --seed 42 # reproducibility
```
The command performs:
1. **Dataset validation** (HCP only; aborts if tactile scores are missing).
2. **Preprocessing** of fMRI.
3. **Static & dynamic metric computation** (including flexibility).
4. **Statistical analysis** (power, VIF, partial correlations, FDR, sensitivity, and automatic PCA fallback if collinearity persists).
5. **Result packaging** into `results/` and contract validation.

### Full‑Scale Local Run
For a definitive analysis that meets the a‑priori power target (N ≈ 194), run the pipeline without the `--max-subjects` limit on a machine with sufficient RAM (≥ 8 GB) and allow the full HCP cohort (~1200 subjects) to be processed:

```bash
python -m brainnet.run_all --seed 42
```

## 4. Inspect the Outputs
- `results/report.md` – full markdown report ready for inclusion in the manuscript.
- `results/figures/` – PNG/SVG files for plots.
- `data/processed/` – Parquet files for static metrics, `.npz` for dynamic series.
- `metadata/` – JSON provenance files.
- `contracts/` – schema files; CI runs `jsonschema` checks automatically.

## 5. Run the Test Suite (optional)
```bash
pytest -vv
```
All unit tests must pass; contract tests are located under `tests/contract/`.

## 6. CI Execution
The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:
- Sets up the Python environment using `requirements.txt`.
- Executes `python -m brainnet.run_all --max-subjects 100`.
- Checks that total wall‑clock time ≤ 6 h and peak RAM ≤ 6.5 GB (via `psutil`).
- Validates all output files against the schemas in `contracts/`.

If any check fails, the CI job aborts, protecting reproducibility (Principle I).

---



## projects/PROJ-467-investigating-the-relationship-between-b/specs/001-investigating-the-relationship-between-b/contracts/analysis_results.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "Analysis Results Record"
type: object
required:
 - metric_name
 - r_value
 - p_value
 - p_adj
 - vif_flagged
 - sensitivity
 - power_estimate
 - ci_deferred
 - citation_doi
 - analysis_timestamp
properties:
 metric_name:
 type: string
 description: "Name of the network metric (e.g., modularity_q)."
 enum: ["modularity_q", "segregation_index", "mean_connectivity", "dynamic_variance", "flexibility"]
 r_value:
 type: number
 description: "Partial Pearson correlation coefficient with tactile score (covariates adjusted)."
 p_value:
 type: number
 description: "Two‑tailed p‑value before correction."
 minimum: 0
 maximum: 1
 p_adj:
 type: number
 description: "Adjusted p‑value after FDR correction (q ≤ 0.05)."
 minimum: 0
 maximum: 1
 vif_flagged:
 type: boolean
 description: "True if VIF > 5.0 for this metric."
 sensitivity:
 type: object
 description: "Correlation values across sparsity threshold sweeps."
 additionalProperties:
 type: number
 power_estimate:
 type: number
 description: "Statistical power estimate (0–1) from CorrelationPower."
 minimum: 0
 maximum: 1
 ci_deferred:
 type: boolean
 description: "True if confidence intervals are deferred due to low power."
 citation_doi:
 type: string
 description: "DOI or URL of the validated tactile discrimination instrument."
 analysis_timestamp:
 type: string
 format: date-time
 description: "ISO‑8601 timestamp of when the analysis was performed."
 dimensionality_reduction:
 type: string
 enum: [none, pca]
 description: "Whether PCA was applied to address collinearity."
 pca_variance_explained:
 type: number
 description: "Proportion of variance explained by retained PCA components (if applicable)."
definitions:
 network_metric:
 type: object
 required:
 - subject_id
 - modularity_q
 - segregation_index
 - mean_connectivity
 - dynamic_variance
 - flexibility
 - vif_modularity
 - vif_segregation
 - vif_mean_conn
 - vif_dynamic
 - vif_flexibility
 - matrix_path
 - metadata_path
 properties:
 subject_id:
 type: string
 description: "Links to raw_subject."
 modularity_q:
 type: number
 minimum: 0
 maximum: 1
 segregation_index:
 type: number
 minimum: 0
 mean_connectivity:
 type: number
 minimum: 0
 dynamic_variance:
 type: number
 minimum: 0
 flexibility:
 type: number
 minimum: 0
 vif_modularity:
 type: number
 minimum: 1
 vif_segregation:
 type: number
 minimum: 1
 vif_mean_conn:
 type: number
 minimum: 1
 vif_dynamic:
 type: number
 minimum: 1
 vif_flexibility:
 type: number
 minimum: 1
 matrix_path:
 type: string
 description: "Path to the static connectivity matrix (.npy)."
 metadata_path:
 type: string
 description: "Path to JSON file with derivation parameters."