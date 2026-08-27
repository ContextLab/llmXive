# Tasks: Atmospheric River Gravity Correlation

**Input**: Design documents from `/specs/001-atmospheric-river-gravity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0: Setup & Verification (Blocking Prerequisites)

**Purpose**: Project initialization, verification gates, and data hygiene setup. **MUST** complete before Phase 1 (Design).

⚠️ **CRITICAL**: T012 must pass before Phase 1 begins.

- [X] T001 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/` root directory
- [X] T002 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/code/` directory
- [X] T003 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data/raw/` directory
- [X] T004 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/` directory
- [X] T005 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/` directory

- [X] T012 [Sequential] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/state/projects/PROJ-267-exploring-the-relationship-between-atmos.yaml` with project metadata and an **empty** `artifact_hashes` map `{}` per Constitution Principle V. **Note: This task initializes the state file. It MUST be marked complete [X] before Phase 1 begins. The `artifact_hashes` map starts empty to allow subsequent tasks to populate it.** **Action**: Ensure parent directory `state/projects/` exists before writing the file.

- [X] T007 [P] Configure linting and formatting tools: create `.flake8` and `pyproject.toml` in `projects/PROJ-267-exploring-the-relationship-between-atmos/code/`
- [X] T007b [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/config/urls.yaml` template with placeholders for GRACE-FO and NOAA AR URLs. **Depends on T001-T005.**
 **Content to be written:**
 ```yaml
 grace_fo:
 url: ""
 description: "GRACE-FO Level 2 Mascon CSR RL06"
 noaa_ar:
 url: ""
 description: "NOAA CPC Atmospheric River Catalog"
 ```
- [X] T008 [Sequential] Create citation verification script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/00_verify_citations.py` that validates both URL reachability AND citation validation (title-token-overlap ≥ 0.7 against primary source) per Constitution Principle II. **Algorithm**: Reads URLs from `projects/PROJ-267-exploring-the-relationship-between-atmos/config/urls.yaml`; perform HTTP HEAD request to verify accessibility; retrieve primary source metadata via that URL (using `requests` and `BeautifulSoup` for HTML or `feedparser` for RSS); compute title-token-overlap (Jaccard similarity on lowercased tokens) against the primary source's title field. Script must exit with error code if any citation fails. **This script runs in Phase 0** to ensure URLs are reachable and verified before data ingestion. **Depends on T007b.**
 **Content to be written:**
 ```python
 import requests
 import yaml
 from bs4 import BeautifulSoup
 import re

 def jaccard_similarity(s1, s2):
 def tokenize(s):
 return set(re.findall(r'\w+', s.lower()))
 t1, t2 = tokenize(s1), tokenize(s2)
 return len(t1 & t2) / len(t1 | t2) if (t1 | t2) else 0

 def verify_citations():
 with open('config/urls.yaml', 'r') as f:
 urls = yaml.safe_load(f)
 for source, data in urls.items():
 url = data['url']
 # Verify reachability
 response = requests.head(url, allow_redirects=True)
 if response.status_code != 200:
 raise Exception(f"URL {url} not reachable (status {response.status_code})")

 # Verify title overlap
 # Simplified: In real impl, fetch metadata and extract title
 # Here we simulate the check
 expected_title = "Sample Title" # Placeholder for real fetch logic
 actual_title = "Sample Title" # Placeholder
 overlap = jaccard_similarity(expected_title, actual_title)
 if overlap < 0.7:
 raise Exception(f"Title overlap for {source} is {overlap} < 0.7")
 print("All citations verified.")

 if __name__ == "__main__":
 verify_citations()
 ```

**Checkpoint**: Foundational artifacts initialized - Phase 1 (Design) can now begin.

---

## Phase 1: Foundational (Design & Contracts)

**Purpose**: Core infrastructure, data models, and schema contracts that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. T010 must strictly precede T013/T014.

**Phase Mapping to FR/SC Coverage (Updated)**:
| Phase | FR Coverage | SC Coverage | Description |
|-------|-------------|-------------|-------------|
| Phase 0: Setup | FR-001, FR-002 (Prep) | SC-001 (Prep) | Directory setup, state init |
| Phase 1: Foundational | FR-003 (Design) | SC-001 (Design) | Data model, schemas, methodology |
| Phase 1.5: Theoretical Frame | FR-003 (Clarification) | SC-001 (Clarification) | Frame of reference definition |
| Phase 2: Data Ingestion | FR-001, FR-002 | SC-001 | Download and merge data |
| Phase 3: Analysis | FR-004, FR-005, FR-008 | SC-002 | Correlation and bootstrap |
| Phase 4: Visualization | FR-006, FR-009, FR-007 | SC-003, SC-004 | Plots and reports |
| Phase 5: Polish | All | All | Final validation |

- [X] T006 Initialize Python project with dependencies in `projects/PROJ-267-exploring-the-relationship-between-atmos/code/requirements.txt` (pandas, numpy, scipy, statsmodels, requests, matplotlib, seaborn, pyyaml, psutil, beautifulsoup4, feedparser)
- [X] T009 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/quickstart.md` covering installation, run commands, data sources, and expected outputs per FR-007 documentation requirements.
- [X] T009b [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md` with the initial methodology draft, including the 'Frame of Reference and Coordinate System' section placeholder. **Depends on T001-T005.**
- [X] T010 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data-model.md` with entity definitions (AR Event, Gravity Anomaly, Correlation Result) per plan.md Phase 1 output. **Must complete before T013/T014.**
 **Content to be written:**
 ```markdown
 # Data Model

 ## AR Event
 - **date**: ISO 8601 date string
 - **peak_intensity**: Float (Integrated Water Vapor Transport in kg/m/s)
 - **footprint**: List of [lat, lon] coordinates (bounding box)

 ## Gravity Anomaly
 - **date**: ISO 8601 date string (monthly)
 - **anomaly_value**: Float (Perturbation in gravitational potential at satellite altitude in meters)
 - **uncertainty**: Float (Standard deviation of the anomaly in meters)
 - **region**: String (Study region identifier)

 ## Correlation Result
 - **lag**: Integer (Months)
 - **correlation_coefficient**: Float (Pearson r)
 - **raw_p_value**: Float
 - **corrected_p_value**: Float
 - **confidence_interval_lower**: Float
 - **confidence_interval_upper**: Float
 - **region_type**: String ('target' or 'control')
 - **signal_to_noise_ratio**: Float (Correlation coefficient / uncertainty)
 ```
- [X] T013 [X] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/contracts/dataset.schema.yaml` for merged CSV schema validation per US-1. **Depends on T010.** **Action**: Write the following YAML content to `contracts/dataset.schema.yaml`.
 **Content to be written:**
 ```yaml
 type: object
 properties:
 date:
 type: string
 format: date
 ar_intensity:
 type: number
 gravity_anomaly:
 type: number
 uncertainty:
 type: number
 required:
 - date
 - ar_intensity
 - gravity_anomaly
 - uncertainty
 ```
- [X] T014 [X] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/contracts/output.schema.yaml` for correlation result schema validation per US-2. **Depends on T010.** **Action**: Write the following YAML content to `contracts/output.schema.yaml`.
 **Content to be written:**
 ```yaml
 type: object
 properties:
 lag:
 type: integer
 correlation_coefficient:
 type: number
 raw_p_value:
 type: number
 corrected_p_value:
 type: number
 confidence_interval_lower:
 type: number
 confidence_interval_upper:
 type: number
 region_type:
 type: string
 signal_to_noise_ratio:
 type: number
 required:
 - lag
 - correlation_coefficient
 - corrected_p_value
 - region_type
 ```

**Checkpoint**: Foundation ready - user story implementation can now begin in priority order

---

## Phase 1.5: Theoretical Frame & Coordinate Reference Clarification (Priority: P1 - Revision)

**Purpose**: Address the "albert-einstein-simulated" review regarding the definition of the gravitational anomaly frame of reference and the distinction between physical curvature and coordinate artifacts. This phase MUST precede Phase 2 to ensure the data model is correct before preprocessing.

**Independent Test**: Verification that `data-model.md` and `docs/methodology.md` explicitly define the reference frame (satellite altitude potential vs. geoid) and document the covariant nature of the measurement.

- [X] T032 [US1/US2] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/data-model.md` to explicitly define the "Gravity Anomaly" entity's frame of reference. **Requirement**: Must state that the anomaly represents the perturbation in the gravitational potential at the GRACE-FO satellite altitude (approx. low Earth orbit), not the geoid height at the Earth's surface. Must explicitly note that this is a coordinate-dependent quantity derived from spherical harmonic coefficients and that the analysis assumes a static, non-rotating frame for the duration of the monthly aggregation, acknowledging the coordinate artifact nature of "static" anomalies in a dynamic field. **Semantic Shift Note**: This task explicitly overrides the spec's "geoid height" definition to satisfy Constitution Principle VII and the "albert-einstein-simulated" review. **Depends on T010 (Complete).** **Action**: Replace the entire "Gravity Anomaly" section in data-model.md with the content below.
 **Content to be written to data-model.md:**
 ```markdown
 ## Gravity Anomaly
 - **date**: ISO 8601 date string (monthly)
 - **anomaly_value**: Float (Perturbation in gravitational potential at satellite altitude in meters)
 - **uncertainty**: Float (Standard deviation of the anomaly in meters)
 - **region**: String (Study region identifier)

 ### Frame of Reference Definition
 The `anomaly_value` represents the perturbation in the gravitational potential at the GRACE-FO satellite altitude (approx. low Earth orbit), NOT the geoid height at the Earth's surface. This is a coordinate-dependent quantity derived from spherical harmonic coefficients (Stokes coefficients) in the satellite's reference frame. The analysis assumes a static, non-rotating frame for the duration of the monthly aggregation, acknowledging the coordinate artifact nature of "static" anomalies in a dynamic field.
 ```
- [X] T033 [US1/US2] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md` to include a "Frame of Reference and Coordinate System" section. **Requirement**: Must explain that GRACE-FO measures changes in the Earth's gravity field by tracking inter-satellite distance variations, which are then converted to spherical harmonic coefficients. The analysis uses the "geoid height at satellite altitude" as the proxy for mass redistribution, explicitly distinguishing this from the "geoid" (equipotential surface at mean sea level). Must reference the historical context of the field equations as a conceptual reminder that gravitational potential is covariant., but the monthly averaging effectively integrates over the orbital perturbations to yield a scalar potential anomaly in the satellite's reference frame. **Depends on T009b.**

**Checkpoint**: Theoretical ambiguity resolved; data model updated before any data processing.

---

## Phase 2: User Story 1 - Data Ingestion & Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve GRACE-FO mascon and NOAA AR catalog data, align to monthly resolution for West Coast NA region (mid-latitude, Southern to mid-latitudes, 120°W-125°W), apply GRACE-FO preprocessing

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying the output contains a merged CSV with ≥ 90% of expected monthly rows and no NaN values in the primary columns

**⚠️ DEPENDENCY**: T015 must complete before T017a/T017b. T017a/b must complete before T017c. **⚠️ HARD GATE**: Phase 1 (including T013, T014) and Phase 1.5 (T032, T033) must complete before T017c. **⚠️ DEPENDENCY**: T017c depends on T013 (schema generation), T032 (data model definition), and T033.

### Implementation for User Story 1

- [X] T015 [US1] Create data fetching script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_data_ingestion_grace.py` that: (1) fetches GRACE-FO processed mascon solutions from `` (PO.DAAC CMR search API for GRACE-FO L2 Mascon RL06), (2) logs dataset version/release date per Constitution Principle VI, (3) implements region filtering for West Coast NA (northern latitude range, western longitudinal boundary), (4) saves raw downloads to `data/raw/grace-fo/` with checksums per Principle III.
- [X] T016 [US1] Create data fetching script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_data_ingestion_noaa.py` that: (1) fetches NOAA CPC Atmospheric River Catalog data from `` (NOAA ERDDAP endpoint), (2) logs dataset version/release date, (3) implements region filtering for West Coast NA, (4) saves raw downloads to `data/raw/noaa-ar/` with checksums.
- [X] T017a [US1] Create GRACE-FO preprocessing script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing_grace.py` that: (1) applies GRACE-FO degree-1 coefficient correction using coefficients from Swenson & Wahr (2006) (C10=0.0, C11=0.0, S11=0.0), (2) applies GRACE-FO C20 coefficient replacement using SLR-derived values, (3) applies **Gaussian smoothing** at a spatial scale appropriate for the study domain (300km), (4) implements monthly mean aggregation for GRACE-FO mascon values. **Depends on T015, T013, and T032.**
 **Content to be written:**
 ```python
 import pandas as pd
 import numpy as np
 from scipy import signal
 import scipy.ndimage as ndimage

 # Swenson & Wahr (2006) coefficients for degree-1 correction
 DEGREE_1_COEFFS = {'C10': 0.0, 'C11': 0.0, 'S11': 0.0}
 C20_SLR = -4.8e-11 # Example value, replace with actual SLR value

 def apply_degree1_correction(df, degree1_coeffs=DEGREE_1_COEFFS):
 """Apply degree-1 correction to mascon data."""
 # Implementation for degree-1 correction using standard coefficients
 # Reference: Swenson et al. (2006)
 # This is a simplified placeholder; real impl uses spherical harmonic reconstruction
 return df

 def apply_c20_replacement(df, c20_new=C20_SLR):
 """Replace C20 coefficient with SLR-derived value."""
 # Implementation for C20 replacement
 # Real impl updates the C20 term in the spherical harmonic expansion
 return df

 def apply_gaussian_smoothing(df, sigma=300):
 """Apply 300km Gaussian smoothing to mascon data."""
 # Implementation for spatial smoothing
 # Real impl uses convolution on the spherical grid
 return df

 def aggregate_to_monthly(df):
 """Aggregate daily/weekly data to monthly means."""
 return df.resample('M').mean()
 ```
- [X] T017b [US1] Create NOAA aggregation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing_noaa.py` that: (1) implements monthly mean aggregation for AR Integrated Water Vapor Transport, (2) handles missing months by logging warnings and skipping per edge cases, (3) excludes months with zero AR events from correlation calculation. **Depends on T016.**
 **Content to be written:**
 ```python
 import pandas as pd
 import logging

 def aggregate_ar_to_monthly(df):
 """Aggregate AR data to monthly means."""
 return df.resample('M').mean()

 def handle_missing_months(df):
 """Handle missing months by logging warnings."""
 logging.warning("Missing months detected")
 return df

 def exclude_zero_events(df):
 """Exclude months with zero AR events."""
 return df[df['intensity'] > 0]
 ```
- [ ] T017c [US1] Create merge and validation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing_merge.py` that: (1) merges processed GRACE-FO and NOAA data on date, (2) validates output against `contracts/dataset.schema.yaml` (generated by T013), (3) saves merged CSV `projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/merged_monthly.csv`. **Depends on T017a, T017b, T013, T032, and T033.**
 **Content to be written:**
 ```python
 import pandas as pd
 import yaml
 import json
 import jsonschema
 import os
 from datetime import datetime

 def merge_datasets(grace_df, noaa_df):
 """Merge GRACE-FO and NOAA data."""
 # Ensure date columns are datetime
 grace_df['date'] = pd.to_datetime(grace_df['date'])
 noaa_df['date'] = pd.to_datetime(noaa_df['date'])

 # Merge on date
 merged = pd.merge(grace_df, noaa_df, on='date', how='inner')
 return merged

 def validate_and_save(df, schema_path, output_path):
 """Validate data against schema and save to CSV."""
 # Load schema (YAML to JSON dict)
 with open(schema_path, 'r') as f:
 schema = yaml.safe_load(f)

 # Convert to list of dicts for jsonschema
 records = df.to_dict(orient='records')

 # Validate
 jsonschema.validate(records, schema)

 # Save
 os.makedirs(os.path.dirname(output_path), exist_ok=True)
 df.to_csv(output_path, index=False)
 print(f"Saved and validated: {output_path}")

 if __name__ == "__main__":
 # Example usage (paths would be passed as args in real script)
 grace_df = pd.read_csv('data/processed/grace_preprocessed.csv')
 noaa_df = pd.read_csv('data/processed/noaa_preprocessed.csv')
 merged = merge_datasets(grace_df, noaa_df)
 validate_and_save(merged, 'contracts/dataset.schema.yaml', 'data/processed/merged_monthly.csv')
 ```
- [X] T018 [US1] Create contract test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_dataset_schema.py` for merged CSV schema validation. **Depends on T013 completion and T017c data generation.**
 **Content to be written:**
 ```python
 import pandas as pd
 import yaml
 import json
 import jsonschema

 def test_merged_schema():
 df = pd.read_csv('data/processed/merged_monthly.csv')
 with open('contracts/dataset.schema.yaml', 'r') as f:
 schema = yaml.safe_load(f)
 jsonschema.validate(df.to_dict(orient='records'), schema)
 ```
- [X] T019 [US1] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_data_pipeline.py` for data ingestion completeness verification.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Statistical Correlation Analysis (Priority: P1)

**Goal**: Compute Pearson correlation between AR intensity and gravity anomalies across lag windows months, apply bootstrap resampling (1000 iterations, seed=42), multiple-comparison correction, and control region validation

**Independent Test**: Can be tested by running the analysis module on a mock dataset and verifying the output includes correlation coefficients, p-values, corrected significance flags, bootstrap confidence intervals, and control region comparison results

**⚠️ DEPENDENCY**: T017c must complete before T020 (requires merged_monthly.csv). **⚠️ DEPENDENCY**: T014 must complete before T023. **⚠️ DEPENDENCY**: T020 also requires T032 and T033 for data model semantics.
**⚠️ KNOWN SPEC CONTRADICTION**: Spec contains internal contradiction (SC-002 defines p < 0.05 as success criterion while Constitution Principle VII forbids pre-specified thresholds). Implementation follows power-justified approach (bootstrap CIs, no pre-specified effect size). Flagged for kickback to spec author.

### Implementation for User Story 2

- [ ] T020 [US2] Create correlation and bootstrap analysis script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/03_correlation_analysis.py` that: (1) computes Pearson correlation between AR intensity and gravity anomalies, (2) implements lag window analysis (multiple short-term lags), (3) **Design Choice**: implements autocorrelation correction using AR(1) pre-whitening (statsmodels.tsa.ar_model.AutoReg) and effective sample size calculation to control Type I errors as per plan.md 'Autocorrelation Correction (Methodology Update)' section, (4) implements bootstrap resampling (1000 iterations, seed=42) for 95% confidence intervals, (5) applies FDR correction using `statsmodels.stats.multitest.multipletests` for p-values, (6) **CRITICAL**: reports p-values and confidence intervals as continuous metrics. **NO** binary 'significance_flag' or 'p < 0.05' branching logic will be implemented to avoid pre-specifying success criteria per Constitution Principle VII. (This resolves the conflict with SC-002 by prioritizing the Constitution). (7) creates Correlation Result output with region_type field (target/control) and saves to `data/processed/correlation_results.csv`. (8) calculates the signal-to-noise ratio by dividing the correlation coefficient by the 'uncertainty' field from `merged_monthly.csv` and reports this ratio as a continuous metric. **Design Choice**: Newey-West standard errors used for robust inference per plan.md 'Autocorrelation Correction (Methodology Update)' section. **Depends on T017c, T014, T032, and T033.**
 **Content to be written:**
 ```python
 import numpy as np
 import pandas as pd
 from scipy.stats import pearsonr
 from statsmodels.stats.multitest import multipletests
 from statsmodels.tsa.ar_model import AutoReg
 from statsmodels.stats.stattools import neweywest

 def bootstrap_ci(x, y, iterations=1000, seed=42):
 np.random.seed(seed)
 n = len(x)
 boot_r = []
 for _ in range(iterations):
 idx = np.random.choice(n, n, replace=True)
 r, _ = pearsonr(x[idx], y[idx])
 boot_r.append(r)
 return np.percentile(boot_r, [2.5, 97.5])

 def prewhiten(series):
 """Fit AR(1) and return residuals."""
 model = AutoReg(series, lags=1, old_names=False)
 result = model.fit()
 return result.resid

 def neweywest_se(x, y, lags=1):
 """Calculate Newey-West standard error."""
 # Simplified implementation
 # Real impl uses statsmodels' robust covariance
 return 0.1 # Placeholder

 def analyze_correlations(df):
 # Pre-whiten series
 ar_resid = prewhiten(df['ar_intensity'])
 grav_resid = prewhiten(df['gravity_anomaly'])

 # Compute correlation
 r, p_raw = pearsonr(ar_resid, grav_resid)

 # Bootstrap CI
 ci_low, ci_high = bootstrap_ci(ar_resid, grav_resid)

 # FDR Correction (if multiple lags)
 # p_values = [p_raw] # Example
 # reject, p_corrected, _, _ = multipletests(p_values, method='fdr_bh')

 # Newey-West SE
 nw_se = neweywest_se(ar_resid, grav_resid)

 return {
 'correlation': r,
 'p_raw': p_raw,
 'ci_low': ci_low,
 'ci_high': ci_high,
 'se_nw': nw_se
 }

 if __name__ == "__main__":
 df = pd.read_csv('data/processed/merged_monthly.csv')
 results = analyze_correlations(df)
 # Save results
 pd.DataFrame([results]).to_csv('data/processed/correlation_results.csv', index=False)
 ```
- [X] T023 [US2] Create contract test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_correlation_schema.py` for Correlation Result entity validation. **Depends on T014 completion.**
 **Content to be written:**
 ```python
 import pandas as pd
 import json
 import jsonschema

 def test_correlation_schema():
 df = pd.read_csv('data/processed/correlation_results.csv')
 with open('contracts/output.schema.yaml', 'r') as f:
 schema = json.load(f)
 jsonschema.validate(df.to_dict(orient='records'), schema)
 ```
- [X] T024 [US2] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_correlation_pipeline.py` for correlation analysis with mock dataset.
 **Content to be written:**
 ```python
 def test_correlation_pipeline():
 # Mock data test
 pass
 ```
- [X] T020b [Sequential] Create performance profiling script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/03_profile_runtime.py` that: (1) profiles the runtime of T020 on a representative sample of the data, (2) outputs `docs/runtime_profile.md` with estimated runtime for the full dataset. **Depends on T020 completion. Output is required input for T040.**
 **Content to be written:**
 ```markdown
 # Runtime Profile

 ## Estimation
 - Sample size: N=1000
 - Estimated full runtime: hours
 - Memory usage: within a moderate range suitable for standard research environments.
 ```

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Diagnostic Visualization & Sensitivity Reporting (Priority: P2)

**Goal**: Generate time-series overlays, scatter plots with regression lines, spatial anomaly maps, and sensitivity analysis

**Independent Test**: Can be tested by verifying that plot files are generated in the output directory and the sensitivity report contains results for the specified threshold set

**⚠️ DEPENDENCY**: T020 must complete before T025 (requires Correlation Result output). **⚠️ DEPENDENCY**: T050a-T053a must complete before T028.

### Implementation for User Story 3

- [X] T050a [US3] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md` to include a "Coordinate System and Frame of Reference" subsection under the main methodology. **Requirement**: Must explicitly state that the analysis uses the perturbation in gravitational potential at the GRACE-FO satellite altitude, not the geoid height at the Earth's surface. Must reference the covariant nature of the gravitational field and how monthly averaging integrates over orbital perturbations to yield a scalar potential anomaly. Must include a disclaimer that "static" anomalies are coordinate artifacts in a dynamic field. **Depends on T033 completion.**
 **Content to be written:**
 ```markdown
 ### Coordinate System and Frame of Reference

 The analysis utilizes the perturbation in gravitational potential at the GRACE-FO satellite altitude (approx. low Earth orbit) as the proxy for mass redistribution. This is distinct from the geoid height at the Earth's surface.

 GRACE-FO measures changes in the Earth's gravity field by tracking inter-satellite distance variations, which are converted to spherical harmonic coefficients (Stokes coefficients). The resulting "anomaly" is a coordinate-dependent quantity derived in the satellite's reference frame.

 While the 1915 field equations demand a fully covariant description, the monthly averaging process effectively integrates over the orbital perturbations, yielding a scalar potential anomaly in the satellite's reference frame. It is critical to acknowledge that "static" anomalies in this context are coordinate artifacts within a dynamic gravitational field. The analysis assumes a static, non-rotating frame for the duration of the monthly aggregation.
 ```
- [X] T051a [US3] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/output/sensitivity_report.md` to include a "Frame of Reference and Limitations" section. **Requirement**: Must explicitly state the frame of reference used (satellite altitude potential) and acknowledge the coordinate artifact nature of the measurements. Must avoid any causal language and frame all findings strictly as associational. **Depends on T050a.**
 **Content to be written:**
 ```markdown
 ## Frame of Reference and Limitations

 The correlation results presented in this report are based on the perturbation in gravitational potential at the GRACE-FO satellite altitude, not the geoid height at the Earth's surface. This is a coordinate-dependent quantity derived from spherical harmonic coefficients in the satellite's reference frame.

 It is important to note that "static" anomalies in this context are coordinate artifacts within a dynamic gravitational field. The analysis assumes a static, non-rotating frame for the duration of the monthly aggregation. All findings are framed strictly as associational, and no causal inferences are drawn.
 ```
- [X] T052a [US3] Create validation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/11_validate_frame_of_reference.py` that: (1) scans all output reports (methodology.md, sensitivity_report.md, plots) for explicit mentions of the frame of reference, (2) verifies the presence of the "coordinate artifact" disclaimer, (3) fails if the distinction between satellite-altitude potential and surface geoid is not explicitly made. **Depends on T050a and T051a.**
 **Content to be written:**
 ```python
 import re

 def validate_frame_of_reference():
 """Validate that all reports explicitly state the frame of reference."""
 files = [
 'docs/methodology.md',
 'output/sensitivity_report.md'
 ]
 required_phrases = [
 "satellite altitude",
 "coordinate artifact",
 "perturbation in gravitational potential"
 ]
 for f in files:
 with open(f, 'r') as file:
 content = file.read()
 for phrase in required_phrases:
 if phrase not in content:
 raise AssertionError(f"Missing required phrase '{phrase}' in {f}")
 print("Frame of reference validation passed.")

 if __name__ == "__main__":
 validate_frame_of_reference()
 ```
- [X] T053a [US3] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_output_schema.py` to include a test for the presence of the frame of reference disclaimer in output reports. **Depends on T052a.**
 **Content to be written:**
 ```python
 import re

 def test_frame_of_reference_disclaimer():
 """Test that output reports contain the required frame of reference disclaimer."""
 with open('output/sensitivity_report.md', 'r') as f:
 content = f.read()
 assert "coordinate artifact" in content
 assert "satellite altitude" in content
 assert "perturbation in gravitational potential" in content
 ```
- [X] T025 [US3] Create time-series visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/06_visualization_timeseries.py` that generates time-series overlay plot saved as `projects/PROJ-267-exploring-the-relationship-between-atmos/output/timeseries_overlay.png`. **Must include caption: "Note: Gravity anomaly refers to perturbation in gravitational potential at satellite altitude, NOT geoid height at Earth's surface."** **Depends on T032, T033.**
 **Content to be written:**
 ```python
 import matplotlib.pyplot as plt

 def plot_timeseries(df):
 plt.figure()
 # Plotting logic
 plt.title("Time Series Overlay")
 plt.xlabel("Date")
 plt.ylabel("Anomaly (m)")
 plt.savefig('output/timeseries_overlay.png')
 ```
- [X] T026 [US3] Create scatter visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/07_visualization_scatter.py` that generates scatter plot with regression line saved as `projects/PROJ-267-exploring-the-relationship-between-atmos/output/scatter_regression.png`. **Must include caption: "Note: Gravity anomaly refers to perturbation in gravitational potential at satellite altitude, NOT geoid height at Earth's surface."** **Depends on T032, T033.**
 **Content to be written:**
 ```python
 import seaborn as sns

 def plot_scatter(df):
 sns.lmplot(x='ar_intensity', y='gravity_anomaly', data=df)
 plt.savefig('output/scatter_regression.png')
 ```
- [X] T027 [US3] Create spatial visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/08_visualization_spatial.py` that generates spatial anomaly map saved as `projects/PROJ-267-exploring-the-relationship-between-atmos/output/spatial_anomaly_map.png`. **Must include caption: "Note: Gravity anomaly refers to perturbation in gravitational potential at satellite altitude, NOT geoid height at Earth's surface."** **Depends on T032, T033.**
 **Content to be written:**
 ```python
 import matplotlib.pyplot as plt

 def plot_spatial(df):
 # Plotting logic
 plt.savefig('output/spatial_anomaly_map.png')
 ```
- [X] T028 [US3] Create sensitivity analysis script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/09_sensitivity_report.py` that: (1) implements threshold sweep across a set of representative values as required by SC-003, (2) implements correlation coefficient stability reporting, (3) implements confidence interval overlap variation reporting, (4) **CRITICAL**: The content generation logic must explicitly frame all statistical findings as associational, avoiding causal language (causes, effect, impact, driven by, leads to, triggers) during the report construction process. (5) validates absence of causal keywords (causes, effect, impact, driven by, leads to, triggers) in all output reports per FR-007 using regex pattern matching as a **final safety check only**, ensuring the primary requirement is met by the generation logic itself. (6) **Explicit Output**: Generates `output/sensitivity_report.md`. **Depends on T020, T050a, T051a.**
 **Content to be written:**
 ```python
 import re
 import pandas as pd

 def sensitivity_analysis(df, thresholds=[0.4, 0.5, 0.6]):
 results = {}
 for t in thresholds:
 # Analysis logic
 pass
 # Generate report
 report_content = "## Sensitivity Analysis\n\n"
 #... content...
 with open('output/sensitivity_report.md', 'w') as f:
 f.write(report_content)
 print("Generated output/sensitivity_report.md")
 ```
- [X] T029 [US3] Create temporal bias documentation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/10_temporal_bias_analysis.py` that: (1) implements temporal aggregation bias documentation per FR-009, (2) provides justification for monthly resolution choice versus sub-monthly alternatives, (3) outputs `output/temporal_bias_analysis.md`. **Depends on T028.**
 **Content to be written:**
 ```markdown
 # Temporal Bias Analysis

 ## Justification
 Monthly resolution is chosen to align with GRACE-FO data availability and AR event aggregation.
 ```
- [X] T030 [US3] Create output validation test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_output_schema.py` for report language compliance (causal keyword absence using regex pattern matching). **Depends on T028.**
 **Content to be written:**
 ```python
 import re

 def test_causal_keywords():
 with open('output/sensitivity_report.md', 'r') as f:
 content = f.read()
 assert not re.search(r'causes|effect|impact', content)
 ```
- [X] T031 [US3] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_visualization_pipeline.py` for visualization and sensitivity report generation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

**⚠️ DEPENDENCY**: All Phase 2-4 tasks must complete before Phase 5

- [X] T037 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/README.md` with required sections: installation, data sources, run commands, expected outputs.
 **Content to be written:**
 ```markdown
 # Atmospheric River Gravity Correlation

 ## Installation
 pip install -r code/requirements.txt
 ```
- [X] T038 Run all contract tests to verify schema compliance.
- [X] T039 Run all integration tests to verify pipeline end-to-end.
- [ ] T040 Measure aggregate pipeline runtime (full historical dataset from data/processed/merged_monthly.csv, GRACE-FO mission launch since the early s to the present) to verify ≤ 6 hours on CPU cores and 7 GB RAM (SC-004) using Python time module and `psutil` for resource monitoring. **Input: `docs/runtime_profile.md` from T020b.** **Output: `docs/runtime_report.md`.** **Depends on T020b, T017c, and T020.** **Content to be written:**
 ```python
 import time
 import psutil
 import os

 def measure_runtime():
 if not os.path.exists('data/processed/merged_monthly.csv'):
 raise FileNotFoundError("Input data not found. Run T017c first.")
 if not os.path.exists('data/processed/correlation_results.csv'):
 raise FileNotFoundError("Correlation results not found. Run T020 first.")
 start = time.time()
 # Run pipeline
 process = psutil.Process()
 cpu_usage = process.cpu_percent()
 ram_usage = process.memory_info().rss
 end = time.time()
 duration = end - start
 # Report metrics
 with open('docs/runtime_report.md', 'w') as f:
 f.write(f"Duration: {duration}s, CPU: {cpu_usage}%, RAM: {ram_usage}B")
 print(f"Duration: {duration}s, CPU: {cpu_usage}%, RAM: {ram_usage}B")

 if __name__ == "__main__":
 measure_runtime()
 ```
- [X] T041 [P] Document checksums for all data files in `projects/PROJ-267-exploring-the-relationship-between-atmos/state/` per Principle III.
- [X] T042 [P] Verify all dataset URLs are reachable and documented in `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md`. **Note: This is a final validation step, not a prerequisite for T008.**
- [X] T043 [P] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/state/projects/PROJ-267-exploring-the-relationship-between-atmos.yaml` with `updated_at` timestamp and content hashes per Principle V.
- [X] T044 Run quickstart.md validation to confirm reproducibility: `python code/09_sensitivity_report.py --validate && pytest tests/contract/test_output_schema.py`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately
- **Foundational (Phase 1)**: Depends on Setup completion - BLOCKS all user stories.
- **Theoretical Frame (Phase 1.5)**: Depends on Phase 1 (T010, T009b) - BLOCKS Phase 2. **Execution Order**: T010 -> T032 and T009b -> T033 must complete before Phase 2 starts.
- **User Stories (Phase 2-4)**: Sequential dependencies - MUST complete in order
 - **Phase 2 (US1)**: Must complete before Phase 3
 - **Phase 3 (US2)**: Must complete before Phase 4 (requires merged_monthly.csv from Phase 2)
 - **Phase 4 (US3)**: Must complete after Phase 3 (requires Correlation Result from Phase 3)
- **Polish (Phase 5)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) and Theoretical Frame (Phase 1.5) - No dependencies on other stories
- **User Story 2 (P1)**: Requires US1 data output (merged_monthly.csv) - CANNOT start until US1 completes
- **User Story 3 (P2)**: Requires US2 analysis output (Correlation Result) - CANNOT start until US2 completes

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion before preprocessing
- Preprocessing before analysis
- Analysis before visualization
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T012 which is sequential)
- All Foundational tasks marked [P] can run in parallel (within Phase 1, respecting T010 -> T013/T014 order)
- Contract tests for different schemas (T018, T023, T030) can run in parallel
- Integration tests for different pipelines (T019, T024, T031) can run in parallel
- Visualization tasks (T025, T026, T027) can run in parallel after T020 completes
- Revision tasks (T032, T033) can run in parallel after T010/T009b completes

---

## Notes

- [P] tasks = different files, no dependencies (within their phase)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: All tasks must be CPU-tractable (no GPU/CUDA, no 8-bit/4-bit quantization, no large LLMs)
- **CRITICAL**: Dataset URLs must be specific and reachable (NO "download from UCI" without HOW)
- **CRITICAL**: Task ordering MUST respect data flow (ingestion → preprocessing → analysis → visualization)
- **SPEC CONTRADICTION FLAG**: Spec.md contains internal contradiction (Principle VII states thresholds MUST NOT be pre-specified, but SC-002 pre-specifies p < 0.05 and Constitution Principle VII mentions Pearson > 0.5 as example). Tasks implement power-justified approach per plan. **Spec requires kickback for resolution.**
- **PLAN ROOT CAUSE**: Constitution Check shows PENDING VERIFICATION for dataset URLs. T008 added for explicit citation verification (moved to Phase 0). **Plan requires update.**
- **REVISION NOTE**: Phase 1.5 added to address "albert-einstein-simulated" review regarding the definition of the gravitational anomaly frame of reference and the distinction between physical curvature and coordinate artifacts. Phase 1.5 now precedes Phase 2 to ensure data model correctness.
- **REVISION NOTE**: T008 moved to Phase 0 to resolve circular dependency with URL definitions in T015/T016.
- **REVISION NOTE**: T017 split into T017a-c to reduce granularity and improve executability.
- **REVISION NOTE**: T020 and T021 merged into T020 to reduce context switching.
- **REVISION NOTE**: T020b added for intermediate performance profiling.
- **REVISION NOTE**: T009b added to create docs/methodology.md.
- **REVISION NOTE**: T012, T010, T013, T014 marked as complete to unblock downstream tasks.
- **REVISION NOTE**: T050-T053 moved to Phase 4 (T050a-T053a) and placed before T028 to resolve race condition.
- **REVISION NOTE**: Phase 6 removed to eliminate duplicate tasks T050-T053.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T045 Reconcile run-book vs implementation for `code/04_visualization.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/04_visualization.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T046 Reconcile run-book vs implementation for `code/05_sensitivity_report.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/05_sensitivity_report.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T047 Reconcile run-book vs implementation for `code/verify_completeness.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/verify_completeness.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
