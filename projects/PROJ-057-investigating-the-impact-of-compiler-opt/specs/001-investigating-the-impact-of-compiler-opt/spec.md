# Specification: Investigating the Impact of Compiler Optimizations on LLM Inference Latency

## 1. Introduction

This project investigates the impact of compiler optimization flags on the latency and numerical stability of LLM inference kernels (MatMul, Softmax, LayerNorm). The goal is to identify Pareto-optimal configurations that balance speed and accuracy.

## 2. User Stories

### US1: Compile and Execute Kernel Benchmarks
As a researcher, I want to compile C++ kernels with varying optimization flags and execute them to measure latency, so that I can establish a baseline performance profile.

### US2: Quantify Numerical Stability Drift
As a researcher, I want to compare optimized kernel outputs against a high-precision reference to calculate relative error, so that I can ensure the optimizations do not compromise numerical validity.

### US3: Statistical Significance and Pareto Frontier Analysis
As a researcher, I want to perform statistical tests on block-averaged latency distributions and generate Pareto frontier plots, so that I can make data-driven decisions on which compiler flags to use.

## 3. Functional Requirements

### FR-001: Kernel Compilation
The system must support compilation of C++ kernels using GCC and Clang with user-specified flag combinations.

### FR-002: Execution and Latency Measurement
The system must execute compiled binaries and measure latency using high-resolution timers, handling memory pressure by downscaling tensor dimensions if necessary.

### FR-003: Reference Generation
The system must generate high-precision reference tensors using Python's `decimal` module with 512-bit precision to serve as the ground truth for stability checks.

### FR-004: Statistical Analysis
The system must perform **Welch's Independent Samples t-test** to compare latency distributions between independent optimization configurations.
**Rationale**: Since each configuration produces a distinct binary with independent execution times, the samples are not paired. Welch's t-test is statistically valid for independent groups with potentially unequal variances, unlike the paired t-test which assumes a dependency between samples.

### FR-005: Pareto Frontier Visualization
The system must generate Pareto frontier plots including both stable and unstable configurations, clearly marking downsampled runs and excluding unstable runs from the final "optimal" frontier.

## 4. Non-Functional Requirements

### NFR-001: Reproducibility
All experiments must be reproducible with fixed seeds and deterministic tensor generation.

### NFR-002: Performance
The analysis pipeline must complete within a 6-hour runtime budget for the full set of configurations.

### NFR-003: Numerical Stability
The system must detect and log NaN values, excluding unstable configurations from statistical analysis.

## 5. Data Model

- **Configuration**: Unique ID, Compiler, Flags, Tensor Dimensions
- **Run**: Configuration ID, Latency (ms), Output Hash, Status (Stable/Unstable)
- **Stability Metric**: Configuration ID, Kernel Type, L2 Error, Max Diff, Status

## 6. Edge Cases

- **Memory Pressure**: If allocation fails, the system must log the event, downscale the tensor, and retry.
- **NaN Detection**: If a kernel produces NaN, the configuration is marked unstable and excluded from final analysis.
- **Compiler Availability**: The system must fail loudly if required compilers (GCC >= 11, Clang >= 14) are not found.

## 7. Validation

- Verify that `data/raw/combinations.json` is generated correctly.
- Verify that `data/results/stability_metrics.csv` contains correct status flags.
- Verify that `data/results/pareto_frontier_final.png` excludes unstable configurations.
- Verify that statistical analysis uses Welch's t-test as defined in FR-004.