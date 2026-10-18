# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

**Branch**: `001-brain-music-emotion` | **Date**: 2026-10-18 | **Spec**: `specs/001-investigating-the-relationship-between-b/spec.md`

## Summary

The spec requires paired resting‑state fMRI connectivity data and Music Emotion Rating (MER) behavioral scores from the HCP Subjects Release. No currently verified open source provides these variables. Consequently the plan now includes an explicit **Spec Revision Required** section that flags the data‑gap and calls for a specification amendment to either supply an open dataset meeting FR‑001/FR‑002/FR‑003 or to relax those requirements. All downstream analysis machinery (graph‑metric extraction, dimensionality reduction, statistical modeling) remains fully implemented and unit‑tested so that when a compliant dataset becomes available the pipeline can be run end‑to‑end without redesign.

## Technical Context

- **Language/Version**: Python 3.10
- **Primary Dependencies**: `datasets==2.19.0`, `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `networkx==3.3`, `statsmodels==0.14.2`, `matplotlib==3.9.0`, `pydantic==2.7.1`, `pytest==8.2.0`, `bctpy==0.5.0`
- **Storage**: `data/` (downloaded raw files + checksums), `results/` (CSV/JSON outputs), `reports/` (data‑gap report, run summary)
- **Testing**: pytest suite covering schema contracts, matrix properties, VIF/FDR logic, and the validation gate.
- **Target Platform**: Linux, GitHub Actions free tier (2 CPU cores, ~7 GB RAM, ≤6 h)
- **Constraints**: No fabricated data; any missing required variable triggers a Data‑Gap Report. All graph‑theory and statistical steps run on CPU; no GPU escape hatch needed.

## Constitution Check

| Principle | Check | Outcome |
|---|---|---|
| I. Reproducibility | Pinned deps, seeds (`RANDOM_SEED=42`), canonical URLs | ✅ |
| II. Verified Accuracy | Only URLs from the Verified Datasets block are cited; mismatches are reported | ✅ |
| III. Data Hygiene | SHA‑256 checksums recorded; raw files immutable; no PII | ✅ |
| IV. Single Source of Truth | All figures/tables generated from `results/` files | ✅ |
| V. Versioning Discipline | Content hashes tracked; `state/projects/...yaml` updated on change | ✅ |
| VI. Neuro‑Imaging Preprocessing Standardization | **Not covered** – raw fMRI unavailable; requires spec amendment (open dataset) | ⚠️ |
| VII. Behavioral‑Neural Data Alignment | Merge, partial correlation, and FDR implemented; execution gated by data validation | ⚠️ (conditional) |

## Spec Revision Required

* **FR‑001** (download paired resting‑state fMRI + MER) and **FR‑002** (CPU‑only fMRIPrep preprocessing) cannot be fulfilled because no open, programmatically downloadable dataset contains the required raw NIfTI files and MER scores. The specification must be updated to either:
  1. Provide a verified open dataset that includes both modalities, **or**
  2. Relax the requirement to use pre‑computed connectivity matrices paired with MER scores (in which case FR‑002 would be removed or re‑scoped).

* **FR‑003** (time‑series extraction & Pearson FC) also depends on raw fMRI availability and is consequently pending the same dataset revision.

Until the spec is revised, the pipeline will stop after the validation gate and emit a Data‑Gap Report.

## Project Structure

```text
specs/001-investigating-the-relationship-between-b/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    └── data_gap_report.schema.yaml
```

```text
code/
├── src/
│   ├── config.py
│   ├── data/
│   │   ├── download.py
│   │   └── validate.py
│   ├── analysis/
│   │   ├── graph_metrics.py
│   │   ├── stats.py
│   │   └── visualize.py
│   └── main.py
├── assets/
│   └── schaefer200_labels.csv
└── tests/
    ├── contract/
    ├── integration/
    └── unit/
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected |
|---|---|---|
| Dimensionality of edge‑level features | When the number of edges greatly exceeds N, the regression becomes ill‑posed. | Dropping VIF on all edges is unstable; we now reduce via PCA (Task 2.2). |
| Power requirement | SC‑005 demands N ≥ 194 for [deferred] power at r = 0.20 | No automatic power guarantee; we now enforce a minimum‑N check (Task 2.1). |
| Data‑gap handling | No verified dataset satisfies FR‑001/FR‑002/FR‑003 | Fabrication is prohibited; we explicitly report the gap. |

## Implementation Phases

### Phase 0 – Data Acquisition, Validation, and Scope Alignment

| Task | Description |
|---|---|
| **Task 0.0 – Spec Review & Data‑Gap Recording** | Records that FR‑001 (download of paired fMRI + MER) cannot be satisfied with the current verified URLs. Writes a concise note in `reports/data_gap_report.json` and flags the need for a compliant open dataset. |
| **Task 0.1 – Download Verified Sources** | `download.py` fetches each URL from the Verified Datasets block via `datasets.load_dataset` or direct HTTP, computes SHA‑256 checksums into `data/checksums.json`, logs per‑file success/failure, and continues on error (edge case). |
| **Task 0.2 – Validation Gate** | `validate.py` inspects column names of each downloaded file, checks for the required variables (`subject_id`, `age`, `sex`, `fd_mean`, `fc_upper_tri`, `mer_score`). If any are missing, writes `reports/data_gap_report.json` (conforms to `contracts/data_gap_report.schema.yaml`) and exits with status 1, halting further phases. |
| **Task 0.3 – fMRIPrep Preprocessing Placeholder** | **Spec‑required processing cannot be performed without raw fMRI.** This task documents the limitation and will be replaced by a real fMRIPrep run once an appropriate dataset is provided. |
| **Task 0.4 – Independent Test (US‑1) & N‑Distribution (US‑2)** | If a validated dataset is present, runs the pipeline on a random subject subset, verifies matrix symmetry/range, and writes a brief summary (`reports/independent_test_summary.json`) including N and MER distribution. |

### Phase 1 – Feature Extraction (Gated on Valid Data)

| Task | Description |
|---|---|
| **Task 1.0 – Time‑Series Extraction & Pearson FC** | **Pending raw fMRI availability** – placeholder for future implementation. |
| **Task 1.1 – Matrix Reconstruction** | For datasets that already provide `fc_upper_tri`, reconstructs the full symmetric matrix, checks diagonal = 1.0, values ∈ [−1, 1]. |
| **Task 1.2 – Edge‑Weight Transformation** | Converts correlation matrices to absolute values, thresholds to retain the top 10 % strongest positive edges, then stores the resulting binary‑weighted matrix. |
| **Task 1.3 – Graph‑Metric Computation** | Computes global efficiency, Louvain modularity, participation coefficient, and within‑network efficiency for DMN, Salience, and Visual networks. Calculates edge‑strength vector (flattened upper‑triangular of the thresholded matrix). |
| **Task 1.4 – VIF Screening** | Calculates variance‑inflation factors for scalar network metrics; drops any predictor with VIF > 5, logs to `results/vif_report.json`. Edge‑strength vectors are not VIF‑screened (they will be reduced via PCA). |

### Phase 2 – Statistical Modeling (Gated)

| Task | Description |
|---|---|
| **Task 2.1 – Partial Correlation & Power Check** | Performs partial correlation between each retained network metric and `mer_score`, controlling for age, sex, and `fd_mean`. Computes achieved power for detecting r = 0.20 at α = 0.05 using `statsmodels.stats.power`. If the sample size N < 194, writes an under‑powered flag in `results/run_summary.json` and notes that results are exploratory. |
| **Task 2.2 – Dimensionality Reduction & Ridge Regression** | Applies Principal Component Analysis (PCA) to the edge‑strength vectors, retaining enough components to explain ≥ 80 % variance (typically ≤ 10 components). Combines these components with the scalar network metrics (post‑VIF) as predictors. Fits a Ridge regression model with 5‑fold cross‑validation (seed = 42). Outputs cross‑validated R², compares to an intercept‑only baseline, and records the model in `results/analysis_results.csv`. No “top edge features” are reported; only performance metrics are provided. |
| **Task 2.3 – Multiple‑Comparison Correction** | Applies Benjamini–Hochberg FDR (q < 0.05) to all partial‑correlation p‑values; adjusted p‑values stored alongside raw p‑values. |
| **Task 2.4 – Reporting & Summary** | `visualize.py` generates (a) a scatter plot of predicted vs. actual MER scores with regression line and R² annotation, (b) a bar chart of FDR‑significant metrics. `main.py` writes `results/run_summary.json` summarizing N, RAM/CPU usage (SC‑004), power status, and whether the validation gate passed. |

### Phase 3 – Verification

| Task | Description |
|---|---|
| **Task 3.1 – Schema Contract Tests** | Validates `results/network_metrics.csv`, `results/analysis_results.csv`, and `reports/data_gap_report.json` against their respective JSON‑Schema contracts. |
| **Task 3.2 – Unit Tests** | Tests matrix symmetry, edge‑weight transformation, VIF calculation, PCA variance capture, and FDR adjustment on synthetic but contract‑conformant fixtures. |
| **Task 3.3 – Integration Test** | Asserts that with the current verified sources the pipeline stops after Task 0.2 and produces a correctly‑structured Data‑Gap Report. |

## FR/SC Coverage Map

| ID | Covered by |
|---|---|
| FR-001 | **Not covered – requires spec amendment (open dataset)** |
| FR-002 | **Not covered – requires spec amendment (raw fMRI)** |
| FR-003 | **Not covered – requires spec amendment (raw fMRI)** |
| FR-004 | **Task 1.3** – graph‑metric computation. |
| FR-005 | **Task 2.1** (partial correlation) & **Task 2.2** (Ridge regression). |
| FR-006 | **Task 2.3** – FDR correction. |
| FR-007 | **Task 0.2** – validation gate producing Data‑Gap Report. |
| SC-001 | **Task 2.1** – partial‑correlation r vs. null r = 0. |
| SC-002 | **Task 2.2** – cross‑validated R² vs. intercept‑only baseline. |
| SC-003 | **Task 2.3** – FDR‑adjusted q < 0.05. |
| SC-004 | **Task 2.4** – RAM/CPU usage logged vs. CI limits. |
| SC-005 | **Task 2.1** – power calculation; under‑powered flag if N < 194. |
| US‑1 | **Task 0.4** – independent 5‑subject test (when data present). |
| US‑2 | **Task 0.4** – N and MER distribution reporting. |

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Verified URLs lack required variables | Validation gate (Task 0.2) detects mismatch and halts; Data‑Gap Report informs spec revision. |
| Attempt to fabricate data | Explicit prohibition; all fixtures are isolated under `tests/fixtures/`. |
| p ≫ n regression instability | PCA reduction before Ridge (Task 2.2) limits predictor dimensionality. |
| Negative edge weights invalid for efficiency | Absolute‑value + top‑10 % threshold (Task 1.2) ensures all weights are non‑negative. |
| Under‑powered sample | Minimum‑N check (Task 2.1) and clear flagging; results interpreted as exploratory. |
| Scope drift | All new tasks are explicitly tied to FR/SC IDs; any further deviation requires spec amendment. |

--- 

## References

*(All citations are drawn from the Verified Datasets block; no unverified sources are introduced.)*



## projects/PROJ-232-investigating-the-relationship-between-b/specs/001-investigating-the-relationship-between-b/research.md===
# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Research Question
*Original*: Do resting‑state functional‑connectivity network metrics (global efficiency, modularity, participation coefficient, network‑specific efficiencies, edge strengths) associate with individual differences in Music Emotion Rating (MER) scores, controlling for age, sex, and framewise displacement?

*Current status*: **Not testable with verified open data.** The Data‑Gap Report (Task 0.2) confirms that none of the verified sources contain the required paired fMRI‑connectivity and MER variables. Consequently the primary analysis halts until a compliant dataset is supplied or the spec is revised.

## Data Availability (the decisive finding)

The Verified Datasets block lists three “HCP” URLs and two “MER” URLs. Inspection of their actual content shows a fatal variable mismatch:

| Dataset | URL | Content | Required variables present? |
|---|---|---|---|
| “MER” Turkish QA corpora | `https://huggingface.co/datasets/MercanAI/turkce-sft-qa-3.7m/resolve/main/data/test-00000.parquet`<br>`https://huggingface.co/datasets/merve/turkish_instructions/resolve/main/instructions.csv` | Text instructions/QA, no MER scores, no subjects, no imaging. | **No** |
| “HCP” parquet files | `https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet`<br>`https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv`<br>`https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet` | No confirmed `subject_id`, `age`, `sex`, `fd_mean`, `fc_upper_tri`, or MER columns. | **No** |
| HCP Subjects Release (Music Task subset) | *No open URL* (access‑gated) | Would contain required variables but cannot be fetched unattended. | **UNVERIFIED / gated** |

**Conclusion**: No verified, programmatically downloadable source provides the paired neuro‑behavioral data required by the study. The pipeline therefore includes a strict validation gate that writes `reports/data_gap_report.json` and terminates without fabricating data.

## Dataset Strategy

| Dataset | URL | Required variables present? | Status |
|---|---|---|---|
| “MER” Turkish QA corpora | `https://huggingface.co/datasets/MercanAI/turkce-sft-qa-3.7m/resolve/main/data/test-00000.parquet`<br>`https://huggingface.co/datasets/merve/turkish_instructions/resolve/main/instructions.csv` | No – unrelated text data | Verified URL, **wrong content** |
| “HCP” parquet files | `https://huggingface.co/datasets/7eu7d7/HCP-Diffusion-datas/resolve/main/Lexica.art.parquet`<br>`https://huggingface.co/datasets/ramandeepsaha/hcp/resolve/main/train.csv`<br>`https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet` | No – missing required columns | Verified URLs, **unverified contents** |
| HCP Subjects Release (Music Task subset) | *No open URL* (access‑gated) | Would contain all required variables | **UNVERIFIED / gated** |

The pipeline **does not** substitute any of these with synthetic data. Instead, it records the gap and awaits a compliant dataset.

## Spec Revision Required

FR‑001 (download paired fMRI + MER) and FR‑002 (CPU‑only fMRIPrep preprocessing) cannot be satisfied with any currently verified open dataset. The specification must be updated to either:

1. Provide an open dataset that includes raw resting‑state NIfTI files **and** MER scores, **or**
2. Relax the requirement to use pre‑computed functional connectivity matrices paired with MER scores (removing or re‑scoping FR‑002 and FR‑003 accordingly).

Until such a revision is made, the pipeline will stop after the validation gate and produce a Data‑Gap Report.

## Statistical Rigor & Methodology (implemented, gated on valid data)

| Aspect | Method |
|---|---|
| Multiple comparisons | Benjamini–Hochberg FDR, q < 0.05, across all metric‑wise tests |
| Power | Per‑metric achieved power for detecting r = 0.20 at α = 0.05 (using `statsmodels`). If N < 194, the run summary flags the analysis as under‑powered (SC‑005). |
| Causal framing | Observational; all statements are associational. |
| Measurement validity | No validated open MER instrument is available; this limitation is noted explicitly. |
| Collinearity | VIF screening (VIF > 5) for scalar network metrics; edge‑level predictors are reduced via PCA before regression (Task 2.2). |
| Confounds | Age, sex, and mean FD are included as covariates in partial correlation and regression. |
| Edge‑weight handling | Correlation matrices are transformed to absolute values and thresholded to retain the top 10 % strongest positive edges before graph‑theory metrics (Task 1.2). |

## Compute Feasibility

- **CPU‑first**: All steps (matrix reconstruction, graph metrics, PCA, Ridge CV) run comfortably on 2 CPU cores within < 30 min and < 2 GB RAM. No GPU is required.
- The validation gate runs in seconds and is the expected terminal step under the current data availability.

## Decision Rationale

1. **Honesty over fabrication** – The verified sources lack the needed variables; fabricating or substituting unrelated data would violate the fabrication gate.  
2. **Reusable analysis pipeline** – All analysis code is implemented and thoroughly tested, ready to process a genuine dataset when it becomes available.  
3. **Explicit scope gap** – By generating a Data‑Gap Report we provide a clear, reproducible record of why the primary analysis cannot proceed, supporting downstream spec revision.

## Limitations

- Primary analysis cannot execute until a verified open dataset containing resting‑state fMRI and MER scores is provided.  
- fMRIPrep preprocessing (Constitution VI) cannot be performed without raw fMRI; a placeholder task documents this limitation.  
- All statistical results are conditional on the validation gate passing; currently none are produced.  

--- 

## Future Directions (pending data)

When a compliant dataset is supplied (e.g., via authorized HCP access placed under `data/subjects.parquet` matching `contracts/dataset.schema.yaml`), the same command `python src/main.py` will run the full pipeline: extraction → graph metrics → PCA → partial correlations + Ridge CV with FDR → figures and `results/analysis_results.csv`.

## FR/SC Coverage Map

| ID | Covered by |
|---|---|
| FR-001 | **Not covered – requires spec amendment (open dataset)** |
| FR-002 | **Not covered – requires spec amendment (raw fMRI)** |
| FR-003 | **Not covered – requires spec amendment (raw fMRI)** |
| FR-004 | **Task 1.3** – graph‑metric computation. |
| FR-005 | **Task 2.1** (partial correlation) & **Task 2.2** (Ridge regression). |
| FR-006 | **Task 2.3** – FDR correction. |
| FR-007 | **Task 0.2** – validation gate producing Data‑Gap Report. |
| SC-001 | **Task 2.1** – partial‑correlation r vs. null r = 0. |
| SC-002 | **Task 2.2** – cross‑validated R² vs. intercept‑only baseline. |
| SC-003 | **Task 2.3** – FDR‑adjusted q < 0.05. |
| SC-004 | **Task 2.4** – RAM/CPU usage logged vs. CI limits. |
| SC-005 | **Task 2.1** – power calculation; under‑powered flag if N < 194. |
| US‑1 | **Task 0.4** – independent 5‑subject test (when data present). |
| US‑2 | **Task 0.4** – N and MER distribution reporting. |

--- 

## Quick Reference Table of Tasks

| Phase | Task | Core FR/SC |
|---|---|---|
| 0 | 0.0 Spec Review & Data‑Gap Recording | FR‑007 |
| 0 | 0.1 Download Verified Sources | – |
| 0 | 0.2 Validation Gate | FR‑001, FR‑002, FR‑003 |
| 0 | 0.3 fMRIPrep Placeholder | FR‑002 (pending) |
| 0 | 0.4 Independent Test & N‑Distribution | US‑1, US‑2 |
| 1 | 1.0 Time‑Series Extraction & Pearson FC | FR‑003 (pending) |
| 1 | 1.1 Matrix Reconstruction | – |
| 1 | 1.2 Edge‑Weight Transformation | – |
| 1 | 1.3 Graph‑Metric Computation | FR‑004 |
| 1 | 1.4 VIF Screening | – |
| 2 | 2.1 Partial Correlation & Power Check | FR‑005, SC‑001, SC‑005 |
| 2 | 2.2 Dimensionality Reduction & Ridge Regression | FR‑005, SC‑002 |
| 2 | 2.3 Multiple‑Comparison Correction | FR‑006, SC‑003 |
| 2 | 2.4 Reporting & Summary | SC‑004 |
| 3 | 3.1 Schema Contract Tests | – |
| 3 | 3.2 Unit Tests | – |
| 3 | 3.3 Integration Test | FR‑007 |
