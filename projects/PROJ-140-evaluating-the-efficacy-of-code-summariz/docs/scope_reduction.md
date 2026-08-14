# Scope Reduction Documentation: Human Subject Study vs. Deterministic Simulation

## Executive Summary

This document explicitly clarifies the scope adaptation implemented for the **llmXive** project (PROJ-140) regarding the execution of the human subject study. While the original research specification (spec.md) assumes a "Human Subject Study" with real participants, the **Continuous Integration (CI) pipeline** utilizes a **Deterministic Simulation** as a substitute for testing purposes only.

**Crucially, this is NOT a permanent scope reduction.** The "Real Study" path remains fully supported, required, and is the designated method for generating the final research output and reproducibility package.

## 1. The Change: CI Simulation vs. Real Study

### 1.1. CI Pipeline (Deterministic Simulation)
To satisfy the constraints of automated CI environments (specifically FR-007: Resource constraints of ≤7GB RAM, ≤6h runtime, and no GPU availability), the pipeline executes a **deterministic simulation** of participant behavior.

- **Implementation**: Tasks `T015-base`, `T015-llm`, and `T015-rule` simulate participant interactions using statistical distributions (Normal distributions for time-to-decision) and pre-computed or rule-based summary artifacts.
- **Purpose**: To validate the data collection pipeline, statistical analysis scripts (McNemar's tests, LME models), and reproducibility package generation logic without requiring human participants or GPU resources.
- **Output**: Synthetic interaction logs (`data/interaction_logs/anonymized_logs.csv`) used strictly for CI validation and unit testing.
- **Constraint**: This simulation **replaces** real participants **ONLY** for the automated CI run.

### 1.2. Final Research Output (Real Human Subject Study)
The actual research findings, as required by the specification and the scientific method, must be derived from real human participants.

- **Implementation**: Task `T015-real` implements the collection of real participant interaction data via a secure web form.
- **Purpose**: To generate the authentic dataset required for the final publication and OSF repository.
- **Prerequisites**: This task requires a manual execution environment with human participants and must pass the `LatencyCalibrator` (T012) verification.
- **Output**: Real interaction logs (`data/interaction_logs/raw_logs_real.csv`) which are then anonymized and analyzed.

## 2. Alignment with Functional Requirements

This scope adaptation directly addresses the following requirements:

- **FR-001 (Data Source)**: The simulation uses the same underlying `Defects4J` dataset (extracted via `T013`) and summary artifacts (pre-computed via `T014-real` or simulated via `T014`) as the real study, ensuring the *data structure* is identical.
- **FR-003 (Latency)**: The simulation respects the latency constraints by using deterministic timestamps, while the real study (`T015-real`) enforces the `LatencyCalibrator` gate to ensure real-world precision ≤100ms.
- **FR-007 (CI Constraints)**: The simulation allows the pipeline to run within the strict resource limits of GitHub Actions free-tier runners, which cannot support GPU-based LLM inference or long-running human interaction sessions.

## 3. Technical Implementation Details

### 3.1. Simulation Mode (CI)
When the pipeline runs in CI (automated triggers):
1. `code/generation/generate_summaries_offline.py` (T014) generates `data/summaries/llm_summaries_sim.csv`.
2. `code/simulation/participant_sim_llm.py` (T015-llm) loads these simulated summaries.
3. Interaction logs are generated using `numpy.random` with fixed seeds to ensure reproducibility.

### 3.2. Real Mode (Manual Study)
When the pipeline is executed manually for the final study:
1. `code/generation/run_gpu_summaries.py` (T014-real) generates `data/summaries/llm_summaries_real.csv` using `CodeLlama` on a GPU.
2. `code/simulation/participant_sim_real.py` (T015-real) collects real timestamps and decisions.
3. The `LatencyCalibrator` (T012) must pass before data collection begins.

## 4. Conclusion

The use of a deterministic simulation in the CI pipeline is a **temporary, procedural substitution** to enable automated testing of the research infrastructure. It does not alter the fundamental scope of the research question, which remains the evaluation of code summarization techniques for bug localization using **real human data** for the final results.

The "Real Study" path (T015-real) is fully implemented and is the mandatory step for producing the final scientific output. The simulation is strictly a validation tool for the pipeline's correctness and resource compliance.

---
*Generated for PROJ-140-evaluating-the-efficacy-of-code-summariz*
*Date: 2023-10-27*