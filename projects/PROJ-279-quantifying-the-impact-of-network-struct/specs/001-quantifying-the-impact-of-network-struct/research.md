# Research: Quantifying the Impact of Network Structure on Heat Transport in Amorphous Silicon

## Dataset Strategy

The study relies on molecular dynamics (MD) trajectories of amorphous silicon (a-Si). The following datasets are identified. Note: The "Verified datasets" block in the input spec currently only lists "LOOCV: NO verified source found". This indicates that **no specific URL for an a-Si trajectory with thermal conductivity has been pre-verified in this context**.

**Critical Finding**: The spec assumes the existence of a-Si trajectories with pre-calculated thermal conductivity. However, the verified dataset list is empty for this specific data type.
- **Action**: The implementation will attempt to locate a-Si datasets from standard repositories (e.g., Zenodo, Materials Cloud, or HuggingFace) during the `download.py` phase.
- **Constraint**: If no verified source is found with both *structure* and *thermal conductivity* metadata, the pipeline will **NOT abort**. Instead, it will switch to **Structure-Only Mode** (see Tiered Execution). In this mode, the project will test H-003 (Ring Statistics) and H-004 (Feature Importance on available features), but will explicitly mark H-001 and H-002 as "Untestable" in the final report.
- **Assumption for Planning**: We assume a dataset exists that provides:
    1.  Atomic coordinates (xyz, cif, or lammps dump).
    2.  Thermal conductivity values (experimental or Green-Kubo derived) **IF** Full Mode is to be executed.
    3.  System size metadata (atom count).
    4.  **Distinct Ensemble Flag**: If thermal conductivity is provided, metadata must indicate it was derived from a distinct ensemble or experimental data, not the same snapshot used for topology.

**Potential Sources (to be verified at runtime):**
- *Zenodo*: Search for "amorphous silicon thermal conductivity trajectory".
- *Materials Cloud*: Search for "a-Si MD".
- *HuggingFace Datasets*: Check for `matbench` or similar materials science collections.

*Note: If the dataset lacks thermal conductivity values, the project will proceed with Structure-Only Mode to ensure partial scientific output (topological characterization). No Green-Kubo simulation will be attempted due to the 6-hour CPU limit.*

## Methodological Rationale

### Graph Construction
- **Cutoff Radius**: A sensitivity analysis will be performed at 2.8, 3.0, and 3.2 Å. This range covers the first coordination shell of a-Si (typically ~2.35 Å bond length, with a cutoff ~3.0 Å to include neighbors).
- **Bond Definition**: Edges are created if distance $d_{ij} < r_{cutoff}$.
- **Handling Defects**: Atoms with coordination < 3 or > 5 will be flagged (Edge Case: unexpected coordination).

### Descriptor Calculation
- **Topological**:
    - *Ring Statistics*: Using the shortest-path algorithm (e.g., `networkx` or `graph-tool`) to count rings of size 3-10.
    - *Bond Orientational Order (Q6)*: Calculated using Steinhardt parameters to quantify local symmetry.
    - *Clustering Coefficient*: To measure local connectivity density.
    - **Covariates**: **Local Atomic Density** and **Mean Coordination Number** will be calculated as explicit covariates to control for confounding effects (methodology-332fa9fe).
- **Vibrational**:
    - **No Internal Calculation**: The plan explicitly **does not** calculate VDOS internally (no mass-spring fallback) to avoid construct validity risks (methodology-3351023c).
    - **Conditional Inclusion**: VDOS and Participation Ratios are **only** included if they are **pre-calculated** and provided in the dataset metadata.
    - **Independence Check**: If VDOS is present, `validation.py` will verify that it was derived from a **distinct ensemble** or experimental data. If VDOS is derived from the same snapshot, it will be excluded to prevent circular validation (scientific_soundness-2f09c60a).
    - **Omission Logic**: If pre-calculated VDOS is absent, the `VibrationalDescriptor` entity is **completely omitted** from the feature matrix, rather than populating with nulls (plan_consistency-91a16f4c).

### Statistical Analysis
- **Dimensionality Reduction**: For N < 30, the feature set will be reduced via **PCA** (retaining [deferred] variance) or **L1-regularization (Lasso)** to prevent overfitting (scientific_soundness-4f48d641).
- **Stability Selection**: A bootstrapping protocol will be used to assess the stability of feature importance ranks across resamples (methodology-0a07cdcd).
- **Models**:
    - *Ridge Regression*: To handle potential multicollinearity among topological descriptors. **Covariates (Density, Coordination)** will be included to partial out density effects.
    - *Random Forest*: To capture non-linear interactions (if N allows after reduction).
- **Validation**:
    - If $N \ge 30$: 5-fold Cross-Validation.
    - If $N < 30$: Leave-One-Out Cross-Validation (LOOCV).
- **Hypothesis Testing**:
    - Pearson correlation ($r$) and p-values will be computed for the top predictor.
    - Feature importance will be extracted from the Random Forest model.
    - **Partial Correlation**: Correlation between topological descriptors and k will be reported **after controlling for density**.

## Statistical Rigor & Limitations

1.  **Multiple Comparisons**: If multiple descriptors are tested for correlation, a Bonferroni or False Discovery Rate (FDR) correction will be applied to the p-values to control family-wise error.
2.  **Sample Size/Power**: The study is limited by the available dataset size ($N$). If $N < 30$, LOOCV is used to maximize data usage, but confidence intervals will be wide. The plan explicitly acknowledges this limitation and uses Stability Selection to mitigate overfitting.
3.  **Causal Inference**: The study is observational. Results will be framed as "associational correlations" between topology and conductivity, not causal effects, unless randomization is present (which is not the case for a-Si trajectories).
4.  **Collinearity**: Ring statistics and bond order parameters may be correlated. Ridge regression is chosen specifically to mitigate this. Independent effects of collinear predictors will be reported as "relative importance" rather than "independent causal contribution".
5.  **Measurement Validity**: Thermal conductivity values are assumed to be derived from Green-Kubo simulations on systems $\ge 1000$ atoms or experimental data. If the dataset contains values from smaller systems, they will be **excluded** from the primary hypothesis test unless convergence is demonstrated (Constitution Principle VI).
6.  **Data Independence**: A strict check is performed to ensure thermal conductivity and VDOS are not derived from the same snapshot used for topology (scientific_soundness-1746af83).

## Compute Feasibility

- **Environment**: GitHub Actions (2 CPU, 7 GB RAM).
- **Strategy**:
    - **Graph Construction**: $O(N \log N)$ or $O(N^2)$ depending on neighbor list implementation; feasible for $N < 10,000$ atoms per configuration.
    - **Descriptors**: Ring statistics on small graphs (local coordination) are fast. VDOS is skipped if not pre-calculated.
    - **Models**: Ridge and Random Forest on tabular data (features $\times$ samples) are highly efficient on CPU.
    - **Memory**: Data will be streamed or loaded in chunks if the total dataset exceeds 7 GB. However, typical MD trajectory analysis fits within 1-2 GB.
- **Fallback**: If VDOS is not pre-calculated, the pipeline proceeds with Topological Descriptors only. No Green-Kubo simulation is attempted.