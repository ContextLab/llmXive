# Research Methodology

This document outlines the research design, hypotheses, and analysis plan for the llmXive Follow-up study.

## Research Question

**RQ1**: Does an iterative exploration agent with static analysis feedback achieve higher line-level coverage and ranking efficiency compared to a static multi-query baseline when solving "hard" software repository issues?

## Hypotheses

### Primary Hypothesis (H1)

The iterative agent will achieve **significantly higher coverage scores** than the baseline.

- **Null (H0)**: No difference in coverage between iterative and baseline agents.
- **Alternative (H1)**: Iterative agent coverage > baseline coverage.
- **Test**: Wilcoxon signed-rank test (paired, one-tailed).
- **Significance**: α = 0.05 (Bonferroni-corrected for multiple comparisons).

### Secondary Hypothesis (H2)

The iterative agent will achieve **significantly lower ranking positions** (i.e., find relevant lines earlier) than the baseline.

- **Null (H0)**: No difference in ranking metrics.
- **Alternative (H2)**: Iterative agent ranking < baseline ranking.
- **Test**: Wilcoxon signed-rank test (paired, one-tailed) or exact permutation test if ties/censoring > 20%.
- **Significance**: α = 0.05 (Bonferroni-corrected).

## Data Sources

### SWE-Explore Benchmark

- **Source**: HuggingFace `bench.final.public.jsonl`
- **Size**: ~300 issues
- **Filtering**: Bottom 20th percentile of `initial_coverage` scores (hard instances)
- **Augmentation**: Up to 50 synthetic ambiguous issues with structural obfuscations

### Synthetic Issues

- **Mutations**: Variable renaming, comment removal, control flow reordering, API signature changes
- **Validity**: All synthetic issues are AST-parseable
- **Ground Truth**: Preserved from original code

## Agent Designs

### Baseline: Static Multi-Query

- **Queries**: 3 parallel queries per issue
- **Context**: Static retrieval without feedback
- **Budget**: Matches iterative agent (3 turns)

### Iterative Agent

- **Turns**: Max 3 turns (configurable)
- **Loop**: Query → Retrieve → Static Analysis → Reformulate (if error)
- **Feedback**: Uses `pylint`/AST analysis to detect missing imports, undefined variables, syntax errors
- **Loop Detection**: Breaks if repeated queries detected

## Metrics

### Coverage

- **Definition**: Percentage of `ground_truth_lines` retrieved across all turns.
- **Formula**: `coverage = (|retrieved_lines ∩ ground_truth_lines| / |ground_truth_lines|) * 100`
- **Range**: 0.0–1.0

### Ranking Efficiency

- **Definition**: Position of the first relevant line in the retrieved context.
- **Censoring**: If no relevant line found, rank = N + 1 (where N = total retrieved lines)
- **Range**: 1–∞ (lower is better)

## Statistical Analysis Plan

### Step 1: Paired Data Collection

- Pair baseline and iterative logs by `issue_id`
- Compute coverage and ranking metrics for each pair

### Step 2: Normality Check

- Shapiro-Wilk test on difference scores
- If non-normal (p < 0.05), use non-parametric tests

### Step 3: Primary Test (Coverage)

- **Test**: Wilcoxon signed-rank test
- **Tie Handling**: Continuity correction
- **Correction**: Bonferroni (α_adj = 0.05 / 2 = 0.025)

### Step 4: Secondary Test (Ranking)

- **Primary**: Wilcoxon signed-rank test
- **Fallback**: Exact permutation test or Cox survival analysis if ties/censoring > 20%
- **Correction**: Bonferroni (α_adj = 0.025)

### Step 5: Effect Size

- **Coverage**: Cohen's d (paired) or rank-biserial correlation
- **Ranking**: Rank-biserial correlation

### Step 6: Sensitivity Analysis

- Vary turn limits (2, 3, 4) on N=20 random issues
- Assess stability of results

## Ethical Considerations

- **Associational Language**: All findings are framed as **associational differences** (FR-007). No causal claims.
- **Reproducibility**: All code, data, and seeds are open-sourced.
- **Bias**: Synthetic issues are validated for AST parseability to avoid trivial failures.

## Limitations

- **Sample Size**: Hard subset may be small (~60 issues); power analysis recommended.
- **Static Analysis**: Limited to syntax/semantic errors; may miss logical bugs.
- **Turn Limit**: 3 turns may be insufficient for complex issues.
- **Generalizability**: Results may not extend to non-"hard" issues.

## Timeline

| Phase | Task | Duration |
|-------|------|----------|
| 1 | Data Curation (US1) | 2 days |
| 2 | Agent Execution (US2) | 3 days |
| 3 | Statistical Analysis (US3) | 2 days |
| 4 | Reporting & Validation | 1 day |

**Total**: ~8 days (CPU-only, 2-core/7GB RAM)

## References

- SWE-Explore: Benchmarking How Coding Agents Explore Repositories
- Wilcoxon, F. (1945). Individual Comparisons by Ranking Methods.
- Bonferroni, C. E. (1936). Teoria statistica delle classi e calcolo delle probabilità.
- Cox, D. R. (1972). Regression Models and Life-Tables.
