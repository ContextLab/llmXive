# Research: Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale‑Free Networks

## 1. Objective
Quantify how geographic proximity—modeled by an exponential decay of transmission probability with Euclidean distance—shifts the epidemic threshold and peak infection rate of an SIR process on a scale‑free network, and assess whether this shift exceeds what would be expected under random spatial arrangements.

## 2. Dataset Strategy
| Role | Dataset | Source URL(s) | Availability | Notes |
|------|---------|---------------|--------------|-------|
| **Real‑world Scale‑Free Network with Coordinates** | Brightkite social network (SNAP) | `https://snap.stanford.edu/data/brightkite.html` (edge list) <br> `https://snap.stanford.edu/data/loc-brightkite.txt.gz` (node latitude/longitude) | Direct download via `urllib` or `datasets.load_dataset` (mirrored on HuggingFace as `snap/brightkite`) | Provides genuine geographic coordinates for tens of thousands of nodes; degree distribution is heavy‑tailed, satisfying FR‑001. |
| **Synthetic Control (Random Coordinates)** | Random uniform coordinates | Generated on‑the‑fly (no external source) | Always available | Serves as the *synthetic‑control* when the real network lacks coordinates; independent of topology, avoiding confounding (FR‑011). |
| **Optional SIR fragments** | SIR parquet | `https://huggingface.co/datasets/ebeaulac/siriccam-sq-400px-16frag-12-25-train-fragments/resolve/main/data/train-00000-of-00001-b8b0b087631f7338.parquet` | Direct download via `datasets.load_dataset` | Retained for possible future extensions; not required for primary analysis. |

*Rationale*: Brightkite offers authentic geographic positions and a heavy‑tailed degree distribution, fulfilling the requirement for a real‑world scale‑free network with coordinates. If Brightkite cannot be fetched, the pipeline aborts with a clear error (no synthetic topology is used for the main analysis). Random coordinates are used only for the synthetic‑control condition.

## 3. Methodology

### 3.1 Network Construction
1. **Primary**: Download the Brightkite edge list and node coordinate file. Build a `networkx` graph, preserving latitude/longitude as node attributes `x` and `y`.  
2. **Abort on Failure**: If the Brightkite download fails, the pipeline stops with an informative error; no synthetic Barabási‑Albert graph is used for the primary scientific analysis (preserves FR‑001).  
3. Extract the largest connected component (LCC); log the size of any discarded components (FR‑008).  

### 3.2 Null Model Generation
- Randomly **permute** the rows of the **empirical** coordinate matrix (the real Brightkite coordinates) 20 times, preserving the adjacency matrix. Each permutation yields a null coordinate set `X_null_i`.

### 3.3 SIR Simulation
- Discrete‑time SIR with synchronous updates.  
- Transmission probability for edge (i,j):  
  \[
  \beta_{ij} = \beta_0 \times \exp(-\lambda \, d_{ij})
  \]
  where `d_{ij}` is Euclidean distance between node coordinates (real or random).  
- Recovery probability `γ = 0.1`.  
- Initial infected fraction = 5 % (randomly selected).  
- Simulate until no infected nodes remain or max steps = 500.

### 3.4 Parameter Sweep
- **β₀ sweep**: 0.01, 0.06, 0.11, 0.16, 0.21, 0.26, 0.31, 0.36, 0.41, 0.46 (step 0.05).  
- **λ values**: {0.05, 0.1, 0.2}.  
- For each (`β₀`, λ) pair, run **15** Monte‑Carlo replicates (different seeds) (FR‑003, reduced for compute).  

### 3.5 Epidemic Threshold Estimation (FR‑015)
- For each λ, binary‑search over β₀ to locate the smallest β₀ where ≥5 % of nodes become infected in >50 % of Monte‑Carlo runs.  
- If no β₀ in the sweep satisfies this, report **“undefined”** (or “> 0.46”) per FR‑009.

### 3.6 Statistical Testing (FR‑014, FR‑010)
- Compare the distribution of peak infection rates between:  
  1. **Spatial model** (λ > 0, using empirical coordinates).  
  2. **Null models** (λ > 0, using each `X_null_i`).  
- Perform a **two‑sample permutation test** (10 000 permutations) to obtain a test statistic and a p‑value.  
- Compute **Cohen’s d** as effect size.  
- Apply **Bonferroni correction** for the three λ values (family‑wise α = 0.05/3).

### 3.7 Sensitivity Analysis (FR‑006)
- Report how the estimated epidemic threshold shifts across λ ∈ {0.05, 0.1, 0.2}.

### 3.8 Runtime & Memory Guardrails (FR‑007)
- After each batch of 10 Monte‑Carlo runs, log cumulative wall‑clock time.  
- If cumulative time > 5 h, truncate remaining iterations to keep total ≤ 6 h (FR‑007).  
- If the graph exceeds ~10 k nodes (≈ 6 GB RAM), uniformly sample 10 k nodes from the LCC and log the down‑sampling action (FR‑008).

## 4. Statistical Rigor Checklist
| Requirement | Implementation |
|-------------|----------------|
| Multiple‑comparison correction | Bonferroni across the three λ tests (α = 0.05/3). |
| Power justification | 15 Monte‑Carlo runs give a Monte‑Carlo standard error ≤ 0.13 for binary outcomes; limitation noted in the manuscript. |
| Causal inference | Observational simulation; claims are *associational* per Constitution Principle VI. |
| Measurement validity | SIR model and exponential distance decay are standard in epidemiology (textbook citations; will be validated by Reference‑Validator). |
| Predictor collinearity | β₀ and λ are independent design parameters; no collinearity concerns. |

## 5. Expected Deliverables
- `data/derived/nodes.csv`, `edges.csv` (network).  
- `data/derived/simulation_results.csv` (primary runs).  
- `data/derived/null_results.csv` (null runs).  
- `data/derived/summary_stats.csv` (aggregated metrics).  
- Figures under `outputs/figures/`: `threshold_curve.png`, `infection_trajectory.png`, `spatial_heatmap.png`.  
- A concise markdown report summarising thresholds, effect sizes, p‑values, and sensitivity plots.

## 6. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Brightkite dataset unavailable | Cannot evaluate genuine geographic effects | Pipeline aborts with clear error; user can manually provide a suitable real‑world dataset. |
| Runtime exceeds 6 h | CI job failure | Dynamic iteration reduction (FR‑007) and optional down‑sampling (FR‑008). |
| Memory > 7 GB | OOM crash | Enforce max 10 k nodes; stream large files where possible. |

---



