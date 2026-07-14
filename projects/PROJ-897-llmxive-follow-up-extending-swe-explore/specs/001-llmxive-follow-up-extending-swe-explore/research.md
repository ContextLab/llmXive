# Research: llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories"

## Research Question

Does an iterative, feedback-driven exploration strategy yield higher line-level coverage and ranking efficiency on ambiguous or unsolvable issues compared to a **Static Multi-Query Baseline** (3 parallel queries) when controlling for search budget?

## Hypothesis

- **H1 (Coverage)**: The iterative agent will achieve statistically significantly higher line-level coverage on "hard" (high complexity) and synthetic ambiguous issues compared to the Static Multi-Query Baseline.
- **H2 (Efficiency)**: The iterative agent will demonstrate improved ranking efficiency (lower position of first relevant line) on these difficult instances, handling censored data appropriately.
- **Null**: There is no statistically significant difference in coverage or efficiency between the two strategies on the random sample, or the iterative strategy degrades performance on "easy" tasks.

## Dataset Strategy

### Verified Datasets

| Dataset Name | Source URL | Usage in Plan | Notes |
|:--- |:--- |:--- |:--- |
| **SWE-Explore** | ` | Primary source for issue selection. Contains `issue_id`, `repo`, `problem_statement`, `solution` (patch). | Used to derive "hard" instances via complexity metrics. Ground truth lines derived from solution patches. |

### Dataset Variable Fit Verification

- **Required Variables**: `issue_id`, `repo_path`, `problem_statement`, `solution` (patch), `code_context`.
- **SWE-Explore Availability**: The verified URL provides a JSONL file. Preliminary inspection confirms the presence of `solution` (patch) and `problem_statement`.
- **Ground Truth Derivation**: The `ground_truth_lines` are **not** explicit fields. They will be derived by parsing the `solution` patch against the `code_context` using `code/data/derive_gt.py`. This script will calculate the line numbers of the changed/added code.
- **Hard Instance Proxy**: Instead of `initial_coverage` (which causes tautology), "Hard" instances are defined by **Cyclomatic Complexity** or **Lines of Code** of the code context. This ensures the selection is independent of the static baseline's performance.
- **Risk Mitigation**: If complexity metrics cannot be calculated for a file, that issue will be excluded or assigned a random complexity score for stratification.

## Methodology

### Phase 0: Data Curation (FR-001, FR-002, FR-008, FR-009, FR-010)

1. **Download**: Fetch `bench.final.public.jsonl`.
2. **Ground Truth Derivation**: Run `code/data/derive_gt.py` to parse patches and generate `ground_truth_lines`.
3. **"Hard" Instance Selection**:
 - Calculate **Cyclomatic Complexity** for each issue's code context.
 - Select the top [deferred] (most complex) as "Hard".
 - **Validation (FR-010)**: Run `code/data/validate_hard.py` to generate a report for a random subset of 10 "hard" issues for **manual human inspection**.
4. **"Easy" Control Group**: Select a random subset of issues with low complexity.
5. **Synthetic Ambiguity Generation**:
 - Select a representative subset of solvable issues from the non-hard set.
 - Apply mutations (variable renaming, comment removal, structural obfuscation).
 - **Oracle Derivation (FR-008)**: Store the `ground_truth_lines` from the original unmutated code.
 - **Validity Check**: Ensure mutated code is syntactically valid (AST parseable). Skip invalid mutations.

### Phase 1: Agent Execution (FR-003, FR-004, SC-006)

1. **Static Multi-Query Baseline**:
 - Run ** parallel** retrieval queries per issue.
 - Record retrieved context and coverage metrics.
2. **Iterative Agent**:
 - **Loop Limit**: Max 3 turns (FR-003).
 - **Turn Logic**: Query -> Retrieve -> Static Analysis -> Reformulate.
 - **Static Analysis (FR-004)**: Use `pylint` or `ast` to detect errors.
 - **Logging (Constitution VI)**: Log `query_history`, `error_signals`, and `reformulation_reason`.
 - **Early Termination**: Stop if solution found or if query repeats.
3. **Turn Limit Sweep (SC-006)**:
 - Run a subset of issues (N=20) with **4 turns** to verify result stability.

### Phase 2: Metric Calculation & Statistical Testing (FR-005, FR-006, FR-007)

1. **Metrics**:
 - **Line-Level Coverage**: % of `ground_truth_lines` retrieved.
 - **Ranking Efficiency**: Position of first retrieved relevant line. **Censored Handling**: If no lines found, assign `N+1` (where N is total lines) or a penalty score.
2. **Statistical Test**:
 - **Coverage**: Wilcoxon signed-rank test (paired) on the **full random sample** (not just "hard") to avoid selection bias.
 - **Efficiency**: **Survival Analysis** (Cox proportional hazards) to handle censored data (issues where no relevant lines were found).
 - **Multiplicity Correction (SC-004)**: Apply Bonferroni correction for the family of tests.
 - **Threshold**: p < 0.05 (adjusted).
3. **Framing (FR-007)**: Results framed as "associational differences in performance".

## Compute Feasibility & Constraints

- **Environment**: GitHub Actions free-tier (limited CPU, 7GB RAM, no GPU).
- **Model Strategy**:
 - Use a **<1B parameter model** (e.g., `Qwen-2.5-0.5B-Instruct`) in **float32** to ensure the OS, tools, and context window fit within 7GB RAM.
 - **Alternative**: `Qwen-2.5-1.5B` in **4-bit quantization** using `llama-cpp-python` (CPU-optimized) if memory pressure is high.
 - **No GPU/CUDA**: Explicitly avoid `device_map="auto"` or `load_in_8bit` which require CUDA.
- **Time Limit**:
 - Target: < 6 hours.
 - Mitigation: Limit total issues to a manageable scope. If runtime exceeds a predetermined threshold, reduce sample size to a manageable level.
- **Memory**:
 - Pin `torch` CPU version.
 - Clear GPU cache (N/A) and Python garbage collect after each issue.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Bonferroni correction applied to the two primary hypotheses (Coverage, Efficiency).
- **Power Analysis**:
 - Sample size is determined by compute constraints.
 - **Limitation**: This study is underpowered for small effect sizes. Results will be interpreted with caution, focusing on effect size magnitude alongside p-values.
- **Causal Claims**:
 - The study is observational regarding the "hard" subset selection (based on complexity).
 - Claims will be limited to "associational differences" between strategies on this specific dataset subset.
- **Collinearity**:
 - Note: "Hard" status (complexity) and "Ambiguity" are correlated by definition. The synthetic generation introduces controlled variance to isolate the "ambiguity" factor.
 - Independent effects of "hardness" vs "ambiguity" are not claimed; the comparison is strictly Strategy A vs Strategy B on the combined difficult set.
- **Censored Data**:
 - The "Ranking Efficiency" metric is heavily censored (many issues have 0 coverage for the static baseline). Standard Wilcoxon is inappropriate. Survival Analysis (Cox) is used to handle this.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Static Multi-Query Baseline** | Isolates "feedback" from "search volume" by matching the total number of retrieval attempts (3). |
| **Complexity-based "Hard" Selection** | Avoids tautological selection bias where the static baseline is pre-selected for failure. |
| **Survival Analysis for Efficiency** | Handles censored data (no relevant lines found) which violates the symmetry assumption of Wilcoxon. |
| **<1B Model / CPU Quantization** | Ensures runnability on free-tier CI; avoids fatal GPU dependency errors and memory overflow. |
| **Bonferroni Correction** | Controls family-wise error rate for the two primary metrics (Coverage, Efficiency). |
| **Manual Validation Step** | Satisfies FR-010 and ensures the "hard" proxy is valid. |
| **Turn Limit Sweep (3 vs 4)** | Satisfies SC-006 to verify result stability. |