# Research: Lottery Draw Integrity and Anomaly Detection

## 1. Research Question
Does the magnitude of the lottery jackpot correlate with statistical anomalies in the winning number distribution (specifically "birthday clustering" and consecutive patterns), or are these anomalies consistent with a uniform random process?

## 2. Dataset Strategy

### Verified Datasets
The following datasets have been verified for availability and format. **Only** these sources will be used.

| Dataset Name | Source URL | Variables Available | Coverage | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **California Lottery (Historical Draw Games)** | ` | `draw_date`, `winning_numbers`, `jackpot_amount`, `total_sales` | 1990-Present | `quick_pick_rate` is **NOT** available. Verified archive. |
| **UK National Lottery (Historical)** | ` | `draw_date`, `winning_numbers`, `jackpot_amount`, `total_sales` | 1994-Present | `quick_pick_rate` is **NOT** available. Verified archive. |
| **Powerball / Mega Millions (US)** | ` (Verified Mirror) | `draw_date`, `winning_numbers`, `jackpot_amount`, `total_sales` | 1992-Present | `quick_pick_rate` is **NOT** available. Verified archive. |

*Note: No verified public source provides `quick_pick_rate` at the draw level. As per FR-003, this variable will be marked `NA`.*

### Variable Fit Verification
- **Winning Numbers**: Present in all verified sources.
- **Jackpot Amount**: Present in all verified sources.
- **Total Sales**: Present in most sources; missing for some older records (handled via FR-001 Edge Case).
- **Quick Pick Rate**: **Absent**. This is a critical limitation. The analysis cannot control for this confounder. The study will explicitly frame results as "Draw Integrity" (machine fairness) rather than "Player Behavior."

## 3. Statistical Methodology

### 3.1 Bias Metric Definition (FR-002)
The previous "Chi-Square Uniformity Deviation" metric was deemed scientifically invalid for single draws. It has been replaced by two specific, valid metrics that measure "human-like" patterns:

1. **Birthday Cluster Ratio ($R$)**:
 $$ R = \frac{\text{count}(x_i \le 31)}{k} $$
 Where $k$ is the total number of balls drawn.
 *Rationale*: In a truly random draw, the proportion of numbers $\le 31$ should be close to $31/N$ (where $N$ is the total pool size). A significantly higher ratio suggests "birthday bias" (human selection).

2. **Consecutive Pattern Count ($C$)**:
 $$ C = \text{count}(x_{i+1} = x_i + 1) $$
 *Rationale*: Random draws rarely produce consecutive numbers. A higher count suggests a non-random pattern.

**Metric Calculation**:
For each draw, we calculate $R$ and $C$. These are the primary metrics for correlation analysis. The "Bias Index" is a composite score if needed, but the analysis will primarily test $R$ and $C$ individually.

### 3.2 Correlation Analysis (FR-004)
- **Method**: Spearman rank correlation (robust to non-normality of jackpot sizes) and Pearson (for comparison).
- **Variables**: $X = \text{Jackpot Amount}$, $Y = \text{Birthday Cluster Ratio}$ (and separately $Y = \text{Consecutive Pattern Count}$).
- **Logic**: If the machine is truly random, the distribution of "birthday numbers" should be independent of the jackpot size. A correlation between Jackpot Size and $R$ would suggest that high-jackpot draws are *more* human-like (suggesting potential machine bias or data tampering).
- **Confounding**: Explicitly note: "Quick Pick rate unobservable; no control applied." The analysis is strictly limited to "Draw Integrity".

### 3.3 Robustness & Sensitivity (FR-005, FR-006)
- **Bootstrapping**: 1000 iterations to generate 95% Confidence Intervals for correlation coefficients.
- **Sensitivity Sweep**: Re-run correlation with `birthday_cluster_ratio` thresholds at {0.50, 0.60, 0.70} to test the "majority" definition.
- **Multiple Comparisons**: Apply Bonferroni correction for tests on Birthday, Consecutive, and Multiples patterns.

## 4. Compute Feasibility
- **Data Size**: Estimated < 500MB for full history. Fits in 7GB RAM.
- **Processing**: Bootstrapping 1000 iterations on < 50k rows is computationally light for CPU.
- **Time Limit**: Estimated runtime < 1 hour on GitHub Actions free tier.

## 5. Limitations
- **Causal Claims**: None. Correlation $\neq$ Causation.
- **Confounding**: Cannot control for Quick Pick proportion. The analysis is strictly a test of "Draw Integrity" (machine output) against a baseline of expected randomness.
- **Data Gaps**: Missing `total_sales` for older draws may reduce sample size for sales-dependent checks.
- **Scope Boundary**: The study scope is limited to analyzing the uniformity of *winning numbers* (machine fairness) rather than *player selections* (behavior), as the latter requires proprietary ticket data not available in public archives.