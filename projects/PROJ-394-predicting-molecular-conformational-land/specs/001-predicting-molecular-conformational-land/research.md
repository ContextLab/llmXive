# Research: Predicting Molecular Conformational Landscapes with Variational Autoencoders

## Scientific Hypothesis

**Hypothesis**: 2D molecular topology (graph structure) contains sufficient information to *approximate* the output of a standard 2D->3D conformational search pipeline (ETKDG + GFN2-xTB) for small organic molecules.

**Rationale**: While 3D geometry is the direct determinant of energy, the 2D graph encodes steric constraints, bond orders, and functional groups that heavily influence the conformational landscape. A VAE trained on 2D graphs may learn a latent space that correlates with the "conformational energy potential" of a molecule, effectively learning the complex function mapping 2D topology to 3D energy rankings.

## Dataset Strategy

### Verified Datasets

| Dataset | Source URL | Usage | Verification |
|---------|------------|-------|--------------|
| **ZINC15 (Processed)** | ` | Training and Evaluation | Verified: Parquet format, contains SMILES. |
| **GFN2-xTB Reference** | N/A (Software) | Energy Calculation | Community standard (Bannwarth et al., 2019). |

**Dataset Fit Analysis**:
The ZINC15 dataset provides the necessary **SMILES strings** (2D topology) required for the VAE input (FR-001). However, the dataset **does not** contain pre-computed 3D conformers or energies. This is consistent with the project assumption that energies must be computed on-the-fly using GFN2-xTB (FR-004).
* **Variable Fit**: The dataset has `SMILES` (Predictor). The target variable (Conformer Energy Ranking) is **generated** via the GFN2-xTB pipeline, not retrieved from the dataset. This is a valid strategy as per the spec's assumption that "Pre-computed DFT or semi-empirical conformer energies are NOT available."
* **Constraint**: The dataset size must be sufficient to train the VAE. The spec requires ≥5,000 molecules for training and ≥1,000 for testing. The ZINC15 processed file is large enough to satisfy this.

### Data Loading Strategy

1. **Download**: Fetch `zinc_processed.parquet` from the verified HuggingFace URL.
2. **Checksum**: Compute and store MD5/SHA256 hash.
3. **Subset**: Randomly split into Train (≥5,000) and Test (≥1,000) sets using a fixed seed.
4. **Conformer Generation (Train)**: For each molecule in the training set, generate **10** conformers using RDKit ETKDG.
5. **Conformer Generation (Test)**: For each molecule in the test set, generate **20** conformers using RDKit ETKDG.
6. **Energy Calculation (Train)**: Run GFN2-xTB (single-point) on each training conformer.
7. **Energy Calculation (Test)**: Run GFN2-xTB (multi-start optimization) on each test conformer.
8. **Parallelization**: Use `joblib` with `n_jobs=2` to parallelize conformer generation and energy calculations across the 2-CPU runner.
9. **Filtering**: Discard molecules where conformer generation or energy calculation fails (target <5% failure rate).

## Methodological Rigor

### Statistical Rigor (Quantitative)

1. **Multiple Comparison Correction**:
 * **Method**: **Mixed-Effects Model** (Random intercept for molecule) or **Permutation Test** on aggregate correlation.
 * **Application**: Instead of Bonferroni correction across molecules (which assumes independence), we model the correlation as a fixed effect with a random intercept for each molecule to account for varying "difficulty" (e.g., number of rotatable bonds).
 * **Rationale**: Molecules vary in complexity; treating each as an independent hypothesis test is statistically inappropriate. The mixed-effects model provides a more robust estimate of the overall correlation.

2. **Sample Size / Power Analysis**:
 * **Method**: `statsmodels.stats.power.tt_solve_power` (adapted for Spearman correlation via approximation).
 * **Parameters**: Effect size (ρ) = 0.5 (moderate-to-strong), Power (1-β) = 0.80, α = 0.05.
 * **Result**: Expected minimum n ≈ 128 (FR-012). The test set (n ≥ 1000) significantly exceeds this, ensuring robust detection of the hypothesized effect.
 * **Limitation**: If the observed ρ is lower than 0.5, the power to detect it will be lower. The plan explicitly reports the observed effect size and power.
 * **Negative Result**: A weak correlation (ρ < 0.5) is a valid scientific outcome indicating 2D topology is insufficient. The power analysis is framed to detect *any* non-zero correlation, not just a strong one.

3. **Causal Inference**:
 * **Statement**: The study is **observational** and **associational**. No causal claims are made (FR-009).
 * **Reasoning**: The VAE learns correlations between 2D topology and 3D energy landscapes. We do not manipulate the topology to observe causal changes in energy in a controlled experiment; we observe the natural correlation.

4. **Measurement Validity**:
 * **Instrument**: GFN2-xTB is used as the "gold standard" for reference energies.
 * **Evidence**: GFN2-xTB is a community-standard semi-empirical method known for accuracy in conformational landscapes (Bannwarth et al., 2019) and is computationally feasible for this scale.
 * **Validation**: The workflow will validate that >95% of conformers converge (FR-011).

5. **Collinearity**:
 * **Issue**: 3D descriptors (e.g., radius of gyration) are derived from the 3D geometry, which is correlated with the energy.
 * **Handling**: In the ablation study (FR-007), 3D descriptors are concatenated to the latent vector. The plan acknowledges that these descriptors are **definitionally related** to the energy. The improvement (Δρ) is reported descriptively, and the collinearity is explicitly noted. The VAE's performance is compared against this "upper bound" to determine the information content of 2D topology alone.
 * **Ablation Logic**: The ablation uses 3D descriptors derived from an **independent** conformer generation method (e.g., random torsion sampling) to avoid tautology. If this is not feasible, the ablation will be redefined as 'VAE vs. ECFP4' only.

### Computational Feasibility

* **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, No GPU).
* **Strategy**:
 * **VAE**: Small architecture (MPNN, 64-dim latent). Training on CPU using `torch.set_num_threads(2)`. Batch size tuned to fit RAM.
 * **GFN2-xTB**: Executed via subprocess with `joblib` parallelization (`n_jobs=2`).
 * **Sampling**: Training set uses 10 conformers/molecule; Test set uses 20 conformers/molecule.
 * **Time Budget**: 6 hours. The pipeline is ordered: Data Download -> Conformer Gen/Energy (parallelized) -> VAE Training -> Evaluation.

### Methodological Limitations

* **Circular Validation**: The study validates the hypothesis that "2D topology predicts conformer energy rankings" by training a model to predict rankings derived from GFN2-xTB energies of conformers generated by RDKit ETKDG. However, the 'ground truth' (energy ranking) is computed on geometries that are *not* independent of the 2D topology used for prediction. The 2D graph *determines* the set of possible conformers generated by ETKDG. The VAE is effectively learning to predict the outcome of a deterministic (or near-deterministic) function of its own input (2D graph -> ETKDG -> GFN2-xTB). This is not an empirical test of whether 2D topology *contains* the information, but a test of whether the VAE can *approximate* the ETKDG/GFN2-xTB pipeline. The validation target is definitionally dependent on the predictor's input domain.
* **Reframed Contribution**: The study's contribution is reframed as: "Can a 2D-based latent space efficiently approximate the output of a standard 2D->3D conformational search pipeline?" This is a valid machine learning task (learning a complex function), even if the function is definitionally dependent on the input.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use GFN2-xTB instead of DFT** | DFT is computationally infeasible for >1,000 molecules with multiple conformers on a 2-core CPU runner. GFN2-xTB is the accepted compromise for conformational landscapes. |
| **Use ZINC15 (Parquet) from HuggingFace** | Verified source. Contains necessary SMILES. No pre-computed energies, which aligns with the "on-the-fly" requirement. |
| **Mixed-Effects Model instead of Bonferroni** | Molecules vary in difficulty; treating each as an independent hypothesis test is statistically inappropriate. |
| **Associative Claims Only** | Required by FR-009. The study design does not support causal inference. |
| **No Experimental Diffraction Validation** | Not feasible within the 6-hour CPU constraint or the scope of the ZINC15 dataset. The study validates against a physics-based baseline (GFN2-xTB), not experimental data. |
| **Reduced Conformer Count for Training** | To meet a constrained training budget, the training set uses 10 conformers/molecule (vs. 20 for test). |
| **Parallelization (joblib)** | Essential to meet the 6-hour budget on a 2-CPU runner. |