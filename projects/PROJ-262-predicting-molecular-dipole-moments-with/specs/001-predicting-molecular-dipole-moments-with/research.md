# Research: Predicting Molecular Dipole Moments with Graph Neural Networks

## Research Question

To what extent does 3D conformational geometry provide independent predictive information for molecular dipole moments beyond 2D connectivity and atom types?

## Background

### Molecular Dipole Moments

The dipole moment is a vector quantity defined as the first moment of the charge distribution in a molecule. For a system of N point charges:

$$\vec{\mu} = \sum_{i=1}^{N} q_i \vec{r}_i$$

where $q_i$ is the charge of atom $i$ and $\vec{r}_i$ is its position vector. This formulation makes it clear that dipole moments depend fundamentally on spatial arrangement of charge centers, not merely atomic connectivity.

### QM9 Dataset

The QM9 dataset contains 134k small organic molecules with quantum mechanical properties computed at the B3LYP/6-31G(2df,p) level. Each molecule includes:
- 3D atomic coordinates (optimized geometry)
- Atom types (C, N, O, F, H)
- Bond connectivity
- Dipole moment reference values (in Debye)

**Dataset Strategy**:

| Dataset | Source URL | Loader | Use Case | Notes |
|---------|------------|--------|----------|-------|
| QM9 (parquet) | https://huggingface.co/datasets/yairschiff/qm9/resolve/main/data/train-00000-of-00001-baa918c342229731.parquet | `datasets.load_dataset()` | Primary training data | Verified source per # Verified datasets block |
| QM9 (parquet alt) | https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet | `datasets.load_dataset()` | Fallback if primary unavailable | Verified source per # Verified datasets block |
| QM9 (parquet alt) | https://huggingface.co/datasets/hadoan/enthalpy-QM9-1k/resolve/main/data/train-00000-of-00001-ffd5f7908688c934.parquet | `datasets.load_dataset()` | Smaller subset option | Verified source per # Verified datasets block |
| QM9 DOI | 10.1038/sdata.2014.22 | N/A | Citation reference only | NO verified source found; cite as DOI only |

**Note**: The DOI 10.1038/sdata.2014.22 is the original publication reference but has NO verified source in the # Verified datasets block. All programmatic loading MUST use the verified HuggingFace parquet URLs above.

### Literature Context

| Citation | Key Finding | Relevance |
|----------|-------------|-----------|
| SchNet (Schütt et al., 2017) | 3D-equivariant GNNs outperform 2D methods on quantum properties | Foundation for GNN architecture choice |
| Coulomb Matrix (Rupp et al., 2012) | 2D descriptors can capture electronic structure | Baseline comparison target |
| Morgan Fingerprints (Rogers & Hahn, 2010) | Standard 2D molecular fingerprints | RF baseline feature set |

**Note**: Full bibliographic details with verified URLs to be added in paper artifact; DOI 10.1038/sdata.2014.22 cited for QM9 dataset origin.

## Methodology

### Data Pipeline

1. **Download**: Fetch QM9 from verified HuggingFace source; verify checksum
2. **Subset**: Random 10k molecules with fixed seed (42)
3. **3D Extraction**: Atomic coordinates, atom types, bond connectivity
4. **2D Descriptors**: Morgan fingerprints (radius=2, n_bits=2048), Coulomb matrices

### Model Architecture

**GNN (SchNet-style)**:
- 3 interaction blocks
- Gaussian distance expansion (50 bins, 0-10 Å)
- 128-dimensional node embeddings
- Readout: sum pooling + MLP head

**Random Forest Baseline**:
- 100 trees
- Max depth: 10
- Features: Morgan fingerprints + Coulomb matrix flattened

### Training Protocol

- 5 random seeds (42, 123, 456, 789, 101112)
- 80/10/10 train/validation/test split
- Early stopping (patience=10 epochs, min_delta=1e-4)
- 50 epochs maximum
- CPU-only mode (batch size=64)

### Evaluation Metrics

- MAE (mean absolute error) in Debye
- RMSE (root mean square error) in Debye
- Paired t-test (α=0.05) comparing RMSE distributions

### Feature Attribution

**Random Forest**: Permutation importance (5 repeats)

**GNN**: Saliency mapping on node embeddings (gradient-based)

**Interpretation**: Rank features by contribution to predictive variance; correlate with chemical intuition (electronegative atom placement, local bond angles)

## Limitations & Assumptions

### Explicit Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| QM9 gas-phase DFT only | No experimental validation | Documented as out-of-scope per spec |
| Single conformer per molecule | Ignores conformational ensemble effects | Acknowledged as future work |
| No hydration state modeling | May miss solvent effects on dipole | Cited as limitation in research.md |
| CPU-only training | Limits model scale | Constrained by 6h runtime requirement |

### Reviewer Feedback Integration

**rosalind-franklin-simulated (hydration)**: Water content can shift molecular conformations (e.g., DNA A-form to B-form). QM9 molecules are gas-phase DFT calculations without explicit solvent. This is a known limitation; hydration effects are out-of-scope for this computational feature but should be addressed in future work with experimental validation.

**rosalind-franklin-simulated (conformational ensembles)**: QM9 provides single lowest-energy conformers per molecule. True conformational ensemble modeling would require sampling multiple conformers at defined energy thresholds. This is documented as future work; current study isolates single-conformer geometry signal.

**richard-feynman-simulated (feature attribution)**: Saliency mapping + permutation importance directly address "which part of the graph is doing the work." Physics-informed loss (Raissi PINN approach) noted as potential enhancement but out-of-scope for current feature scope.

**richard-feynman-simulated (physical validation)**: Physical measurement validation (X-ray diffraction, dielectric spectroscopy) is explicitly out-of-scope per spec assumptions. Validation against QM9 DFT reference data (B3LYP/6-31G(2df,p)) serves as ground truth for this computational feature.

## Success Criteria Alignment

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| SC-001: GNN MAE < RF MAE | Test set MAE comparison | Statistically significant (p < 0.05) |
| SC-002: 3+ structural features | Attribution ranking | Top 3 features identifiable |
| SC-003: Runtime < 6h | Wall-clock measurement | Complete on 2 CPU cores |
| SC-004: Paired t-test significance | RMSE distribution comparison | p < 0.05 across 5 seeds |
| SC-005: Reproducibility | RMSE variance across seeds | < 10% variance |
