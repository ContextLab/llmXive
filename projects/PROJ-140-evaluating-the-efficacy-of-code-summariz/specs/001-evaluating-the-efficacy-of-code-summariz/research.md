# Research: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

## 1. Dataset Strategy

The study relies on the **Defects4J v2.0** dataset, which provides buggy Java methods and ground-truth buggy lines. To ensure reproducibility and CI feasibility, we use verified HuggingFace Parquet mirrors.

### Verified datasets

| Dataset | Source URL | Variables Used | Access Method | Notes |
|:--- |:--- |:--- |:---:--- |
| Defects4J (Parquet) | ` | `code`, `buggy_line`, `project_name` | `datasets.load_dataset("parquet", data_files=...)` | Primary source for buggy methods. |
| Defects4J (Alt) | ` | `code`, `buggy_line` | `datasets.load_dataset("parquet",...)` | Fallback source if primary is unavailable. |

**Dataset Fit Verification**:
- **Required Variables**: The study needs `code` (for summary generation), `buggy_line` (ground truth for accuracy), and `project_name` (for stratification).
- **Match**: The verified HuggingFace Parquet files contain these fields.
- **Gap Check**: The spec assumes "official bug report text". **Verification Step**: The `verify_schema.py` script will check for `bug_report_text`. If missing (as expected in community mirrors), the script will log a warning and proceed with the "code-only" analysis path. This deviation is documented as a known limitation. The study will not use bug report text if it is unavailable.
- **Decision**: The plan uses code context only for summary generation to ensure robustness against missing metadata.

**Data Availability & Feasibility**:
- **Download**: The datasets are directly downloadable via `datasets` library. No credentials or DRAs required.
- **Size**: The Parquet files are small (<100MB), fitting easily within the 14GB disk and 7GB RAM limits.
- **Streaming**: Not required due to small size, but the code will use `streaming=True` if the dataset grows.
- **Sampling**: We will extract a stratified sample of methods across Chart, Time, and Math projects to ensure balanced representation.

## 2. Statistical Methodology

### 2.1. Accuracy Analysis (McNemar's Test)
- **Metric**: Binary outcome (Correct/Incorrect) based on whether the participant selected the `buggy_line`.
- **Test**: McNemar's test for paired nominal data (Baseline vs. LLM; Baseline vs. Rule).
- **Effect Size**: Odds Ratio (OR) with 95% Confidence Interval (CI) via bootstrapping (10,000 resamples, fixed seed).
- **Correction**: Holm-Bonferroni correction applied across the 4 tests (2 accuracy, 2 speed) to control family-wise error rate at α=0.05.

### 2.2. Speed Analysis (Linear Mixed-Effects Models)
- **Metric**: Time-to-decision (milliseconds) from task display to line click.
- **Model**: LME with fixed effects for `condition` and random intercepts for `participant_id`.
 - Formula: `time ~ condition + (1 | participant_id)`
- **Effect Size**: Cohen's d (standardized mean difference) with 95% CI via bootstrapping.
- **Assumptions**: Normality of residuals will be checked; if violated, robust standard errors or non-parametric alternatives (Wilcoxon signed-rank) will be reported as sensitivity analysis.

### 2.3. Power & Sample Size
- **Limitation**: The study uses a simulated cohort of participants (multiple observations). This is a convenience sample for pipeline validation.
- **Acknowledgement**: The plan explicitly states that power calculations for the *simulated* data are not the goal; the goal is to validate the *analysis pipeline*. For a real study, a power analysis would be required to determine N.
- **Correction**: The plan includes a sensitivity analysis section to report how results vary with different significance thresholds.
- **Interpretation Warning**: P-values derived from this simulation are **not** evidence of human efficacy. They are a check that the statistical engine correctly recovers the parameters programmed into the simulation.

## 3. Compute Feasibility & GPU Strategy

### 3.1. CPU-First Approach (Analysis)
- **Statistical Analysis**: All statistical tests (McNemar's, LME, bootstrapping) are implemented in `statsmodels` and `scipy`, which run efficiently on CPU.
- **Data Processing**: `pandas` operations on ~360 rows are negligible in time/memory.
- **LLM Generation**: The spec requires LLM generation for the *data collection phase*.
 - **Constraint**: Running `CodeLlama-7b` (even 8-bit) on a GitHub Actions free-tier CPU is infeasible (would take hours per sample, exceeding 6h job limit).
 - **Resolution**: The "LLM-generated summary" condition is **generated offline** using the required `codellama/CodeLlama-7b-hf` model on a GPU machine. The resulting summaries are stored as static artifacts in `data/processed/summaries/llm_summaries.json`.
 - **CI Execution**: The CI job loads these pre-generated summaries. It does *not* run the LLM inference. This ensures the analysis runs within 6h on CPU while still analyzing the *actual* LLM outputs.
 - **Fallback Logic**: The code retains the fallback logic (if a summary is missing in the pre-generated file, use rule-based), satisfying the spec's robustness requirement.
 - **Reproducibility**: The "Offline Generation Protocol" (documented in `docs/README.md`) ensures that the generation step can be re-run on a GPU machine to regenerate the artifacts if the model or data changes.

### 3.2. GPU Escape Hatch (Not Required for Analysis)
- No GPU is needed for the statistical analysis phase.
- The LLM generation step is an offline pre-requisite, not part of the CI pipeline.

## 4. Data Model & Variable Fit

- **Participant**: `participant_id` (anonymized), `condition_assignments` (Latin-square).
- **Task**: `task_id`, `method_id`, `condition`, `ground_truth_line`, `selected_line`, `timestamp_ms`.
- **Summary**: `summary_id`, `method_id`, `type`, `text`.
- **Fit**: All variables are present in the simulated data generation logic and the Defects4J source. No missing variables.

## 5. Simulation Validity

The study uses a **Simulated Human Study** to validate the analysis pipeline.
- **Purpose**: To verify that the pipeline correctly handles Latin-square designs, missing data, and computes statistical metrics (p-values, effect sizes) without crashing.
- **Mechanism**: Participant behavior is generated deterministically based on programmed parameters (e.g., "if summary_quality > threshold, select correct line with probability P").
- **Validity Check**: The analysis will include a step to verify that the pipeline correctly recovers the known input parameters (e.g., does the computed OR match the programmed effect size?).
- **Limitation**: The p-values and effect sizes from this simulation are **artifacts of the simulation logic** and do not represent empirical human performance. They are used solely to validate the *pipeline*, not to claim efficacy.

## 6. Statistical Assumption Check

- **LME Models**: Applied to simulated data to verify that the model correctly estimates random effects variance. The input variance is known; the output is compared to ensure the model is functioning correctly.
- **Normality**: Since the data is simulated, normality assumptions are controlled by the simulation parameters. The pipeline will still check for normality to ensure robustness.

## 7. Decision Rationale

- **Why Simulation?**: Real human subjects cannot be recruited in a 6h CI window. Simulation allows the *pipeline* to be tested end-to-end.
- **Why Pre-generated Summaries?**: Running 7B parameter models on CPU is too slow. Pre-generation separates the "data creation" (GPU/Offline) from "data analysis" (CPU/CI).
- **Why Bootstrapping?**: Small sample size (N=12) violates parametric assumptions; bootstrapping provides robust CIs.
- **Why Holm-Bonferroni?**: Controls family-wise error rate across 4 tests more powerfully than Bonferroni.
- **Why CodeLlama-7b-hf?**: Required by the spec. The offline generation step ensures this requirement is met without violating CI constraints.