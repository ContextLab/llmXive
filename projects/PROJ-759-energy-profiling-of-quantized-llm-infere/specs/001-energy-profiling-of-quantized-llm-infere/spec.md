# Feature Specification: Energy Profiling of Quantized LLM Inference on Edge CPUs

**Feature Branch**: `001-energy-profiling-of-quantized-llm-inference-on-edge-cpus`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "How does the quantization level of a language model (FP16, INT8, 4‑bit) influence the energy‑per‑token consumed during inference on an edge‑class CPU, after controlling for model size?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CPU-Feasible Quantized Inference Benchmarking (Priority: P1)

The researcher needs to execute inference for multiple model sizes (125M, 1.3B) across three quantization levels (FP16, INT8, 4-bit) on a CPU-only environment (GitHub Actions free tier) to generate raw energy consumption data without requiring GPU hardware.

**Why this priority**: This is the foundational data collection step. Without successful CPU-based inference and energy measurement, no statistical analysis or scaling laws can be derived. It addresses the primary constraint of the project (free CPU CI) and the core research question.

**Independent Test**: Can be fully tested by running a script that loads a 125M model in 4-bit quantization, processes a fixed WikiText-2 sample, and outputs a non-zero energy value in Joules within 10 minutes, proving the CPU-only pipeline works.

**Acceptance Scenarios**:
1. **Given** a GitHub Actions runner with 2 CPU cores and 7GB RAM, **When** the inference script loads a 125M GPT-Neo model quantized to 4-bit, **Then** the script completes inference on a 500-token prompt without OOM errors or CUDA dependency errors.
2. **Given** the same environment, **When** the script attempts to load a 7B model in FP16, **Then** the script fails gracefully with a memory error message or is skipped, confirming the dataset/model size boundary for the hardware constraints.

---

### User Story 2 - Energy Measurement and Data Aggregation (Priority: P2)

The researcher needs to capture precise energy consumption (Joules) and latency (ms) for each inference run, repeating the process 3 times per configuration to calculate mean and standard deviation, ensuring the data is statistically robust.

**Why this priority**: The research question specifically asks for the influence of quantization on "energy-per-token." Raw inference logs are insufficient; the system must isolate the energy cost of the model execution from system noise via repetition and aggregation.

**Independent Test**: Can be fully tested by running the measurement pipeline on a single model-quantization pair and verifying that the output CSV contains exactly 3 rows with valid energy values, a calculated mean, and a standard deviation > 0.

**Acceptance Scenarios**:
1. **Given** a valid model configuration (e.g., 1.3B INT8), **When** the benchmark script executes 3 independent runs with different random seeds, **Then** the aggregated results file contains a row with `mean_energy` and `std_energy` calculated from exactly 3 samples.
2. **Given** the aggregated data, **When** the researcher requests a summary report, **Then** the report displays energy-per-token values for all valid configurations, excluding any configurations that failed to run due to memory constraints.

---

### User Story 3 - Statistical Scaling Analysis and Visualization (Priority: P3)

The researcher needs to perform a one-way ANOVA on energy-per-token across quantization levels and fit a log-log scaling relationship (energy vs. model size) to determine if the energy exponent is sublinear, visualizing the results in a plot.

**Why this priority**: This addresses the "geoffrey-west-simulated" reviewer suggestion to embed the claim in a scaling framework. It transforms raw data into the scientific conclusion required by the research question.

**Independent Test**: Can be fully tested by running the analysis script on the aggregated CSV and verifying it outputs a JSON summary containing an ANOVA p-value and a fitted log-log exponent, along with a generated PNG plot file.

**Acceptance Scenarios**:
1. **Given** the aggregated energy data for 125M and 1.3B models across 3 quantization levels, **When** the statistical analysis script runs, **Then** it outputs a p-value < 0.05 if the null hypothesis (no difference in energy) is rejected, or a specific "non-significant" flag otherwise.
2. **Given** the same data, **When** the scaling analysis runs, **Then** it calculates a log-log slope (exponent) for energy vs. parameter count and reports whether this exponent is < 1.0 (sublinear) or ≥ 1.0 (linear/superlinear).

### Edge Cases

- What happens when the `pyRAPL` library fails to detect the CPU power counter on the specific GitHub Actions runner architecture (x86 vs. ARM)?
- How does the system handle a model configuration where the quantization process (e.g., 4-bit) results in a crash due to unsupported operators on the CPU backend?
- What is the behavior if the WikiText-2 dataset download fails or the tokenization step produces 0 tokens for a specific model's context window?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load and execute inference for GPT-Neo 125M, GPT-Neo 1.3B, and LLaMA 7B models in FP16, INT8, and 4-bit quantization formats on a CPU-only backend (See US-1).
- **FR-002**: System MUST measure energy consumption in Joules per token using `pyRAPL` (or a compatible CPU energy counter) for every inference step, excluding system idle time (See US-2).
- **FR-003**: System MUST execute exactly 3 independent inference runs per model-quantization configuration with different random seeds to capture variance (See US-2).
- **FR-004**: System MUST aggregate results by calculating the mean and standard deviation of energy-per-token, latency, and perplexity for each configuration (See US-2).
- **FR-005**: System MUST perform a one-way ANOVA test on energy-per-token across quantization levels and a log-log regression analysis for energy vs. model size (See US-3).
- **FR-006**: System MUST generate a visualization plot showing energy-per-token vs. quantization level and a log-log plot of energy vs. parameter count (See US-3).

### Key Entities

- **Configuration**: Represents a unique combination of Model Size (e.g., 125M) and Quantization Level (e.g., 4-bit).
- **InferenceRun**: Represents a single execution of a Configuration, storing raw energy, latency, and token count.
- **AggregatedMetric**: Represents the statistical summary (mean, std) of InferenceRuns for a specific Configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Energy-per-token reduction is measured against the FP16 baseline to determine if INT8 and 4-bit quantization yield lower values (See US-2, US-3).
- **SC-002**: Statistical significance of quantization effects is measured against the standard alpha threshold of 0.05 via one-way ANOVA (See US-3).
- **SC-003**: Scaling exponent (log-log slope of energy vs. parameters) is measured against the theoretical sublinear threshold of 1.0 to validate the scaling hypothesis (See US-3).
- **SC-004**: Variance stability is measured by ensuring the standard deviation of energy measurements across the 3 repetitions remains within 15% of the mean (See US-2).

## Assumptions

- The GitHub Actions free-tier runner (2 CPU, 7GB RAM) is sufficient to run the 125M and 1.3B models in 4-bit quantization, but the 7B model in FP16 will likely exceed memory limits and is excluded from the primary energy analysis (scoping decision based on hardware constraints).
- The `pyRAPL` library or an equivalent CPU energy counter (e.g., `powerstat`) is available and functional on the GitHub Actions runner environment; if not, a fallback simulation or proxy metric based on CPU cycles is used.
- The WikiText-2 dataset is accessible via HuggingFace Datasets and provides a consistent, representative sample of text for inference benchmarking.
- The quantization process using `bitsandbytes` or `GPTQ` does not introduce significant overhead that would invalidate the energy measurement (i.e., quantization overhead is negligible compared to inference energy).
- The relationship between quantization level and energy is monotonic, and any deviation from this trend will be investigated as an anomaly rather than a systemic failure.
- The "edge CPU" environment in the experiment is approximated by the GitHub Actions x86 runner, acknowledging that specific ARM-based Raspberry Pi performance may differ slightly but the relative trends (quantization impact) will remain consistent.
