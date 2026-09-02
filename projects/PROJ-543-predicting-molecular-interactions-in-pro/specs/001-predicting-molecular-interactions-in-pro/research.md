# Research: Predicting Molecular Interactions in Protein-Ligand Complexes Using Graph Neural Networks

## Dataset Strategy

The project relies on the **PDBbind v2020 refined set** (or the closest verified proxy). This dataset provides 3D structural coordinates (PDB files) and experimental binding affinities (pKd/pKi) for protein-ligand complexes.

### Verified Datasets

| Dataset | Source URL | Access Method | Variables Available | Suitability |
|:--- |:--- |:--- |:---:--- |
| **PDBbind Complexes (Parquet)** | ` | `datasets.load_dataset("jglaser/pdbbind_complexes")` | 3D coordinates, atom types, pKd/pKi, resolution | **Primary**: Directly provides the necessary 3D coordinates and affinity labels. |
| **PDBbind Full (CSV)** | ` | `pandas.read_csv` | Metadata, affinity, links to PDB | **Supplementary**: Used for indexing if the parquet source lacks specific metadata. |
| **PDBbind Affinities** | ` | `datasets.load_dataset` | Processed affinities | **Backup**: If the primary source is unavailable. |

**Selection Rationale**: The `jglaser/pdbbind_complexes` parquet source is selected as the primary because it is verified to contain pre-processed structural data required for graph construction. If this specific file lacks explicit 3D coordinates for a specific entry, the pipeline will fallback to downloading the raw PDB files via the `biopython` `PDBList` or `rcsb` API. This fallback is budgeted for in the feasibility analysis to ensure the total runtime remains within limits.

**Data Availability & Feasibility**:
- **Open Access**: The Hugging Face sources are directly downloadable via programmatic API, satisfying the "no registration" constraint.
- **Size Management**: The full PDBbind refined set consists of a large collection of complexes. The raw PDB files are small (a few megabytes each). The total raw data size is manageable (< 50 GB), but the *processed* graph data (with 3D edges) will be larger.
- **Streaming Plan**: The `code/data/ingest.py` will use `datasets.load_dataset(..., streaming=True)` to iterate through complexes. Graphs will be constructed one-by-one and saved to `data/processed/` immediately, preventing RAM overflow.
- **Filtering**: Per FR-001 and T020, complexes with resolution > 2.5 Å will be filtered *before* graph construction to save compute. This is implemented as a pre-filter in the ingestion loop.

**Missing Variable Check**:
- The spec requires "explicit water-mediated interactions" (FR-009). The PDBbind refined set *does* contain explicit water molecules in the PDB files. The ingestion script will parse these. If the parquet source aggregates or removes waters, the code will fallback to downloading the raw PDB for complexes where water analysis is critical, or use the distance heuristic on the ligand-protein interface as a proxy.
- **Variable Fit**: The dataset contains `pKd` (outcome), `3D coordinates` (predictors), and `resolution` (covariate/filter). This is a perfect fit for the study. No synthetic data is needed.

## Methodology & Statistical Rigor

### 1. Graph Construction (FR-001)
- **Nodes**: Atoms with features: atomic number, formal charge, hybridization, hydrophobicity (calculated via RDKit).
- **Edges**:
 - *Covalent*: RDKit bond detection.
 - *Non-covalent*: Euclidean distance < 5.0 Å between any protein atom and ligand atom.
- **Steric Constraints**: The 5.0 Å cutoff explicitly encodes the steric environment, addressing the reviewer's concern about 3D physics.
- **Water Flagging**: A heuristic (distance < 3.5 Å to oxygen atoms) is used to flag water-mediated interactions (FR-009).

### 2. Model Training (FR-002, FR-007)
- **Architecture**: A multi-layer Message Passing Neural Network (MPNN) with 128 hidden units.
- **Loss**: Mean Squared Error (MSE) on pKd.
- **Hardware Strategy**:
 - **CPU-First**: Training runs on CPU with `batch_size` tuned to fit available RAM.
 - **GPU Escape Hatch**: If the model definition includes `device="cuda"`, the execution runner will detect the CUDA requirement and offload to Kaggle (16 GB VRAM). The plan uses a **scaled-down** approach: training on the full dataset but with fewer epochs (e.g., -30) or a smaller batch size if GPU memory is tight, to fit within the Kaggle kernel.
- **Early Stopping**: Triggered if validation loss does not improve for a specified number of epochs (FR-007).

### 3. Interpretability & Validation (FR-003 - FR-006, FR-008, Constitution Principle VII)
- **Attribution**: Integrated Gradients (IG) applied to the trained model to generate atom-level importance scores.
- **Clustering**: DBSCAN (eps=0.5, min_samples=5) on the coordinates of high-importance atoms (top [deferred] by score) to find recurring motifs.
- **Statistical Validation**:
 - **Null Distribution**: Generate a set of permutations by **shuffling the attribution scores** across the fixed atomic positions of the test set. This preserves the molecular graph topology and steric constraints, testing whether the observed clustering of high-importance atoms is statistically distinct from a random assignment of importance.
 - **Significance**: Compare observed cluster overlaps against the null distribution.
 - **Multiple Testing**: Apply Benjamini-Hochberg FDR correction (alpha=0.01) to the p-values of motif enrichment (FR-006, Constitution Principle VII).
 - **High/Low Affinity Discrimination**: Perform a **two-sample t-test** comparing the frequency of motif presence in high-affinity (pKd > 8) vs. low-affinity (pKd < 6) complexes. This ensures the motifs discriminate between affinity levels, satisfying Constitution Principle VII.
 - **Pharmacophore Matching**: Cross-reference clusters against an **independent** pharmacophore set (derived from a source not heavily represented in PDBbind v2020) using RMSD < 1.5 Å (FR-005). This mitigates the tautology risk of validating against the same data the model was trained on.

### 4. Power & Sample Size
- **Limitation**: The study is observational (PDBbind is a collection of crystal structures, not a randomized trial).
- **Acknowledgement**: Claims will be framed as "associational" or "predictive" rather than causal. The GNN+IG approach identifies correlations between substructures and binding affinity, not causal mechanisms.
- **Power**: With [deferred] complexes (after filtering), the sample size is sufficient for GNN training. The permutation test (sufficient iterations) and t-test provide robust significance estimation for the motifs.

## Decision Rationale: CPU vs. GPU
- **Decision**: The plan is **CPU-first** for data ingestion and graph construction (these are not GPU-intensive). The GNN training is **GPU-optional** (via offload) because a 3-layer GNN on 10k graphs may take > 4 hours on CPU.
- **Rationale**: Running on CPU ensures the pipeline works on the free tier. The "GPU escape hatch" allows the *real* training to complete within the time limit if the CPU run is too slow. We do **not** fabricate a CPU approximation (e.g., a tiny synthetic model) because the spec requires a "3-layer message-passing GNN" on the real dataset. The offload ensures the real computation happens.

## Risk Mitigation
- **Risk**: PDBbind refined set lacks specific hydration data.
 - **Mitigation**: Use distance heuristic (3.5 Å) to flag water-mediated interactions (FR-009).
- **Risk**: Model overfitting on small subsets.
 - **Mitigation**: Strict train/val/test split with a dominant training proportion and early stopping.
- **Risk**: Graph construction memory overflow.
 - **Mitigation**: Stream data, process one complex at a time, and write to disk immediately.
- **Risk**: Tautology in pharmacophore validation.
 - **Mitigation**: Use an independent pharmacophore set for validation.
