# Research: llmXive follow-up: extending "Trust-Region Behavior Blending for On-Policy Distillation"

## Dataset Strategy

The project relies on the following verified datasets. **Critical Note**: These datasets are **not** the original "Math" and "Code" training sweep logs mentioned in the spec. They are text corpora and retrieval benchmarks. The project scope is adjusted to use them as *proxy* data for diversity profiling and correlation analysis.

| Dataset Name | Source URL | Role in Plan | Variable Fit Check |
|:--- |:--- |:--- |:--- |
| **Source Dataset (Book Corpus)** | ` | **Source**: Text corpus for diversity profiling. | **Check**: Contains `text` column. **Missing**: `optimal_epsilon_0`, `collapse_label`, `loss_variance`. **Proxy**: Will use text length and entropy as proxy stability metrics. |
| **Target Dataset (BEIR)** | ` | **Target**: Retrieval benchmark for cross-domain validation. | **Check**: Contains `query`, `document`, `score`. **Missing**: `optimal_epsilon_0`, `collapse_label`. **Proxy**: Will use `score` (relevance) as a proxy for "quality" to correlate with diversity. |
| **Supplemental Teacher Outputs** | ` | **Backup**: Potential source for diverse text if primary datasets are insufficient. | **Check**: Contains `prompt` and `completion`. **Missing**: Training logs. |

**Critical Note on Variable Fit**:
The spec requires ground-truth "optimal $\varepsilon_0$" and "collapse labels". The verified datasets listed above **do not contain these variables**.
- **Action**: The project **cannot** train a regression or classification model to predict these missing variables.
- **Revised Methodology**: The project will perform a **correlation analysis**:
 1. Compute diversity profiles for all samples.
 2. Correlate diversity metrics with available metadata (e.g., `score` in BEIR, text length in Book Corpus).
 3. Explicitly state that the "collapse prediction" hypothesis cannot be validated with current data.
- **Blocking Condition**: If no metadata exists to serve as a proxy, the project will halt.

## Statistical Rigor

1. **Multiple Comparison Correction**:
 - The project involves multiple hypothesis tests (correlation of metrics with proxy scores).
 - **Method**: Apply Benjamini-Hochberg (FDR) correction to the p-values of all correlation tests reported.

2. **Sample Size / Power**:
 - **Acknowledgement**: The sample size is constrained by the availability of the verified datasets.
 - **Action**: The `research.md` will report the effective sample size ($N$) and calculate the minimum detectable effect size for the given $N$ and $\alpha=0.05$.

3. **Causal Inference Assumptions**:
 - **Observational Nature**: This study is observational. We observe diversity profiles and proxy quality scores. We **do not** claim that diversity *causes* quality, only that it *correlates* with it.
 - **Framing**: All claims in the paper will be framed as "associational" or "correlational" relationships.

4. **Measurement Validity**:
 - **Lexical Metrics**: `distinct-4` and `n-gram entropy` are standard proxies for lexical diversity.
 - **Syntactic Metrics**: `parse tree depth variance` is a proxy for syntactic complexity.
 - **Validation**: FR-008 requires validating the syntactic metric. If the correlation with proxy quality < 0.3, the plan mandates a fallback to token-level entropy. This fallback will be documented as a sensitivity analysis.

5. **Predictor Collinearity**:
 - **Risk**: `distinct-4` and `ngram_entropy` are mathematically related.
 - **Mitigation**: The plan will calculate the Variance Inflation Factor (VIF) for predictors. If VIF > 5, the model will be re-run with one of the collinear features removed, and the results will be reported descriptively.

## Decision Rationale: CPU-Only & Correlation Analysis

- **Why Correlation Analysis?**
 - **Feasibility**: The required ground truth for regression/classification is missing. Correlation analysis is the only valid statistical approach with the available data.
 - **Memory**: Correlation tests fit easily within 7 GB RAM.
- **Why Not Model Training?**
 - **Data Limitation**: No ground truth labels exist. Training a model would be meaningless.
- **Why Proxy Targets?**
 - **Circularity Avoidance**: By correlating text features with *independent* proxy scores (e.g., relevance scores in BEIR) rather than the hyperparameters that generated the text, we avoid trivial identity learning.

## Edge Case Handling

1. **Empty/Whitespace Responses**:
 - **Action**: Assign `NaN` to all metrics. The pipeline will log a warning and exclude these rows from analysis.
2. **Syntactic Parsing Failures**:
 - **Action**: Catch `spacy` exceptions. Return `NaN` for `syntactic_variation_score`.
3. **Missing Proxy Metadata**:
 - **Action**: If no proxy score exists for a sample, exclude from analysis and report coverage percentage.

## References

- **Source Dataset (Book Corpus)**: `
- **Target Dataset (BEIR)**: `
- **Supplemental Teacher Outputs**: `