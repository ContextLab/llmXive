# Research: AutoResearchClaw Reproduction & Validation

## Executive Summary

This research phase validates the feasibility of reproducing the `AutoResearchClaw` system's core claims—autonomous execution, self-healing, and cross-run learning—within the strict constraints of a GitHub Actions free-tier runner (CPU-only, 7 GB RAM, 6h limit). The primary challenge is adapting the original system, which may rely on heavy LLM inference or large datasets, to a resource-constrained environment without losing the integrity of the "self-reinforcing" loop.

**Critical Limitation**: This pilot validates the *system mechanism* (code execution, error handling, HITL compliance) using synthetic data. It explicitly does *not* validate the *scientific validity* of the research outputs or the *semantic learning* capabilities claimed in the original paper. Claims regarding "self-reinforcing research" on real-world scientific nuance are out of scope for this CPU-only pilot.

## Dataset Strategy

The original `AutoResearchClaw` paper likely uses large, diverse datasets (e.g., from ARC-Bench). However, the verification block for this project lists **no verified datasets** that match the specific "research topic" requirements of the original paper. The provided URLs (Ram, OOM) are either unrelated to research topics or are specifically labeled as "OOM" (Out of Memory) test cases, which are unsuitable for the primary validation loop but useful for stress-testing the memory guard.

**Decision**: We will **NOT** use the provided "OOM" datasets for the primary research loop, as they are designed to fail memory checks. Instead, we will:
1. **Synthetic Data Generation**: For the primary validation (FR-001), we will generate small, synthetic datasets (e.g., 100-500 rows) representing "research topics" (e.g., "Effect of X on Y"). This ensures the system can run end-to-end without hitting memory limits or requiring external downloads.
2. **Fallback to Small Public Data**: If synthetic data is insufficient for specific analysis steps, we will use the **lex-friddman-podcasts** dataset (uploaded by `RamAnanth1`) as a source for "topic extraction" or "literature review" simulation, but only in a sampled capacity (e.g., first 100 lines) to fit the 7 GB RAM constraint.
3. **OOM Stress Testing**: The "OOM" datasets will be used *only* in the `test_memory_guard.py` unit tests to verify that the system correctly detects and mitigates memory pressure before crashing.

**Verified Dataset Sources**:
* **Synthetic Data**: Generated internally (no external URL).
* **lex-friddman-podcasts**: ` (Used for topic simulation only, sampled). *Note: Dataset name is 'lex-friddman-podcasts' by 'RamAnanth1'.*
* **OOM Test Cases**: ` (Used for memory guard validation only). *Note: This is a temporary upload; if the URL breaks, the test will use a locally generated synthetic large file.*

**Scope Boundary: Semantic Nuance**: Synthetic data lacks the noise, contradiction, and nuance required to trigger the "Pivot/Refine" logic meaningfully in a scientific context. The validation will confirm the system can process clean data and handle injected errors, but cannot empirically validate the "self-reinforcing" claim regarding scientific discovery.

## Methodology & Statistical Rigor

Since this is a system validation project rather than a scientific study, standard statistical power analysis is not directly applicable. However, the following rigor principles are applied:

1. **Multiple Comparison / Error Rate Control**: The system will run 5 distinct topics (SC-001). To avoid "cherry-picking" a successful run, the success rate (≥ 80%) is pre-defined. The self-healing mechanism (FR-002) will be evaluated on a fixed set of injected errors to measure recovery rate (SC-003).
 * **Statistical Power Limitation**: With N=5, a single failure drops the rate to [deferred], and a single success is [deferred]. This sample size provides **zero statistical power** to distinguish a true [deferred] success rate from random chance or a [deferred] rate.
 * **Revised Interpretation**: SC-001 is treated as a **Minimum Viability Threshold** (Pass/Fail: ≥4/5 successful runs) for the *mechanism*, not a statistical inference. A larger N (e.g., N=30) is required for statistical power, which is deferred to Phase 2.

2. **Causal Inference (HITL)**: The HITL intervention (FR-003) is a controlled experiment. We will compare runs *with* intervention vs. *without* intervention on the same topic.
 * **Metric Change**: The "quality score" (SC-004) is replaced by a **Plan Adherence Metric** (binary: did the system execute the specific human instruction?). This avoids the tautology of checking for structural elements the system is designed to produce.
 * **Power Limitation**: The N=5 pilot is insufficient to detect a [deferred] improvement with statistical significance. The plan defines a controlled A/B test design (N=10 per group) for the full study, but notes that the N=5 pilot is a feasibility check only.

3. **Measurement Validity**: The "Plan Adherence Metric" is explicitly defined in the `artifact_validator.py` (e.g., "Did the generated code use the variable specified in the feedback?"). This rubric will be documented in `quickstart.md`.

4. **Collinearity**: Not applicable for system validation; the focus is on code execution and state management, not statistical modeling of variables.

5. **Circularity Mitigation (SC-005)**: To avoid validating that the system prevents errors it *itself* recorded (circularity), we will use an **Injected Failure Registry**. This is a pre-defined list of known errors (independent of the system's log) that the system is tested against. The system's ability to avoid these *external* failures validates the "lesson learned" mechanism.

## Compute Feasibility Analysis

The GitHub Actions free-tier runner (2 CPU, 7 GB RAM, 14 GB disk) imposes severe constraints:

* **LLM Inference**: The original system likely uses large LLMs. We will **mock** the LLM provider or use a small, CPU-tractable model (e.g., `HuggingFace`'s `distilbert` or a local `llama.cpp` quantized model if memory permits, but likely just a mock for the validation loop to ensure speed). The plan prioritizes **mocking** the LLM to guarantee the 6h limit is met.
* **Memory**: The 7 GB limit is tight. The `memory_guard.py` will monitor RSS (Resident Set Size) and trigger a "sampling" fallback if usage exceeds 6 GB. This will involve reducing the dataset size or skipping complex analysis steps.
* **Time**: The 6h limit is generous for a small loop, but the self-healing loop (Pivot/Refine) could cause infinite loops. A hard limit on the number of retries per error is enforced.
* **No GPU**: All code must run on CPU. No CUDA dependencies.

## Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| **OOM Crash** | High | Critical | `memory_guard.py` monitors RAM; triggers data sampling or graceful exit. |
| **Infinite Self-Healing Loop** | Medium | High | Hard limit of 3 retries per error; logs failure and moves to next topic. |
| **LLM API Timeout/Rate Limit** | Medium | High | Mock provider for validation; retry with exponential backoff (max 3) for real API. |
| **6h Timeout** | Low | High | Checkpointing every 30 mins; partial report generation on timeout. |
| **Dataset Mismatch** | High | Medium | Use synthetic data for core loop; do not rely on external datasets for primary validation. |
| **Statistical Power** | High | Medium | Explicitly frame SC-001/SC-004 as viability gates for N=5; defer statistical claims to Phase 2. |
| **Circularity in SC-005** | Medium | High | Use "Injected Failure Registry" (external oracle) instead of system log for validation. |

## Decision Rationale

* **Mocking LLM**: The primary goal is to validate the *loop mechanism* (healing, HITL, memory), not the quality of LLM-generated text. Mocking ensures deterministic, fast execution and avoids API costs/rate limits.
* **Synthetic Data**: Using the provided "OOM" datasets for the main loop would cause the system to fail the memory test by design. Synthetic data allows us to control the data size and complexity to fit the 7 GB limit.
* **File-based Evolution Log**: A database is too heavy. A JSON file is sufficient for the scale (multiple runs, multiple topics) and easily parsable by the CI pipeline.
* **Plan Adherence Metric**: Replacing "quality score" with "Plan Adherence" avoids the tautology of measuring structural existence vs. scientific quality.