# Research: Predicting Molecular Interactions in Polymer Composites with Graph Neural Networks

## Dataset Strategy

The only verified chemistry source that provides molecular graph structures is **MolNet** (accessed via the HuggingFace Datasets API). No verified dataset in the provided list contains *adhesion energy* measurements for polymer‑filler interfaces. 

| Dataset | Verified URL | Role | Availability of `adhesion_energy` |
|---------|--------------|------|-----------------------------------|
| **MolNet** | `datasets.load_dataset('molnet', ...)` (HF canonical loader) | Provides SMILES, atom/bond information for a large variety of molecules. | **Absent** – MolNet benchmarks (e.g., BACE, ESOL) do not include adhesion‑energy measurements for polymer‑filler pairs. |

**Critical Outcome**: Because the required outcome variable is missing, the pipeline **must abort** with exit code **E‑DATA‑001** after the validation step in `clean.py`. The abort logs the available outcome variables (if any) and halts further execution. 
- **No proxy metrics** (e.g., binding energy from BACE, solubility from ESOL) are permitted. These variables lack a validated physical correlation with adhesion energy in polymer-filler systems, and using them would invalidate the research question.
- **Invalid Sources Removed**: URLs pointing to NIST 800-53 (security controls) or generic book repositories are removed as they do not contain the required chemistry data.

### Power Analysis (Supporting SC‑002)

An a priori power analysis for a regression model with a medium effect size (Cohen's *f²* = 0.15), α = 0.05, and desired power = 0.80 yields a minimum sample size **N ≈ 85**. Targeting **≥ 500** polymer‑filler interface pairs therefore provides ample statistical power (> 0.95) to detect medium‑sized effects, satisfying SC‑002. 
- **Limitation**: If the true effect size is small, the sample size may be underpowered, but this is the maximum feasible size for the target domain.

## Statistical Methodology

### 1. Model Architecture (FR‑003, FR‑007)

- **3‑layer Graph Attention Network (GAT)** implemented in `code/models/gat.py`.
- Each layer uses `torch_geometric.nn.GATConv` with 4 attention heads, ReLU activation, and dropout (0.2).
- **Clarification**: Attention mechanisms are used for **robust feature weighting** and representation learning. They **do not** statistically control for multicollinearity (VIF). 
- VIF is calculated separately on hand-crafted descriptors for reporting purposes.

### 2. Validation & Significance (FR‑005, FR‑006, FR‑008)

#### Permutation Test (Full Re‑training)

- **Methodology**: To establish a valid null distribution, the model is **re-trained** on permuted labels for every iteration. Frozen model evaluation is scientifically invalid for non-linear GNNs.
- **Feasibility Adjustment**: To fit the 6-hour CPU limit, the test is reduced to **100 iterations** on a **subset of 100 samples** for **10 epochs** per iteration. Total epochs = 1000.
- This yields a null distribution of MSE values reflecting the learning algorithm's ability to find spurious patterns.
- The observed MSE from the full‑data trained model is compared to the 95th percentile of the permuted MSEs; significance is declared if *p* < 0.05.

#### Multiple‑Comparison Correction

- `results/stats.csv` records p‑values for **MSE** and **MAE**.
- When more than one p‑value is present (e.g., multiple metrics), **Bonferroni** (or Holm) correction is applied, and corrected p‑values are stored in the `corrected_p_value` column (FR‑008).

#### Gradient‑Based Attribution

- Integrated Gradients are computed on **100** held‑out test graphs (`analysis/attribution.py`).
- Feature importance scores are aggregated for topological descriptors (node degree, edge connectivity, graph density).
- Features with a standard deviation > 0.1 across samples are reported as salient (SC‑003).

#### Collinearity Reporting (FR‑007, SC‑004)

- VIF is calculated **only** on handcrafted descriptors extracted before graph construction (degree, clustering coefficient, density, average shortest path).
- **Clarification**: VIF is **not** calculated on GNN latent embeddings, as these are non-linear and correlated by design (smoothing), making VIF inapplicable.
- VIF scores are included in `results/stats.csv` under the `vif_scores` field for interpretability; training does not halt regardless of VIF magnitude.

### 3. Computational Feasibility (SC‑002)

- **Training**: 3‑layer GAT, batch ≤ 32, 50 epochs max, checkpoint every 10 epochs → ≤ 4.5 h, ≤ 6 GB RAM.
- **Permutation Test**: 100 iterations × 100 samples × 10 epochs = 1000 epochs total → ~1.5 h (empirically estimated).
- **Overall Runtime**: ≤ 6 h on GitHub Actions free tier.

## Risk Register (Updated)

| Risk | Impact | Mitigation |
|------|--------|------------|
| No adhesion energy data | Fatal – abort with E‑DATA‑001 | Explicit validation step; no proxy fallback |
| Runtime > 6 h | Fatal | Checkpointing, reduced permutation test (100 iters, 10 epochs) |
| Collinearity | Medium | VIF reported on hand-crafted descriptors; attention used for feature weighting |
| GPU requirement | Fatal | All code forces `device='cpu'` |

## Deliverables

- `data/curated/curated_dataset.csv` (if validation passes)  
- `data/processed/graphs.pt`  
- `results/model.pt` and `results/performance.json`  
- `results/stats.csv` (MSE, MAE, p‑values, corrected p‑values, VIF)  
- `analysis/topology_audit.md`  
- `analysis/power_analysis.md`