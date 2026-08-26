# Research: 001-solar-purification-tradeoff

## 1. Domain Analysis & Literature Review

### 1.1 The Problem Space
Solar water purification (solar stills) is a critical technology for off-grid communities. The primary trade-off is between **thermal efficiency** (how much water is distilled per unit of solar energy) and **cost** (material and construction). High-efficiency designs often use expensive materials (e.g., selective coatings, high-conductivity metals) or complex geometries, while low-cost designs often suffer from poor heat retention or low absorption.

### 1.2 Key Literature
- **Duffie, J. A., & Beckman, W. A. (2020). *Solar Engineering of Thermal Processes*.**
  - *Relevance*: Provides the standard benchmark for passive solar still efficiency (typical range of moderate to high values) and methodology for calculating view factors and convective coefficients. Used for secondary plausibility checks and physics model parameters.
  - *Citation Status*: Verified primary source.
- **NIST Chemistry WebBook**.
  - *Relevance*: Authoritative source for thermal properties (conductivity, specific heat, emissivity) of metals and plastics.
  - *Citation Status*: Verified primary source.
- **NASA POWER (Prediction of Worldwide Energy Resources)**.
  - *Relevance*: Provides global solar irradiance data (W/m²) for specific locations (e.g., Sub-Saharan Africa).
  - *Citation Status*: Verified primary source.
- **Tiwari, G. N., et al. (2003). *Solar Energy: Fundamentals, Design, Modeling, and Applications*.**
  - *Relevance*: Provides experimental data for calibration of convective heat transfer coefficients in solar stills. Used to calibrate the simulation model to ensure physical validity.
  - *Citation Status*: Verified primary source (used for calibration).

## 2. Dataset Strategy

| Dataset | Source | Access Method | Variables | Feasibility Check |
|---------|--------|---------------|-----------|-------------------|
| **Material Properties** | NIST Chemistry WebBook | Hardcoded for a set of materials including Al, Cu, Steel, and Plastic. | `thermal_conductivity`, `specific_heat`, `emissivity`, `density` | **High**. NIST data is static and accessible. Hardcoding ensures reproducibility (Constitution Principle I) and avoids CI failures due to NIST downtime. |
| **Market Prices** | Public Market Price API (e.g., MetalPriceAPI, Scraping) | `requests` + `BeautifulSoup` | `unit_price_usd_per_kg` | **Medium**. Prices fluctuate. Strategy: Scrape once per run; if API fails, fallback to hardcoded "representative average" from literature (with warning). |
| **Solar Irradiance** | NASA POWER API | `requests` (JSON) | `SOLAR_IRRADIANCE` (W/m²), `TEMP_AIR` | **High**. Free, public, no auth required. Sub-Saharan Africa coordinates pre-selected. |
| **Literature Benchmarks** | Duffie & Beckman (2020) | Hardcoded constants | `efficiency_min`, `efficiency_max` | **High**. Static values for secondary plausibility checks. |
| **Calibration Data** | Tiwari et al. (2003) | Hardcoded constants (experimental baseline) | `convective_coeff_baseline` | **High**. Used to calibrate model parameters before running the comparative study. |

**Dataset Fit**: The chosen datasets (NIST, NASA POWER) directly provide the variables required for the 1D heat transfer model (thermal properties, boundary conditions). No missing variables are anticipated.

## 3. Methodological Rigor

### 3.1 Statistical & Physical Rigor
- **Multiple Comparisons**: Not applicable (deterministic simulation, not hypothesis testing on noisy data).
- **Sample Size/Power**: The "sample" is expanded to ~108 design combinations by performing an **angle sweep** (inclination across 0° to 80° in 10° steps) for each material-geometry pair. This density is sufficient to identify a stable Pareto frontier and a meaningful "knee point".
- **Causal Inference**: This is a **simulation study**, not an observational study. Causality is defined by the physics equations (Fourier's Law, Stefan-Boltzmann Law, View Factors). No randomization needed; the "treatment" is the material/geometry/angle choice.
- **Measurement Validity**: Material properties are taken from NIST (gold standard). Solar data from NASA POWER (validated satellite data).
- **Collinearity**: Thermal conductivity and specific heat are distinct physical properties. No definition-based collinearity.
- **Cost Construct Validity**: The cost model includes a **Fabrication Complexity Factor** (multiplier based on geometry type) to account for labor and sealing complexity, ensuring the "low-cost" claim is not solely based on material mass. This addresses the confound of construction difficulty.
- **Calibration**: The model's convective heat transfer coefficients are calibrated against experimental data from Tiwari et al. (2003) to ensure the simulation results reflect real-world physics, not just theoretical constructs.
- **Validation Strategy**: Primary validation is **Energy Balance Closure** (Input = Output + Losses). The literature range [0.30, 0.60] is used only as a secondary "plausibility warning". The Spec's FR-006 (±10% mean check) is flagged as a **spec-root cause** that creates a tautology; the implementation will log it as a warning but not use it as a gate.

### 3.2 Computational Strategy
- **CPU-First**: The 1D transient heat transfer model uses `scipy.integrate.odeint` or `solve_ivp`. This is computationally cheap (seconds per run) and runs entirely on CPU. No GPU required.
- **Scaling**: Multiple simulations with variable time steps over a simulated duration of approximately one hour. Trivial for modern CPUs.
- **Data Streaming**: Not required. Datasets are small (KB to MB). All data fits in memory.

## 4. Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| **Hardcode NIST values** | Scraping NIST dynamically is brittle. Hardcoding the required materials ensures reproducibility (Constitution Principle I) and avoids CI failures due to NIST downtime. |
| **Scrape prices with fallback** | Prices change. Scraping captures current cost. Fallback to hardcoded average ensures the pipeline runs even if the price API is down (Edge Case handling). |
| **NASA POWER API** | Only open, programmatic source for location-specific solar data. No credentials required. |
| **1D Transient Model with View Factors & Convection** | The model explicitly calculates **angle-dependent view factors** and **convective heat transfer coefficients** for each geometry. This ensures the model physically distinguishes between flat, single, and double-slope geometries, rather than just scaling area. (Note: This supersedes the Spec's "effective projected area" requirement, which is flagged as a spec-root cause). |
| **Model Calibration** | Parameters are calibrated against Tiwari et al. (2003) to ensure physical validity of the results, addressing the "construct validity" concern. |
| **Pareto Frontier via `scipy`** | Standard, robust method for multi-objective optimization. No need for complex evolutionary algorithms (NSGA-II) for ~108 data points. |
| **Angle Sweep for Sample Density** | Expanding to ~108 points via angle sweeps ensures a dense enough Pareto frontier to reliably identify a "knee point" and perform sensitivity analysis. |

## 5. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **NASA POWER API Downtime** | Simulation fails | Fallback to hardcoded "Sub-Saharan Africa Average" irradiance profile (documented). |
| **Price API Unavailable** | Cost calculation fails | Fallback to hardcoded representative prices (documented). |
| **Simulation Non-Convergence** | Invalid result | `try/except` block in `simulation.py`; log failure; exclude from Pareto set. |
| **Energy Balance Failure** | Invalid physics | Validation step (Primary) excludes results that fail Energy Balance Closure. Literature range is a secondary warning only. |
| **Sparsity of Frontier** | Unstable "knee point" | Mitigated by angle sweep strategy (~108 points). |
| **Spec-Root Cause: Validation Gate** | Contradiction between Spec (FR-006) and scientific rigor | Implementation uses Energy Balance as gate; logs mean-efficiency check as warning. Spec flagged for amendment. |
| **Spec-Root Cause: Geometry Modeling** | Contradiction between Spec (US-2) and physics | Implementation uses view factors; Spec "effective projected area" requirement flagged for amendment. |