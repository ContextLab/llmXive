# Research: The Influence of Visual Complexity on Implicit Bias

## Domain Overview

This project investigates the cognitive mechanism of "attentional capture" and "cognitive load" in the context of implicit bias. The hypothesis posits that increasing the visual complexity of background stimuli during an Implicit Association Test (IAT) increases cognitive load, thereby diverting attention away from the automatic activation of stereotypical associations, resulting in reduced implicit bias scores (D-scores).

### Key Concepts
- **Implicit Association Test (IAT)**: A reaction-time based measure of implicit bias. The D-score (Greenwald et al.) is the standard effect size metric, calculated as the difference in mean reaction times between compatible and incompatible blocks, divided by the pooled standard deviation.
- **Visual Complexity**: A multidimensional construct quantified here by:
 - **Edge Density**: Proportion of pixels identified as edges via Canny detection.
 - **Entropy**: Shannon entropy of the grayscale histogram, measuring information content/randomness.
 - **Fractal Dimension**: A measure of self-similarity and roughness, calculated via box-counting.
- **Cognitive Load Theory**: Suggests that limited working memory resources, when taxed by complex stimuli, reduce the capacity for automatic processing of task-irrelevant (stereotypical) associations.

## Dataset Strategy

### Primary Data Source
The project assumes **new data collection** as per the Spec's "Assumption about data source" and Constitution Principle VI. No existing public dataset currently contains the specific experimental design (IAT with manipulated visual complexity in two sessions) required for this analysis.

**Strategy for Implementation**:
1. **Stimuli**: A set of grayscale images will be sourced or generated to span the complexity spectrum (low: solid colors/gradients; high: noise/textures).
2. **Response Data**: Since actual participant recruitment is outside the scope of the CI pipeline, the implementation will include a **synthetic data generator** that simulates IAT response times.
 - **Critical Distinction**: The synthetic generator is used **ONLY** for unit/integration testing of the code logic (e.g., verifying the pipeline handles null results correctly). It is **NOT** used for the final scientific conclusion.
 - **Null Mode**: The generator includes a `--null-effect` flag to simulate data where complexity has no effect (effect size = 0), ensuring the pipeline can detect non-significant results and avoiding tautological validation.
 - **Parameterization**: When not in Null Mode, the generator models realistic variance structures (e.g., based on Greenwald et al. parameters) without hard-coding the specific hypothesis effect size, ensuring the pipeline is tested for sensitivity rather than confirmation.
3. **Verification**: The pipeline will be validated against the provided "ANOVA (json)" dataset for *statistical output verification* only (checking calculation logic), not for the experimental data itself.

### Verified Datasets
The following dataset is available for statistical validation (checking calculation logic):
- **ANOVA (json)**: `
 - *Usage*: This dataset contains pre-calculated ANOVA results. It will be used in `tests/test_analysis.py` to verify that the `code/analysis/permutation.py` module produces identical F-statistics and p-values for the same input data, ensuring numerical correctness. It does *not* contain IAT data or complexity metrics.

### Dataset Fit & Limitations
- **Gap**: No public dataset exists with the specific "IAT + Visual Complexity Manipulation" design.
- **Mitigation**: The project will generate synthetic data that adheres to the statistical properties of real IAT data (e.g., Greenwald et al., 2003 parameters) and the complexity distribution of the stimuli. The sensitivity analysis (FR-007) will ensure robustness regardless of the specific data distribution.
- **Constraint**: The synthetic data generator must be deterministic (seeded) to satisfy Constitution Principle I (Reproducibility).
- **Scientific Validity**: The final Power Analysis and scientific conclusion MUST be conducted on **real collected data** (or a generator that does not assume the effect). The synthetic generator's `null_mode` is used only to validate the pipeline's ability to handle null results during CI.

## Statistical Methodology

### Hypothesis Testing
- **Null Hypothesis (H0)**: There is no difference in mean D-scores between Low and High visual complexity conditions ($\mu_{low} = \mu_{high}$).
- **Alternative Hypothesis (H1)**: Mean D-scores differ between conditions ($\mu_{low} \neq \mu_{high}$).
- **Test**: **Permutation Test** (not ANOVA/LMM).
 - *Rationale*: The design assigns different images to Low vs. High conditions. 'Stimulus Set' is perfectly confounded with 'Complexity Level'. A standard ANOVA or LMM cannot separate the fixed effect of complexity from the random effect of the stimulus set (singular fit/unidentifiable).
 - *Method*: The test randomly re-assigns the 'Low'/'High' labels to the observed D-score pairs (or permutes stimulus labels) to build a null distribution. This isolates the complexity effect by testing if the observed difference is extreme relative to all possible labelings of the *same* stimulus sets, effectively controlling for the specific image set used. This solves the confound identified in Methodology Concern 5878fce0.
- **Effect Size**: Cohen's $d$ and Permutation p-value.
- **Significance Level**: $\alpha = 0.05$.

### Multivariate Approach (Addressing Construct Validity)
To address the concern of 'cherry-picking' a single metric (Edge, Entropy, Fractal):
1. **PCA Dimensionality Check**: Run PCA on the three metrics.
 - If PC1 explains **>70%** of variance: Use PC1 as the `Complexity_Factor` for the Permutation Test.
 - If PC1 explains **<70%** of variance: Use a **Multivariate Permutation Test** (MANOVA-style) on all three metrics simultaneously to avoid researcher degrees of freedom.
2. This protocol is pre-registered in the analysis code to prevent post-hoc selection.

### Sensitivity Analysis
To address SC-003 (robustness) and the concern about outlier images:
1. **Threshold Sweep**: Sweep the complexity threshold used to categorize images into "Low" and "High" groups (Median split $\pm 0.05, \pm 0.10, \pm 0.15$ SD).
2. **Leave-One-Image-Out (LOIO)**: Iteratively remove one image from the 'High' set and re-run the Permutation Test. This ensures the effect is not driven by a single outlier image, addressing Methodology Concern 1ea5d194.
3. **Validity Check**: Any sweep point resulting in $n < 15$ per condition is marked 'invalid' and excluded from the robustness conclusion (FR-007).

### Power Analysis
- **Target**: Power $\ge 0.80$ for a medium effect size ($\eta^2 > 0.02$) with $N=60$.
- **Method**: Post-hoc power calculation will be performed on the **real collected data** (or a realistic simulation that does not assume the effect).
- **Note**: The synthetic generator's `null_mode` is used for CI testing to ensure the pipeline can handle null results, but the scientific power analysis must not rely on a generator that hard-codes the effect size.

### Multiple Comparisons & Collinearity
- **Multiple Comparisons**: The Permutation Test inherently controls for family-wise error rate when testing a single hypothesis. If multiple tests are run (e.g., LOIO), Bonferroni correction will be applied.
- **Collinearity**: The PCA/Multivariate approach (above) handles collinearity and construct validity. The plan will compute all three metrics (FR-001) but use the appropriate statistical method (PC1 or Multivariate) based on the dimensionality check.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Permutation Test** | Required because 'Stimulus Set' is perfectly confounded with 'Complexity Level'. ANOVA/LMM fails here. Permutation tests the null distribution without assuming independence. |
| **PCA Dimensionality Check** | Prevents 'cherry-picking' a single metric. Ensures the analysis reflects the full 'Visual Complexity' construct. |
| **Leave-One-Image-Out (LOIO)** | Addresses the concern that the effect might be driven by a single outlier image. |
| **Synthetic Data Null Mode** | Ensures the pipeline can handle null results during CI testing, avoiding tautological validation. |
| **Greenwald D2 Algorithm** | Standard for IAT analysis (FR-002). Ensures validity and comparability with existing literature. |

