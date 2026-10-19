# Research: Mesh Network Supercomputer Using Pooled Idle Computing Resources

## 1. Research Question & Hypotheses
**Primary Question**  
What is the non‑linear relationship between task granularity, resource heterogeneity, and injected network latency in a physical Wi‑Fi mesh supercomputer, and how does the observed throughput scaling compare to the theoretical wireless capacity bound of Ong & Motani (2007)?

**Hypotheses**  
- **H1**: Throughput versus granularity follows a non‑linear curve with an optimal “sweet spot” where coordination overhead is minimized.  
- **H2**: Heterogeneity (CPU speed variance, latency variance) interacts with granularity, amplifying straggler effects for coarse chunks.  
- **H3**: Empirical normalized efficiency never exceeds the Ong & Motani (2007) bound; deviations grow under high injected latency.

## 2. Dataset Strategy
The study **generates its own dataset** from the physical mesh; no external datasets are required.

| Dataset | Source | Access Method | Variables Captured |
|---------|--------|---------------|--------------------|
| Physical Execution Logs | Local testbed (10‑20 devices) | SSH‑driven instrumentation (`tcpdump`, `mpstat`) | `node_id`, `wall_clock_time`, `cpu_utilization_pct`, `packet_count`, `task_id`, `granularity`, `injected_latency`, `current_latency`, `packet_loss_rate` |
| Baseline Channel Metrics | Pre‑run `iperf3` / `iwconfig` on each node | CLI on each node | `baseline_bandwidth_Mbps`, `baseline_snr_db` |
| Runtime Channel Metrics | Continuous monitoring during benchmark | `tcpdump` & `iwconfig` | `runtime_bandwidth_Mbps`, `runtime_snr_db` |
| Calibration Data | Synthetic runs on mock nodes | Internal scripts (`calibrate_network.py`, `calibrate_cpu.py`) | Conversion factors for packet counts ↔ throughput, mpstat % ↔ CPU load |
| Theoretical Bound Parameters | Ong & Motani (2007) formula | Parameterized with measured bandwidth & SNR | `bandwidth_Mbps`, `snr_db`, `node_count` |

*Dataset‑Variable Fit*: All predictors required by the regression (CPU variance, latency variance, injected latency, node count, granularity) and the outcome (throughput) are present. Missing variables (e.g., thermal throttling) are now captured via `cpu_temperature_avg`; OS‑level noise and Wi‑Fi interference are recorded as optional covariates.

## 3. Statistical Analysis Plan
### 3.1 Modeling
- **Baseline OLS** via `statsmodels.api.OLS`.  
  - **Outcome**: `throughput` (tasks / sec).  
  - **Predictors**: `node_count`, `granularity` (categorical), `injected_latency`, `cpu_variance`, `latency_variance`, plus interaction terms `granularity:cpu_variance` and `granularity:latency_variance`.  
- **Non‑Linear Extensions** (selected based on AIC/BIC):
  - **Polynomial Terms**: quadratic (`granularity²`, `injected_latency²`) added to capture curvature.
  - **Spline / GAM**: if `pygam` is installed, fit a Generalized Additive Model with spline bases for continuous predictors (`injected_latency`, `cpu_variance`, `latency_variance`).  
- **Model Selection**: Compare candidate models using AIC and BIC; retain the model with lowest criterion.  
- **ANOVA** (`statsmodels.stats.anova.anova_lm`) on the selected model to test overall granularity effect.  
- **Multiple‑Comparison Correction**: Benjamini‑Hochberg FDR applied to all p‑values (`statsmodels.stats.multitest.multipletests`).  
- **Collinearity Check**: Compute Variance Inflation Factor (VIF) for continuous predictors; if any VIF > 5, report collinearity and refrain from claiming independent effects.

### 3.2 Power & Sample‑Size Justification
- Desired **≥ 82 independent runs** (medium effect size f² = 0.15, α = 0.05, power = 0.80 per G*Power).  
- With a moderate number of predictors (including polynomial/GAM basis functions), the required sample size is **≈ 82**.  
- Planned design: 3 granularity × 3 node counts × 4 latency levels × 2 replicates = 72 runs; we double the replicates for robustness, yielding **144** runs, and add a few extra runs for dropout recovery → **150** runs total.  
- This exceeds the required N, guaranteeing ≥ 80 % power for detecting interaction effects.

### 3.3 Measurement Validity
- **Network Calibration**: Run `iperf3` between a pair of nodes to map `tcpdump` packet counts to known throughput; repeat three times and average.  
- **CPU Utilization Calibration**: Run `sysbench cpu --threads=1 run` to produce known CPU loads; compare `mpstat` %util to benchmarked load; derive a linear conversion factor.  
- **Thermal Throttling**: Record per‑node CPU temperature via `sensors`; store average as `cpu_temperature_avg`.  
- **OS‑Level Noise**: Compute standard deviation of 1‑minute load average over the run; store as `os_noise`.  
- **Wi‑Fi Interference**: Record RSSI variance from `iwconfig`; store as optional `wifi_interference`.  
- All nodes synchronized via NTP to ensure comparable timestamps.

### 3.4 Causal Framing
- **Injected latency** is an experimental factor (causal).  
- **Heterogeneity metrics** (CPU variance, latency variance) are observational covariates; regression coefficients are interpreted associationally.

### 3.5 Predictor Collinearity
- Compute VIF for each continuous predictor; report any VIF > 5 and note the limitation in interpreting independent effects.

### 3.6 Theoretical Bound Validation
- Compute **Normalized Efficiency** = `throughput` / `theoretical_capacity`, where `theoretical_capacity` follows the Ong & Motani (2007) Shannon‑based formula using measured baseline bandwidth and SNR per node.  
- Fit a power‑law `throughput = a * node_count^b` (log‑log OLS) and compare exponent `b` to the theoretical scaling exponent derived from the same bound.  
- Calculate **Deviation Ratio** = `b_empirical / b_theoretical`.  
- Flag runs where Normalized Efficiency > 1 as potential measurement errors and report any statistically significant deviation of `b` from theory (p < 0.05).

## 4. Compute Feasibility
- **CPU‑First**: All statistical analyses (OLS, ANOVA, GAM, power analysis) run comfortably on the free‑tier CI runner.  
- No GPU is required; no large‑scale model training.  
- Generated dataset ≤ 2 GB, well within RAM/disk limits.

## 5. Decision Rationale
| Decision | Rationale |
|----------|-----------|
| Use **real testbed** (not pure simulation) | Spec mandates “real execution logs” to falsify linear scaling. |
| Choose **Monte Carlo integration** as benchmark | Embarrassingly parallel, isolates coordination overhead, matches scope. |
| Use **OLS + polynomial/GAM** (not only linear) | Directly satisfies FR‑005 and addresses non‑linear hypothesis H1. |
| Apply **Benjamini‑Hochberg** correction | Controls false discovery rate across many coefficients. |
| Include **VIF** check | Prevents over‑interpretation of collinear predictors. |
| Generate **dropout_events.json** | Provides required covariate for regression and resolves T002. |
| Add **comprehensive calibration** (network & CPU) | Guarantees construct validity of packet counts and CPU utilization. |
| Add **additional covariates** (temperature, OS noise, Wi‑Fi interference) | Addresses potential confounders highlighted in the methodology review. |
| Expand **theoretical bound validation** to scaling‑law exponent comparison | Provides a substantive test of the scaling hypothesis beyond a trivial sanity check. |
| Keep **pipeline within 6 h** | Meets SC‑004 (CI time limit) and respects free‑tier constraints. |

---


