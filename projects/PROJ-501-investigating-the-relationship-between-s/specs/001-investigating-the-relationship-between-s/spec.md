# Feature Specification: Investigating the Relationship Between Stellar Flare Frequency and Exoplanet Atmospheric Retention

**Feature Branch**: `001-stellar-flare-atmospheric-retention`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Stellar Flare Frequency and Exoplanet Atmospheric Retention"

## User Scenarios & Testing

### User Story 1 - Retrieve and Filter Multi-Source Astrophysical Data (Priority: P1)

The researcher needs to automatically retrieve stellar flare event catalogs from MAST (TESS data) and exoplanet physical parameters from the NASA Exoplanet Archive, then filter this combined dataset to include only valid targets (M-dwarf hosts with ≥10 flare events) to establish the foundation for analysis.

**Why this priority**: Without a clean, filtered dataset linking specific flare histories to specific planetary parameters, no statistical analysis can be performed. This is the prerequisite for all subsequent modeling and correlation testing.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying that the output CSV contains exactly the expected columns (star ID, flare count, planet radius, planet mass, semi-major axis, host density) and that the row count matches the expected number of M-dwarf systems with sufficient flare history, without running any statistical models.

**Acceptance Scenarios**:

1. **Given** the MAST and NASA Exoplanet Archive APIs are accessible, **When** the script executes the retrieval and filtering logic, **Then** the output CSV contains only planets orbiting M-dwarf hosts with ≥10 recorded flare events, and all required physical parameters (radius, mass, semi-major axis, density) are populated with no null values.
2. **Given** a star in the TESS catalog has <10 flare events, **When** the filtering logic runs, **Then** that star and any associated planets are excluded from the final dataset.
3. **Given** the NASA Exoplanet Archive returns a planet with missing mass or radius data, **When** the script processes the record, **Then** that specific planet entry is excluded or flagged as invalid to prevent division-by-zero errors in the density calculation.

---

### User Story 2 - Compute Cumulative XUV Flux and Model Mass Loss (Priority: P2)

The researcher needs to calculate the cumulative high-energy (XUV) flux received by each filtered planet based on flare frequency and host luminosity, then apply the energy-limited escape model to derive an estimated atmospheric mass loss rate for each planet (used for internal validation, not the primary hypothesis test).

**Why this priority**: This transforms raw observational data into the specific physical quantities required to test the research hypothesis. It is the core scientific computation of the project.

**Independent Test**: Can be fully tested by running the calculation module on a small, hardcoded subset of known values (e.g., a synthetic planet with defined flare rate and distance) and verifying the output matches the manually calculated mass loss rate using the standard energy-limited escape formula (with K_tide=1.0, f_XUV=0.1) within a 1% tolerance.

**Acceptance Scenarios**:

1. **Given** a planet with known flare frequency, host star luminosity, and orbital distance, **When** the flux calculation module runs, **Then** the cumulative XUV flux is computed and stored with units of erg/s/cm².
2. **Given** the cumulative XUV flux and planetary parameters, **When** the energy-limited escape model runs, **Then** the atmospheric mass loss rate (kg/s) is calculated using the standard efficiency factor (η = 0.15) and K_tide = 1.0, and stored.
3. **Given** a dataset with 100 planets, **When** the computation completes, **Then** the output CSV contains a new column `mass_loss_rate_kg_s` with no NaN values for valid inputs.

---

### User Story 3 - Perform Statistical Correlation and Visualization (Priority: P3)

The researcher needs to perform a Spearman rank correlation test between cumulative flare flux and an independent measure of atmospheric retention (planetary density), determine statistical significance (p-value), and generate a scatter plot with a regression line to visualize the relationship.

**Why this priority**: This delivers the final scientific answer to the research question. It validates whether the observed data supports the theoretical hypothesis of a negative correlation between high-energy flux and atmospheric retention (density), avoiding the tautology of correlating flux with its own derived mass loss.

**Independent Test**: Can be fully tested by running the analysis script on the generated dataset and verifying that the output includes a correlation coefficient (ρ) and p-value for the relationship between XUV flux and planetary density, and that a PNG plot file is generated showing the data points and a trend line.

**Acceptance Scenarios**:

1. **Given** the final dataset with flux and planetary density columns, **When** the statistical test runs, **Then** the Spearman rank correlation coefficient (ρ) and p-value are calculated and printed to the console and saved to a results JSON file.
2. **Given** the correlation results, **When** the visualization module runs, **Then** a scatter plot is generated with Cumulative XUV Flux on the X-axis and Planetary Density on the Y-axis, including a regression line and axis labels.
3. **Given** the p-value is < 0.05, **When** the results are summarized, **Then** the output explicitly states "Statistically significant correlation detected" (sign depends on ρ).

### Edge Cases

- What happens if the MAST API returns no flare events for a known M-dwarf? (System must exclude the star to avoid division by zero in flux calculation).
- How does the system handle planets with extremely high eccentricity where the "semi-major axis" approximation for flux fails? (System must flag or exclude these to maintain model validity).
- What if the energy-limited model yields a mass loss rate exceeding 10% of the planet's total mass per Gyr? (System must flag the result as "unphysical" and exclude that data point from the statistical analysis to prevent skewing the correlation).
- How does the system handle API rate limits from NASA Exoplanet Archive during bulk retrieval? (System must implement a retry mechanism with exponential backoff, max 3 attempts).

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve stellar flare catalogs from MAST and exoplanet parameters from the NASA Exoplanet Archive via API or `wget` and merge them by host star ID. (See US-1)
- **FR-002**: System MUST filter the merged dataset to include only systems where the host star is an M-dwarf and has ≥10 recorded flare events. (See US-1)
- **FR-003**: System MUST calculate cumulative XUV flux for each planet using the formula $F_{XUV} = \sum (E_{flare} \times f_{XUV} / (4 \pi a^2))$, where $E_{flare}$ is the bolometric flare energy in ergs, $f_{XUV}$ is a fixed conversion factor of 0.1, and $a$ is the semi-major axis in cm. The output MUST be in erg/s/cm². (See US-2)
- **FR-004**: System MUST estimate atmospheric mass loss rates using the energy-limited escape model $\dot{M} = \frac{\epsilon \pi R_p^3 F_{XUV}}{G M_p K_{tide}}$ with a fixed efficiency $\epsilon = 0.15$, $K_{tide} = 1.0$, and $G$ as the gravitational constant. (See US-2)
- **FR-005**: System MUST perform a Spearman rank correlation test between cumulative XUV flux and planetary density (calculated as $M_p / \frac{4}{3}\pi R_p^3$) and report the coefficient (ρ) and p-value. (See US-3)
- **FR-006**: System MUST generate a scatter plot visualizing the relationship between flux and planetary density with a regression line. (See US-3)
- **FR-007**: System MUST handle API rate limiting by implementing a retry mechanism with exponential backoff (max 3 attempts, initial delay 1s) before failing. (See US-1)
- **FR-008**: System MUST flag and exclude any data point where the calculated mass loss rate exceeds 10% of the planet's total mass per Gyr, marking it as "unphysical" in the output log. (See US-2)

### Key Entities

- **FlareEvent**: Represents a single stellar flare detection (attributes: star_id, timestamp, energy [erg], duration).
- **ExoplanetSystem**: Represents a planet orbiting a host star (attributes: planet_id, star_id, radius [cm], mass [g], semi_major_axis [cm], host_type, density [g/cm³]).
- **AnalysisResult**: Represents the computed metrics for a single system (attributes: star_id, cumulative_flux, mass_loss_rate, density, is_valid).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Spearman rank correlation coefficient (ρ) and p-value between XUV flux and planetary density are measured and reported. The methodological validity is measured against the requirement that the correlation uses an independent observable (density) rather than a derived quantity. (See US-3)
- **SC-002**: The dataset completeness is measured against the requirement that every retained planet has non-null values for radius, mass, semi-major axis, flare count, and density. (See US-1)
- **SC-003**: The mass loss rate calculation accuracy is measured against a manual verification of the energy-limited escape formula using a synthetic test case (with K_tide=1.0, f_XUV=0.1). (See US-2)
- **SC-004**: The algorithmic complexity of the data processing pipeline is measured against O(N log N) to ensure scalability for datasets up to 100,000 records. (See US-2, US-3)

### Methodological Soundness & Compute Feasibility

- **SC-005**: The analysis frames findings as **associational** only, explicitly avoiding causal language in the final report, as the design is observational (no random assignment). (See US-3)
- **SC-006**: The dataset variable fit is verified by confirming the TESS flare catalog and NASA Exoplanet Archive contain all required variables (flare energy, star luminosity, planet radius, planet mass, semi-major axis); if any are missing, a `[NEEDS CLARIFICATION]` marker is inserted. (See US-1)
- **SC-007**: The analysis uses only CPU-tractable methods (Python `scipy`, `numpy`, `astropy`) without GPU acceleration, quantization, or large-model inference to ensure execution on 2 CPU cores / 7 GB RAM. (See US-2, US-3)
- **SC-008**: No multiple-comparison correction is required as the primary hypothesis is a single correlation test; if sub-group analyses are added, a family-wise error correction (e.g., Bonferroni) MUST be applied. (See US-3)
- **SC-009**: The correlation test (FR-005) must utilize planetary density as the dependent variable to ensure the hypothesis test is not a tautology of the flux calculation. (See US-3)

## Assumptions

- The MAST archive and NASA Exoplanet Archive APIs will remain accessible and stable during the CI runtime window.
- The energy-limited escape model with a fixed efficiency factor ($\epsilon = 0.15$) and a fixed tidal efficiency factor ($K_{tide} = 1.0$) is a sufficient approximation for the initial empirical correlation study.
- The sample size of M-dwarf exoplanets with ≥10 recorded flares in the TESS catalog is sufficient (>30) to perform a meaningful Spearman correlation test.
- The "cumulative XUV flux" can be reasonably approximated by summing the bolometric energy of detected flares and applying a fixed conversion factor ($f_{XUV} = 0.1$), ignoring the quiescent XUV emission of the star which is assumed to be secondary to flare-driven erosion for this specific hypothesis.
- The GitHub Actions runner provides at least 7 GB of RAM and 14 GB of disk space, and the entire dataset (flares + planets) fits within this memory footprint without requiring chunked processing.
- The efficiency factor $\epsilon = 0.15$ and tidal factor $K_{tide} = 1.0$ are treated as community-standard defaults for this initial study; sensitivity analysis on these parameters is out of scope for the initial correlation but noted as a future work.