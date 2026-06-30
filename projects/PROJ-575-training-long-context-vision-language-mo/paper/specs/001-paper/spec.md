# Feature Specification: Reproduce & Validate Long-Context VLM Training with MMLongBench

**Feature Branch**: `575-reproduce-long-context-vlm`
**Created**: 2026-07-01
**Status**: Draft
**Input**: Research-stage artifacts (spec.md, plan.md, tasks.md) and code/data summaries.

## User Scenarios & Testing

### User Story 1 - Reproduce Core Evaluation Results (Priority: P1)

The reader (peer reviewer or researcher) MUST be able to follow the paper's "Methods" section and execute the provided evaluation pipeline to reproduce the primary quantitative results (long-document VQA scores) without requiring specialized hardware (GPU).

**Why this priority**: This is the fundamental test of scientific reproducibility. If a reader cannot regenerate the core numbers claimed in the abstract using the provided code and standard compute (CPU), the paper's validity is immediately compromised. This story covers the "Results" section's primary claims.

**Independent Test**: Execute the `src/eval/run_cpu_eval.py` script with a minimal sample size (`--sample-size=10`) on a CPU-only environment. Verify that the output file `results/sample_results.json` is generated and contains the expected columns (`context_length`, `task_type`, `model_baseline_score`, `model_target_score`) matching the schema defined in `contracts/`.

**Acceptance Scenarios**:
1. **Given** a standard CPU environment with < 8 GB RAM, **When** the user runs the evaluation script with the `yubo2333/MMLongBench-Doc` dataset, **Then** the system completes the run within 60 minutes and outputs a valid JSON file containing at least 10 rows of evaluation data.
2. **Given** the generated `sample_results.json`, **When** a reader inspects the `model_target_score` for the "long-document VQA" task, **Then** the value is present and numerically comparable to the baseline score, allowing for a direct calculation of the reported improvement.

### User Story 2 - Verify Generalization Claims (Priority: P2)

The reader MUST be able to locate the evidence supporting the paper's claim of "generalization beyond 128K context" by examining performance retention rates at 256K and 512K context lengths relative to the 128K baseline.

**Why this priority**: The paper's novel contribution is the claim of scaling beyond the training window. A reader needs to verify that the model does not degrade catastrophically at these lengths. This story addresses the specific "Generalization" findings in the Results section.

**Independent Test**: Run the validation script `src/eval/validate_results.py` against the generated results. The script must calculate the retention rate (Performance@256K / Performance@128K) and compare it against the paper's implicit or explicit threshold (≥ 80%).

**Acceptance Scenarios**:
1. **Given** the evaluation results covering context lengths up to 512K, **When** the validation logic computes the retention rate for the 256K and 512K contexts, **Then** the output report explicitly states whether the retention rate meets the ≥ 80% threshold and highlights any significant drop-offs.
2. **Given** the `results/validation_report.md`, **When** a reviewer reads the "Generalization" section, **Then** they can clearly see the delta between the 128K baseline and the extended context performance, confirming the "beyond 128K" claim.

### User Story 3 - Analyze Scaling Trends (Priority: P3)

The reader (specifically a methodologist or statistician) MUST be able to access the scaling analysis to determine if the performance relationship with context length is linear, sublinear, or superlinear, acknowledging the statistical limitations of the sample size.

**Why this priority**: This addresses the specific reviewer concern (Geoffrey West) regarding the lack of scaling law analysis. While statistical significance is limited by the small sample size (n=10), the descriptive trend provides necessary context for interpreting the model's behavior at scale.

**Independent Test**: Execute `src/eval/scaling_analysis.py` to fit a regression model of `score` vs. `log(context_length)`. Verify that `results/scaling_report.json` contains the slope coefficient, R², and a trend classification.

**Acceptance Scenarios**:
1. **Given** results from at least 5 distinct context lengths (32K to 512K), **When** the analysis script fits the regression model, **Then** the output includes a clear classification (e.g., "sublinear", "inconclusive") and a disclaimer stating that multiple-comparison corrections were not applied due to insufficient statistical power.
2. **Given** the final `results/final_report.md`, **When** a reader reviews the "Scaling Analysis" section, **Then** they find a plot or table data mapping performance against context length, along with the calculated slope and an explicit statement of limitations regarding the small sample size.

### Reader Scenarios (Paths)

1. **Skim Path (Primary Contribution)**: A motivated outsider must grasp the single, unambiguous scientific finding without running code.
 * **Requirement**: The Abstract must contain a **Primary Citation Claim** that is a single sentence reporting the *measured result* (e.g., "We observed a deviation of X%...", "Retention was Y%...", or "Evaluation failed due to Z").
 * **Requirement**: The Introduction must explicitly state the hypothesis and the primary measured outcome.
 * **Abstract Construction Logic**: The claim in the Abstract must be dynamically selected based on the execution outcome:
 - **If** Claim 5 (Negative Result/Failure) is triggered, the Primary Citation Claim MUST be the specific failure statement (e.g., "Evaluation failed due to OOM").
 - **Otherwise**, the Primary Citation Claim MUST be the measured reproduction deviation (Claim 1).

2. **Deep-Read Path (Reproducibility Surface)**: A researcher must be able to reproduce the exact numbers and fail the experiment if conditions are not met.
 * **Requirement**: The Methods section must explicitly enumerate the "Reproducibility Surface":
 * Exact code commit hash used (populated from `results/evaluation_run.json`).
 * Data seed and specific dataset version (manifest.json checksum, populated from `data/manifest.json`).
 * Environment versions (Python, PyTorch, Transformers, populated from `requirements.txt` or runtime logs).
 * Hardware constraints (7GB RAM, CPU).
 * **Dynamic Insertion**: The spec requires that these values are not hardcoded in the draft but are inserted by the generation process from the actual execution artifacts.

3. **Citation Path**: A citing scientist needs one unambiguous sentence to attribute.
 * **Requirement**: The "Required Claims" section must define a single "Primary Citation Claim" that is the measured scientific result, distinct from the process of attempting the reproduction.
 * **Selection Logic**: The paper must adhere to the **Primary Claim Selection Logic** defined in the Skim Path: Claim 5 takes precedence if triggered; otherwise, Claim 1 is the primary claim.

## Required Sections

The paper text generated from this specification must include the following sections, mapped to the validation tasks:

1. **Abstract**: Must summarize the reproduction attempt, the *measured* primary finding on long-document VQA improvement (exact deviation %), and the *measured* generalization retention rate. Must contain the **Primary Citation Claim** selected per the logic above.
2. **Introduction**: Must state the problem of long-context generalization, the specific hypothesis being tested, and the *measured* outcome of the test.
3. **Methods**: Must explicitly detail:
 * The CPU-only execution environment.
 * The low-bit quantization strategy (Qwen2.5-VL-7B).
 * The specific dataset split (`test` from `yubo2333/MMLongBench-Doc`).
 * **Reproducibility Surface**: Code commit hash (from execution log), data seed, environment versions, and manifest checksum (from `data/manifest.json`).
4. **Results**: Must present:
 * The *measured* reproduction metrics (exact deviation %).
 * The *measured* retention rates at 256K/512K.
 * The *measured* scaling trend analysis (slope/R²/classification).
 * **Negative Results**: Explicit reporting of any failures (OOM, Data Unavailable) if they occurred.
5. **Discussion**: Must interpret the *measured* scaling trends, explicitly discuss the limitations of the small sample size (n=10) and the lack of multiple-comparison correction, and compare findings to the original paper. Must include a "Discrepancy Analysis" if deviation > 1.0%.
6. **References**: Must cite the original paper, the MMLongBench dataset, and the specific model weights used.

## Required Figures

1. **Figure 1: Performance vs. Context Length Scaling Curve**
 * **Purpose**: Visualize the relationship between model score and log(context_length) to demonstrate the *measured* trend.
 * **Data Source**: `results/scaling_report.json` (aggregated scores from `results/sample_results.json`).

2. **Figure 2: Generalization Retention Rate Bar Chart**
 * **Purpose**: Compare *measured* performance at 128K (baseline) against 256K and 512K.
 * **Data Source**: `results/validation_report.md` (calculated retention rates).

3. **Figure 3: Reproduction Delta Plot**
 * **Purpose**: Show the *measured* difference between reproduced scores and the original paper's claimed scores.
 * **Data Source**: `results/sample_results.json` vs. the paper's abstract values.

## Required Claims

The paper MUST explicitly state the following findings based on the *measured* results. If a result is negative or inconclusive, the corresponding claim template MUST be used.

### Claim 1: Reproduction Validity (Primary Citation Claim if no failure)
* **Template**: "We evaluated the long-document VQA scores and observed a deviation of **X%** from the original paper's claims."
* **Requirement**: The value X must be the exact measured deviation.
* **Condition**: If X > 1.0%, the Discussion MUST include a "Discrepancy Analysis" subsection detailing potential causes (quantization noise, dataset drift).
* **Note**: This claim is the *measured result*, not a statement of success or failure.

### Claim 2: Generalization Capability
* **Template**: "We measured the performance retention rate at 256K and 512K context lengths to be **Y%** of the 128K baseline."
* **Requirement**: The value Y must be the exact measured retention rate.
* **Condition**: If Y < 80%, the paper must explicitly state that the "generalization beyond 128K" hypothesis was not supported by this specific evaluation.

### Claim 3: Scaling Behavior
* **Template**: "The relationship between performance and context length exhibited a **Z** trend (Slope: **S**, R²: **R**)."
* **Requirement**: **Z** must be one of: "sublinear", "superlinear", "linear", or "inconclusive".
* **Condition**: If R² < 0.1, **Z** MUST be "inconclusive" or "highly variable". The paper MUST NOT claim a specific trend if the data is inconclusive.

### Claim 4: Resource Feasibility
* **Template**: "We evaluated the feasibility of long-context VLM evaluation on standard CPU hardware with limited RAM using 4-bit quantization."
* **Requirement**: The paper must state the *outcome*:
 * **Success**: "The evaluation completed successfully within the memory constraints."
 * **Failure**: "The evaluation failed due to [Specific Error: e.g., OOM during model loading]."
* **Condition**: If the evaluation failed, the paper MUST report the specific error and cannot claim feasibility.

### Claim 5: Negative Results & Failure Modes (First-Class Claim)
* **Template**: "We encountered a [Data Unavailability / OOM / Inconclusive Scaling] failure mode."
* **Requirement**: If the research plan encounters any of the defined edge cases (Data Unavailable, OOM, Inconclusive Trend), this claim MUST be the primary finding.
* **Condition**: This claim takes precedence over Claims 1-4 if the experiment could not be completed as intended.

## Edge Cases (Specific to Paper Drafting)

- **Discrepant Results**: If the reproduced scores deviate by > 2.0% from the paper's claims, the Discussion section MUST explicitly analyze potential causes (e.g., quantization noise, dataset version drift) rather than silently ignoring the discrepancy.
- **Missing Data**: If the `yubo2333/MMLongBench-Doc` dataset is unavailable or corrupted, the paper MUST state "Evaluation could not be completed due to data unavailability" and not fabricate results. This triggers Claim 5.
- **Ambiguous Trend**: If the regression R² is < 0.1, the paper MUST avoid claiming a specific scaling law and instead describe the data as "highly variable" or "inconclusive" (Claim 3).

## Requirements

### Functional Requirements

- **FR-001**: The paper MUST explicitly state the use of low-bit quantization for the Qwen-VLB model to satisfy the GB RAM constraint.
- **FR-002**: The paper MUST include a "Limitations" subsection in the Discussion explicitly acknowledging the small sample size (n=10) and the lack of statistical power for hypothesis testing.
- **FR-003**: The paper MUST present the performance retention rate at 256K and 512K contexts as a percentage of the 128K baseline.
- **FR-004**: The paper MUST include a scaling analysis section with a regression slope and trend classification derived from `results/scaling_report.json`.
- **FR-005**: The paper MUST cite the specific dataset source (`yubo2333/MMLongBench-Doc`) and the split used (`test`) in the Methods section.
- **FR-006**: The paper MUST explicitly state the *measured deviation* from the original paper's claims. The ±1.0% tolerance is a threshold for analysis, not a pass/fail condition for the claim itself.
- **FR-007**: The paper MUST include a "Data Provenance" statement referencing the `manifest.json` checksums or dataset version.
- **FR-008**: The paper MUST NOT claim statistical significance (p < 0.05) for the scaling trends due to the sample size constraints.
- **FR-009**: The paper MUST include a "Reproducibility Surface" section listing code commit hashes, data seeds, and environment versions (populated from execution artifacts).
- **FR-010**: The paper MUST define a single "Primary Citation Claim" in the Abstract that summarizes the measured scientific result, selected per the **Primary Claim Selection Logic**.

## Key Entities

- **EvaluationRun**: Represents a single execution of the evaluation pipeline, containing metadata (run_id, timestamp, sample_size, context_lengths) and the resulting metrics.
- **BenchmarkResult**: Represents the score of a model on a specific task at a specific context length, containing `task_id`, `context_length`, `score`, and `baseline_score`.
- **ScalingAnalysis**: Represents the aggregated analysis of performance across context lengths, containing `slope_coefficient`, `r_squared`, and `trend_classification`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The reproduction of the long-document VQA score is measured against the paper's claimed value. The paper MUST report the *exact measured deviation* (X%). The ±1.0% tolerance is used to determine if a "Discrepancy Analysis" is required, not to determine if the claim is valid.
- **SC-002**: The generalization retention rate at 256K/512K is measured against the 128K baseline. The paper MUST report the *exact measured percentage* (Y%).
- **SC-003**: The scaling trend classification is measured against the regression slope of performance vs. log(context_length). The paper MUST report the *measured classification* (including "inconclusive").
- **SC-004**: The paper's "Limitations" section is measured against the requirement to explicitly state the lack of multiple-comparison correction and small sample size.
- **SC-005**: The data provenance is measured against the presence of a valid dataset checksum in the `manifest.json` referenced in the paper.
- **SC-006**: The "Primary Citation Claim" is measured against the requirement to be a single, unambiguous sentence about the measured result, selected per the **Primary Claim Selection Logic**.

## Assumptions

- **Assumption about Data Availability**: The `yubo2333/MMLongBench-Doc` dataset is accessible via the Hugging Face Hub and remains unchanged during the evaluation period.
- **Assumption about Model Weights**: The `Qwen2.5-VL-7B` model weights are available in a format compatible with 4-bit quantization on CPU.
- **Assumption about Scope**: The paper focuses on the *evaluation* and *validation* of the existing code, not on re-training the model from scratch.
- **Assumption about Statistical Interpretation**: The term "generalization beyond 128K" is interpreted as maintaining performance retention (≥ 80%) rather than achieving perfect parity with the 128K baseline.
- **Assumption about Reviewer Expectations**: Reviewers will accept descriptive trend analysis in lieu of rigorous hypothesis testing due to the resource constraints of the reproduction environment.

## Primary Claim Selection Logic

To ensure a single, unambiguous Primary Citation Claim for the Abstract:

1. **Check for Failure**: If the execution results in a failure mode defined in Claim 5 (Data Unavailable, OOM, or Inconclusive Scaling where R² < 0.1 and no trend can be described), then **Claim 5** is the Primary Citation Claim.
2. **Default to Reproduction**: If no failure mode is triggered, **Claim 1** (Reproduction Validity) is the Primary Citation Claim.
3. **Secondary Claims**: Claims 2, 3, and 4 are reported in the Results and Discussion but do not serve as the Primary Citation Claim in the Abstract.