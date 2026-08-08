# Research: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

## Research Question
Can lightweight, heterophily-aware Graph Neural Networks trained on the QM9 dataset outperform traditional Random Forest baselines (using Morgan fingerprints) in predicting molecular reactivity proxies (HOMO-LUMO gap) under strict CPU-only constraints?

## Dataset Strategy

| Dataset | Purpose | Source (Verified) | Access Method | Constraints/Notes |
|:--- |:--- |:--- |:--- |:--- |
| **QM9 (Parquet)** | Primary training data (SMILES, DFT properties). | `torch_geometric.datasets.QM9` (Ramakrishnan et al., 2014) | `torch_geometric.datasets.QM9` | Must stream to fit RAM. Target: HOMO-LUMO gap derived from columns `homo` and `lumo` (in eV). |
| **Reference Substructures** | Ground truth for attribution (FR-008). | **Curated from Literature** | Static asset (curated in `data/raw`) | Source: *J. Chem. Inf. Model.* 2020, 60, 12, 5785–5796 (). **Extraction**: Table 2, Entries 1-50. |
| **Kinetic Dataset** | Proxy consistency check (FR-009). | **Curated from Literature** | Static asset (curated in `data/raw`) | Source: *J. Phys. Chem. A* 2018, 122, 15, 4053–4062 (). **Extraction**: Table 3, Entries 1-20. |

**Decision/Rationale**:
- **CPU-First**: The QM dataset is large. Direct loading exceeds the RAM limit of the GitHub Actions runner. The plan uses `torch_geometric` which handles streaming/loading efficiently.
- **GPU Escape Hatch**: The primary models (Spectral GNN, Heterophily GNN) are implemented in PyTorch with `device='cpu'`. The "GPU escape hatch" is a **failure recovery mechanism** only: if the CPU run fails with OOM or timeout, the pipeline re-runs on a Kaggle GPU with a smaller batch size. It is not a standard execution path.
- **Missing Data**: No public API exists for the "Curated Reference Set" or "Kinetic Dataset". The plan mandates manual curation from specific literature sources (DOIs above) to satisfy FR-008 and FR-009.

## Methodology

### 1. Data Ingestion & Preprocessing (FR-001)
- **Ingestion**: Download QM9 via `torch_geometric.datasets.QM9`.
- **Graph Construction**: Convert SMILES to `torch_geometric.data.Data` objects using RDKit.
 - *Node Features*: Atomic number, hybridization, formal charge.
 - *Edge Features*: Bond type (single, double, triple, aromatic), conjugation, ring membership.
- **Filtering**: Exclude molecules with invalid SMILES (< 0.1% expected). Log exclusions to `artifacts/exclusion_report.json`.
- **Splitting**: Apply Murcko Scaffold split with a majority allocation to the training set, with smaller portions reserved for validation and testing.
 - **Scaffold Similarity Filter**: After splitting, calculate Tanimoto similarity (Morgan fingerprint, radius=2) between test molecules and training molecules. If similarity > 0.8, move the test molecule to a "near-miss" holdout or exclude it to ensure true generalization to unseen chemotypes.

### 2. Model Training (FR-002, FR-003)
- **Spectral GNN**: A lightweight graph convolution using spectral filters (e.g., ChebNet or simple Laplacian-based).
- **Heterophily GNN**: Based on VR-GNN principles (e.g., GPRGNN or H2GCN) to handle low homophily.
 - **Heterophily Justification**: While local atom types are similar, the *electronic properties* (HOMO/LUMO) exhibit low homophily across bonds (e.g., a C-C bond in a conjugated system connects atoms with different orbital energies). This justifies the Heterophily-aware architecture for this specific target variable.
- **Baseline**: Random Forest trained on Morgan Fingerprints (radius=2, nBits=2048).
- **Training**: 50 epochs, early stopping on **validation loss** (using the [deferred] split carved from the [deferred] Train set). `device='cpu'`.
 - **Strict Separation**: A portion of the Test set is held out completely; no hyperparameter tuning or early stopping uses data from this set.
- **Memory Safety**: Batch size adjusted dynamically; if RAM > 4GB, reduce batch size or sample subset.

### 3. Evaluation & Attribution (FR-005, FR-006)
- **Metrics**: MSE, MAE, Pearson R (SC-001, SC-002).
- **Statistical Test**: Paired t-test on prediction errors (GNN vs. RF) using scaffold split (SC-002). Bonferroni correction applied for multiple comparisons.
- **Attribution**: GNNExplainer to identify top 5 structural features (SC-003).
 - **Attribution Validation Metric**:
 - *Algorithm*: For each molecule, extract the top-k attributed subgraph, generate its Morgan fingerprint, and compute Tanimoto similarity with fingerprints of the reference set.
 - *Score*: **Mean Maximum Tanimoto Similarity (MMTS)** = Mean(max Tanimoto similarity) across the test set.
 - *Null Model*: Compare MMTS against a baseline where subgraphs are selected randomly. If MMTS does not exceed the null baseline, the attribution is deemed non-informative.
 - *Threshold*: MMTS > Null Baseline + 0.1.
 - **Scientific Limitation**: The model predicts the HOMO-LUMO gap. The attribution is validated against the *gap's known drivers* (thermodynamic substructures), not general chemical reactivity. This avoids circular logic.

### 4. Proxy Validation (FR-009, SC-006)
- **Qualitative Trend Check**: Correlate predicted HOMO-LUMO gaps with experimental reaction rates from the kinetic dataset.
- **Filtering**: Restrict analysis to **thermodynamically controlled reactions** (e.g., simple additions, electron transfers) where the HOMO-LUMO gap is a known dominant predictor. Exclude kinetically controlled reactions (e.g., SN2 with high activation barriers) where the correlation is not expected to hold.
- **Metric**: Visual inspection of monotonic trend. Acknowledge n=20 is insufficient for robust statistical validation; used for trend confirmation and outlier detection only. **No statistical claim of validation is made.**

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: Bonferroni correction applied if multiple metrics are tested simultaneously.
- **Power Analysis**: Acknowledged limitation: Sample size is fixed by QM9 subset. Power is assumed sufficient for large effect sizes (GNN vs. RF) but may be low for subtle differences.
- **Causal Inference**: Claims are strictly associational. No causal claims are made about molecular structure causing reactivity; the model learns correlation.
- **Collinearity**: Node features (atomic number) and edge features (bond order) are inherently related. The plan acknowledges this collinearity and reports feature importance descriptively, not as independent causal effects.
- **Independence**: A substantial majority split of the dataset combined with a Tanimoto similarity filter ensures the test set is distinct from the training set. A post-hoc check (T032) will verify error independence; if violated, a non-parametric test (Wilcoxon) will be used.

## Risks & Mitigations
- **Risk**: QM9 download fails or API unreachable.
 - *Mitigation*: Retry logic (limited attempts, exponential backoff). Exit with clear error if failed.
- **Risk**: Memory OOM during graph construction.
 - *Mitigation*: Stream processing; dynamic batch size reduction; fallback to 10k molecule sample if full set fails.
- **Risk**: HOMO-LUMO gap is a poor proxy for reactivity.
 - *Mitigation*: Validate against the external kinetic dataset (SC-006) with strict filtering for thermodynamically controlled reactions. If correlation is weak, the limitation is explicitly reported as a "Consistency Check" rather than "Validation".
