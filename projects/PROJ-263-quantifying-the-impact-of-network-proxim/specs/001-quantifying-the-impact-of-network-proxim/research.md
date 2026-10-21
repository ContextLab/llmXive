# Research: Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale‑Free Networks

## 1. Objective
Quantify how geographic proximity (modeled by an exponential decay of transmission probability with Euclidean distance) shifts the epidemic threshold and peak infection rate of an SIR process on a scale‑free network, and assess whether this shift exceeds what would be expected under random spatial arrangements.

## 2. Dataset Strategy
| Role | Dataset | Source URL(s) | Availability | Notes |
|------|---------|---------------|--------------|-------|
| **Synthetic Control (MDS coordinates)** | MDS JSON (various) | `https://huggingface.co/datasets/Heitechsoft/Wizard_Vicuna_MDS/...` (see verified list) | Direct download via `datasets.load_dataset` (streaming) | Used when a network lacks coordinates; acts as the *synthetic‑control* condition (FR‑011). |
| **Optional SIR fragments** | SIR parquet | `https://huggingface.co/datasets/ebeaulac/siriccam-sq-400px-16frag-12-25-train-fragments/...` | Direct download via `datasets.load_dataset` | Not required for primary analysis; retained for possible future extensions. |
| **Network Topology** | **None** (no verified open dataset with real coordinates) | — | — | No open, verifiable scale‑free network with geographic coordinates exists. Consequently, we will **generate** a synthetic Barabási‑Albert (BA) graph (10 k nodes) using `networkx.barabasi_albert_graph`. Real‑world geographic effects cannot be examined; the study will focus on synthetic coordinates vs. randomised coordinates. This limitation is explicitly reported in the final manuscript. |

*Rationale*: The lack of a verified real‑world network with coordinates forces a redesign. A synthetic BA graph preserves the hallmark power‑law degree distribution while allowing us to attach synthetic coordinates (via MDS on the adjacency matrix) and randomised controls. This satisfies FR‑001 in a *fallback* sense and preserves the core scientific question about spatial modulation, albeit on synthetic geometry.

## 3. Methodology

### 3.1 Network Construction
1. Generate a BA graph `G` with `n=10,000` nodes and `m=5` edges per new node (scale‑free degree distribution).  
2. Extract the largest connected component (LCC); log size of discarded components (FR‑008).  
3. Compute a shortest‑path distance matrix `D_sp` (graph distance) for use in MDS.  
4. Apply Classical MDS (`sklearn.manifold.MDS(metric=True, n_components=2, random_state=SEED)`) on `D_sp` to obtain 2‑D synthetic coordinates `X_mds`. Store as `data/derived/coordinates_mds.csv`. This constitutes the *empirical‑spatial* condition (though synthetic).  

### 3.2 Null Model Generation
- Randomly permute the rows of `X_mds` 100 times, preserving the adjacency matrix. Each permutation yields a null coordinate set `X_null_i`.  

### 3.3 SIR Simulation
- Discrete‑time SIR with synchronous updates.  
- Transmission probability for edge (i,j):  
  \[
  \beta_{ij} = \beta_0 \times \exp(-\lambda \, d_{ij})
  \]
  where `d_{ij}` is Euclidean distance between node coordinates (real or synthetic).  
- Recovery probability `γ` fixed at 0.1 (standard in literature).  
- Initial infected fraction = 5 % (randomly selected).  
- Simulate until no infected nodes remain or max steps = 500.  

### 3.4 Parameter Sweep
- **β₀ sweep**: 0.01 → 0.5 (step = 0.01).  
- **λ values**: {0.05, 0.1, 0.2}.  
- For each (`β₀`, λ) pair, run **50 Monte‑Carlo** replicates (different seeds).  

### 3.5 Epidemic Threshold Estimation (FR‑015)
- For each λ, binary‑search over β₀ to locate the smallest β₀ where ≥5 % of nodes become infected in >50 % of Monte‑Carlo runs.  
- If no β₀ in the sweep satisfies this, report **“> 0.5”** (i.e., undefined) as per FR‑009.  

### 3.6 Statistical Testing (FR‑014, FR‑010)
- Compare the distribution of peak infection rates between:
  1. **Spatial model** (λ > 0, using `X_mds`).  
  2. **Null models** (λ > 0, using each `X_null_i`).  
- Use a **two‑sample permutation test** (10 000 permutations) to obtain a test statistic (difference in means) and a p‑value.  
- Compute **Cohen’s d** as effect size.  
- Apply **Bonferroni correction** for the three λ values (family‑wise α = 0.05/3).  

### 3.7 Sensitivity Analysis (FR‑006)
- Report how the estimated epidemic threshold shifts across λ ∈ {0.05, 0.1, 0.2}.  

### 3.8 Runtime & Memory Guardrails (FR‑007)
- The pipeline logs elapsed wall‑clock time after each batch of 10 Monte‑Carlo runs.  
- If cumulative time > 5 h, remaining Monte‑Carlo iterations are truncated to keep total ≤ 6 h.  
- If the graph exceeds ~10 k nodes (memory > 6 GB), a subgraph of 10 k nodes is sampled uniformly from the LCC and a warning is logged.  

## 4. Statistical Rigor Checklist
| Requirement | Implementation |
|-------------|----------------|
| Multiple‑comparison correction | Bonferroni across λ values (3 tests). |
| Power justification | 50 Monte‑Carlo runs per config provide a Monte‑Carlo standard error ≈ √(p(1‑p)/50) ≤ 0.07 for binary outcomes; noted as a limitation in the manuscript. |
| Causal inference | Observational simulation; claims are strictly *associational* (per Constitution Principle VI). |
| Measurement validity | The SIR model and exponential distance decay are standard in epidemiology (cited to classic textbooks; will be validated by Reference‑Validator). |
| Predictor collinearity | β₀ and λ are independent design parameters; no collinearity concerns. |

## 5. Expected Deliverables
- CSV file `simulation_results.csv` (schema in `contracts/simulation_output.schema.yaml`).  
- Null‑model CSV `null_results.csv`.  
- Figures: `threshold_curve.png`, `infection_trajectory.png`, `spatial_heatmap.png`.  
- A concise markdown report summarizing thresholds, effect sizes, p‑values, and sensitivity plots.  

## 6. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No real‑world network with coordinates | Inability to test genuine geographic effect | Explicitly state limitation; use synthetic coordinates (MDS) and treat results as proof‑of‑concept. |
| Runtime exceeds 6 h | Pipeline failure on CI | Dynamic iteration reduction (FR‑007) and optional subgraph down‑sampling (FR‑008). |
| Memory > 7 GB | CI out‑of‑memory crash | Enforce max 10 k nodes; stream any large auxiliary files (MDS JSON). |

---
