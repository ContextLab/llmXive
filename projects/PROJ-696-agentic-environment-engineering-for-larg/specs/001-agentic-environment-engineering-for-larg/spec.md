# Feature Specification: Agentic Environment Engineering for Large Language Models

**Feature Branch**: `[001-agentic-environment-engineering]`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "How does the richness of a simulated environment—characterized by modality diversity, interactivity level, and task complexity—affect the emergent agentic performance of large language models on standardized tool‑use and planning benchmarks?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Environment Metadata Acquisition (Priority: P1)

As a researcher, I want to download publicly available environment collections (WebShop, MiniWoB, ToolBench) and extract their metadata into a unified format, so that I can establish the baseline data required for richness metric computation.

**Why this priority**: This is the foundational step; without environment metadata, no richness scores can be computed, and the entire analysis pipeline cannot proceed.

**Independent Test**: Can be fully tested by executing the data download script and verifying that CSV files exist with the required columns (modality, interactive objects, task horizon) for all three environments.

**Acceptance Scenarios**:

1. **Given** a clean working directory, **When** the data download script runs, **Then** three environment metadata CSV files exist with ≥100 rows each containing the required columns
2. **Given** partial network interruption, **When** the script retries up to 3 times, **Then** the script either completes successfully or fails with an explicit error message identifying the failed environment

---

### User Story 2 - Richness Metric Computation (Priority: P2)

As a researcher, I want to compute three normalized richness scores (Modality Diversity, Interactivity Level, Task Complexity) and a composite Richness Index for each environment, so that I can quantify the independent variables for the correlation analysis.

**Why this priority**: This delivers the core predictor variable; without richness scores, the relationship between environment properties and agentic performance cannot be measured.

**Independent Test**: Can be fully tested by running the metric computation script on pre-existing metadata CSVs and verifying that output contains normalized scores in [0,1] range and a composite index.

**Acceptance Scenarios**:

1. **Given** environment metadata CSVs exist, **When** the metric computation script runs, **Then** output CSV contains columns for each of the 3 richness dimensions and the composite Richness Index
2. **Given** an environment with only text modality, **When** the script computes Modality Diversity, **Then** the score equals 0.0 (minimum possible value)

---

### User Story 3 - Statistical Analysis Pipeline (Priority: P3)

As a researcher, I want to run correlation tests (Pearson/Spearman) and linear regression between the Richness Index and agentic performance metrics (success rate, task completion time), with Holm-Šídák correction for multiple comparisons, so that I can quantify the relationship and determine statistical significance.

**Why this priority**: This delivers the final research output; without statistical analysis, the collected data remains descriptive rather than evidential.

**Independent Test**: Can be fully tested by running the analysis script on pre-existing performance CSVs and verifying that output includes correlation coefficients, p-values, regression β coefficients, R², and 95% confidence intervals.

**Acceptance Scenarios**:

1. **Given** performance metrics CSV exists with ≥10 data points, **When** the analysis script runs, **Then** output includes Pearson correlation coefficient, Spearman correlation coefficient, and corresponding p-values
2. **Given** 3 richness dimensions tested, **When** the script applies Holm-Šídák correction, **Then** adjusted p-values are reported alongside raw p-values

---

### Edge Cases

- What happens when an environment dataset contains missing values for a required metadata field (e.g., branching factor not recorded)?
- How does the system handle an environment with zero interactive objects (division by zero in interactivity calculation)?
- What if the performance evaluation yields success rate = 0.0 for all test episodes (correlation undefined)?
- How does the script respond if the CI runner exceeds the 6-hour time budget during model evaluation?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse metadata from WebShop, MiniWoB, and ToolBench repositories, storing results in a unified CSV format with columns for modality count, action space size, and task horizon (See US-1)
- **FR-002**: System MUST compute three normalized richness scores (Modality Diversity, Interactivity Level, Task Complexity) in the range [0,1], and combine them into a composite Richness Index using a weighted sum with weights summing to 1.0 (See US-2)
- **FR-003**: System MUST fine-tune a base LLaMA-2-7B model on each environment's training split using LoRA scripts, with fixed random seeds for reproducibility (See US-2) `[NEEDS CLARIFICATION: Does the LLaMA-2-7B fine-tuning fit within 6-hour CPU-only CI budget, or should a smaller model be substituted?]`
- **FR-004**: System MUST evaluate fine-tuned models on held-out test splits, recording success rate (≥0.0, ≤1.0) and average step count (positive integer) for ≥100 test episodes per environment (See US-3)
- **FR-005**: System MUST perform Pearson correlation, Spearman correlation, and linear regression analysis with Richness Index as predictor, applying Holm-Šídák correction for the 3 richness dimensions tested, reporting β coefficient, R², and 95% confidence intervals (See US-3)

### Key Entities

- **EnvironmentMetadata**: Represents each benchmark environment; key attributes include modality_types (categorical), action_space_size (integer), task_horizon (integer), branching_factor (float)
- **RichnessScore**: Represents computed richness metrics; key attributes include modality_diversity (float [0,1]), interactivity_level (float [0,1]), task_complexity (float [0,1]), richness_index (float [0,1])
- **PerformanceMetrics**: Represents agent evaluation results; key attributes include success_rate (float [0,1]), average_step_count (integer), environment_id (string)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Pearson and Spearman correlation coefficients between Richness Index and performance metrics are measured against statistical significance threshold of α=0.05 with Holm-Šídák correction (See US-3)
- **SC-002**: Linear regression β coefficient and R² are measured against 95% confidence intervals to determine effect direction and explanatory power (See US-3)
- **SC-003**: Model evaluation success rate and step count are measured against baseline (pre-training) performance to verify fine-tuning impact (See US-2)
- **SC-004**: Total analysis runtime is measured against the 6-hour GitHub Actions free-tier time budget, with logging of each pipeline stage duration (See US-3)

## Assumptions

- **Assumption about compute feasibility**: LLaMA-2-7B fine-tuning with LoRA on 7B parameters must complete within 6-hour CPU-only CI budget; if not, a smaller base model (e.g., LLaMA-2-7B with 4-bit quantization or LLaMA-2-1B) will be substituted, recorded as a scoping decision
- **Assumption about dataset-variable fit**: WebShop, MiniWoB, and ToolBench metadata contain all required variables (modality types, action space size, task horizon, branching factor); if any environment lacks a required field, a [NEEDS CLARIFICATION] marker will be inserted and the field will be estimated or excluded
- **Assumption about inference framing**: All analyses are observational (no random assignment of environments to agents); findings will be framed as associational correlations, not causal claims about environment richness causing performance changes
- **Assumption about multiplicity correction**: Three richness dimensions are tested simultaneously; Holm-Šídák correction will be applied to control family-wise error rate at α=0.05
- **Assumption about threshold justification**: No decision cutoffs are introduced in the core analysis; the richness index uses equal weights (1/3 each) as a community-standard default; sensitivity analysis sweeping weights ∈ {0.25, 0.33, 0.5} will be recorded if the correlation is borderline (|r| ∈ [0.3, 0.5])
- **Assumption about measurement validity**: Environment metadata is derived from public repository documentation and code, not self-reported; performance metrics use standard success-rate definitions from each benchmark's original evaluation scripts
- **Assumption about predictor collinearity**: The three richness dimensions may be correlated (e.g., higher interactivity may correlate with higher task complexity); variance inflation factor (VIF) diagnostics will be computed and reported, and if VIF > 5, the regression will be re-framed as descriptive rather than claiming independent effects
