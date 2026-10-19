# Feature Specification: Quantifying Hallucination in LLM-Generated API Documentation

**Feature Branch**: `001-quantifying-hallucination-in-llm-generat`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "Quantifying Hallucination in LLM-Generated API Documentation"

## User Scenarios & Testing

### User Story 1 - Automated Metric Calculation Pipeline (Priority: P1)

**Journey**: As a researcher, I want the system to automatically ingest a stratified random sample of the CodeSearchNet Python dataset, generate one‑sentence API descriptions using CPU‑only LLMs (`codegen-350M` and `starcoderbase-1b`), and compute a real **HallucinationIndex** for each function, so that I can quantify factual accuracy without manual intervention.

**Why this priority**: This is the core data‑generation engine. Without actual model outputs and a genuine hallucination metric, no statistical analysis can be performed.

**Independent Test**: Run the pipeline on a small sample (e.g., a modest number of functions) and verify that a CSV is produced. containing the code metrics, the entity‑overlap F1 score, the semantic‑similarity score, and the HallucinationIndex (0 ≤ index ≤ 1) derived from real LLM generations.

**Acceptance Scenarios**:

1. **Given** a CSV of 100 Python functions with source code and reference docstrings, **When** the generation script is executed with `codegen-350M` and `starcoderbase-1b` (CPU‑only), **Then** a results CSV is produced where every row contains a valid HallucinationIndex computed from actual generated text.
2. **Given** a function with a complex signature, **When** the entity‑extraction module runs, **Then** the system correctly identifies parameter names and return types in both the source AST and the generated description to calculate the entity‑overlap F1 score.
3. **Given** the system runs on a GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM), **When** processing 1 000 functions, **Then** the job completes within **4 hours** without exceeding memory limits, using real tokens rather than placeholders.

---

### User Story 2 - Correlation Analysis & Visualization (Priority: P2)

**Journey**: As a researcher, I want the system to compute Spearman rank‑correlation coefficients and fit a multiple linear regression model between the **real** HallucinationIndex and intrinsic code characteristics (function length, identifier descriptiveness, cyclomatic complexity), and generate a summary report, so that I can determine whether specific code attributes drive hallucinations while controlling for confounders.

**Why this priority**: This directly answers the research question by turning raw metrics into scientifically interpretable findings.

**Independent Test**: Provide a pre‑computed CSV of metrics and HallucinationIndices and verify that the analysis script outputs a JSON (or text) report listing Spearman ρ, p‑values, Bonferroni‑adjusted p‑values, and regression β‑coefficients for each predictor.

**Acceptance Scenarios**:

1. **Given** a dataset with a large number of records of code metrics and HallucinationIndices, **When** the analysis script runs, **Then** it outputs a Spearman ρ and p‑value for the relationship between token count and HallucinationIndex, controlling for generated description length via the partial‑Spearman method (see FR‑019).
2. **Given** a dataset where function names use mixed naming styles, **When** the naming‑style metric is calculated, **Then** the system correctly categorizes each function and reports the correlation between naming style and HallucinationIndex.
3. **Given** the analysis is observational, **When** the report is generated, **Then** it explicitly frames findings as associational (e.g., “a positive correlation was observed”) rather than causal.

---

### User Story 3 - Robustness & Sensitivity Verification (Priority: P3)

**Journey**: As a researcher, I want the system to (a) perform a sensitivity analysis on the HallucinationIndex classification threshold, (b) validate the automated index against a manually verified subset, and (c) apply a family‑wise error correction to all hypothesis tests, so that the conclusions are robust to methodological choices and statistical artifacts.

**Why this priority**: Without sensitivity checks, manual validation, and multiplicity correction, the results could be driven by arbitrary cut‑offs or false positives, which would be rejected by the methodology panel.

**Independent Test**: Verify that the output includes (a) a table showing how the “high‑hallucination” rate varies for thresholds {0.01, 0.05, 0.1}, (b) a validation report comparing automated scores to manual median scores (including Cohen’s κ > 0.7), and (c) Bonferroni‑adjusted p‑values for all three correlation tests.

**Acceptance Scenarios**:

1. **Given** a calculated HallucinationIndex, **When** the sensitivity analysis runs, **Then** it reports the proportion of functions with index ≥ threshold for each threshold in {0.01, 0.05, 0.1}.
2. **Given** a manually verified subset of **≥ 5 % of the dataset (≥ 50 items)**, **When** the validation runs, **Then** it reports Pearson r between the automated **entity‑F1** component and the median manual **entity‑F1** score, and Krippendorff’s α for inter‑rater reliability (α > 0.7).
3. **Given** three hypothesis tests (length, naming, complexity), **When** the multiple‑comparison correction runs, **Then** it applies Bonferroni correction and reports the adjusted p‑values.
4. **Given** the dataset is observational, **When** the final report is generated, **Then** it includes a disclaimer that no causal claims are made.

### Edge Cases

- **Empty LLM output**: If the model returns an empty string or non‑text, the entity‑F1 score is set to **0.0** and the row is flagged with `empty_output=True` in the CSV.
- **Missing reference docstring**: Functions lacking a reference docstring are **skipped**, logged with `missing_docstring=True`, and excluded from all downstream statistical analyses.
- **Radon parsing failure**: When `radon` cannot parse a function, the cyclomatic‑complexity field is set to **NaN**, the row is flagged with `radon_parse_failure=True`, and the function is omitted from regression models.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the Python subset of CodeSearchNet, extracting source code, reference docstrings, and function names, and calculate cyclomatic complexity using the `radon` library (See US-1).
- **FR-002**: System MUST generate a **single‑sentence** description for each function using the `codegen-350M` model **and** the `bigcode/starcoderbase-1b` model quantized to 4‑bit via Hugging Face Transformers in CPU‑only mode. The system MUST enforce the one‑sentence constraint by (1) checking for sentence delimiters (`.`, `!`, `?`); if multiple are found, truncate to the first sentence; if none, truncate to **64 tokens**. This mechanism MUST be deterministic and verifiable (See US-1).
- **FR-003**: System MUST compute a **HallucinationIndex** defined as  

  \[
  \text{HallucinationIndex}=0.5\,(1-\text{entity‑overlap F1})\;+\;0.5\,(1-\text{semantic similarity})
  \]

  where both components are bounded in \([0,1]\); the resulting index is also in \([0,1]\) (See US-1). The two components will each be independently validated (see FR‑020).
- **FR-004**: System MUST perform **partial Spearman rank‑correlation** between the HallucinationIndex and each predictor (function token count, identifier‑entropy metric, cyclomatic complexity) while controlling for generated description length using the partial‑Spearman method defined in FR‑019 (See US-2).
- **FR-005**: System MUST apply a **Bonferroni** family‑wise error correction to the p‑values of all correlation tests and report the adjusted significance (See US-3).
- **FR-006**: System MUST conduct a sensitivity analysis sweeping the HallucinationIndex classification threshold (`index ≥ threshold`) over the set {0.01, 0.05, 0.1} and report the variation in the “high‑hallucination” rate (See US-3).
- **FR-007**: System MUST output a final JSON/CSV report containing (a) correlation coefficients and raw/adjusted p‑values, (b) regression coefficients with 95 % confidence intervals, (c) sensitivity‑analysis results, and (d) the phrase “correlation observed” to explicitly frame findings as associational (See US-2, US-3).
- **FR-008**: System MUST fit a multiple linear regression model (`HallucinationIndex ~ Length + Entropy + CyclomaticComplexity + DescriptionLength`) and report β‑coefficients with 95 % confidence intervals (See US-2).
- **FR-009**: System MUST randomly select a **stratified subset of at least 5 % of the dataset (≥ 50 items)** for manual verification. For this subset, three independent annotators must (a) label factual accuracy using the 0‑3 rubric **and** (b) assign an entity‑F1 score (0–1) for each function. The system MUST compute the median of the three normalized factual scores, compute the median manual entity‑F1, calculate Krippendorff’s α for the factual scores, and flag the subset if α < 0.7 or if score spread exceeds 1.0 (see US-3).
- **FR-010**: System MUST compare HallucinationIndices and correlation results generated by `codegen-350M` and `starcoderbase-1b` to assess model‑specific variance (See US-1, US-2).
- **FR-011**: System MUST compute Pearson’s r between the **automated entity‑F1 component** and the **median manual entity‑F1 score** collected in FR‑009. If r < 0.7, the system MUST flag the index calibration as “needs review” and report the 95 % confidence interval for the correlation (See US-3, FR‑020). *Rationale*: using a manual entity‑F1 rating isolates the overlap component from semantic‑similarity judgments, preserving statistical independence.
- **FR-012**: System MUST **reject** any mode of operation that generates placeholder, simulated, or hard‑coded scores. No `--simulate` flag or equivalent is permitted (See US-1).
- **FR-013**: System MUST orchestrate the manual verification workflow described in FR‑009, including generation of the adjudication report when a senior reviewer is invoked (See US-3).
- **FR-014**: System MUST assign an entity‑F1 score of **0.0** and flag `empty_output=True` for any function where the LLM returns an empty string or non‑text output (See Edge Cases).
- **FR-015**: System MUST skip any function lacking a reference docstring, log `missing_docstring=True`, and exclude the row from all downstream statistical analyses (See Edge Cases).
- **FR-016**: System MUST set cyclomatic complexity to **NaN** and flag `radon_parse_failure=True` when `radon` cannot parse a function; such rows are excluded from regression models (See Edge Cases).
- **FR-017**: System MUST designate a senior reviewer (e.g., a senior researcher) who, when invoked by FR‑009 step 5, resolves flagged reliability issues and produces a final adjudicated manual score.
- **FR-018**: System MUST record provenance metadata for every generated description, including a unique **generation_id**, **timestamp**, **model_name**, and **input_function_hash**. This metadata must be stored alongside each metric row and be verifiable in the final report (See US-1, SC-007).
- **FR-019**: System MUST compute partial Spearman correlations by (a) ranking all variables, (b) regressing the ranked HallucinationIndex on the ranked description length to obtain residuals, and (c) calculating Spearman ρ between each predictor’s ranked values and the residuals from step (b). This preserves the non‑parametric nature of Spearman while controlling for description length (See US-2).
- **FR-020**: System MUST validate the **semantic‑similarity** component of the HallucinationIndex by (a) sampling a stratified subset of ≥ 5 % of generated descriptions, (b) obtaining human judgments of semantic similarity on a 0‑1 Likert scale, and (c) computing Pearson’s r between the automated semantic‑similarity scores and the human ratings. A correlation ≥ 0.7 is required; otherwise, the component is flagged for review (See US-3).

### Key Entities

- **FunctionRecord**: Represents a single code unit; attributes include `source_code`, `reference_docstring`, `token_count`, `identifier_entropy`, `cyclomatic_complexity`, `generated_description_codegen350M`, `generated_description_starcoder1b`.
- **HallucinationMetrics**: Derived values for a `FunctionRecord`; attributes include `entity_f1`, `semantic_similarity`, and `hallucination_index`.
- **AnalysisResult**: Aggregated statistical output; attributes include `spearman_rho`, `p_value`, `adjusted_p_value`, `regression_coefficients`, `sensitivity_table`, `manual_validation_correlation`, `krippendorff_alpha`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The pipeline’s peak RAM usage **must not exceed 7 GB** while generating descriptions for **1 000** functions on a GitHub Actions free‑tier runner (See US-1). *Pass condition*: peak RAM ≤ 7 GB.
- **SC-002**: Total execution time **must complete within 4 hours** for processing the full sample of **1 000** functions on the same runner (See US-1). *Pass condition*: runtime ≤ 4 h.
- **SC-003**: The entity‑overlap metric’s validity is measured against manual verification of a random stratified sample of **≥ 5 % (≥ 50 items)**. Success requires Pearson r ≥ 0.7 **or** the system flags “needs review” (See US-3).
- **SC-004**: Sensitivity analysis must produce a table showing the “high‑hallucination” rate for thresholds {0.01, 0.05, 0.1}. Presence of this table constitutes pass (See US-3).
- **SC-005**: All hypothesis‑test p‑values must have Bonferroni‑adjusted counterparts reported. Presence of adjusted p‑values constitutes pass (See US-3).
- **SC-006**: Regression coefficients for the two models (`codegen-350M` and `starcoderbase-1b`) must have the **same sign** and an **absolute difference ≤ 0.15**. This tolerance is based on pilot analyses indicating that larger discrepancies reflect model‑specific behavior rather than systematic effects (See US-2, Assumptions).
- **SC-007**: Every metric row in the final dataset must include non‑empty provenance fields (`generation_id`, `timestamp`, `model_name`). Automated checks must verify that these fields are present and correctly formatted for **all** rows (See FR-018).

## Assumptions

- The `codegen-350M` model fits in CPU memory (≤ 7 GB) when loaded in 16‑bit precision with a batch size of 1.
- The `starcoderbaseb` model is quantized to 4‑bit to satisfy the same memory constraints.
- The CodeSearchNet Python subset contains enough functions with non‑empty docstrings to achieve a statistical power of **≥ 0.8** for detecting a small effect size (Spearman ρ > 0.1) with a sample of **1 000** functions (based on standard Spearman sample‑size formulas).
- The `radon` library successfully parses the vast majority of Python functions; any failures are random and do not bias the overall analysis.
- The entity‑extraction logic (using `spacy` with `en_core_web_sm`) correctly identifies parameters and return types in standard docstring formats (Google, NumPy, reStructuredText) and in the source‑code AST.
- The identifier‑entropy metric (Shannon entropy of identifier tokens) is a reasonable proxy for “descriptiveness” and aligns with the entropy‑based measure proposed in the original idea.
- The manually verified subset size of **≥ 5 %** provides a stable estimate of inter‑rater reliability for the prototype scope.
- The GitHub Actions free‑tier runner provides sufficient disk space for the dataset, model weights, and intermediate CSVs. without external storage.
- The study is observational; all reported relationships are framed as **associational** correlations, not causal effects.
- The acceptable absolute difference of **≤ 0.15** between regression coefficients across the two models is justified by pilot analyses that showed larger differences correspond to model‑specific idiosyncrasies rather than true underlying relationships.
