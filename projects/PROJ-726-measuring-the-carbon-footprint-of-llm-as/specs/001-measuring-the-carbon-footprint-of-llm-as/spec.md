# Feature Specification: Measuring the Carbon Footprint of LLM‑Assisted Code Generation

**Feature Branch**: `001-carbon-footprint-llm-code`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "Measuring the Carbon Footprint of LLM‑Assisted Code Generation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - LLM Inference & Energy Instrumentation (Priority: P1)

The system MUST execute a code generation task using a lightweight open-source model (GPT-2-medium) on a CPU-only environment and simultaneously record the energy consumption and carbon emissions using the CodeCarbon library.

**Why this priority**: This is the core data generation step for the experimental condition (LLM-assisted). Without this, no comparison can be made. It establishes the primary metric (CO₂-eq) for the "LLM" arm of the study.

**Acceptance Scenarios**:

1. **Given** a valid prompt from the CodeXGLUE dataset, **When** the system runs GPT-2-medium inference with CodeCarbon wrapping, **Then** the system outputs a JSON record containing `prompt_id`, `co2_emitted_kg`, and `energy_kWh`.
2. **Given** the GitHub Actions CPU runner environment (no GPU), **When** the inference job starts, **Then** the CodeCarbon tracker must report the device as "cpu" and not throw an error regarding CUDA/GPU availability.
3. **Given** a 200-prompt batch, **When** the loop completes, **Then** the output file contains valid JSON records with non-zero `energy_kWh` and `co2_emitted_kg` for each successful prompt, and excludes any prompts that failed to generate code.
4. **Given** the full pipeline script, **When** executed on the GitHub Actions free-tier runner, **Then** the system completes the full cycle (download, inference, normalization, stats) without crashing and produces the final markdown report.

---

### User Story 2 - Human Baseline Estimation & Normalization (Priority: P2)

The system MUST calculate the estimated carbon footprint for human-written code by converting reported developer time (from the 2025 comparative analysis paper) into energy usage using a standard CPU power model, then normalize both LLM and human emissions per Line of Code (LOC).

**Why this priority**: This establishes the control condition (human-assisted). It allows the study to answer the research question by providing the denominator for the comparison.

**Acceptance Scenarios**:

1. **Given** the average human development time per prompt (from the 2025 comparative analysis paper) where a range is reported, **When** the calculation runs, **Then** the system uses the mean of the reported range to calculate `estimated_human_co2_kg` for each prompt.
2. **Given** the LLM-generated code and human baseline data, **When** the normalization step executes, **Then** the system produces a table with `prompt_id`, `loc_count`, `llm_co2_per_loc`, and `human_co2_per_loc`, excluding any record where the `loc_count` is 0 for either the LLM or the human baseline.
3. **Given** a prompt where the LLM generates 0 lines of code or the human baseline is 0, **When** the normalization runs, **Then** the system excludes that specific record from the paired analysis rather than attempting division by zero or including incomplete pairs.

---

### User Story 3 - Statistical Comparison & Robustness Check (Priority: P3)

The system MUST perform a paired statistical test (t-test or Wilcoxon) to determine if the difference in emissions per LOC is significant, and repeat the analysis with a second model (a distilled variant) to verify robustness.

**Why this priority**: This fulfills the "Expected results" requirement of the research question, providing the scientific conclusion (significant difference vs. null) and ensuring the finding is not an artifact of a single model architecture.

**Acceptance Scenarios**:

1. **Given** the paired `llm_co2_per_loc` and `human_co2_per_loc` values for the valid subset of prompts, **When** the statistical test runs, **Then** the output includes the test statistic, p-value, and the appropriate effect size (Cohen's d if t-test is selected; rank-biserial correlation if Wilcoxon is selected).
2. **Given** the results from GPT-2-medium, **When** the robustness check runs with DistilGPT-2, **Then** the system reports whether the direction of the effect (lower/higher emissions) remains consistent.
3. **Given** a p-value < 0.05, **When** the report is generated, **Then** the system explicitly labels the result as "statistically significant" in the summary markdown.

---

### Edge Cases

- **What happens when** the CodeXGLUE dataset sample contains prompts that result in empty code generation (0 LOC) from the LLM? (Handled by exclusion or flagging in normalization).
- **How does the system handle** a CodeCarbon measurement failure (e.g., library crash) for a specific prompt? (The pipeline must log the error, skip the specific prompt, and proceed to the next to ensure the target sample size is met).
- **What happens when** the human baseline paper reports a time range rather than a single point estimate? (The system defaults to the mean value as per the methodology sketch).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and sample up to 200 prompts from the CodeXGLUE Python code-generation dataset, ensuring the sample size is as close to 200 as possible given dataset availability. (See US-1)
- **FR-002**: System MUST wrap the GPT-2-medium inference loop with the CodeCarbon library to record `energy_kWh` and `co2_emitted_kg` for each prompt. (See US-1)
- **FR-003**: System MUST convert human development time to CO₂-eq using a representative power draw and the same regional conversion factor as the LLM measurement, using data from the 2025 comparative analysis paper. (See US-2)
- **FR-004**: System MUST calculate emissions per Line of Code (LOC) for both LLM-generated and human-written solutions, explicitly excluding any prompt where the LOC count is 0 for either the LLM or the human baseline to maintain paired integrity. (See US-2)
- **FR-005**: System MUST perform a paired-samples t-test (or Wilcoxon signed-rank test if normality fails) to compare emissions per LOC between LLM and human baselines. (See US-3)
- **FR-006**: System MUST repeat the entire analysis pipeline using the DistilGPT-2 model to verify that results are not specific to the GPT-2-medium architecture. (See US-3)
- **FR-007**: System MUST output a markdown report containing summary statistics, effect size, confidence intervals, boxplots of emissions per LOC, and a dedicated "Limitations" section. (See US-3)
- **FR-008**: System MUST validate that the source data from the 2025 comparative analysis paper represents raw developer time (minutes/hours) and not pre-calculated CO₂ values. (See US-2)
- **FR-009**: System MUST perform a sensitivity analysis on the human power model by recalculating human emissions using representative low, medium, and high power draws to assess the stability of the comparison. (See US-2)

### Key Entities

- **Prompt**: A text input from the CodeXGLUE dataset requiring code generation.
- **Generation**: The code output produced by the LLM for a specific prompt.
- **EmissionRecord**: A data entity containing `prompt_id`, `model_used`, `energy_kWh`, `co2_kg`, `loc_count`, and `co2_per_loc`.
- **HumanBaseline**: A static dataset mapping `prompt_id` to `estimated_human_minutes`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The difference in mean emissions per LOC between LLM-assisted and human-written code is measured against the null hypothesis of zero difference using a paired t-test (p < 0.05 threshold). (See FR-005)
- **SC-002**: The robustness of the primary finding is measured by comparing the direction of the effect (higher/lower) between GPT-2-medium and DistilGPT-2 runs. (See FR-006)
- **SC-003**: The computational feasibility of the study is measured by ensuring total runtime ≤ 6 hours and peak RAM usage ≤ 7 GB on the GitHub Actions free-tier runner. (See FR-001)
- **SC-004**: The validity of the human baseline is measured by the successful conversion of the target paper's time data into CO₂-eq using the power model. (See FR-003)
- **SC-005**: The methodological rigor is measured by the inclusion of a log output containing the Shapiro-Wilk p-value (or equivalent normality test result) and the specific statistical test selected (t-test or Wilcoxon). (See FR-005)

## Assumptions

- The CodeXGLUE dataset is publicly accessible via HuggingFace Datasets and contains at least 200 valid prompts for the specific Python code-generation subset.
- The forthcoming comparative analysis paper provides reliable average developer time estimates (raw time, not pre-calculated CO₂) for the specific tasks in the CodeXGLUE subset.
- A typical laptop CPU power draw serves as a valid proxy for the energy consumption of a developer writing code, acknowledging that this is a theoretical construct.
- The CodeCarbon library functions correctly on GitHub Actions CPU runners without requiring GPU-specific dependencies.
- The GPT-2-medium and DistilGPT-2 models can generate valid code for the sampled prompts without excessive hallucination or repetition that would invalidate the LOC count.
- The regional CO₂ conversion factor used by CodeCarbon (dynamic/grid-average) is the best available proxy for the inference moment, though it may differ from the static factor used in the human baseline study; this mismatch is acknowledged as a limitation in the final report.
- The "human baseline" calculation assumes a linear relationship between time and energy, ignoring idle time or multi-tasking, which is a necessary simplification for this study design.