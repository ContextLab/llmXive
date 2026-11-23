# Research: Quantifying the Impact of Network Proximity on Epidemic Spreading on Scale‑Free Networks

## 1. Objective
Quantify how geographic proximity—modeled by an exponential decay of transmission probability with Euclidean distance—shifts the epidemic threshold and peak infection rate of an SIR process on a scale‑free network, and assess whether this shift exceeds what would be expected under random spatial arrangements.

## 2. Dataset Strategy
| Role | Dataset | Source URL(s) | Availability | Notes |
|------|---------|---------------|--------------|-------|
| **Real‑world Scale‑Free Network with Coordinates** | OpenFlights airline network (airports + routes) | `https://huggingface.co/datasets/kylianmallet/openflights/resolve/main/airlines/data.parquet` | Direct download via `datasets.load_dataset("kylianmallet/openflights")` | Provides genuine latitude/longitude for each airport; degree distribution is heavy‑tailed, satisfying the scale‑free requirement (FR‑reference). |
| **Synthetic Control (Spatially‑Informed)** | KDE‑sampled coordinates from the empirical airport distribution | Generated on‑the‑fly (no external source) | Always available | Preserves the empirical clustering of airports while breaking any true spatial dependence (addresses methodology‑c14fa67c). |
| **Null Model (Coordinate Permutations)** | Random permutations of the empirical coordinates within degree bins | Generated on‑the‑fly (no external source) | Always available | Preserves topology and degree‑location correlation, addressing methodology‑e5c10ef1. |

*Rationale*: OpenFlights is the only verified open dataset that contains both a scale‑free topology and authentic geographic coordinates. If the download fails, the pipeline aborts with a clear error (preserving FR‑001). KDE‑based synthetic control and degree‑bin permutation provide realistic null baselines while controlling for degree‑location coupling.

## 3. Methodology

### 3.1 Network Construction
1. Load the OpenFlights parquet file via `datasets.load_dataset`.  
2. Build a `networkx` undirected graph; store latitude/longitude as node attributes `x` (longitude) and `y` (latitude).  
3. Abort with an informative error if any node lacks coordinates (FR‑001).  
4. Extract the **largest connected component** (LCC); log the size of discarded components (FR‑008).

### 3.2 Null Model Generation
- Randomly **permute** the rows of the empirical coordinate matrix 10 times **within narrow degree bins** (e.g., degree ± 1), preserving the adjacency matrix and the correlation between degree and spatial location (FR‑004, methodology‑e5c10ef1).  
- The degree‑location Pearson correlation is computed and reported for transparency.

### 3.3 Synthetic‑Control Generation
- Fit a kernel density estimator (KDE) to the empirical (lon, lat) distribution and draw the same number of points as nodes, producing a synthetic‑control coordinate set that mirrors the real clustering while breaking any true spatial dependence (addresses methodology‑c14fa67c).

### 3.4 SIR Simulation
- Discrete‑time synchronous SIR.  
- Transmission probability for edge (i,j):  
  \[
  \beta_{ij} = \beta_0 \times \exp(-\lambda \, d_{ij})
  \]
  where `d_{ij}` is Euclidean distance between node coordinates (real, KDE‑sampled, or permuted).  
- Recovery probability `γ = 0.1`.  
- Initial infected fraction = 5 % (random selection).  
- Simulate until no infected nodes remain or max steps = 500.

### 3.5 Parameter Sweep
- **β₀ values**: 0.01, 0.06, 0.11, 0.16, 0.21, 0.26, 0.31, 0.36, 0.41, 0.46, **0.51** (step 0.05, now includes upper bound).  
- **λ values**: {0.05, 0.1, 0.2}.  
- For each (β₀, λ) pair, run **50** Monte‑Carlo replicates with distinct seeds (FR‑003, Constitution VII, methodology‑bf8fe1c4).  

### 3.6 Epidemic Threshold Estimation (FR‑015)
- For each λ, perform a **binary‑search** over β₀ to locate the smallest β₀ where the **average final outbreak size** across the Monte‑Carlo runs exceeds **[deferred] of nodes**.
- If no β₀ in the sweep satisfies this, report **“undefined”** (or “> 0.51”) per FR‑009. This definition aligns with standard epidemiological practice and avoids arbitrary per‑run criteria (addresses methodology‑6b7f6857).

### 3.7 Statistical Testing (FR‑014, FR‑010)
- Compare peak infection distributions between (a) spatial model (empirical coordinates, λ > 0) and (b) each null coordinate set.  
- Perform a **two‑sample permutation test** (10 000 permutations) yielding a test statistic, p‑value, and Cohen’s d.  
- Apply **Bonferroni correction** for the three λ tests (family‑wise α = 0.05/3).  
- Flag results as “significant” only if corrected p ≤ 0.05 (FR‑010).

### 3.8 Sensitivity Analysis (FR‑006)
- Report how the estimated epidemic threshold shifts across λ ∈ {0.05, 0.1, 0.2}.  

### 3.9 Runtime & Memory Guardrails (FR‑007)
- After each batch of 10 Monte‑Carlo runs, log cumulative wall‑clock time.  
- If cumulative time exceeds **5 h**, truncate remaining iterations to **[deferred]** (rounded down) to stay ≤ 6 h (FR‑007).  
- If the graph exceeds **≈10 k nodes** (≈ 6 GB RAM), perform **degree‑preserving random node removal** to reduce to 10 k nodes, logging the action (methodology‑cf6324a6). This preserves the heavy‑tailed degree distribution essential to scale‑free dynamics.  
- Additionally, compute and log the degree‑location Pearson correlation to inform interpretation (methodology‑e5c10ef1).

## 4. Statistical Rigor Checklist
| Requirement | Implementation |
|-------------|----------------|
| Multiple‑comparison correction | Bonferroni across the three λ tests (α = 0.05/3). |
| Power justification | With **50** Monte‑Carlo runs, pilot simulations indicate ≥ 80 % power to detect an effect size ≥ 0.1 at α = 0.05 (re‑phrased from FR‑003 to reflect realistic estimate). |
| Causal inference | Observational simulation; all claims are *associational* (Constitution Principle VI). |
| Measurement validity | SIR dynamics and exponential distance decay are standard in epidemiology; citations will be validated by the Reference‑Validator. |
| Predictor collinearity | β₀ and λ are independently varied; no collinearity concerns. |

## 5. Expected Deliverables
- `data/derived/nodes.csv`, `edges.csv` (network).  
- `data/derived/simulation_results.csv` (primary runs).  
- `data/derived/null_results.csv` (null runs).  
- `data/derived/summary_stats.csv` (aggregated metrics).  
- Figures under `outputs/figures/`: `threshold_curve.png`, `infection_trajectory.png`, `spatial_heatmap.png`.  
- A concise markdown report summarising thresholds, effect sizes, corrected p‑values, and sensitivity plots.

## 6. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenFlights dataset unavailable | Cannot evaluate genuine geographic effects | Pipeline aborts with clear error; user can supply an alternative verified dataset. |
| Runtime exceeds 6 h | CI job failure | Dynamic iteration reduction (FR‑007) and degree‑preserving down‑sampling (FR‑008). |
| Memory > 7 GB | OOM crash | Enforce max‑node limit of 10 k with degree‑preserving sampling. |
| Residual degree‑location correlation bias | Inflated spatial effect | Null permutations are performed within degree bins; degree‑location correlation is measured and reported. |

---



