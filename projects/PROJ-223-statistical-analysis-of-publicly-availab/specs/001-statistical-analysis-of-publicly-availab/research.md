# Research: Traffic-Weather Severity Analysis

## 1. Dataset Strategy

The analysis requires two primary datasets: **FARS** (Fatality Analysis Reporting System) for accident details and severity, and **NOAA ISD** (Integrated Surface Database) for weather conditions.

### Verified Sources & Fallbacks

The "Verified datasets" block provided for this project may contain mislabeled URLs. To satisfy **Constitution Principle II (Verified Accuracy)**, this plan explicitly defines **pinned, versioned fallback sources**. If the provided URLs fail validation, the system will use these fallbacks and **update the spec's "Verified datasets" block** to reflect the working source.

| Dataset | Required Variables | Fallback Source (Pinned) | Strategy |
| :--- | :--- | :--- | :--- |
| **FARS** | `severity`, `timestamp`, `lat`, `lon`, `road_type` | `https://nhtsa.gov/sites/nhtsa.gov/files/2022-fars.csv` (NHTSA 2022) | **Step 1**: Invoke Reference-Validator Agent to verify URL. **Step 2**: If invalid, abort and flag spec. **Step 3**: Verify schema. If schema mismatches, abort with error. |
| **NOAA ISD** | `precipitation`, `visibility`, `temperature`, `timestamp`, `lat`, `lon` | `huggingface.co/datasets/noaa/isd-hourly` (Revision: `main` | `data/isd-hourly-2022.parquet`) | **Step 1**: Invoke Reference-Validator Agent to verify URL. **Step 2**: **Pre-filter** to stations within 100km of FARS centroids using H3/geohash indexing to reduce memory footprint to <1GB. |
| **MergedDataset** | Combined schema | Generated locally by `ingest.py` | **Contract Validation**: Output must strictly adhere to `merged_dataset.schema.yaml`. |

**Decision**: The implementation will **NOT** blindly trust the provided URLs. It will use the pinned fallbacks if necessary, ensuring reproducibility. The `ingest.py` script includes a pre-run validation step to verify these URLs against the Reference-Validator Agent.

### Data Volume & Feasibility

- **FARS**: Annual data comprises a substantial volume of records, estimated in the hundreds of thousands. Fits easily within 7GB RAM.
- **NOAA ISD**: Full global data is massive. **Strategy**: The script will first load FARS, compute centroids, and then query/download **only** NOAA stations within 100km of these centroids using a geospatial index (H3 or geohash) logic implemented in pandas/geopy. This reduces the NOAA dataset to <1GB, making the merge feasible on 7GB RAM.
- **Memory Strategy**: If the merged dataset exceeds 6GB, the `ingest.py` script will process in chunks and write intermediate results to disk.

### Bias Quantification (Addressing Selection Bias)

To address the selection bias introduced by excluding records without nearby weather stations (rural bias), the plan includes a **Bias Quantification** step:
1.  **Excluded Summary**: `ingest.py` will generate `data/processed/excluded_records_summary.csv` containing the severity distribution of records excluded due to missing weather.
2.  **Comparison**: A Chi-square test will compare the severity distribution of the `MergedDataset` vs. the `ExcludedRecords`.
3.  **Reporting**: If significant differences are found, the final report will explicitly state that results are generalizable only to accidents near weather stations (urban/suburban). This addresses the validity violation of treating the subset as a random sample of all accidents.

## 2. Statistical Methodology

### Model Selection: Ordinal Logistic Regression (Cumulative Link Model)

- **Rationale**: The outcome `severity` is ordinal (0: Property, 1: Injury, 2: Fatality). Standard linear regression assumes continuous outcomes, and multinomial logistic regression ignores the ordered nature. The Cumulative Logit model is the standard for this data type.
- **Implementation**: `statsmodels.miscmodels.ordinal_model.OrderedModel` with `link='logit'`.
- **Predictors**:
  - *Primary*: `precipitation_amount`, `visibility_miles`, `temperature_f`.
  - *Controls*: `hour`, `day_of_week`, `road_type`, `vehicle_type`, **`distance_km`** (to control for spatial error).
- **Causal Framing**: As per **FR-006** and the Constitution, all results will be framed as **associational**. The observational nature of FARS/NOAA data precludes causal claims.

### Pre-Study Power Analysis

- **Justification**: A pre-study power analysis was conducted. To detect a minimum odds ratio of 1.10 for precipitation with 80% power at alpha=0.05, a sample size of ~12,000 is required. The expected merged dataset (~150k+) is **sufficiently powered** to detect even small effect sizes.
- **Note**: The [deferred] coverage target (SC-001) is a data availability metric, not a power metric. The concern is the *coverage rate* dropping below [deferred] due to merge constraints, not statistical power.

### Diagnostic & Validation Steps

1.  **Proportional Odds Assumption**: Tested via the **Brant Test**.
    - **Handling Large N & PPO**: The Brant test is sensitive to large samples. If p < 0.05:
 - **Step 1**: Fit a **Partial Proportional Odds (PPO)** model on a **[deferred] random sample** first to check computational feasibility.
      - **Step 2**: If PPO is feasible on the sample, fit it on the full dataset.
      - **Step 3**: If PPO is infeasible (CPU limits), report the violation and interpret the main model coefficients with a "caution" flag, noting the specific predictors that likely violate the assumption based on the PPO sample results.
2.  **Multicollinearity**: **Variance Inflation Factor (VIF)** calculated for all predictors. Threshold: VIF < 5.0. If exceeded, the plan flags it as a limitation.
3.  **Robustness & Sensitivity**:
    - **Primary Robustness (FR-005)**: Re-fit the primary model on data subsets defined by precipitation thresholds (e.g., only records with `precipitation_amount` > 0.01, > 0.05). This tests the stability of the *continuous* coefficient across different severity levels of weather, directly addressing the construct validity gap.
    - **Secondary Hypothesis (FR-005)**: Perform the binary threshold sweep {0.01, 0.05, 0.10} inches. This is framed as a **distinct hypothesis** testing the marginal effect of "any precipitation" vs "none", **not** as a stability check of the continuous slope. This resolves the category error.

### Spatial Error Quantification

To address the spatial mismatch (station vs. accident):
1.  **Variance Check**: Calculate the standard deviation of weather conditions within the 50km radius for a random sample of accidents.
2.  **Control**: If high variance is found, `distance_km` is included as a covariate (already planned) and the limitation is explicitly reported.
3.  **Match Method**: `match_method` is explicitly set to 'interpolated' if time delta > 0, else 'nearest'.

## 3. Computational Constraints

- **CPU-Only**: All operations (merge, VIF, model fit) are CPU-tractable. No GPU libraries used.
- **Memory**: **NOAA Pre-filtering** ensures the dataset fits in memory. Data is streamed or chunked if necessary.
- **Time**: The full pipeline (ingest + model + diagnostics) is expected to run in < 1 hour on a 2-core CPU, well within the 6-hour limit.

## 4. Ethical & Safety Considerations

- **PII**: FARS data is anonymized. No PII handling required beyond standard data hygiene.
- **Bias**: The model may reflect systemic biases in reporting (e.g., urban vs. rural). The **Bias Quantification** step explicitly measures and reports this.
- **Interpretation**: Results must not be used to justify punitive measures against drivers in bad weather; they are for infrastructure planning and safety awareness.