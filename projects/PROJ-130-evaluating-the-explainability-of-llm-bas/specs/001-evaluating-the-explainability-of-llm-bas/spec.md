# Feature Specification: Evaluating the Explainability of LLM-Based Bug Fixes

**Feature Branch**: `001-eval-explainability-llm-bug-fixes`  
**Created**: 2026-06-29  
**Status**: Draft  
**Input**: User description: "How well do different explainability techniques (attention visualization, code‑diff saliency maps, and generated natural‑language rationales) reflect the actual correctness and safety of bug fixes suggested by large language models for source‑code defects? The project will use Defects4J, CodeLlama‑7B‑Instruct, and statistical analysis to evaluate correlation and predictive power of each technique."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Generate Explainable Patches (Priority: P1)

A researcher wants to run the pipeline on a set of buggy programs, obtain a generated patch from CodeLlama, and automatically extract three explainability artefacts (attention heatmap, saliency map, natural‑language rationale) for each patch.

**Why this priority**: This story delivers the core data needed for any downstream analysis; without it the research question cannot be addressed.

**Independent Test**: Execute the pipeline on a single Defects4J bug and verify that (a) a diff‑style patch is saved, (b) an attention heatmap file is produced, (c) a saliency‑score CSV is generated, and (d) a textual rationale file is created.

**Acceptance Scenarios**:

1. **Given** a buggy version of a Defects4J project and the associated failing test description, **When** the pipeline is invoked, **Then** a patch file, attention heatmap, saliency scores, and rationale text are written to the output directory.
2. **Given** a bug where the model fails to produce a syntactically valid patch, **When** the pipeline reaches the generation step, **Then** it logs a warning and skips explainability extraction for that bug without aborting the whole run.

---

### User Story 2 – Assess Patch Correctness and Safety (Priority: P2)

A developer wants to automatically apply each generated patch to the buggy code, run the full Defects4J test suite, and record whether the patch passes all original tests and does not introduce new failures.

**Why this priority**: Correctness labels are the ground‑truth outcome against which explainability scores are correlated.

**Independent Test**: Run the correctness assessment on the output of User Story 1 for a single bug and confirm that a binary pass/fail flag and a count of newly failing tests are stored.

**Acceptance Scenarios**:

1. **Given** a generated patch and its corresponding buggy source, **When** the patch is applied and the test suite is executed, **Then** the system records `correct = True` if all original tests pass and no new failures appear, otherwise `correct = False`.

---

### User Story 3 – Quantitative Evaluation & Reporting (Priority: P3)

A researcher wants to compute explainability scores, correlate them with patch correctness, fit logistic‑regression models, perform multiple‑comparison‑corrected hypothesis tests, and generate a reproducible Jupyter notebook summarizing the results.

**Why this priority**: This story produces the empirical evidence needed to answer the research question and supports reproducibility.

**Independent Test**: Execute the analysis script on a pre‑computed dataset of 50 bugs and verify that (a) Spearman ρ values, (b) logistic‑regression odds ratios, (c) AUC‑ROC scores, and (d) a notebook with tables/figures are produced, and that all statistical tests report p‑values ≤ 0.05 after Bonferroni correction where appropriate.

**Acceptance Scenarios**:

1. **Given** a CSV containing explainability scores and correctness labels for 50 bugs, **When** the analysis notebook is run, **Then** it outputs correlation coefficients, regression summaries, and a table of pairwise t‑test results with Bonferroni‑adjusted p‑values.
2. **Given** the same input, **When** the notebook is executed with a different threshold for attention‑weight aggregation (e.g., 0.01 vs. 0.05), **Then** a sensitivity‑analysis section reports how the headline correlation and regression odds ratios vary across thresholds.

---

### Edge Cases

- What happens when a bug lacks a human‑written patch note in Defects4J?  
  *The pipeline falls back to a placeholder rationale and records `[NO_HUMAN_RATIONALE]` for BLEU computation.*

- How does the system handle a model‑generated patch that does not compile?  
  *The patch is flagged as invalid, `correct = False`, and explainability extraction is skipped for that bug.*

- What if Captum’s Integrated Gradients fails on a very long diff?  
  *The script truncates the diff to the first 512 tokens (the model’s context limit) and logs the truncation.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and extract the Defects4J v2.0 dataset, preserving buggy source files, test suites, and any available human patch notes. (See US‑1)  
- **FR-002**: System MUST load the CodeLlama‑7B‑Instruct model using the `transformers` library in CPU‑only mode and generate a diff‑format patch for each bug prompt. (See US‑1)  
- **FR-003**: System MUST extract per‑token attention weights from the model’s final decoder layer for the generated patch and aggregate them into a file‑level heatmap. (See US‑1)  
- **FR-004**: System MUST compute Integrated Gradients saliency scores for each edited line of the diff using Captum and output a numeric importance score per line. (See US‑1)  
- **FR-005**: System MUST prompt the model to produce a short natural‑language rationale for each edit and compute BLEU and ROUGE scores against the human‑written patch note when available. (See US‑1)  
- **FR-006**: System MUST apply each generated patch to the buggy source, run the full Defects4J test suite, and record a binary correctness label plus a count of newly failing tests. (See US‑2)  
- **FR-007**: System MUST compute three explainability scores per bug: (a) average attention weight on edited tokens, (b) summed absolute saliency magnitude on edited lines, (c) BLEU similarity of the rationale. (See US‑3)  
- **FR-008**: System MUST perform Spearman correlation analysis between each explainability score and the binary correctness label, reporting ρ and two‑tailed p‑value. (See US‑3)  
- **FR-009**: System MUST fit logistic‑regression models predicting correctness from each explainability score individually and from the multivariate combination, reporting odds ratios, confidence intervals, and AUC‑ROC. (See US‑3)  
- **FR-010**: System MUST conduct paired t‑tests comparing the predictive performance of the three techniques, applying Bonferroni correction for multiple comparisons. (See US‑3)  
- **FR-011**: System MUST include a sensitivity analysis that sweeps the attention‑aggregation threshold over a low, intermediate, and higher range of values and the saliency‑magnitude threshold over a comparable set of values, reporting how correlation coefficients and regression odds ratios change. (Methodological soundness: threshold justification & sensitivity) (See US‑3)  
- **FR-012**: System MUST generate a reproducible Jupyter notebook that contains all data tables, figures, and statistical test outputs, and can be executed on the CI runner using the same 50‑bug subset. (See US‑3)  
- **FR-013**: System MUST enforce CPU‑only execution; any attempt to enable CUDA or GPU‑accelerated libraries must raise a runtime error and abort the job. (Compute feasibility) (See US‑1)  

### Clarification Needs

- **FR-014**: System MUST verify that Defects4J provides a human‑written patch note for each bug used in BLEU evaluation. [NEEDS CLARIFICATION: Does Defects4J contain human rationale text for all selected bugs?] (See US‑1)  
- **FR-015**: System MUST ensure that the test suite for each bug fully captures functional correctness and safety; otherwise, additional safety checks must be defined. [NEEDS CLARIFICATION: Are there known safety‑critical test failures in Defects4J that should be treated specially?] (See US‑2)  
- **FR-016**: System MUST determine the minimum sample size required for adequate power to detect a Spearman ρ of 0.3 at α = 0.05. [NEEDS CLARIFICATION: Desired power level (e.g., 0.8) and whether 50 bugs is sufficient.] (See US‑3)

### Key Entities

- **BugInstance**: Represents a single Defects4J bug, with attributes `bug_id`, `buggy_source`, `test_suite`, `human_patch_note` (optional).  
- **GeneratedPatch**: Contains `diff_text`, `attention_heatmap`, `saliency_scores`, `rationale_text`, and derived explainability scores.  
- **EvaluationResult**: Holds `correctness_label`, `new_failure_count`, and statistical outputs for the bug.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ≥ 95% of bugs in the 50‑bug subset produce a syntactically valid diff file (See US‑1).  
- **SC-002**: All attention, saliency, and rationale artefacts are generated within 30 seconds per bug on the CI runner (CPU‑only) (See US‑1).  
- **SC-003**: Spearman correlation between saliency‑map score and correctness is statistically significant (p < 0.05) after Bonferroni correction (See US‑3).  
- **SC-004**: Logistic‑regression model using rationale‑BLEU achieves an odds‑ratio > 2 with 95% confidence interval not crossing 1 (See US‑3).  
- **SC-005**: Sensitivity analysis shows that varying the attention threshold across {0.01, 0.05, 0.1} changes the Spearman ρ by no more than ±0.05, demonstrating robustness (See US‑3).

## Assumptions

- The CI environment provides 2 CPU cores, ~7 GB RAM, and ≤ 6 h runtime; all scripts are written in pure Python 3.11 with CPU‑only libraries.  
- Defects4J v2.0 contains both buggy source files and corresponding JUnit test suites for every selected bug.  
- CodeLlama‑7B‑Instruct can be loaded in CPU memory (~13 GB) within the CI runner’s 7 GB RAM limit by using `torch_dtype=torch.float16` and `low_cpu_mem_usage=True`.  
- Human‑written patch notes are available for at least 30 of the 50 bugs; for the remainder, BLEU will be computed against a manually curated subset (assumed sufficient for exploratory analysis).  
- Statistical significance thresholds (α = 0.05) and Bonferroni correction are appropriate for the three pairwise comparisons.  
- No GPU or CUDA libraries will be installed; any attempt to import them will cause the job to fail, satisfying the free‑CPU feasibility requirement.
