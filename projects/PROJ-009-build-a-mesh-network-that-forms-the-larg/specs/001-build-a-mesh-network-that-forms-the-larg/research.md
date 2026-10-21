# Research: Mesh Network Supercomputer Using Pooled Idle Computing Resources

## 1. Research Question & Hypotheses
**Primary Question**  
What is the non‑linear relationship between task granularity, resource heterogeneity, and injected network latency in a physical Wi‑Fi mesh supercomputer, and how does the observed throughput scaling compare to the theoretical wireless capacity bound of Ong & Motani (2007)?

**Hypotheses**  
- **H1**: Throughput vs. granularity follows a non‑linear curve with an optimal “sweet spot” where coordination overhead is minimized.  
- **H2**: Heterogeneity (CPU speed variance, latency variance) *associatively* interacts with granularity, amplifying straggler effects for coarse chunks.  
- **H3**: Empirical normalized efficiency never exceeds the Ong & Motani (2007) bound; any violation indicates a measurement error.

## 2. Dataset Strategy
The study **generates its own dataset**; no external dataset download is required.

| Dataset | Source | Access Method | Variables Captured |
|---------|--------|---------------|--------------------|
| Physical Execution Logs | Local testbed (on the order of tens of devices) | SSH‑driven instrumentation (`tcpdump`, `mpstat`) | `node_id`, `wall_clock_time`, `cpu_utilization_pct`, `packet_count`, `task_id`, `granularity`, `injected_latency`, `current_latency`, `packet_loss_rate` |
| Baseline Channel Metrics | Pre‑run `iperf3` / `iwconfig` on each node | CLI on each node | `baseline_bandwidth_Mbps`, `baseline_snr_db` |
| Runtime Channel Metrics | Continuous monitoring (`tcpdump`, `iwconfig`) | Same as above | `runtime_bandwidth_Mbps`, `runtime_snr_db` |
| Calibration Data | Synthetic runs on mock nodes | Internal scripts (`calibrate_network.py`, `calibrate_cpu.py`) | Conversion factors for packet counts → throughput, mpstat % → CPU load |
| Theoretical Bound Parameters | Ong & Motani (2007) formula | Parameterized with measured bandwidth & SNR | `bandwidth_Mbps`, `snr_db`, `node_count` |

*Dataset‑Variable Fit*: All predictors required by the regression (CPU variance, latency variance, injected latency, node count, granularity) and the outcome (throughput) are present. Optional covariates (CPU temperature, OS noise, Wi‑Fi interference) are also captured when available.

## 3. Statistical Analysis Plan
### 3.1 Modeling
- **Baseline OLS** (`statsmodels.api.OLS`)  
  - **Outcome**: `throughput` (tasks / sec)  
  - **Predictors**: `node_count`, `granularity` (categorical), `injected_latency`, `cpu_variance`, `latency_variance`, plus interaction terms `granularity:cpu_variance` and `granularity:latency_variance`.  
- **Mixed‑effects extension** (`statsmodels.regression.mixed_linear_model.MixedLM`) adds a random intercept for `node_id` to account for within‑node correlation (observational heterogeneity).  
- **Non‑Linear Extensions** (selected by AIC/BIC)  
  - **Polynomial**: quadratic terms for `granularity` (encoded numerically) and `injected_latency`.  
  - **GAM**: if `pygam` is installed, fit spline bases for continuous predictors.  
- **Model Selection**: lowest AIC/BIC retains the final model.  
- **ANOVA** (`statsmodels.stats.anova.anova_lm`) on the selected model to test overall granularity effect.  
- **Multiple‑Comparison Correction**: Benjamini‑Hochberg FDR applied to all p‑values (`statsmodels.stats.multitest.multipletests`).  
- **Collinearity Check**: VIF computed for continuous predictors; any VIF > 5 reported and the corresponding coefficient is not claimed as an independent effect.

### 3.2 Power & Sample‑Size Justification (updated)
- Desired **≥ 80 % power**, α = 0.05, medium effect size f² = 0.15 (G*Power convention).  
- Required **N ≈ 82** independent runs for detecting interaction effects.  
- **Clustering adjustment**: runs share nodes, inducing intra‑class correlation (ICC ≈ 0.05). Design effect ≈ 1 + (m − 1)·ICC, with *m* ≈ 4 runs per node ⇒ design effect ≈ 1.15. Effective N = total / 1.15.  
- **Planned design**: 3 granularity × 3 node counts × 4 latency levels × 4 replicates = 144 runs.  
- **Extra dropout‑recovery runs**: 36 runs (one extra per configuration) → **total 180 runs**. Effective N ≈ 180 / 1.15 ≈ 156 > 82, satisfying the power requirement even after accounting for clustering.  
- The mixed‑effects model (node random effect) further mitigates residual intra‑node correlation.

### 3.3 Measurement Validity
- **Network Calibration**: `iperf3` between a pair of nodes maps `tcpdump` packet counts to known throughput; linear regression is performed and R² ≥ 0.9 is required.  
- **CPU Utilization Calibration**: `sysbench cpu --threads=1 run` provides known CPU loads; linear regression between `mpstat` % and load is performed; R² ≥ 0.9 required.  
- **Throughput Derivation**: Primary outcome is computed from *task‑completion timestamps* (wall‑clock time per chunk) rather than raw packet counts alone. Packet‑count data are used only as a secondary consistency check against the calibrated conversion factor.  
- All calibrations are rerun on each CI execution; failures abort the pipeline with a clear error message.

### 3.4 Causal Framing
- **Injected latency** = experimental factor (causal manipulation).  
- **Heterogeneity metrics** = observational covariates; coefficients are interpreted *associationally* (no claim of causality).  
- The mixed‑effects model isolates the effect of injected latency while controlling for node‑level random effects.

### 3.5 Predictor Collinearity
- VIF computed for each continuous predictor; any VIF > 5 flagged and the corresponding coefficient is not claimed as an independent effect.

### 3.6 Theoretical Bound Validation
- **Normalized Efficiency** = `throughput` / `theoretical_capacity`, where `theoretical_capacity` follows the Ong & Motani (2007) Shannon‑based formula using measured baseline bandwidth and SNR per node.  
- Fit power‑law `throughput = a * node_count^b` (log‑log OLS) and compare exponent `b` to the theoretical scaling exponent derived from the same bound.  
- Compute **Deviation Ratio** = `b_empirical / b_theoretical`.  
- Flag runs where Normalized Efficiency > 1 as potential measurement errors; report any statistically significant deviation of `b` from theory (p < 0.05).

## 4. Variable‑Fit Verification (new)
A dedicated verification script runs after each raw‑data generation step:

- Checks that every required predictor (`cpu_variance`, `latency_variance`, `injected_latency`, `node_count`, `granularity`) and the outcome (`throughput`) is present in `run_*.csv`.  
- If a *critical* variable is missing (e.g., `throughput`, `cpu_variance`, `latency_variance`), the run is logged as **WARN** and excluded from the regression dataset.  
- Optional covariates may be missing without exclusion.  
- Results are written to `data/processed/validation_status.json` and validated against a lightweight schema.  
- This step directly satisfies SC‑006.

## 5. Compute Feasibility
- **CPU‑First**: All statistical analyses (OLS, ANOVA, mixed‑effects, GAM, calibration) run comfortably on the free‑tier CI runner (2 CPU cores, ~7 GB RAM).  
- No GPU is required; dataset size ≤ 2 GB, well within RAM/disk limits.  

## 6. Decision Rationale
| Decision | Rationale |
|----------|-----------|
| Split pipeline into **mock CI‑verified** and **manual physical** stages | Resolves the structural contradiction flagged by reviewers; CI can verify deterministic artefacts while the real testbed supplies the scientific data. |
| Use **Monte Carlo integration** as benchmark | Embarrassingly parallel, isolates coordination overhead, aligns with scope. |
| Include **calibration** (network & CPU) | Guarantees construct validity of packet‑count and CPU‑util metrics (required by SC‑006). |
| Apply **Benjamini‑Hochberg** FDR correction | Controls false discoveries across many coefficients without excessive conservatism. |
| Add **VIF** check | Prevents over‑interpretation of collinear predictors (Principle VII). |
| Generate **dropout_events.json** and **task_chunks/*.jsonl** | Satisfies T003, T001, and provides the dropout covariate required by regression. |
| Provide **sample fixture logs** (tcpdump, mpstat, iwconfig, sensors, ping) | Satisfies T014 and enables unit tests without real hardware. |
| Implement **runtime_tracker** producing JSON and log files | Satisfies T011 (timeout enforcement evidence). |
| Create **network & CPU calibration JSON** files | Satisfies T015 and supplies conversion factors for analysis. |
| Ensure **config.yaml** exists and is version‑controlled | Satisfies T001 (test suite expects it). |
| Adjust contract tests to use `TaskChunkStore.base_dir` instead of `ProjectPaths.root` | Fixes T016 failure. |
| Produce **run_001.csv**, **task_chunks/run_001.jsonl**, **validation_status.json** via mock run | Satisfies T004. |
| Add **Variable‑Fit Verification** phase | Directly addresses SC‑006 and ensures dataset‑variable fit. |
| Reconcile power‑analysis totals to **180 runs** and account for clustering | Guarantees the claimed ≥ 80 % power under realistic correlation structure. |
| Clarify **associational** interpretation of heterogeneity effects | Removes unsupported causal claims per methodology‑8ff4adb8. |
| Add explicit **measurement‑validity** steps | Addresses methodology‑a05aa0de concerns about construct validity. |

---

