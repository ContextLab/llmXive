# Feature Specification: Energy Profiling of Quantized LLM Inference on Edge CPUs

**Feature Branch**: `001-energy-profiling-of-quantized-llm-infere`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "How does the quantization level of a language model (FP16, INT8, 4‑bit) influence the energy‑per‑token consumed during inference on an edge‑class CPU, after controlling for model size?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CPU-Feasible Quantized Inference Benchmarking (Priority: P1) (See US-1)

The researcher needs to execute inference for multiple model sizes (a small‑scale model, 350M, 1.3B) across three quantization levels (higher‑precision floating‑point, INT8, 4‑bit) on a CPU‑only environment (Raspberry Pi 4) to generate raw energy consumption data without requiring GPU hardware. The system MUST also attempt to load LLaMA models (all quantizations) but MUST gracefully skip and log the event if it exceeds memory limits, as it is out of scope for primary energy analysis.

**Why this priority**: This is the foundational data collection step. Without successful CPU-based inference and energy measurement, no statistical analysis or scaling laws can be derived. It addresses the primary constraint of the project (edge‑CPU hardware) and the core research question.

**Independent Test**: Can be fully tested by running a script that loads a 125M model in 4-bit quantization on a Raspberry Pi 4, processes a fixed WikiText-2 sample, and outputs a non‑zero energy value in Joules within 10 minutes, proving the CPU‑only pipeline works.

**Acceptance Scenarios**:
1. **Given** a Raspberry Pi runner with several CPU cores and multiple gigabytes of RAM, **When** the inference script loads a medium‑sized GPT‑Neo model quantized to 4-bit, **Then** the script completes inference on a moderately sized prompt without OOM errors or CUDA dependency errors.
2. **Given** the same environment, **When** the script attempts to load a multi‑billion‑parameter model in FP16 or 4‑bit, **Then** the script fails gracefully with a memory error message or is skipped, confirming the dataset/model size boundary for the hardware constraints and that the event is logged.
3. **Given** the same environment, **When** the script loads a multi‑hundred‑million‑parameter model in 4-bit, **Then** the script completes inference without OOM errors, providing the necessary third data point for scaling analysis.

---

### User Story 2 - Energy Measurement and Data Aggregation (Priority: P2) (See US-2)

The researcher needs to capture precise energy consumption (Joules) and latency (ms) for each inference run, repeating the process multiple times per configuration to calculate mean and standard deviation, ensuring the data is statistically robust.

**Why this priority**: The research question specifically asks for the influence of quantization on "energy‑per‑token." Raw inference logs are insufficient; the system must isolate the energy cost of the model execution from system noise via repetition and aggregation.

**Independent Test**: Can be fully tested by running the measurement pipeline on a single model‑quantization pair and verifying that the output CSV contains a sufficient number of rows with valid energy values, a calculated mean, and a standard deviation > 0.

**Acceptance Scenarios**:
1. **Given** a valid model configuration (e.g., 1.3B INT8), **When** the benchmark script executes multiple independent runs with different random seeds, **Then** the aggregated results file contains a row with `mean_energy` and `std_energy` calculated from exactly 12 samples.
2. **Given** the aggregated data, **When** the researcher requests a summary report, **Then** the report displays energy‑per‑token values for all valid configurations, excluding any configurations that failed to run due to memory constraints or energy measurement unavailability.

---

### User Story 3 - Statistical Scaling Analysis and Visualization (Priority: P3) (See US-3)

The researcher needs to perform a log‑log regression analysis (OLS) on energy‑per‑token vs. model size to determine if the energy exponent is sublinear, and perform pairwise t‑tests (with Bonferroni correction) for quantization level comparisons, visualizing the results in a plot.

**Why this priority**: This addresses the "geoffrey‑west‑simulated" reviewer suggestion to embed the claim in a scaling framework. It transforms raw data into the scientific conclusion required by the research question.

**Independent Test**: Can be fully tested by running the analysis script on the aggregated CSV and verifying it outputs a JSON summary containing a fitted log‑log exponent (including quantization as a covariate) and p‑values for pairwise comparisons, along with a generated PNG plot file.

**Acceptance Scenarios**:
1. **Given** the aggregated energy data for a small‑scale (≈10^8‑parameter) model, 350M, and 1.3B models across 3 quantization levels, **When** the statistical analysis script runs, **Then** it outputs a Bonferroni‑corrected p‑value < 0.05 if the null hypothesis (no difference in energy between quantization levels) is rejected, or a specific "non‑significant" flag otherwise.
2. **Given** the same data, **When** the scaling analysis runs, **Then** it calculates a log‑log slope (exponent) for energy vs. parameter count (controlling for quantization) and reports whether this exponent is < 1.0 (sublinear) or ≥ 1.0 (linear/superlinear).

### Edge Cases

- What happens when the `pyRAPL` library fails to detect the CPU power counter on the Raspberry Pi 4?
- How does the system handle a model configuration where the quantization process (e.g., 4-bit) results in a crash due to unsupported operators on the CPU backend?
- What is the behavior if the WikiText‑2 dataset download fails or the tokenization step produces 0 tokens for a specific model's context window?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load and execute inference for GPT‑Neo 125M, GPT‑Neo 350M, and GPT‑Neo 1.3B models in FP16, INT8, and 4‑bit quantization formats on a CPU‑only backend (Raspberry Pi 4). The system MUST attempt to load LLaMA 7B (all quantizations) but MUST gracefully skip and log the event if it exceeds memory limits, as LLaMA 7B is out of scope for primary energy analysis (See US-1).
- **FR-002**: System MUST measure energy consumption in Joules per token using `pyRAPL` (or a compatible CPU energy counter) on the **physical Raspberry Pi 4 hardware** for every inference step, excluding system idle time. Measurements performed on virtualised CI environments or emulated hardware are not considered valid. Idle time is defined as the baseline power measured during a 10‑second no‑op loop executed immediately before each inference run. If `pyRAPL` fails, the system MUST attempt to measure power via an external calibrated wattmeter interface; if no external interface is available, the system MUST log "Energy measurement unavailable" and skip energy aggregation for that run (See US-2).
- **FR-003**: System MUST execute at least 12 independent inference runs per model‑quantization configuration, each with a different random seed, to capture variance (See US-2).
- **FR-004**: System MUST aggregate results by calculating the mean and standard deviation of energy‑per‑token, latency, and perplexity for each configuration **when energy measurements are available**; if energy data are unavailable, the system MUST log the omission and still produce aggregated latency and perplexity metrics (See US-2).
- **FR-005**: System MUST perform a log‑log regression analysis using Ordinary Least Squares (OLS) with Energy‑per‑Token as the dependent variable, Parameter Count as a continuous predictor, and Quantization Level as a categorical predictor (including interaction terms) to isolate size‑scaling effects. The system MUST also perform pairwise t‑tests with Bonferroni correction to compare energy‑per‑token across quantization levels (See US-3).
- **FR-006**: System MUST generate a visualization plot showing energy‑per‑token vs. quantization level and a log‑log plot of energy vs. parameter count (See US-3).
- **FR-007**: System MUST measure dequantization overhead by comparing the energy of a quantized inference run against a baseline FP16 run (scaled by parameter count) and flag if the overhead exceeds 10 % of the total energy (See US-2).

### Key Entities

- **Configuration**: Represents a unique combination of Model Size (e.g., 125M) and Quantization Level (e.g., 4‑bit).
- **InferenceRun**: Represents a single execution of a Configuration, storing raw energy, latency, and token count.
- **AggregatedMetric**: Represents the statistical summary (mean, std) of InferenceRuns for a specific Configuration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Energy‑per‑token reduction is measured against the FP16 baseline to determine if INT8 and 4‑bit quantization yield lower values (See US-2, US-3).
- **SC-002**: Statistical significance of quantization effects is measured against the standard alpha threshold of 0.05 (Bonferroni‑corrected) via pairwise t‑tests (See US-3).
- **SC-003**: Scaling exponent (log‑log slope of energy vs. parameters, controlling for quantization) is measured against the theoretical sublinear threshold of 1.0. If ≥3 data points are available, the exponent is tested for statistical significance; if only 2 points are available, the deterministic slope is reported without statistical significance testing (See US-3).
- **SC-004**: Variance stability is measured by ensuring the standard deviation of energy measurements across the 12 repetitions remains within 15 % of the mean for *each* configuration individually (See US-2).
- **SC-005**: CPU‑only inference succeeds for all supported configurations; for unsupported configurations the system logs a graceful‑skip OOM event and continues without failure (See US-1).
- **SC-006**: Twelve independent runs per configuration provide ≥90 % statistical power to detect a medium effect size (Cohen's d ≈ 0.5) at α = 0.05, as confirmed by a pre‑study power analysis (See US-2).
- **SC-007**: CPU‑only inference succeeds for all supported configurations (FP16, INT8, 4‑bit for 125M, 350M, 1.3B models) without GPU dependency, and any OOM or memory‑limit event is logged as a graceful‑skip with a clear message (See US-1).

## Assumptions

- The primary measurement platform is a Raspberry Pi 4 (edge‑CPU) running a Linux distribution with `pyRAPL` support; this hardware provides representative energy readings for edge deployments.
- The GitHub Actions free‑tier runner (x86) is used only for functional sanity checks (e.g., code linting, quick dry‑run) and not for final energy measurement.
- The `pyRAPL` library or an equivalent CPU energy counter (e.g., `powerstat`) is available and functional on the Raspberry Pi 4; if not, a calibrated external wattmeter will be used as a fallback.
- The WikiText‑2 dataset is accessible via HuggingFace Datasets and provides a consistent, representative sample of text for inference benchmarking.
- The quantization process using `bitsandbytes` or `GPTQ` may introduce significant overhead (dequantization) that must be measured and controlled, rather than assumed to be negligible.
- The relationship between quantization level and energy is expected to be monotonic; any deviation will be investigated as an anomaly rather than a systemic failure.
- Edge‑CPU performance on the Raspberry Pi 4 is taken as the target; variations on other ARM boards are considered out of scope for this study.