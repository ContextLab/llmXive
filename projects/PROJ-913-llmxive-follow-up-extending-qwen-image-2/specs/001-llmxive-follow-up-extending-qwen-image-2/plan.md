# Implementation Plan: llmXive Follow-up: OPD Generalization Gap in Unified Diffusion

**Branch**: `001-opd-generalization-gap` | **Date**: 2026-07-15 | **Spec**: `specs/001-opd-generalization-gap/spec.md`
**Input**: Feature specification from `/specs/001-opd-generalization-gap/spec.md`

## Summary

This project investigates whether the On-Policy Distillation (OPD) stage in unified diffusion frameworks induces a measurable degradation in zero-shot generalization performance. The technical approach involves acquiring pre-trained base and RL-unified Qwen-Image-2.0 weights, curating distinct in-distribution and out-of-distribution (OOD) prompt sets from verified image-generation datasets, and executing CPU-only inference using `diffusers` with float16 precision and CPU offloading. The study computes mean score degradation across three VLM-based reward metrics (Aesthetics, Prompt Adherence, Identity Preservation) and performs an **Independent Samples T-Test (Welch's t-test)** to determine the statistical significance of the "Generalization Gap" between the ID and OOD sets. A **Human Proxy Validation** step using `HuggingFaceH4/image-reward` is included to break circular dependency on VLM scores.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `diffusers`, `transformers`, `torch` (CPU-only), `scikit-learn`, `pandas`, `numpy`, `requests`, `huggingface_hub`, `seaborn`, `datasets`  
**Storage**: Local filesystem (`data/`, `outputs/`) with SHA-256 checksums; no external database.  
**Testing**: `pytest` (unit tests for data validation, statistical analysis mocks); integration tests for inference pipeline on CPU.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, no GPU).  
**Project Type**: Computational research pipeline / CLI tool.  
**Performance Goals**: Complete inference and analysis within 6 hours; memory usage < 7 GB via batch processing and CPU offloading.  
**Constraints**: No GPU; no 8-bit/4-bit quantization for base models (only for VLM reward models if necessary); strict OOD prompt validation (cosine similarity < 0.3); reproducibility via pinned seeds and checksums.  
**Scale/Scope**: Target: A balanced set of in-distribution and out-of-distribution (OOD) prompts for evaluation.; Pilot: a small subset of prompts per set to estimate runtime and effect size.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (NON-NEGOTIABLE)**:
    *   **Plan**: All random seeds will be pinned in `code/`. External datasets (models, prompts) will be fetched from canonical Hugging Face sources with SHA-256 checksum verification recorded in `data/`.
    *   **Status**: Compliant.

2.  **Verified Accuracy**:
    *   **Plan**: Citations for models (Qwen-Image-2.0) and datasets (OPD, OOD) will be verified against primary Hugging Face repositories by the **Reference-Validator Agent**. Title-token-overlap threshold **≥ 0.7** will be enforced.
    *   **Status**: Compliant.

3.  **Data Hygiene**:
    *   **Plan**: Raw data (model weights, prompt sets) will be checksummed. No in-place modifications; derivations (generated images, scores) will be written to new files. PII scan will be run on committed data.
    *   **Status**: Compliant.

4.  **Single Source of Truth**:
    *   **Plan**: All statistics in the final report will trace to specific rows in `data/` (scored images) and code blocks in `code/`. No hand-typed numbers.
    *   **Status**: Compliant.

5.  **Versioning Discipline**:
    *   **Plan**: Artifacts will carry content hashes. The `state/` file will be updated upon any artifact change.
    *   **Status**: Compliant.

6.  **Out-of-Distribution Evaluation Integrity**:
    *   **Plan**: The OOD set (abstract physics/historical artifacts) will be validated against the in-distribution set (Qwen-Image-Bench) via latent-space cosine similarity (< 0.3) AND semantic keyword filtering. VLM reward models will be identical to the original paper.
    *   **Status**: Compliant.

7.  **Statistical Significance of Generalization Degradation**:
    *   **Plan**: The "Generalization Gap" (difference in mean score degradation between OOD and In-Distribution sets) will be tested against a null hypothesis of zero using an **Independent Samples T-Test (Welch's t-test)**. This test compares two independent groups (ID degradation distribution vs. OOD degradation distribution).
    *   **Clarification**: While Constitution Principle VII mentions a "paired t-test," this refers to the *calculation* of degradation (paired Base vs. RL scores per prompt). The *test of the gap* itself compares two independent distributions of these degradation values, requiring an Independent Samples T-Test.
    *   **Status**: Compliant.

## Statistical Power & Sample Size Strategy (Addressing SC-002)

To satisfy SC-002 ("measured against the requirement for a minimum sample size sufficient for statistical power"):

1.  **Pilot Phase**: Execute the full pipeline on **N=20** prompts per set (ID and OOD).
2.  **Effect Size Estimation**: Calculate the Cohen's d effect size from the pilot degradation differences.
3.  **Power Calculation**: Use `statsmodels.stats.power.tt_solve_power` to determine the required N to achieve adequate power (1-β) for the observed effect size (α=0.05).
4.  **Feasibility Check**:
    *   If `Required_N <= 500` and `Estimated_Runtime(Required_N) <= 6h`: Proceed to **Target**.
    *   If `Estimated_Runtime(Required_N) > 6h`: Proceed to **Max-Feasible** (N where runtime ≈ h to allow buffer).
    *   If `Max-Feasible_N < 30`: Report **Power Limitation**. Proceed with **Max-Feasible_N** and explicitly report the achieved power (likely < 0.80) in the final results.
5.  **Reporting**: The final analysis report will explicitly state: "Target Power: Sufficient statistical power to detect meaningful effects.. Achieved Power: [X]. Effect Size: [d]. Sample Size Used: [N]." This directly measures the requirement against the constraint.

## Pilot-to-Target Decision Logic

To resolve the conflict between the 500-prompt mandate and the 6-hour runtime constraint:

1.  **Pilot Phase**: Execute the full pipeline on **N=20** prompts per set (ID and OOD).
2.  **Runtime Measurement**: Measure total time `T_pilot`.
3.  **Decision Logic**:
    *   If `T_pilot < 4.0 hours`: Proceed to **Target (N=500)** (subject to power analysis above).
    *   If `4.0 <= T_pilot < 6.0 hours`: Proceed to **Max-Feasible (N = floor(* (/ T_pilot)))**.
    *   If `T_pilot >= 6.0 hours`: Report **Power Limitation**. Proceed with **N=20** (Pilot) and document the inability to scale.
4.  **Power Reporting**: For any N < 500, the analysis will calculate and report the achieved statistical power for the observed effect size, satisfying SC-002 by measuring the power rather than assuming it.

## Project Structure

### Documentation (this feature)

```text
specs/001-opd-generalization-gap/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── prompt.schema.yaml
│   ├── generated_image.schema.yaml
│   └── score.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2/
├── data/
│   ├── prompts/
│   │   ├── in_distribution.csv
│   │   └── ood.csv
│   ├── models/
│   │   ├── base_qwen_image_2.0/
│   │   └── rl_unified_qwen_image_2.0/
│   └── outputs/
│       ├── base/
│       └── rl_unified/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data_acquisition.py
│   ├── prompt_curation.py
│   ├── inference.py
│   ├── scoring.py
│   ├── analysis.py
│   └── human_proxy.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── docs/
```

**Structure Decision**: Single project structure (`projects/PROJ-913...`) with a dedicated `code/` directory for scripts and `data/` for artifacts. This aligns with the "Reproducibility" and "Data Hygiene" principles, ensuring all data and code are co-located and versioned.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| CPU-only inference for large diffusion models | The spec mandates execution on free-tier GitHub Actions (no GPU). | GPU-based inference is not feasible on the target platform; CPU offloading is the only compliant path. |
| Independent Samples T-Test (Welch's) | Required to compare two independent groups (ID vs OOD degradation) as per corrected methodology. | Paired T-Test is invalid for comparing two distinct distributions of degradation values. |
| Human Proxy Validation | Required by FR-008 to rule out circular dependency on VLM reward models. | Relying solely on VLM scores would make the "Generalization Gap" a tautology of the training objective. |
| Dynamic Batching & Pilot Scaling | Required to fit within 7 GB RAM and 6-hour time limit while maximizing statistical power. | Fixed batch sizes or fixed N=500 would either crash the runner or exceed the time limit. |
| Semantic OOD Verification | Required to ensure OOD prompts are truly distinct in the image domain, not just textually. | Simple cosine similarity may not capture domain shift; keyword filtering and latent checks are needed. |
