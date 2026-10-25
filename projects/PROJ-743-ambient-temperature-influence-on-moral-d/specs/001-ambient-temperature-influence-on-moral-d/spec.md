# Feature Specification: Ambient Temperature Influence on Moral Decision Speed

**Feature Branch**: `001-ambient-temp-moral-speed`  
**Created**: 2026-06-21  
**Status**: Draft  
**Input**: User description: "Ambient Temperature Influence on Moral Decision Speed"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Temperature Matching (Priority: P1)
(Identifier: US-1)

The system must ingest the Moral Machine dataset and successfully match each response record with historical ambient temperature data from ERA5 Reanalysis based on geographic coordinates and timestamps.

**Why this priority**: This is the foundational data layer. Without accurate temperature variables linked to specific moral decisions, no statistical analysis can occur. It is the prerequisite for all subsequent modeling.

**Independent Test**: Can be fully tested by running the ingestion script on a small, known subset of the Moral Machine data and verifying that every output record contains a valid temperature value within a reasonable geographic range and that no records are dropped due to missing location data.

**Acceptance Scenarios**:

1. **Given** a valid Moral Machine CSV file and access to ERA5 hourly reanalysis data for 2014‑2018, **When** the ingestion script runs, **Then** the percentage of original records successfully matched with ERA5 temperature data is measured against the total number of records with valid location data.
2. **Given** a record with ambiguous location data (e.g., missing latitude/longitude), **When** the script processes the record, **Then** the record is flagged in a `data_quality_log` and excluded from the primary analysis dataset.
3. **Given** a record where the timestamp falls outside the available ERA5 coverage period, **When** the script processes the record, **Then** the record is excluded and logged with the reason "ERA5 coverage gap".

---

### User Story 2 - Mixed-Effects Regression Modeling (Priority: P2)
(Identifier: US-2)

The system must fit a linear mixed‑effects model (with log‑transformed response times) to quantify the association between ambient temperature and moral decision response time, controlling for participant ID, cultural region, latitude, dilemma complexity, and response type.

**Why this priority**: This addresses the core research question. It transforms the raw data into a statistical estimate of the temperature effect, directly testing the hypothesis while accounting for the non‑normal distribution of reaction times and potential confounds.

**Independent Test**: Can be fully tested by running the modeling script on the pre‑processed dataset and verifying that the model converges, produces a coefficient for `temperature_celsius`, and reports a p‑value for the fixed effect.

**Acceptance Scenarios**:

1. **Given** the merged dataset with temperature and response time, **When** the regression model is fitted, **Then** the output includes a fixed‑effect coefficient for `temperature_celsius` with a standard error and p‑value.
2. **Given** the model output, **When** the likelihood‑ratio test is performed against a null model (without temperature), **Then** the test statistic and p‑value are recorded in the results log.
3. **Given** the fitted model, **When** residuals are analyzed, **Then** diagnostic plots (QQ‑plot, residual vs. fitted) are generated to assess normality and homoscedasticity assumptions of the transformed data.

---

### User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)
(Identifier: US-3)

The system must execute robustness checks, including alternative temperature metrics (e.g., 3‑hour moving average), sensitivity analysis on temperature thresholds, and a specific analysis for the indoor/outdoor confound, to ensure the findings are not artifacts of specific data choices.

**Why this priority**: This validates the reliability of the P2 results. It ensures the observed effect is robust to minor variations in data processing, modeling assumptions, and the validity of the temperature proxy.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces a summary table comparing the primary model results with alternative specifications.

**Acceptance Scenarios**:

1. **Given** the primary model results, **When** the robustness script runs, **Then** it generates a comparison table showing the temperature coefficient and p‑value for at least two alternative temperature metrics (e.g., raw hourly vs. 3‑hour moving average).
2. **Given** a decision cutoff for temperature outliers, **When** the sensitivity analysis runs, **Then** it sweeps the cutoff threshold over 2, 3, and 4 standard deviations and reports how the headline temperature coefficient varies.
3. **Given** the full analysis pipeline, **When** it completes, **Then** all generated figures (scatter plots, conditional effect plots) are saved to the `results/` directory in a standard format (e.g., PNG).

---

### Edge Cases

- What happens when the ERA5 grid cell nearest to a Moral Machine response location is >100 km away? (System MUST flag this as a "low confidence match" and log the reason "distance > 100 km" in the data quality log, then exclude the record). This safeguard ensures temperature assignments are reliable.
- How does the system handle response times that are physically impossible (e.g., <100 ms or >10 000 ms)? (If a response‑time field is present, the system MUST apply a hard filter to remove these outliers before modeling).
- What happens if the temperature data contains missing values for a specific hour? (System should interpolate linearly or use the nearest available hourly reading, but only if the gap is ≤2 hours; otherwise, exclude the record).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest the Moral Machine dataset and merge it with ERA5 hourly reanalysis temperature data (2014‑2018) using geographic coordinates **and** timestamps as keys, and must validate that the source meets the hourly‑resolution standard (see `contracts/moral_temperature.schema.yaml`). *Justification*: ERA provides hourly fine‑scale grid resolution, which is essential for precise temporal‑spatial matching; NOAA GSS lacks the required hourly granularity. (See US-1)
- **FR-002**: System MUST filter out records with temperature values outside the extreme range **−10 °C ≤ temperature ≤ 40 °C**. (See US-1)
- **FR-003**: System MUST fit a linear mixed‑effects model with log‑transformed response time as the dependent variable, ambient temperature as the fixed effect, and random intercepts for participant ID and cultural region. (See US-2)
- **FR-004**: System MUST include covariates for participant age (if available at aggregate country level), gender (if available at aggregate country level), dilemma complexity score, time‑of‑day, and latitude (to control for regional climate gradients) in the primary regression model. (See US-2)
- **FR-005**: System MUST perform a likelihood‑ratio test comparing the full model (with temperature) to a null model (without temperature) to assess statistical significance. (See US-2)
- **FR-006**: System MUST execute a sensitivity analysis that sweeps the temperature outlier threshold over **2, 3, 4 standard deviations** and reports the variation in the temperature coefficient. (See US-3)
- **FR-007**: System MUST generate diagnostic plots for model residuals (QQ‑plot and residual vs. fitted) to verify normality and homoscedasticity assumptions of the transformed data. (See US-2)
- **FR-008**: System MUST export all results, including model coefficients, p‑values, and generated figures, to the `results/` directory in a reproducible format. (See US-3)
- **FR-009**: System MUST flag or exclude records where the distance to the nearest ERA5 grid point exceeds 100 km and log the reason "distance > 100 km" (see `exclusion_log.schema.yaml`). (See US-1)
- **FR-010**: If response‑time data is present, System MUST filter out response times **< 100 ms** or **> 10 000 ms** before any modeling occurs. (See US-1)
- **FR-011**: System MUST compute a **dilemma complexity metric** that is *derived independently of response time*:  
  1. **Lives at stake** – sum of all lives indicated as potentially saved or sacrificed in the scenario.  
  2. **Difficulty score** – a categorical value (Low, Medium, High) based solely on scenario attributes (e.g., number of parties involved, presence of children, vehicular vs. pedestrian victims).  
  The final complexity score is the numeric sum of lives at stake plus a numeric mapping of the difficulty score (Low = 0, Medium = 1, High = 2). This procedure uses only the scenario description and does not reference any response‑time field, satisfying testability. (See US-2)
- **FR-012**: System MUST assess the indoor/outdoor confound as follows:  
  *If* GHSL urban/rural classification is available, stratify the dataset by this label and compute the temperature coefficient within each stratum; report the change in R² between stratified and unstratified models.  
  *If* GHSL is unavailable, perform a **bootstrap robustness check**: repeatedly (1,000 resamples) assign a random urban/rural label preserving overall proportions, re‑fit the model, and record the distribution of the temperature coefficient. Report the 95 % confidence interval width of this distribution as the **noise impact metric**. This explicit method makes the requirement verifiable. (See US-3) *Justification*: Controlling for indoor/outdoor context is essential to avoid confounding ambient temperature with exposure conditions.
- **FR-013**: System MUST test for non‑linearity in the temperature effect by including a quadratic term (`temperature_celsius^2`) and compare model fit against the linear‑only model using AIC; retain the model with lower AIC. *Justification*: Prior literature suggests possible inverted‑U relationships between temperature and cognitive speed, so testing curvature is essential for valid inference. (See US-2)
- **FR-014**: System MUST validate all data sources against the project's constitution 'Verified Accuracy' principle and **reject** any source that does not meet the hourly‑resolution standard before ingestion. (See US-1)
- **FR-015**: System MUST conduct a pre‑study power analysis (α = 0.05, target power = 0.8) based on an expected small effect size (Cohen’s d ≈ small) and report the required sample size; the analysis must be documented in `results/power_analysis.txt`. *Justification*: Ensures the corpus is sufficiently large to detect the hypothesized small temperature effect, aligning with the core research question. (See US-2)
- **FR-016**: System MUST obtain response‑time measurements from an auxiliary crowdsourced experiment (e.g., a short online study replicating a subset of Moral Machine scenarios) and merge these latency values with the Moral Machine records using scenario ID and participant pseudonym. This provides the necessary outcome variable for the speed hypothesis. (See US-2)
- **FR-017**: System MUST treat `data/processed/merged_dataset.parquet` as the **single source of truth** for all downstream analysis steps, satisfying Constitution Principle I. (See US-1)
- **FR-018**: System MUST validate the merged dataset against the `contracts/moral_temperature.schema.yaml` contract and log any schema violations before modeling. (See US-1)

### Key Entities

- **Moral Response**: A single decision event containing participant ID, location coordinates, timestamp, dilemma ID, *optional* response time (sourced from the auxiliary experiment defined in FR‑016), and demographic data.
- **Temperature Record**: A meteorological data point containing grid ID, timestamp, latitude, longitude, and ambient temperature in Celsius.
- **Merged Dataset**: The combined entity linking Moral Responses to Temperature Records, serving as the input for statistical modeling. Conforms to `contracts/moral_temperature.schema.yaml`.
- **Model Output**: The statistical result containing fixed‑effect coefficients, standard errors, p‑values, and random effect variances.
- **Dilemma Complexity**: A metric derived as described in FR‑011, based solely on scenario attributes and lives at stake, explicitly excluding any response‑time information.
- **Indoor/Outdoor Classification**: GHSL urban/rural label when available; otherwise handled via the bootstrap robustness method in FR‑012.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage of Moral Machine records successfully matched with ERA5 temperature data is measured against the total number of records with valid location data. (See US-1)
- **SC-002**: The statistical significance of the temperature coefficient (p‑value) is measured against a standard alpha threshold **α = 0.05** to determine if the association is non‑zero. (See US-2)
- **SC-003**: The variation in the temperature coefficient across the sensitivity analysis thresholds is measured against the primary model coefficient to assess robustness. (See US-3)
- **SC-004**: The convergence status of the mixed‑effects model is measured against the requirement of successful optimization (no convergence warnings) to ensure valid inference. (See US-2)
- **SC-005**: Normality of model residuals is assessed with the Shapiro‑Wilk test on a random sample of size **min(500, N_residuals)** and requires **p > 0.05** to indicate a good fit; visual inspection of QQ‑plots supplements this check. (See US-2)

## Assumptions

- The Moral Machine dataset contains sufficient geographic and timestamp granularity to be matched with hourly ERA5 temperature data for at least 90 % of the records.
- The relationship between ambient temperature and response time may be non‑linear (e.g., inverted‑U), justifying the inclusion of quadratic terms or spline testing.
- The ERA reanalysis provides accurate hourly temperature estimates for the specific locations and times of the Moral Machine responses (covering the study period).
- The GitHub Actions free‑tier runner (multiple CPU cores, sufficient RAM) is sufficient to process the merged dataset and fit the mixed‑effects model without memory overflow or timeout, provided the dataset is sampled if necessary.
- The "dilemma complexity score" and "time‑of‑day" covariates are either present in the Moral Machine dataset or can be derived from the available data without introducing circularity.
- Any observed association between temperature and response time is correlational; the design does not support causal claims due to the observational nature of the data (no random assignment of temperature).
- The auxiliary crowdsourced experiment (FR‑016) will reliably capture response latency for a representative subset of scenarios, enabling the speed analysis.
- The "3‑hour moving average" temperature metric is a valid proxy for the thermal environment experienced by the participant during the decision‑making task.
- The micro‑climate (indoor vs. outdoor) effect is addressed using GHSL urban/rural classification when available; otherwise, its potential impact is quantified via the bootstrap robustness check defined in FR‑012.
