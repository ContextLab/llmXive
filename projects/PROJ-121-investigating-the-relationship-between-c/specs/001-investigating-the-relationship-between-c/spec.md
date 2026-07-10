# Feature Specification: Cosmic Ray Anisotropy Solar‑Cycle Modulation

**Feature Branch**: `[###-cosmic-ray-anisotropy-solar-cycle]`  
**Created**: 2026‑06‑24  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Cosmic Ray Anisotropy and Solar Cycle Variations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – End‑to‑end Data Pipeline (Priority: P1)

A researcher wants to run a fully automated pipeline that downloads the IceCube and Pierre Auger public event data for the 2010‑2020 interval, retrieves solar‑activity indices from NOAA, and outputs a time‑series of dipole amplitude and phase for each 27‑day (Carrington) interval.

**Why this priority**: This story delivers the core scientific asset – a reproducible, calibrated anisotropy time‑series – without which any subsequent analysis is impossible.

**Independent Test**: Execute the pipeline on a fresh GitHub Actions runner; verify that (a) all three data sources are downloaded, (b) a HEALPix sky map (Nside 64) is produced for each interval, and (c) a CSV file containing dipole amplitude, phase, and timestamp is generated with ≥ 95 % of expected rows (i.e., ≤ 5 % missing intervals).

**Acceptance Scenarios**:

1. **Given** a clean runner environment, **When** the `run_all.sh` script is invoked, **Then** the script finishes within 6 hours, the output CSV contains ≥ 115 rows (≈10 years ÷ 27 days), and a log reports “Data acquisition completed” without errors.  
2. **Given** a corrupted or missing IceCube file, **When** the script reaches the download step, **Then** it retries up to 3 times, logs a warning, and proceeds using the available Auger data, still producing a CSV with ≥ 90 % of rows.

---

### User Story 2 – Statistical Correlation & Significance (Priority: P2)

A scientist wants to apply Lomb‑Scargle periodograms and block‑bootstrap cross‑correlations to the dipole amplitude series and to each solar proxy (sunspot number, solar‑wind speed, IMF magnitude), obtaining quantitative significance values.

**Why this priority**: This story directly tests the hypothesis and yields the primary quantitative result (e.g., a 3 σ detection or a robust upper limit).

**Independent Test**: Run the `analyze_correlation.py` module on the CSV from Story 1; verify that it outputs (a) a periodogram with a peak at approximately a decadal timescale, (b) Pearson/Spearman coefficients with associated p‑values, and (c) a Monte‑Carlo false‑alarm probability (FAP) ≤ 0.01 for any claimed correlation.

**Acceptance Scenarios**:

1. **Given** a complete dipole‑amplitude CSV and solar‑proxy series, **When** the analysis script is executed, **Then** it produces a PDF containing (i) a Lomb‑Scargle plot showing a peak at the solar‑cycle frequency with power ≥ 3 σ above the noise floor, (ii) cross‑correlation coefficients ≥ 0.4 (or ≤ ‑0.4) with p‑value ≤ 0.01, and (iii) a Monte‑Carlo FAP ≤ 0.01.  
2. **Given** a deliberately shuffled dipole series, **When** the script runs, **Then** the reported FAP exceeds a conventional significance threshold, demonstrating that the test correctly identifies lack of correlation.

---

### User Story 3 – Reproducible Reporting & Packaging (Priority: P3)

A collaborator wants a single command that regenerates all figures, tables, and a short LaTeX report, and bundles the environment specifications so the analysis can be rerun on any compatible CI platform.

**Why this priority**: This story ensures transparency, facilitates peer review, and satisfies the project’s reproducibility requirement.

**Independent Test**: Invoke `make_report.sh` on a fresh runner; confirm that (a) all figures (time‑series, heat‑maps, periodograms) are saved as PNG/SVG, (b) `report.pdf` compiles without LaTeX errors, and (c) `requirements.txt` lists exact package versions used.

**Acceptance Scenarios**:

1. **Given** the pipeline output and analysis results, **When** `make_report.sh` is run, **Then** a PDF report of ≤ 25 pages is generated within 30 minutes, containing a summary of methods, quantitative results, and all visualizations, and the GitHub Actions log records “Report built successfully”.  
2. **Given** a missing `requirements.txt`, **When** the script attempts to set up the environment, **Then** it aborts with a clear error message “requirements.txt not found – cannot guarantee reproducibility”.

---

### User Story 4 – Configurable Temporal Binning (Priority: P2)

A researcher wants to experiment with different temporal bin sizes (e.g., 14, 27, 54 days) to test the sensitivity of the anisotropy signal to the chosen interval length.

**Why this priority**: Enables systematic checks of bin‑size dependence, directly exercising Functional Requirement **FR‑010** (configurable bin size).

**Independent Test**: Run the pipeline with `--bin-size 14` and `--bin-size 54` and verify that the generated CSV contains the expected number of intervals (≥ 90 % of the theoretical count) and that the log records the selected bin size.

**Acceptance Scenarios**:

1. **Given** a clean runner environment, **When** `run_all.sh --bin-size 14` is invoked, **Then** the pipeline completes within 6 hours, outputs a CSV with ≈ 10 years ÷ 14 days rows, and logs “Using bin size: 14 days”.  
2. **Given** a clean runner environment, **When** `run_all.sh --bin-size 54` is invoked, **Then** the pipeline completes within 6 hours, outputs a CSV with ≈ 10 years ÷ 54 days rows, and logs “Using bin size: 54 days”.

---

### Edge Cases

- What happens when a data source (IceCube or Auger) is unavailable for > 30 days?  
- How does the system handle timestamps that are not aligned to the 27‑day Carrington grid (e.g., leap‑second adjustments)?  
- How is the analysis affected if a solar‑proxy series contains gaps longer than 5 days?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the IceCube muon‑track dataset (2010‑2020) and Pierre Auger surface‑detector files from their respective open‑data portals, verifying file integrity via SHA‑256 checksums. (See US‑1)
- **FR-002**: System MUST retrieve daily solar‑activity indices (sunspot number, solar‑wind speed, IMF magnitude) from NOAA NGDC, handling FTP failures with up to 3 automatic retries and exponential back‑off. (See US‑1)
- **FR-003**: System MUST convert event timestamps to UTC Julian dates, bin events into non‑overlapping intervals of length specified by FR‑010, and generate HEALPix Nside 64 sky maps for each interval. (See US‑1)
- **FR-004**: System MUST fit spherical‑harmonic coefficients up to ℓ = 2 for each sky map and export dipole amplitude, phase, and quadrupole metrics to a CSV file with column headers `interval_start, dipole_amp, dipole_phase, quad_amp`. (See US‑1)
- **FR-005**: System MUST perform, for each detector (IceCube and Pierre Auger) separately, Lomb‑Scargle periodogram analysis on the dipole‑amplitude series, compute Pearson and Spearman cross‑correlations with each solar proxy, and estimate significance via (i) block‑bootstrap (block = 27 days, 10 000 resamples) and (ii) Monte‑Carlo shuffle (10 000 permutations). (See US‑2)
- **FR-006**: System MUST apply a Bonferroni correction for the six hypothesis tests (2 detectors × 3 proxies) with an adjusted significance threshold of α = 0.0017, and declare a positive result only if |r| ≥ 0.4 **and** the corrected p‑value ≤ 0.0017 for at least one proxy–detector pair. (See US‑2)
- **FR-007**: System MUST produce a LaTeX‑based PDF report that includes (a) time‑series plots, (b) periodograms, (c) correlation heat‑maps, and (d) a concise interpretation of statistical significance, for each detector independently and optionally a combined analysis. (See US‑3)
- **FR-008**: System MUST expose a single entry‑point script (`run_all.sh`) that orchestrates data acquisition, preprocessing, analysis, and reporting, invoking the modular scripts (`run_pipeline.sh`, `analyze_correlation.py`, `make_report.sh`) as sub‑steps, exiting with status 0 on success and non‑zero on any failure. (See US‑3)
- **FR-009**: System MUST generate a `requirements.txt` pinning exact versions of all Python packages used (minimum Python 3.11) and ensure all dependencies are CPU‑only (no CUDA/GPU requirements). (See US‑3)
- **FR-010**: System MUST allow the temporal bin size to be configurable (e.g., 14, 27, 54 days) – the default value is **27 days** (one Carrington rotation). Allowed values are **integers between 7 days and 60 days inclusive**; values that are multiples of 7 days are recommended to maintain alignment with solar‑rotation sub‑structures. (See US‑4)

### Key Entities

- **EventDataset**: Represents a raw IceCube or Auger event file; attributes include `source`, `filepath`, `checksum`.  
- **SolarProxySeries**: Time‑ordered series of a solar activity indicator; attributes `proxy_name`, `date`, `value`.  
- **AnisotropyInterval**: One interval of length specified by FR‑010 (default 27 days); attributes `start_date`, `end_date`, `dipole_amplitude`, `dipole_phase`, `quadrupole_amplitude`.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: End‑to‑end pipeline completes within 6 hours on a standard GitHub Actions runner (2 CPU, 4 GB RAM) for the full 10‑year dataset. (See US‑1)
- **SC-002**: Dipole‑amplitude CSV contains ≥ 115 rows (≤ 5 % missing intervals) and passes schema validation (all numeric columns non‑null). (See US‑1)
- **SC-003**: Lomb‑Scargle periodogram exhibits a peak at the 11‑year frequency with power ≥ 3 σ above the median noise level, as reported in the PDF. (See US‑2)
- **SC-004**: For each detector (IceCube and Pierre Auger) separately, at least one solar proxy yields a Pearson or Spearman correlation coefficient with absolute value ≥ 0.4 and a two‑sided p‑value ≤ 0.01 after block‑bootstrap correction. (See US‑2)
- **SC-005**: For each detector separately, the Monte‑Carlo shuffle test returns a false‑alarm probability ≤ 0.01 for any claimed correlation, confirming statistical robustness. (See US‑2)
- **SC-006**: The generated `report.pdf` compiles without LaTeX errors and is ≤ 25 pages, containing all required figures and a clear statement of whether the hypothesis is supported at ≥ 3 σ confidence. (See US‑3)
- **SC-007**: The analysis executes entirely on CPU without invoking CUDA libraries or requiring GPU acceleration, verified by the absence of GPU-specific error logs during the 6‑hour runner execution. (See US‑2)

## Assumptions

- The IceCube and Pierre Auger open‑data portals will remain accessible for the duration of the analysis and will provide files ≤ 1 GB total.
- NOAA NGDC provides daily solar‑activity indices with ≤ 1 day latency and no missing days for the 2010‑2020 interval.
- The 27‑day Carrington rotation is an appropriate temporal resolution for capturing solar‑cycle modulation of TeV–PeV anisotropy; alternative bin sizes are optional enhancements.
- All Python dependencies are compatible with the Ubuntu‑22.04 environment used by GitHub Actions.
- Researchers using the pipeline have internet connectivity sufficient to download ≤ 1 GB of data within the 6‑hour runner limit.
- The statistical methods (Lomb‑Scargle, block‑bootstrap with 27‑day blocks, shuffle test) are accepted in the cosmic‑ray community for detecting periodic signals at the 11‑year scale.
- The relationship between solar activity and cosmic-ray anisotropy is observational; findings will be framed as associational correlations rather than causal effects, consistent with the lack of random assignment in the data.
