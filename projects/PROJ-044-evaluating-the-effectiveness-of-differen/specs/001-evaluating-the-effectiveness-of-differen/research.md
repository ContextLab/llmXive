# Research: Evaluating the Effectiveness of Differential Privacy in Federated Learning

## Research Question

Does data heterogeneity (simulated via Dirichlet concentration parameter α) significantly degrade the utility of Differentially Private Federated Learning (DP-FL) for minority clients compared to majority clients, and is there a critical threshold (α ≤ 0.1) where this degradation becomes statistically significant?

## Dataset Strategy

### Verified Sources

The project relies exclusively on the following verified Hugging Face datasets, which are directly downloadable via `datasets.load_dataset()` or direct parquet URLs.

| Dataset | Source URL | Load Method | Suitability |
|---------|------------|-------------|-------------|
| **FEMNIST** | ` (and test splits) | `datasets.load_dataset("parquet", data_files=...)` | **Primary**. A set of classes comprising digits and letters, suitable for CNN. Verified for image classification. |
| **Shakespeare** | *No verified source found for raw LEAF Shakespeare in the provided block.* | **N/A** | **Excluded**. The spec mentions Shakespeare, but the verified list only contains protein/URL datasets. **Decision**: We will proceed with **FEMNIST** as the sole primary dataset for this implementation. The Shakespeare requirement is noted as a gap; if a verified URL appears later, it will be added. For now, FEMNIST is sufficient to test the heterogeneity hypothesis. |

**Note on Shakespeare**: The spec requires Shakespeare, but the `# Verified datasets` block does not contain a verified URL for the Shakespeare LEAF dataset. The listed "LEAF" entries are for SwissProt (protein sequences), not Shakespeare. To avoid fabrication, we will **exclude Shakespeare** from this initial run and focus entirely on FEMNIST, which is fully verified. The plan will be updated if a verified Shakespeare source is identified.

### Data Partitioning Strategy

1. **Download**: Fetch FEMNIST train/test parquet files.
2. **Preprocessing**: Flatten images, normalize to [0,1].
3. **Dirichlet Partitioning**:
 * Assign labels to clients using a Dirichlet distribution $Dir(\alpha)$.
 * **α values**: 0.1 (High Heterogeneity), 0.5 (Medium), 1.0 (Homogeneous).
 * **Client Count**: A simulated cohort of clients.
 * **Minority Definition**: Clients assigned to the "minority" group if their partition is generated with α ≤ 0.1. This is a **pre-specified** condition based on the Dirichlet parameter, not a post-hoc selection based on sample counts, to avoid selection bias.
4. **Validation**: Verify label distribution variance matches theoretical expectations for each α.

## Computational Strategy

### Hardware Constraints & Escape Hatch

* **Primary**: GitHub Actions CPU (limited vCPU, constrained memory).
 * **Feasibility**: FEMNIST is a dataset of moderate size.. Small CNN (2-3 layers) fits in memory.
 * **Risk**: Training runs (Multiple seeds × multiple ε × 4 α) might exceed 6h on CPU due to Opacus overhead.
* **Fallback Strategy**: If the run time exceeds a predefined threshold, the system automatically reduces the number of rounds from 50 to 20. and flags the result as "Time-Limited". This ensures a deterministic fallback rather than relying on non-deterministic external GPU availability.
* **GPU Offload**: Not used for primary CI runs. If a future run requires GPU, it will be explicitly configured and documented, but the current plan targets CPU feasibility.

### Algorithm Details

1. **Federated Optimization**: FedAvg.
2. **Differential Privacy**: Opacus `GradSampleModule`.
 * **Mechanism**: Per-sample gradient clipping + Gaussian noise injection.
 * **Accountant**: Moments Accountant for accurate ε tracking.
 * **Parameters**:
 * Noise Multiplier (σ): Derived from ε, δ (1e-5), and clip norm.
 * δ: e (standard for FL).
 * ε: {a range of values spanning from low to high magnitudes}.
3. **Training Loop**:
 * Local Epochs: A suitable number of epochs will be determined during the implementation phase to balance convergence and computational efficiency..
 * Batch Size: A moderate batch size will be employed..
 * Rounds: A sufficient number to ensure convergence (reduced to a lower number if timeout risk).

## Statistical Analysis Plan

### Hypothesis Testing

* **H0**: There is no difference in the *degradation* (DP accuracy - Non-DP accuracy) between minority and majority clients.
* **H1**: Minority clients suffer significantly higher accuracy degradation than majority clients under DP, especially at low α.

### Paired Generation Strategy

To ensure valid pairing:
1. **Partition Generation**: For each seed, generate a single partition file (JSON/Parquet) with a specific α.
2. **Dual Execution**: Run the training loop **twice** on this *exact same* partition file:
 * Run A: With DP (Opacus enabled).
 * Run B: Without DP (Opacus disabled, same model, same seed).
3. **Pairing**: The pair (Run A, Run B) constitutes a single experimental unit. This ensures the Non-DP baseline uses the exact same data distribution and random seed as the DP run.

### Tests

1. **Difference-in-Differences (DiD)**:
 * Calculate `Degradation = Accuracy_NonDP - Accuracy_DP` for each client.
 * Compare `Degradation_Minority` vs `Degradation_Majority`.
 * **Test**: Linear Mixed-Effects Model (LMM) with `Degradation` as the dependent variable, `Group` (Minority/Majority) as a fixed effect, and `Seed` as a random effect. This accounts for the nested structure (clients within seeds).
 * **Null Hypothesis**: The coefficient for `Group` is zero (no difference in degradation).
2. **Sensitivity Analysis**: Sweep α ∈ {0.05, 0.1, 0.5, 1.0} and plot accuracy gap vs. α.
3. **Collinearity Control**: Include `samples_per_class` as a covariate in the LMM to isolate the effect of heterogeneity (distribution shape) from data scarcity (sample count).

### Power & Rigor

* **Seeds**: Multiple independent runs per configuration (reduced from a baseline level for CPU feasibility, but sufficient for LMM).
* **Multiple Comparison Correction**: Bonferroni correction applied if > 5 hypothesis tests are run simultaneously.
* **Selection Bias Mitigation**: Minority status is defined by the pre-specified α parameter (α ≤ 0.1), not by post-hoc sample counts, ensuring the group definition is independent of the outcome.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Shakespeare Data Missing** | High | Proceed with FEMNIST only; document the gap; flag for spec amendment. |
| **CPU Timeout** | Medium | Reduce rounds (50 → 20) and flag as "Time-Limited"; exclude from convergence metrics. |
| **Utility Collapse (ε=0.1)** | Low | Flag as "utility collapse" rather than valid data point; exclude from slope calculation if accuracy < random chance. |
| **Opacus CPU Performance** | Medium | Use `cpu` backend; if too slow, reduce batch size or rounds. |
