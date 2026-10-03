# Implementation Notes

This document provides detailed implementation notes for key components of the Equivalence Principle testing pipeline.

## 1. Data Ingestion Strategy

### ILRS Archive Access
The pipeline fetches data from the ILRS archive using the URL pattern:
` Network is unreachable"))]<satellite_id>.dat.gz`

**Retry Logic:**
- Maximum 3 retries with exponential backoff (1s, 2s, 4s)
- Handles HTTP 403, 503, and timeout errors
- Logs warnings but does not halt pipeline on individual satellite failures

### Data Availability Gap Handling
If a satellite's data is unavailable:
1. Log a warning with the error reason
2. Generate `data/feasibility_gap_report.json`
3. Proceed with available satellites
4. Mark the report as "Incomplete" if critical satellites are missing

## 2. Dynamical Model Implementation

### GGM Geopotential (GGM05C)
- Uses `astropy.coordinates` for coordinate transformations
- Implements spherical harmonic expansion up to degree/order 70
- Constants: GM = 3.986004418e14 m³/s², R_earth = 6378136.6 m

### Jacchia Drag Model
- Uses Jacchia 1971/1977 atmospheric density model
- Satellite-specific parameters: mass, cross-sectional area, drag coefficient
- Requires solar flux and geomagnetic indices (F10.7, Ap)

### Solar Radiation Pressure (SRP)
- Cannonball model with satellite-specific reflectivity
- Sun position computed using `astropy.coordinates.get_body`
- Shadow function for eclipse conditions

### Relativistic Corrections
- **Schwarzschild**: Main relativistic effect (GM/c² terms)
- **Lense-Thirring**: Frame-dragging effect (Earth's rotation)
- **De Sitter**: Geodetic precession (optional, typically small)

## 3. Estimator Implementation

### Separate Fit (Primary Method)
- Levenberg-Marquardt algorithm (`scipy.optimize.least_squares`)
- Parameters: 6 orbital elements + 1 non-gravitational acceleration
- Convergence tolerance: 1e-8
- Initial guess from TLE data

### Joint Fit (Comparison Method)
- Stacks residuals from two satellites
- Estimates combined parameter vector: [θ₁, θ₂, a_c]
- a_c is the differential acceleration term
- Weighted by inverse variance of observations

### Force Subtraction
The critical step in isolating the WEP signal:
```
a_c_anomalous = (a_obs_1 - a_obs_2) - (a_expected_1 - a_expected_2)
```
Where `a_expected` is computed from `force_calculator` using satellite-specific properties.

## 4. Eötvös Parameter Calculation

### Mean Orbital Radius
- Computed from the arc time range and initial state vector
- `r_mean = mean(|state|)` over the observation arc
- **Do NOT use instantaneous r** to avoid noise amplification

### Local Gravity
```
g = GM / r_mean²
```
Where GM is Earth's gravitational constant.

### Confidence Interval
- 95% CI derived from covariance matrix of the fit
- `CI = [η - 1.96*σ_η, η + 1.96*σ_η]`
- σ_η propagated from covariance of a_c and g

## 5. Statistical Validation

### F-Test
Compares Null model (no WEP violation) vs Alternative model (WEP violation):
```
F = ((χ²_null - χ²_alt) / (dof_null - dof_alt)) / (χ²_alt / dof_alt)
```

### BIC (Bayesian Information Criterion)
```
BIC = n * ln(χ²/n) + k * ln(n)
```
Where n = number of observations, k = number of parameters.

### Multiple Comparison Correction
- **Bonferroni**: p_corrected = p * m (conservative)
- **Holm-Bonferroni**: Step-down procedure (less conservative)
- **Benjamini-Hochberg**: False discovery rate control (least conservative)

### Sensitivity Analysis
- Sweeps across geopotential models: GGM05C, EGM2008, GOCO
- Computes z-score variation across models
- Flags "Unreliable" if variation > 20%

## 6. Resource Constraints

### Memory Management
- Monitored using `psutil.Process().memory_info().rss`
- Polling interval: 1 second
- Hard exit if RSS > 6GB
- Error message: `CRITICAL: Memory limit (6GB) exceeded. Current RSS: {rss_mb}MB`

### Time Constraints
- Global timer for full pipeline
- Hard exit if runtime > 6 hours (exit code 124)
- Logs timing data to `data/logs/resource_monitor.log`

### CPU-Only Execution
- No GPU imports (no TensorFlow, PyTorch, etc.)
- Uses `scipy` and `numpy` for numerical operations
- `astropy` for coordinate transformations

## 7. Data Products

### Input Data
- Raw SLR normal points from ILRS archive
- Satellite metadata (mass, area, reflectivity)
- Geopotential model coefficients

### Intermediate Products
- Cleaned SLR data CSV
- Orbit solutions JSON
- Excluded satellites list (if any)

### Final Outputs
- Eötvös parameter estimate with 95% CI
- Sensitivity analysis plot
- Feasibility gap report
- Diagnostic report with Δχ², F-statistic, p-value

## 8. Error Handling

### Data Unavailable
- Logs warning, proceeds with available data
- Generates feasibility gap report
- Does NOT fail pipeline

### Solver Non-Convergence
- Relaxes tolerance (1e-8 → 1e-6)
- Logs warning with best-fit result
- Continues with conservative uncertainty

### Missing Benchmark
- Logs warning "Benchmark value missing. Research task T048.0d must be completed first."
- Sets `precision_goal_met = False`
- Does NOT raise FileNotFoundError

## 9. Testing Strategy

### Unit Tests
- Test individual functions (dynamics, estimator, validation)
- Mock external dependencies (ILRS fetch)
- Verify mathematical correctness

### Integration Tests
- End-to-end pipeline on 1-year subset
- Verify artifact generation
- Assert data completeness (≥95% of available points)

### Edge Cases
- Missing data for one satellite
- Empty results
- Non-convergent solver
- Memory limit exceeded

## 10. Future Improvements

### Planned Enhancements
- Add more satellites (LARES, Ajisai)
- Implement full relativistic model (post-Newtonian)
- Add atmospheric tide corrections
- Parallelize sensitivity analysis
- Web-based visualization dashboard

### Known Limitations
- Single-arc fitting (no multi-arc combination)
- Simplified SRP model (cannonball)
- Limited geopotential models (GGM05C, EGM2008, GOCO)
- No tides modeling (solid Earth, ocean)
