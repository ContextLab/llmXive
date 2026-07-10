# Research: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Dataset Strategy

The project relies on particle tracking data containing positions ($x, y, z$), orientations ($\theta$), and driving signal metadata.

| Dataset Name | Source / URL | Variables Available | Fit Assessment |
|--------------|--------------|---------------------|----------------|
| **Synthetic Granular Generator** | `code/data/synthetic.py` (Local) | Positions, orientations, material type, driving frequency, friction coefficient, deviation factor. | **Primary Source**. No verified real-world dataset exists for the specific variables required. This generator is designed to produce realistic deviations from equipartition via friction coupling, avoiding circular validation (unlike a generator that enforces equality). |
| **OpenGranular** | NO verified source found | *Hypothetical*: Positions, orientations, material type, driving frequency. | **Unavailable**. No verified URL exists. The project proceeds with synthetic data for this feature branch. |
| **Granular experiment dataset (Zenodo)** | NO verified source found | *Hypothetical*: Positions, orientations, material type. | **Unavailable**. No verified URL exists. |

**Decision**: The pipeline will be designed to accept a generic CSV/Parquet input format. For this feature branch, the **Synthetic Granular Generator** is the primary data source. It models surface roughness via a friction coefficient to generate controlled deviations from equipartition, ensuring the pipeline is tested against non-trivial data. If a verified real-world dataset is discovered later, the loader can be adapted. **Scope Note**: This study is a "Methodology Validation" using synthetic data; final physical claims require a verified real-world source.

## Statistical Methodology & Rigor

### 1. Hypothesis Testing Strategy
- **Null Hypothesis ($H_0$)**: The mean difference between translational and rotational kinetic energy is zero ($\mu_{diff} = 0$) within a specific frequency/material bin, where $diff = E_{trans} - E_{rot}$ for each particle frame.
- **Alternative Hypothesis ($H_1$)**: $\mu_{diff} \neq 0$.
- **Test**: **Paired t-test** on the difference distribution (correcting for the paired nature of $E_{trans}$ and $E_{rot}$).
  - *Rationale*: $E_{trans}$ and $E_{rot}$ are derived from the same particle frames (paired observations). A Two-Sample t-test assumes independence and is statistically invalid here.
- **Distributional Test**: **Kolmogorov-Smirnov (KS) test** to compare the observed energy ratio distribution against the theoretical equipartition distribution (as required by Constitution Principle VII).
- **Multiple Comparisons**: Holm-Bonferroni correction applied to all p-values generated across frequency bins and material types (FR-004).
- **Power & Sample Size**: A formal **post-hoc power analysis** will be conducted to estimate the effect size (Cohen's d for paired differences) and verify sample size sufficiency. We do not assume high power based on N alone; the effect size depends on the friction coupling strength in the synthetic generator.

### 2. Regression Analysis
- **Model**: Linear regression relating energy deviation ($\Delta E = \mu_{trans} - \mu_{rot}$) to driving frequency and material type.
- **Assumption**: Observational study. No causal claims made; results framed as associational.
- **Collinearity**: Frequency and material type are treated as independent predictors. If material type correlates with driving frequency in the experimental design, this will be noted as a limitation.

### 3. Sensitivity Analysis
- **Thresholds**: $\alpha \in \{0.01, 0.05, 0.10\}$.
- **Metric**: Count of bins classified as "significant deviation" for each $\alpha$.
- **Stability**: If the conclusion (significant vs. non-significant) changes across the swept thresholds, the result is flagged as "unstable" (US-3).

### 4. Measurement Validity
- **Instruments**: Synthetic data generator uses standard physics formulas ($E = 0.5mv^2$) and explicitly models **friction coupling** to generate realistic deviations from equipartition.
- **Derivation**: If mass is missing, $m$ is derived from material density and default radius (2.5mm) (FR-006).
- **Potential Energy**: Excluded from the ratio test as it is not a quadratic degree of freedom in this specific driven context, but calculated for diagnostics.

### 5. Frequency Binning Clarification
- Driving frequency is a **global experimental parameter**. Binning is performed to stratify analysis by different experimental conditions (if multiple frequencies were tested) or as a robustness check. If only one frequency is present, the binning reduces to a single group, and the analysis proceeds on the full dataset.

## Compute Feasibility & Constraints

- **Environment**: GitHub Actions Free Tier (multi-core CPU, 7 GB RAM, 14 GB disk).
- **Memory Management**: **Mandatory chunked processing** (100k frames/chunk) to avoid OOM. `pandas` will be used with `dtype` optimization (float for coordinates, float64 for energies) to reduce memory footprint.
- **Runtime**: Target < 6 hours.
  - Energy calculation: $O(N)$, fast with vectorized numpy.
  - Statistical tests: $O(N)$ or $O(N \log N)$, negligible for 1M rows.
  - No GPU/CUDA usage.
- **Libraries**: `numpy`, `pandas`, `scipy`, `scikit-learn` (all CPU-optimized).

## Assumptions & Risks

- **Assumption**: The synthetic data generator can approximate the statistical properties of real granular systems sufficiently to test the pipeline logic.
- **Risk**: The lack of a verified real-world dataset means the final scientific result is limited to "methodology validation" rather than "new physical discovery" unless a verified source is found.
- **Mitigation**: The pipeline will be robust enough to handle real data if/when it becomes available. The `research.md` will explicitly state the data source used for the current run.
- **Constraint**: The dataset size is assumed to exceed 7GB RAM, making chunked processing the primary execution path.

## Decision Rationale

- **Synthetic Data**: Chosen because no verified real-world dataset exists for the specific variables required. The generator is designed to produce controlled deviations (via friction) to avoid circular validation.
- **Paired t-test**: Mandatory due to the paired nature of the data (same particle, two energy modes). Two-Sample t-test is statistically invalid.
- **Chunked Processing**: Mandatory due to 7GB RAM constraint. This is the primary execution path, not a fallback.
- **KS Test**: Added to satisfy Constitution Principle VII.
- **Power Analysis**: Added to validate sample size claims.