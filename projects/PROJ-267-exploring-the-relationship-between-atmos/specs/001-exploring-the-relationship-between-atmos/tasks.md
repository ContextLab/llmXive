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

**Purpose**: Project initialization, verification gates, and data hygiene setup. **MUST** complete before Phase 1 (Design).

⚠️ **CRITICAL**: T012 must pass before Phase 1 begins.

- [X] T001 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/` root directory  
- [X] T002 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/code/` directory  
- [X] T003 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data/raw/` directory  
- [X] T004 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/` directory  
- [X] T005 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/` directory  

- [X] T012 [Sequential] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/state/projects/PROJ-267-exploring-the-relationship-between-atmos.yaml` with project metadata and an **empty** `artifact_hashes` map `{}` per Constitution Principle V. **Note**: Ensure parent directory `state/projects/` exists before writing the file.  

- [X] T007 [P] Configure linting and formatting tools: create `.flake8` and `pyproject.toml` in `projects/PROJ-267-exploring-the-relationship-between-atmos/code/`  
- [X] T007b [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/config/urls.yaml` template with placeholders for GRACE‑FO and NOAA AR URLs. **Depends on T001‑T005.**  
```yaml
grace_fo:
  url: ""
  description: "GRACE‑FO Level‑2 Mascon CSR RL06"
noaa_ar:
  url: ""
  description: "NOAA CPC Atmospheric River Catalog"
```

**Checkpoint**: Foundational artifacts initialized – Phase 1 (Design) can now begin.

---

## Phase 1: Foundational (Design & Contracts)

**Purpose**: Core infrastructure, data models, and schema contracts that MUST be complete before ANY user story can be implemented.

⚠️ **CRITICAL**: No user story work can begin until this phase is complete. T010 must strictly precede T013/T014.

| Phase | FR Coverage | SC Coverage | Description |
|-------|-------------|-------------|-------------|
| Phase 0: Setup | FR‑001, FR‑002 (Prep) | SC‑001 (Prep) | Directory setup, state init |
| Phase 1: Foundational | FR‑003 (Design) | SC‑001 (Design) | Data model, schemas, methodology |
| Phase 1.5: Theoretical Frame | FR‑003 (Clarification) | SC‑001 (Clarification) | Frame of reference definition |
| Phase 2: Data Ingestion | FR‑001, FR‑002 | SC‑001 | Download and merge data |
| Phase 3: Analysis | FR‑004, FR‑005, FR‑008 | SC‑002 | Correlation and bootstrap |
| Phase 4: Visualization | FR‑006, FR‑009, FR‑007 | SC‑003, SC‑004 | Plots and reports |
| Phase 5: Polish | All | All | Final validation |

- [X] T006 Initialize Python project with dependencies in `projects/PROJ-267-exploring-the-relationship-between-atmos/code/requirements.txt` (pandas, numpy, scipy, statsmodels, requests, matplotlib, seaborn, pyyaml, psutil, beautifulsoup4, feedparser)  
- [X] T009 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/quickstart.md` covering installation, run commands, data sources, and expected outputs per FR‑007 documentation requirements.  
- [X] T009b [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md` with the initial methodology draft, including a placeholder "Frame of Reference and Coordinate System" section. **Depends on T001‑T005.**  
- [X] T010 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data-model.md` with entity definitions (AR Event, Gravity Anomaly, Correlation Result) per plan.md Phase 1 output. **Must complete before T013/T014.**  
```markdown
# Data Model

## AR Event
- **date**: ISO 8601 date string
- **peak_intensity**: Float (Integrated Water Vapor Transport in kg m⁻¹ s⁻¹)
- **footprint**: List of [lat, lon] coordinates (bounding box)

## Gravity Anomaly
- **date**: ISO 8601 date string (monthly)
- **anomaly_value**: Float (Perturbation in gravitational potential at satellite altitude in meters)
- **uncertainty**: Float (Standard deviation of the anomaly in meters)
- **region**: String (Study region identifier)

## Correlation Result
- **lag**: Integer (Months)
- **correlation_coefficient**: Float (Pearson r)
- **raw_p_value**: Float
- **corrected_p_value**: Float
- **confidence_interval_lower**: Float
- **confidence_interval_upper**: Float
- **region_type**: String ('target' or 'control')
- **signal_to_noise_ratio**: Float (Correlation coefficient / uncertainty)
```

- [X] T013 [X] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/contracts/dataset.schema.yaml` for merged CSV schema validation per US‑1. **Depends on T010.**  
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

- [X] T014 [X] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/contracts/output.schema.yaml` for correlation‑result schema validation per US‑2. **Depends on T010.**  
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

**Checkpoint**: Foundation ready – user‑story implementation can now begin in priority order.

---

## Phase 1.5: Theoretical Frame & Coordinate Reference Clarification (Priority: P1 – Revision)

**Purpose**: Resolve the "albert‑einstein‑simulated" review regarding the definition of the gravity‑anomaly frame of reference and the distinction between physical curvature and coordinate artifacts. Must precede Phase 2.

- [X] T032 [US1/US2] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/data-model.md` to explicitly define the "Gravity Anomaly" entity's frame of reference. **Depends on T010.**  
```markdown
## Gravity Anomaly
- **date**: ISO 8601 date string (monthly)
- **anomaly_value**: Float (Perturbation in gravitational potential at satellite altitude in meters)
- **uncertainty**: Float (Standard deviation of the anomaly in meters)
- **region**: String (Study region identifier)

### Frame of Reference Definition
The `anomaly_value` represents the perturbation in the gravitational potential at the GRACE‑FO satellite altitude (≈ 500 km), **NOT** the geoid height at the Earth's surface. This is a coordinate‑dependent quantity derived from spherical‑harmonic coefficients in the satellite's reference frame. The analysis assumes a static, non‑rotating frame for the duration of the monthly aggregation, acknowledging the coordinate‑artifact nature of "static" anomalies in a dynamic field.
```

- [X] T033 [US1/US2] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md` to include a "Frame of Reference and Coordinate System" subsection. **Depends on T009b.**  
```markdown
### Frame of Reference and Coordinate System

The analysis utilizes the perturbation in gravitational potential at the GRACE‑FO satellite altitude (≈ low Earth orbit) as the proxy for mass redistribution. This is distinct from the geoid height at the Earth's surface.

GRACE‑FO measures changes in the Earth's gravity field by tracking inter‑satellite distance variations, which are converted to spherical‑harmonic (Stokes) coefficients. The resulting "anomaly" is a coordinate‑dependent quantity derived in the satellite's reference frame.

While the field equations demand a fully covariant description, the monthly averaging process effectively integrates over orbital perturbations, yielding a scalar potential anomaly in the satellite's reference frame. It is critical to acknowledge that "static" anomalies in this context are coordinate artifacts within a dynamic gravitational field. The analysis assumes a static, non‑rotating frame for the duration of the monthly aggregation.
```

**Checkpoint**: Theoretical ambiguity resolved; data model updated before any processing.

---

## Phase 2: User Story 1 – Data Ingestion & Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve GRACE‑FO mascon and NOAA AR catalog data, align to monthly resolution for the West Coast NA region, and apply standard GRACE‑FO preprocessing.

**Independent Test**: Execute the data pipeline script and verify the merged CSV contains ≥ 90 % of expected monthly rows and no NaN values in primary columns.

⚠️ **DEPENDS**: T015/T016 must complete before T008; T017a/b must complete before T017c; T017c must run after T017a/b and after schema files (T013).  

- [X] T015 [US1] Create data‑fetching script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_data_ingestion_grace.py` that (1) fetches GRACE‑FO Level‑2 mascon solutions via the PO.DAAC CMR API, (2) logs dataset version/release date, (3) filters to the West Coast NA region (35°N‑50°N, 120°W‑125°W), (4) saves raw files under `data/raw/grace-fo/` and records SHA‑256 checksums. **This task MUST populate `config/urls.yaml` with the actual URL used.**
- [X] T016 [US1] Create data‑fetching script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_data_ingestion_noaa.py` that (1) fetches the NOAA CPC Atmospheric River Catalog via the ERDDAP endpoint, (2) logs dataset version/release date, (3) filters to the same geographic window, (4) saves raw files under `data/raw/noaa-ar/` with checksums. **This task MUST update `config/urls.yaml` with the actual URL used.**
- [X] T008 [P] Create citation‑verification script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/00_verify_citations.py`. **Prerequisite**: `config/urls.yaml` MUST be populated with actual URLs by T015 and T016. The script performs an HTTP HEAD request for each URL and checks that the fetched HTML title overlaps ≥ 0.7 with the expected title (stored in the YAML). It exits with a non‑zero code on any failure, ensuring Constitution Principle II is satisfied before data ingestion. **This task runs AFTER T015/T016.**
- [X] T017a [US1] Create GRACE‑FO preprocessing script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing_grace.py`. The script () loads the downloaded mascon CSV, (2) applies **degree‑1 correction** using Swenson & Wahr (2006) coefficients (read from a local `coeffs/degree1.yaml` file), (3) replaces the **C20** coefficient with the latest SLR‑derived value (read from `coeffs/c20.yaml`), (4) performs **Gaussian smoothing** with a 300 km sigma via a convolution on the spherical grid (using `scipy.ndimage.gaussian_filter` on the gridded data), (5) aggregates to monthly means, and (6) writes `data/processed/grace_preprocessed.csv`. The script raises informative errors if required columns are missing.
- [X] T017b [US1] Create NOAA preprocessing script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing_noaa.py`. The script (1) loads the raw AR catalog, (2) aggregates Integrated Water Vapor Transport to monthly means, (3) logs warnings for any missing months, (4) drops months where total AR intensity equals zero, and (5) writes `data/processed/noaa_preprocessed.csv`.
- [X] T017c [US1] Create merge and validation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing_merge.py`. The script (1) reads `grace_preprocessed.csv` and `noaa_preprocessed.csv`, (2) merges on the `date` column (inner join), (3) validates the merged DataFrame against `contracts/dataset.schema.yaml` using `jsonschema`, (4) writes the validated output to `data/processed/merged_monthly.csv`. **Full script:**  
```python
import pandas as pd
import yaml
import jsonschema
import os
import sys

def load_schema(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def main():
    grace_path = "data/processed/grace_preprocessed.csv"
    noaa_path = "data/processed/noaa_preprocessed.csv"
    out_path = "data/processed/merged_monthly.csv"
    schema_path = "contracts/dataset.schema.yaml"

    if not os.path.exists(grace_path) or not os.path.exists(noaa_path):
        sys.exit("Preprocessed input files missing. Ensure T017a and T017b have run.")

    grace_df = pd.read_csv(grace_path, parse_dates=["date"])
    noaa_df = pd.read_csv(noaa_path, parse_dates=["date"])

    merged = pd.merge(grace_df, noaa_df, on="date", how="inner")

    schema = load_schema(schema_path)
    try:
        jsonschema.validate(merged.to_dict(orient="records"), schema)
    except jsonschema.ValidationError as e:
        sys.exit(f"Schema validation failed: {e.message}")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    merged.to_csv(out_path, index=False)
    print(f"Validated merged dataset written to {out_path}")

if __name__ == "__main__":
    main()
```

- [X] T018 [US1] Create contract test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_dataset_schema.py` that loads `merged_monthly.csv` and validates against `contracts/dataset.schema.yaml`.  
- [X] T019 [US1] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_data_pipeline.py` that runs the three scripts (`01_data_ingestion_*`, `02_preprocessing_*`, `02_preprocessing_merge.py`) on a small sample and asserts the merged CSV contains the expected columns and no NaNs.  

**Checkpoint**: User Story 1 is fully functional and independently testable.

---

## Phase 3: User Story 2 – Statistical Correlation Analysis (Priority: P1)

**Goal**: Compute Pearson correlation between AR intensity and gravity anomalies across lag windows, apply bootstrap resampling (1000 iterations, seed=42), perform autocorrelation correction, and apply FDR multiple‑testing correction. Also validate against control regions.

**Independent Test**: Run the analysis on a mock dataset and verify the output CSV includes correlation coefficients, raw and corrected p‑values, 95 % bootstrap confidence intervals, and control‑region results.

⚠️ **DEPENDS**: T017c must be complete; T014 must be present for output schema; T032/T033 provide data‑model semantics.

- [X] T020 [US2] Create correlation and bootstrap analysis script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/03_correlation_analysis.py`. The script (1) loads `merged_monthly.csv`, (2) pre‑whitens both series using an AR(1) model (`statsmodels.tsa.AutoReg`), (3) for each lag in a symmetric range of negative to positive integer lags, computes Pearson r and raw p‑value, (4) performs **bootstrap** (1000 iterations, seed 42) to obtain 95 % CI, (5) applies **FDR** correction (`statsmodels.stats.multitest.multipletests`) to all raw p‑values, (6) calculates a signal‑to‑noise ratio as `r / mean(uncertainty)`, (7) writes results to `data/processed/correlation_results.csv` conforming to `output.schema.yaml`. **No hard‑coded significance flag** is produced; downstream reporting may interpret corrected p‑values as needed. **Full script:**  
```python
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from statsmodels.tsa.ar_model import AutoReg
from statsmodels.stats.multitest import multipletests
import sys
import os

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
    try:
        model = AutoReg(series, lags=1, old_names=False)
        res = model.fit()
        return res.resid
    except Exception as e:
        sys.exit(f"Pre‑whitening failed: {e}")

def analyze(df):
    results = []
    lags = [-3, -2, -1, 0, 1, 2, 3]
    raw_ps = []

    ar_series = prewhiten(df["ar_intensity"].values)
    grav_series = prewhiten(df["gravity_anomaly"].values)

    for lag in lags:
        if lag > 0:
            x = ar_series[:-lag]
            y = grav_series[lag:]
        elif lag < 0:
            x = ar_series[-lag:]
            y = grav_series[:lag]
        else:
            x, y = ar_series, grav_series

        if len(x) < 5:
            continue  # insufficient points

        r, p_raw = pearsonr(x, y)
        raw_ps.append(p_raw)

        ci_low, ci_high = bootstrap_ci(x, y)

        uncertainty = df["uncertainty"].mean() if "uncertainty" in df.columns else 1.0
        snr = r / uncertainty if uncertainty != 0 else 0.0

        results.append({
            "lag": lag,
            "correlation_coefficient": r,
            "raw_p_value": p_raw,
            "confidence_interval_lower": ci_low,
            "confidence_interval_upper": ci_high,
            "region_type": "target",
            "signal_to_noise_ratio": snr
        })

    # FDR correction
    if raw_ps:
        _, p_corr, _, _ = multipletests(raw_ps, method="fdr_bh")
        for i, res in enumerate(results):
            res["corrected_p_value"] = p_corr[i]
    else:
        for res in results:
            res["corrected_p_value"] = 1.0

    return pd.DataFrame(results)

def main():
    merged_path = "data/processed/merged_monthly.csv"
    out_path = "data/processed/correlation_results.csv"
    if not os.path.exists(merged_path):
        sys.exit("Merged data not found. Run T017c first.")
    df = pd.read_csv(merged_path, parse_dates=["date"])
    results_df = analyze(df)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    results_df.to_csv(out_path, index=False)
    print(f"Correlation analysis complete. Results saved to {out_path}")

if __name__ == "__main__":
    main()
```

- [X] T023 [US2] Create contract test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_correlation_schema.py` that validates `correlation_results.csv` against `contracts/output.schema.yaml`.  
- [X] T024 [US2] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_correlation_pipeline.py` that runs the full analysis on a synthetic small dataset and asserts the output CSV contains the required columns and no NaNs.  
- [X] T020b [Sequential] Create performance‑profiling script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/03_profile_runtime.py` that (1) loads a 100‑row sample of `merged_monthly.csv`, (2) times the `analyze` function from T020, (3) extrapolates to the full dataset size, and (4) writes `docs/runtime_profile.md` with the estimate. **Depends on T020 and T017c.**

**Checkpoint**: User Stories 1 & 2 are now functional and independently testable.

---

## Phase 4: User Story 3 – Diagnostic Visualization & Sensitivity Reporting (Priority: P2)

**Goal**: Produce time‑series overlays, scatter plots with regression lines, spatial anomaly maps, and a sensitivity‑analysis report that sweeps the explicit threshold set {0.4, 0.5, 0.6}.

**Independent Test**: Verify that PNG files are generated in `output/` and that `sensitivity_report.md` contains results for each of the three thresholds.

- [X] T025 [US3] Create time‑series visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/06_visualization_timeseries.py` that plots gravity anomaly and AR intensity, saves `output/timeseries_overlay.png`, and adds the mandatory caption.
- [X] T026 [US3] Create scatter visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/07_visualization_scatter.py` that generates a regression scatter plot, saves `output/scatter_regression.png`, and includes the caption.
- [X] T027 [US3] Create spatial visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/08_visualization_spatial.py` that produces a placeholder spatial anomaly map, saves `output/spatial_anomaly_map.png`, and includes the caption.  

- [X] T028 [US3] Create sensitivity‑analysis script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/09_sensitivity_report.py`. The script () loads `correlation_results.csv`, (2) sweeps the **explicit** threshold set `{0.4, 0.5, 0.6}`, (3) for each threshold computes (a) count of correlations exceeding the threshold, (b) variance of those coefficients (stability), (c) proportion of confidence‑intervals overlapping the overall mean CI, (4) writes a markdown report `output/sensitivity_report.md` that (i) lists the three thresholds with their statistics, (ii) repeats the frame‑of‑reference disclaimer (referencing T033), and (iii) **explicitly checks** that no causal keywords appear (regex safety check).  

```python
import pandas as pd
import numpy as np
import os
import re

THRESHOLDS = [0.4, 0.5, 0.6]

def main():
    df = pd.read_csv("data/processed/correlation_results.csv")
    mean_ci_low = df["confidence_interval_lower"].mean()
    mean_ci_high = df["confidence_interval_upper"].mean()
    report_lines = ["## Sensitivity Analysis\n"]
    for t in THRESHOLDS:
        subset = df[df["correlation_coefficient"] > t]
        stability = subset["correlation_coefficient"].var() if len(subset) > 1 else 0.0
        overlap = ((df["confidence_interval_lower"] <= mean_ci_high) &
                   (df["confidence_interval_upper"] >= mean_ci_low)).mean()
        report_lines.append(
            f"- Threshold {t}: {len(subset)} correlations exceed this value. "
            f"Stability (variance): {stability:.4f}, CI overlap ratio: {overlap:.2f}"
        )
    # Frame‑of‑reference disclaimer (referencing T033)
    report_lines.extend([
        "\n## Frame of Reference and Limitations",
        "The correlation results presented in this report are based on the perturbation in gravitational potential at the GRACE‑FO satellite altitude, not the geoid height at the Earth's surface.",
        "This is a coordinate‑dependent quantity derived from spherical harmonic coefficients in the satellite's reference frame.",
        "All findings are strictly associational; no causal language is used."
    ])
    content = "\n".join(report_lines) + "\n"
    os.makedirs("output", exist_ok=True)
    out_path = "output/sensitivity_report.md"
    with open(out_path, "w") as f:
        f.write(content)
    # Safety check for causal language
    if re.search(r"causes|effect|impact|driven by|leads to|triggers", content, re.IGNORECASE):
        raise ValueError("Causal language detected in sensitivity report!")
    print(f"Sensitivity report written to {out_path}")

if __name__ == "__main__":
    main()
```

- [X] T029 [US3] Create temporal‑bias documentation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/10_temporal_bias_analysis.py` that (1) compares monthly vs. simulated sub‑monthly aggregation, (2) reports the bias in correlation coefficient, and (3) writes `output/temporal_bias_analysis.md`.  
- [X] T030 [US3] Create output‑validation test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_output_schema.py` that checks `output/sensitivity_report.md` for absence of causal keywords.  
- [X] T031 [US3] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_visualization_pipeline.py` that runs the three visualization scripts and the sensitivity‑analysis script, then asserts that the three PNG files and the markdown report exist.  

**Checkpoint**: All user stories now independently functional.

---

## Phase 5: Polish & Cross‑Cutting Concerns

**Purpose**: Final refinements affecting multiple stories and overall validation.

⚠️ **DEPENDS**: All Phase 2‑4 tasks must be complete. T040 depends on T017c, T020, T020b. T045-T047 depend on the existence of `quickstart.md` and the actual scripts.

- [X] T037 [P] Create `README.md` with installation, data‑source URLs, run commands (including the corrected quick‑start steps), and expected outputs.  
- [X] T038 Run all contract tests to verify schema compliance.  
- [X] T039 Run all integration tests to verify end‑to‑end pipeline execution.  
- [X] T040 [P] Measure aggregate pipeline runtime. The script reads the estimated full‑run time from `docs/runtime_profile.md` (generated by T020b), compares it against the specified time limit, and writes `docs/runtime_report.md` indicating PASS/FAIL. **Prerequisites**: T017c (merged_monthly.csv), T020 (correlation_results.csv), T020b (runtime_profile.md) must be complete. **Full script:**  
```python
import os
import sys

PROFILE_PATH = "docs/runtime_profile.md"
REPORT_PATH = "docs/runtime_report.md"
LIMIT_SECONDS = 6 * 3600

def parse_estimate(path):
    with open(path) as f:
        for line in f:
            if line.startswith("- Estimated full runtime:"):
                # format: - Estimated full runtime: X.XXs (Y.YY hours)
                parts = line.split(":")[1].strip().split("s")[0]
                return float(parts)
    sys.exit("Could not parse runtime estimate from profile.")

def main():
    if not os.path.exists(PROFILE_PATH):
        sys.exit("Runtime profile missing. Run T020b first.")
    est = parse_estimate(PROFILE_PATH)
    status = "PASS" if est <= LIMIT_SECONDS else "FAIL"
    with open(REPORT_PATH, "w") as f:
        f.write("# Runtime Report\n\n")
        f.write(f"- Estimated full runtime: {est:.2f}s ({est/3600:.2f} hours)\n")
        f.write(f"- Constraint (≤ 6 h): {status}\n")
    print(f"Runtime report written to {REPORT_PATH} – {status}")

if __name__ == "__main__":
    main()
```

- [X] T041 [P] Document SHA‑256 checksums for all raw data files in `state/projects/PROJ-267-exploring-the-relationship-between-atmos.yaml`.  
- [X] T042 [P] Verify that all dataset URLs in `config/urls.yaml` are reachable and that `docs/methodology.md` lists them.  
- [X] T043 [P] Update the project‑state YAML with a fresh `updated_at` timestamp and content hashes for every artifact.  
- [X] T044 Run quickstart validation: `python code/09_sensitivity_report.py --validate && pytest tests/contract/test_output_schema.py`.  
- [X] T045 [P] Reconcile run‑book vs implementation: **Update `quickstart.md`** to invoke the existing scripts (`06_visualization_timeseries.py`, `09_sensitivity_report.py`, etc.) instead of the non‑existent `04_visualization.py`. **Verification**: `quickstart.md` must contain `code/06_visualization_timeseries.py` and `code/09_sensitivity_report.py`.
- [X] T046 [P] Reconcile run‑book vs implementation: **Update `quickstart.md`** to invoke `09_sensitivity_report.py` (the actual script) instead of the missing `05_sensitivity_report.py`. **Verification**: `quickstart.md` must NOT contain `05_sensitivity_report.py`.
- [X] T047 [P] Reconcile run‑book vs implementation: **Remove or replace the reference to `verify_completeness.py`** in `quickstart.md` with a call to the existing contract test suite (`pytest tests/contract/`). **Verification**: `quickstart.md` must contain `pytest tests/contract/` and NOT `verify_completeness.py`.

**All tasks complete – the feature is ready for final review.**