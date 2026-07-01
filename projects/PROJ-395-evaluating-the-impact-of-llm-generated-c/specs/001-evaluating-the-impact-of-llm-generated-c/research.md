# Research: Evaluating the Impact of LLM-Generated Code on Memory Usage

## Overview

This research plan outlines data sources, methodology, and statistical rigor required to evaluate memory consumption of LLM‑generated code versus human‑written code. The study is **observational** (A‑005); no causal claims are made.

## Dataset Strategy

The project **exclusively** uses **HumanEval** as the benchmark dataset.

| Dataset Name | Source URL (Verified) | Loader Method | Variable Fit Check |
|--------------|-----------------------|---------------|--------------------|
| HumanEval | https://huggingface.co/datasets/openai/humaneval | `datasets.load_dataset("openai/humaneval")` | **Satisfied**: Provides `prompt`, deterministic `test` inputs, and executable human reference solutions. |

**Dataset Variable Fit Confirmation**:
- **Predictors**: Code features (LOC, cyclomatic complexity, import count) extracted via static analysis (A‑006).
- **Outcomes**: Memory usage (peak, steady), execution time.
- **Covariates**: Problem ID, source type (LLM/Human).
- All required variables are present in HumanEval.

## Methodology

### Phase 1: Data Collection (FR‑001, FR‑002, FR‑003)
1. **Selection**: HumanEval (single dataset).
2. **Generation**: For **N = 30** problems, generate LLM solutions with Phi‑3‑mini‑3.8B (CPU) using a 180 s timeout (FR‑002). Problems where generation exceeds the timeout are logged and skipped.
3. **Profiling**: Execute both LLM and human reference solutions on identical test inputs.
   - `tracemalloc` records **peak** and **steady‑state** memory (FR‑003).
   - Enforce a 60 s execution timeout (A‑011). Record status (`Success`, `SyntaxError`, `Timeout`, `OOM`).
   - Run each solution **3 times**; store the **median** peak memory to mitigate nondeterminism.
4. **Pairing Logic**: Only problems where **both** LLM and human solutions have a recorded status are retained for the paired efficiency analysis. Failures are retained for the reliability analysis.
5. **Derived Metrics**:
   - **Efficiency Score** = `peak_memory_bytes * execution_time_seconds` (used for the primary paired test).
   - **Total Resource Cost** = `Memory * Time + (Failure_Penalty * 7 GB * 60 s)` (descriptive only).

### Phase 2: Feature Extraction (FR‑006)
1. Extract static features from each code solution:
   - Lines of Code (LOC).
   - Cyclomatic Complexity (McCabe, via `radon` or `networkx`).
   - Number of library import statements.
2. Store results in `features.csv`. No residual‑memory dependent variable is used; regression will model **raw** `peak_memory_bytes`.

### Phase 3: Statistical Analysis (FR‑004, FR‑005, FR‑013)
The analysis is split into two complementary tracks:

1. **Efficiency Comparison (Primary Test)**
   - **Metric**: Efficiency Score (successful runs only).
   - **Test**: **Permutation test** (10 000 iterations) on paired differences between LLM and human Efficiency Scores.
   - **Multiple‑Comparison Correction**: If ≥3 metrics are examined (e.g., peak, steady, composite), apply Holm‑Bonferroni; report raw and corrected p‑values.

2. **Reliability Comparison (Secondary Test)**
   - **Metric**: Failure rate (proportion of non‑Success statuses).
   - **Test**: Chi‑square test (or Fisher’s Exact for small counts) comparing LLM vs. Human failure counts.
   - **Effect Size**: Cramér’s V.

3. **Regression Analysis**
   - **Model**: `peak_memory_bytes ~ LOC + cyclomatic_complexity + library_import_count`.
   - **Diagnostics**: Compute Variance Inflation Factors (VIF) for each predictor; flag any VIF > 5 (FR‑007).
   - **Report**: Coefficients, standard errors, p‑values, and model R².

### Statistical Rigor & Assumptions
- **Multiple Comparisons**: Holm‑Bonferroni controls Family‑Wise Error Rate (FR‑005).
- **Power**: Target N = 30 paired observations; if fewer are available, report the achieved N and acknowledge power limitation (SC‑005).
- **Measurement Validity**: `memory_profiler` and `tracemalloc` are standard, validated tools (A‑002).
- **Collinearity**: VIF diagnostics guard against inflated standard errors; no independent‑effect claims will be made if VIF > 5.
- **Failure Handling**: Failures are excluded from the Efficiency test (to avoid penalty‑driven dominance) but are fully incorporated in the Reliability test and the descriptive Total Resource Cost.
- **Causal Claims**: None; findings are framed as associational (A‑005).

## Compute Feasibility

- **Model**: Phi‑3‑mini‑3.8B (CPU‑only) ≈ 4–5 GB RAM.
- **Memory**: CI limit 7 GB; profiling will terminate if limit exceeded, recording “exceeded_limit”.
- **Runtime**: Estimated total ≤ 3.5 h (see Technical Context in `plan.md`), comfortably within the 6 h GitHub Actions budget.
- **Disk**: HumanEval is ≈ 200 MB; all outputs are small CSV/JSON files.

## Decision Rationale

- **Dataset**: HumanEval uniquely provides executable human reference solutions, enabling a valid paired design.
- **Model**: Phi‑3‑mini‑3.8B fits CPU constraints while being a state‑of‑the‑art code model.
- **Metric Separation**: Using Efficiency Score for the primary test isolates pure memory‑time efficiency from failure penalties, addressing the floor‑effect concern.
- **Regression DV**: Raw `peak_memory_bytes` avoids mathematical coupling inherent in normalizing by LOC.
- **Sample Size**: N = 30 balances statistical power with CI runtime limits; detailed budgeting confirms feasibility.
