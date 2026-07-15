# Statistical Interpretation Guidelines

## Understanding Complexity Metrics in Cognitive Fatigue

### Theoretical Framework

Cognitive fatigue is conceptualized not as simple resource depletion but as a
**phase transition** in the brain's problem-solving dynamics. Complexity metrics
serve as proxies for these dynamical states, capturing how neural systems reorganize
under cognitive load.

### Lempel-Ziv Complexity (LZC)

**What it measures**: The rate at which new patterns emerge in a time series.
Higher LZC indicates more unpredictable, complex dynamics; lower LZC suggests
more regular, predictable patterns.

**Interpretation in Fatigue Context**:

| LZC Change | Possible Interpretation | Supporting Evidence |
|-------------|------------------------|---------------------|
| Decrease | **Adaptive Simplification**: System becomes more efficient, reducing computational overhead | Observed in expert performers under load |
| Increase | **Degenerative Noise**: System loses structure, becoming erratic | Associated with cognitive overload |
| No Change | **Resilience**: System maintains optimal complexity despite fatigue | Individual differences in fatigue resistance |

**Critical Considerations**:
- LZC alone cannot distinguish between adaptive and degenerative changes
- Must be interpreted alongside behavioral measures and context
- Channel-specific patterns may reveal regional differences in fatigue effects

### Permutation Entropy (PE)

**What it measures**: The complexity of ordinal patterns in a time series,
focusing on the order of values rather than their magnitudes. More robust to
amplitude variations and noise than LZC.

**Interpretation in Fatigue Context**:

| PE Change | Possible Interpretation | Relationship to LZC |
|-------------|------------------------|---------------------|
| Decrease | More deterministic structure, reduced dynamical richness | Often correlates with LZC decrease |
| Increase | Greater randomness, loss of structured dynamics | May diverge from LZC in noisy conditions |
| Divergence from LZC | **Key Insight**: PE-LZC dissociation may indicate specific types of dysfunction | Suggests amplitude-independent vs. dependent effects |

**Why Use Both Metrics**:
- LZC is sensitive to amplitude variations and new pattern emergence
- PE is robust to amplitude changes and focuses on temporal ordering
- **Concordance**: Both metrics decreasing suggests global simplification
- **Discordance**: May reveal nuanced mechanisms (e.g., adaptive amplitude control with structural degradation)

### Statistical Analysis Guidelines

#### Correlation Interpretation

**Spearman vs. Pearson**:
- **Spearman** (default): Robust to non-linear relationships and outliers
- **Pearson**: Only if linearity is confirmed and data is normally distributed

**Effect Size Benchmarks** (Cohen's d):
- Small: 0.2
- Medium: 0.5
- Large: 0.8

**Significance Thresholds**:
- **Primary**: p ≤ 0.05 (FDR-corrected) - standard for discovery
- **Secondary**: p ≤ 0.01 (FDR-corrected) - for robust findings
- **Exploratory**: Uncorrected p-values reported with caution

#### Multiple Comparisons Correction

**Benjamini-Hochberg (FDR)**:
- Controls expected proportion of false positives among rejected hypotheses
- Less conservative than Bonferroni, better suited for EEG's many channels
- **Interpretation**: A corrected p-value of 0.05 means 5% of significant findings are expected to be false positives

**When to Use**:
- Always apply FDR when testing multiple electrodes (typically 19-64 (2403.09707, https://arxiv.org/abs/2403.09707)+ channels)
- Report both raw and corrected p-values
- Highlight channels that remain significant after correction

#### Sensitivity Analysis

**Purpose**: Assess how robust findings are to differentsignificance thresholds.

**Interpretation**:
- **Consistent**: Significant at both p≤0.05 and p≤0.01 → Highly robust
- **Threshold-Dependent**: Significant only at p≤0.05 → Moderate evidence
- **Inconsistent**: Changes across thresholds → Requires replication

### Distinguishing Adaptive vs. Degenerative Changes

**Key Diagnostic Patterns**:

1. **Adaptive Simplification** (Efficient Resource Allocation):
 - Decreased LZC and PE
 - Stable or improved behavioral performance
 - Consistent across multiple channels
 - Moderate effect sizes (d ≈ 0.5)

2. **Degenerative Noise** (System Breakdown):
 - Increased LZC and PE (or divergent patterns)
 - Declining behavioral performance
 - Irregular spatial patterns
 - Large effect sizes (d > 0.8) with high variability

3. **Mixed Signals** (Complex Dynamics):
 - LZC decrease but PE increase (or vice versa)
 - Suggests amplitude-independent structural changes
 - Requires careful behavioral correlation
 - May indicate transition states

### Reporting Standards

**Required Elements**:
1. **Metric Values**: Mean ± SD for each condition
2. **Correlation Coefficients**: r (or ρ) with 95% confidence intervals
3. **P-values**: Both raw and FDR-corrected
4. **Effect Sizes**: Cohen's d with interpretation
5. **Sample Size**: N after artifact rejection
6. **Limitations**: Explicit discussion of metric constraints

**Avoid**:
- Claiming causation from correlation
- Overinterpreting single-channel findings
- Ignoring behavioral validation
- Reporting only p-values without effect sizes

### Practical Example

**Scenario**: Analyzing Fz channel data from 45 participants

**Results**:
- LZC: r = -0.42, p = 0.003 (FDR-corrected p = 0.018), d = 0.65
- PE: r = -0.38, p = 0.008 (FDR-corrected p = 0.032), d = 0.58

**Interpretation**:
> Both LZC and PE show significant negative correlations with fatigue scores,
> indicating **adaptive simplification**. The concordance between metrics and
> moderate effect sizes suggest efficient resource reallocation rather than
> system breakdown. FDR correction confirms robustness across multiple channels.
> However, behavioral validation is needed to confirm performance maintenance.

### References

- **Lempel-Ziv Complexity**: Lempel, A., & Ziv, J. (1976). On the complexity of finite sequences. IEEE Transactions on Information Theory.
- **Permutation Entropy**: Bandt, C., & Pompe, B. (2002). Permutation entropy: A natural complexity measure for time series. Physical Review Letters.
- **FDR Correction**: Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate. Journal of the Royal Statistical Society.
- **EEG Complexity in Fatigue**: Recent literature on dynamical systems approaches to cognitive neuroscience.
