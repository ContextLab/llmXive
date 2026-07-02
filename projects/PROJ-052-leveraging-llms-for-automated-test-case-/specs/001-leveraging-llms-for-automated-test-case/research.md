# Research: Leveraging LLMs for Automated Test Case Generation from Natural Language Requirements

## Overview
This research phase validates the feasibility of using the Phi-2 model to generate JUnit tests from Defects4J bug descriptions, ensuring the pipeline runs within CPU-only constraints and produces statistically valid coverage comparisons on **changed lines**.

## Dataset Strategy

The project relies on the **Defects4J** dataset for input requirements (bug fix descriptions) and target source code. The "Verified datasets" block confirms the availability of Parquet files containing prompt-ready data.

| Dataset Name | Purpose | Source URL (Verified) | Loading Method |
|:--- |:--- |:--- |:--- |
| **Defects4J Context** | Input: Bug fix descriptions for prompt generation. | ` | `pandas.read_parquet` or `datasets.load_dataset` |
| **Defects4J Context (All)** | Input: Larger context for robustness checks (if sample size allows). | ` | `pandas.read_parquet` |
| **Defects4J Adapt** | Fallback/Alternative source for bug descriptions. | ` | `pandas.read_parquet` |

**Note on JUnit Datasets**: While JUnit test datasets exist in the verified list, this project focuses on **generating** tests from bug descriptions. The manual baseline tests are extracted from the Defects4J project structure itself (specifically the test methods covering the changed lines) to ensure the "same scope" comparison required by SC-001.

**Dataset Fit Check**:
- The Defects4J Parquet files contain `prompt` or `description` fields suitable for FR-001.
- The Defects4J dataset includes the target Java source code and the manual test files (in the repository structure).
- **Constraint**: The dataset does not contain "post-task anxiety" or non-technical variables; it strictly contains software engineering data, which is a perfect fit.

## Model Strategy

**Selected Model**: Microsoft Phi (2.7B parameters).
**Reasoning**:
- **Fit**: The spec mandates a CPU-optimized model. Phi (small-scale parameter counts) is small enough to be quantized (Q_K_M) to a storage footprint of approximately 2 GB., fitting comfortably within the available RAM limit alongside the Java runtime and OS overhead.
- **Capability**: Known for strong reasoning in code generation tasks relative to its size.
- **Implementation**: `llama-cpp-python` with `n_gpu_layers=0` (CPU only) and `n_ctx` set to a safe value (e.g., 2048 or 4096 depending on prompt length).

**Quantization Strategy**:
- The model will be loaded using a pre-quantized GGUF file (Q4_K_M or Q5_K_M).
- **Rationale**: Full precision would require substantial memory just for weights, risking OOM when Java builds are active. Quantization is essential for FR-002 compliance.

## Methodology

### 1. Data Preparation & Scope Isolation
- Download Defects4J Parquet.
- **Line-Level Mapping**: For each bug, extract the set of changed lines (from the Defects4J patch metadata).
- **Manual Test Identification**: Identify the specific manual test methods that cover these changed lines using JaCoCo's line mapping.
- **Strict Filtering**: **Exclude** samples where no specific manual test method is isolated in the metadata or where the manual test does not cover the changed lines. This ensures the "paired" design is valid.
- **Logging**: All excluded samples are logged with the reason (e.g., "no isolated baseline") for descriptive analysis.

### 2. Test Generation (FR-001, FR-002)
- **Prompt Engineering**: Construct prompts using `jinja2` templates: "Generate a JUnit test for the following bug fix description...".
- **Inference**: Run Phi-2 with `seed=42`, `temperature=0.0`.
- **Output**: Save generated Java code to `output/generated/{project_id}/{test_name}.java`.

### 3. Execution & Coverage (FR-003, FR-004)
- **Compilation**: Use `javac` to compile generated tests against the target project's classes.
- **Timeout**: Enforce a time limit per test execution. (FR-003).
- **Retry**: Implement a limited number of retry attempts for transient failures. (FR-006).
- **Coverage**: Run tests via `java -jar jacocoagent.jar...` to collect coverage data.
- **Metric Calculation**: Calculate coverage **only on the changed lines** for both generated and manual tests.
- **Output**: Aggregate results into `coverage_metrics.csv` (SC-001).

### 4. Statistical Analysis (FR-005, FR-008, FR-010)
- **Normality Check**: Shapiro-Wilk test on the differences (Generated - Manual) on changed lines.
- **Test Selection**:
 - **Primary**: Wilcoxon signed-rank test (robust to skew/boundedness).
 - **Sensitivity**: Paired t-test (only if Shapiro-Wilk p > 0.10).
- **Metrics**: Calculate mean difference, p-value, confidence interval, and effect size.
- **Power Analysis**:
 - **A Priori**: Calculate required N for a target effect size (e.g., d=0.5) to inform expectations.
 - **Post-hoc**: Calculate achieved power based on observed effect size and N. **Explicitly report if power < 0.8 and frame study as "exploratory" if so.**
- **Assertion Density**: Calculated and reported as a **descriptive** metric (FR-009), NOT used for validation.

## Decision Rationale & Constraints

| Decision | Rationale | Constraint Addressed |
|:--- |:--- |:--- |
| **Line-Level Coverage** | Ensures valid pairing (Generated vs. Manual on same scope). | Scientific Soundness (Construct Validity) |
| **Strict Exclusion** | Prevents comparing a single test against a global suite (Category Error). | Scientific Soundness (Pairing Validity) |
| **Wilcoxon Primary** | Robust to bounded, skewed coverage data with small N. | Scientific Soundness (Statistical Assumptions) |
| **Exploratory Framing** | Acknowledges power limitations of small N. Avoids Type II errors by focusing on effect sizes/CI. | Methodology (Power Analysis) |
| **Phi-2 (Quantized)** | Only viable 2.7B model fitting 7GB RAM on CPU. | FR-002, SC-004 |
| **CPU Only** | GitHub Actions free tier has no GPU. | SC-004 |
| **JaCoCo** | Industry standard for Java coverage; supports line-level mapping. | FR-004, SC-001 |
| **30s Timeout** | Prevents infinite loops in generated code (Edge Case). | FR-003 |
| **Sample Limit** | Hard stop at a predefined runtime limit or N samples to ensure CI success. | FR-007 |
| **Schema Validation** | Ensures data integrity before analysis. | Plan Consistency (Testing Strategy) |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Invalid Pairing** | High (Scientific invalidity) | Strict line-level mapping. **Exclude** unpairable samples. |
| **High Exclusion Rate** | Medium (Sample size reduction) | Monitor rate. Flag study as limited to subset if rate is high. |
| **OOM during Java Build** | High (Pipeline crash) | Limit Java heap (`-Xmx2g`); run generation and execution in separate processes. |
| **Model Hallucination** | Medium (Invalid code) | Retry mechanism; mark as "failed to compile". |
| **Defects4J Extraction Failure** | Medium (Data loss) | Skip failed projects, log error, continue (Edge Case). |
| **Statistical Power < 0.8** | High (Inconclusive results) | Perform a priori analysis. If N is insufficient, explicitly label study as "exploratory" and report effect sizes/CI rather than relying on p-values. |

## References
- Defects4J Dataset: Verified URLs in "Dataset Strategy" table.
- Phi-2 Model: Microsoft Research (via `llama.cpp` community quantizations).
- JaCoCo: https://www.eclemma.org/jacoco/