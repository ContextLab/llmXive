# Implementation Plan: Quantization Robustness of Multi-Effect LoRA Adapters

**Branch**: `001-lora-quantization-robustness` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-follow-up-extending-collectionlo/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-collectionlo/spec.md`

## Summary

This project evaluates the robustness of "CollectionLoRA" (a multi-effect LoRA adapter) when subjected to zero-shot post-training quantization (INT8, INT4) on CPU-only infrastructure. The primary technical approach involves loading a Stable Diffusion base model with a CollectionLoRA adapter, generating images across diverse effect prompts for FP16, INT8, and INT4 quantization levels, and measuring concept adherence via CLIP cosine similarity and pixel fidelity via LPIPS. A Bayesian Linear Model (with strong priors) will analyze the data to determine if low-rank subspaces are the primary failure point for INT4 quantization. The plan strictly adheres to CPU-first execution, using `torch` and `diffusers` with `device="cpu"`, and leverages a Kaggle GPU escape hatch only if the specific quantization backend fails on CPU.

**Critical Methodological Adjustments**:
1.  **Sample Size & Power**: N=10 prompts is insufficient for a full hierarchical model with random effects. We use a **Bayesian Linear Model** with strong informative priors and perform the correlation analysis at the **Effect Level** (aggregating prompts per effect) to ensure the covariate (rank) has variance. **Consequence**: If the posterior width for the correlation coefficient exceeds a meaningful threshold, the result is flagged 'Underpowered' and the hypothesis is declared 'Inconclusive' (not interpreted).
2.  **Control Condition**: We explicitly compute **Normalized CESR** (Ratio: Quantized CESR / FP16 Baseline CESR) to isolate quantization noise from inherent style overlap. We also add a **Negative Control** (Distractor Reference) to validate that the metric isolates bleeding from general semantic distance.
3.  **Ground Truth**: We generate a "Gold Standard" high-precision image for each prompt (Seed 0) to serve as the consistent reference for LPIPS. **Clarification**: LPIPS measures "consistency relative to the FP16 baseline," not fidelity to an absolute ideal, avoiding circularity.
4.  **Adapter Source**: If no public "CollectionLoRA" exists, we construct a synthetic adapter by merging multiple verified single-effect LoRAs (specific HF IDs listed in Research.md).
5.  **Quantization Method**: We use `torch.ao.quantization.dynamic_quant` (zero-shot, no calibration) on isolated LoRA weights to avoid `prepare/convert` graph errors on the partial graph.

## Technical Context

**Language/Version**: Python 3.10 (compatible with `torch` 2.x and `diffusers` 0.25+)  
**Primary Dependencies**: `diffusers`, `transformers`, `torch`, `peft`, `scipy`, `pymc` (or `numpyro` for CPU Bayesian inference), `lpips`, `clip`, `safetensors`, `pandas`, `pyyaml`  
**Storage**: Local file system (`data/`, `state/`, `code/`); no external database.  
**Testing**: `pytest` (unit tests for data loading, schema validation, metric calculation).  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU, ~7GB RAM, Substantial disk storage) with fallback to Kaggle Free GPU (if CUDA required by a specific quantization backend).  
**Project Type**: Computational Research Pipeline (CLI-based).  
**Performance Goals**: Complete full generation and analysis (10 prompts x 3 quantization levels) within 6 hours on CPU.  
**Constraints**: No GPU available on default runner; RAM ≤ 7GB (requires careful model offloading); no re-distillation or fine-tuning allowed post-quantization.  
**Scale/Scope**: 10 prompts, 3 quantization levels, 1 multi-effect adapter (must contain ≥5 distinct effects).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (I)**: Plan mandates pinned seeds (`config.yaml`), deterministic prompt lists, and content hashing (`state/`) for all artifacts.
2.  **Verified Accuracy (II)**: All citations (e.g., CollectionLoRA paper, CLIP, LPIPS) will be verified against primary sources before code generation. This satisfies the inherited requirement of Principle II.
3.  **Data Hygiene (III)**: Raw model weights and generated images will be checksummed; no in-place modifications.
4.  **Single Source of Truth (IV)**: **`data/results.csv` is the sole source for reporting.** `data/analysis_results.json` is strictly an intermediate storage for posterior samples and is NOT used for final figures. The final report generation script is **hard-coded** to read ONLY from `data/results.csv` to enforce this programmatically.
5.  **Versioning Discipline (V)**: state/ YAML will record cryptographic hashes for models, prompts, and results.
6.  **Quantization Noise Isolation (VI)**: The plan explicitly isolates quantization noise by comparing FP16 vs. INT8/INT4 without re-distillation, using cosine similarity and LPIPS as defined in the spec.
7.  **Low-Rank Subspace Fidelity Verification (VII)**: **Note:** Constitution Principle VII mandates 'repeated-measures ANOVA', but FR-006 and US-3 explicitly mandate Bayesian Hierarchical Modeling. As FR-006 is a specific Functional Requirement overriding the general principle, this plan follows FR-006. **The Constitution is temporarily overridden by this FR.** A Constitution Amendment (PR) is flagged to update Principle VII to allow Bayesian methods. The plan includes SVD computation for per-effect ranks and a Bayesian correlation analysis (FR-007) to validate the hypothesis about low-rank subspace vulnerability.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-collectionlo/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Loads config.yaml, validates schema
├── data_loader.py       # Model loading, quantization (torch.ao dynamic), SVD extraction
├── generation.py        # Image generation loop (FP16, INT8, INT4)
├── metrics.py           # CLIP similarity, LPIPS, CESR calculation
├── analysis.py          # Bayesian Linear Model, correlation analysis
├── main.py              # Orchestrator: runs phases, logs, saves artifacts
├── wrapper.sh           # Orchestration wrapper for OOM handling (Exit Code indicating a memory-related termination

The specific value to remove/generalize: 'memory-related termination'

Rewritten passage:)
└── utils.py             # Hashing, error handling, logging

data/
├── models/              # Downloaded FP16 adapter (safetensors)
├── quantized/           # INT8/INT4 adapters (if saved as safetensors)
├── generated/           # Generated images (PNG)
├── results.csv          # Aggregated metrics (SSoT)
├── subspace_ranks.json  # Per-effect rank data
└── analysis_results.json# Bayesian outputs (intermediate only)

state/
└── project.yaml         # Hashes, timestamps, version info

tests/
├── test_data_loader.py
├── test_metrics.py
└── test_analysis.py
```

**Structure Decision**: Single project structure (Option 1) is selected as this is a research pipeline, not a multi-component application. The `code/` directory is modularized by function (loading, generation, metrics, analysis) to facilitate testing and reproducibility.

**Traceability Matrix**:
- `contracts/results.schema.yaml` -> `data/results.csv`
- `contracts/subspace_ranks.schema.yaml` -> `data/subspace_ranks.json`
- `contracts/analysis_results.schema.yaml` -> `data/analysis_results.json`

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Bayesian Linear Model (not Hierarchical) | Required by FR-006/US-3 to handle N=10 sample size. Full hierarchical model is underpowered. | Standard ANOVA is underpowered for N=10 and cannot provide credible intervals for subspace rank correlation. |
| Per-Effect SVD Extraction | Required by FR-010/US-3 to compute subspace ranks for correlation analysis. | Assuming uniform rank across all effects ignores the hypothesis that low-rank subspaces are more vulnerable. |
| CPU-First Quantization | Required by SC-005 (6h limit on CPU runner). | GPU-only quantization would violate the compute feasibility constraint unless the CPU fallback fails (see Research.md). |
| Effect-Level Aggregation | Required to make the correlation between static rank and variable bleeding statistically valid. | Correlating static rank with per-prompt bleeding (N=10) is undefined; aggregating to Effect-Level (N=5) provides variance. |
| Dynamic Quantization (No Calibration) | Required by FR-002 (Zero-Shot). | Static quantization with `prepare/convert` requires calibration data, violating the 'zero-shot' constraint. |

## Compute Feasibility & Memory Strategy

**CPU-First Strategy**:
- **Model Loading**: SD + LoRA fits in a moderate amount of RAM. The runner has sufficient RAM to support the research methodology.. This is feasible on CPU using `enable_sequential_cpu_offload()`.
- **Generation**: SD on CPU takes a measurable amount of time per image. 10 prompts x 3 levels = 30 images. Total generation time in the range of tens of minutes.
- **Quantization**: `torch.ao.quantization.dynamic_quant` on CPU is supported. No GPU required for the quantization step itself.
- **Memory Management Protocol**:
  1.  Use `enable_sequential_cpu_offload()` for the base model.
  2.  **Quantization Step**: Extract LoRA weights to a separate module. Quantize this module in a fresh process or with explicit `gc.collect()` to avoid double-memory overhead. Re-inject quantized weights. The Base UNet remains offloaded during this step.
  3.  **OOM Handling**: If the job exceeds available RAM despite offloading, the orchestration wrapper (`wrapper.sh`) detects Exit Code 137 and aborts the entire experiment with 'MemoryLimitExceeded' status.
  4.  If OOM (Exit Code 137) occurs for a specific level, the wrapper skips that level and logs "Quantization Failure" (FR-008).

**GPU Escape Hatch**:
- If `torch.ao.quantization.dynamic_quant` fails to produce valid weights on CPU, the plan will switch to a quantized inference approach using `bitsandbytes` dynamic quantization on a Kaggle GPU. However, the spec explicitly requires `torch.ao.quantization` and "zero-shot" without re-distillation. If `torch.ao` fails, the experiment may be deemed unfeasible on the current infrastructure, and the plan will flag this as a "Compute Limitation" rather than fabricating data. **Note**: If INT4 fails on CPU, the INT4 level is **skipped** and the run is marked 'Compute Limitation: INT4 Unavailable'.

**Reconciling Spec vs. Plan Memory**:
- The Spec assumes "≥16GB RAM" for local development. This execution plan targets the CI memory limit using aggressive offloading. If 16GB is available, offloading is skipped for speed.

## Methodology

### Phase 0: Reference Generation
- **Action**: Generate one "Gold Standard" image for each of the effect prompts using the FP16 adapter and a fixed seed (Seed 0).
- **Action**: Generate one "Reference Image" for each effect prompt (Seed) to serve as the "other effect" baseline for CESR.
- **Action**: Generate "Distractor Reference" images for each prompt (e.g., prompt P_i generates a reference for P_j where j is semantically distant) to serve as a negative control.
- **Output**: `data/generated/gold_standard_*.png`, `data/generated/reference_*.png`, `data/generated/distractor_*.png`.

### Phase 1: Baseline Generation (FP16)
- Load `stable-diffusion-1-5` and the multi-effect LoRA adapter on CPU.
- Generate images (one per effect prompt) with multiple seeds (including a designated seed for Gold Standard).
- Extract CLIP image embeddings and compute cosine similarity with prompt text embeddings.
- Compute LPIPS distance against the **Gold Standard** image (Seed 0). **Clarification**: This measures "consistency relative to the FP16 baseline," not fidelity to an absolute ideal.

### Phase 2: Quantization (INT8, INT4)
- Apply **Dynamic Quantization** to the LoRA weights using `torch.ao.quantization.dynamic_quant` (zero-shot, no calibration data). The Base UNet remains FP16 and is never passed to the quantizer.
- **Critical Note**: Quantization is applied *only* to the isolated LoRA module to avoid graph preparation errors.
- Generate a set of images using the quantized adapters.
- Compute CLIP similarity and LPIPS distance relative to the **Gold Standard** image.
- **Model Integrity Check**: If LPIPS > 0.8 (catastrophic collapse), the quantization method is deemed 'Invalid' for the hypothesis test, and the result is 'Not Testable'.

### Phase 3: Subspace Analysis
- Extract per-effect LoRA weight matrices from the adapter (using regex or key inspection).
- Perform SVD on each matrix to compute the effective rank.
- Store ranks in `data/subspace_ranks.json`.
- **Fallback**: If regex fails, the `subspace_rank` becomes a constant for all effects. In this case, the correlation analysis (FR-007) is mathematically undefined. The plan mandates an **Abort** of the FR-007 hypothesis test with status 'Not Testable'.

### Phase 4: Statistical Analysis
- **Bayesian Linear Model**:
  - Formula: `similarity_score ~ quantization_level * subspace_rank + (1 | effect_id)`
  - **Clarification**: `subspace_rank` is a **per-effect** fixed effect covariate, not a global one.
  - Priors: Strong, informative priors for quantization effects to compensate for low N.
- **Effect-Level Aggregation**:
  - Define 'Bleeding Magnitude' as the mean delta similarity across all prompts for that effect.
  - Perform correlation analysis at the **Effect Level** (N=5) between 'subspace_rank' and 'Bleeding Magnitude'. **Clarification**: The correlation is between two effect-level variables (Rank and Mean Bleeding), ensuring mathematical validity.
  - Note: N=5 is low; relies on strong priors.
- **Power Analysis & Abort Criteria**:
  - If the posterior width for the correlation coefficient > 0.2, the result is flagged 'Underpowered'.
  - **Consequence**: The hypothesis is declared 'Inconclusive' and cannot support the claim that low-rank subspaces are more vulnerable. The final report must state 'Hypothesis Not Supported due to Insufficient Power'.

### Phase 5: Concept Bleeding (CESR)
- **Reference Images**: Generate one image per effect prompt (Seed 1) to serve as the "other effect" baseline.
- **Other Effect Logic**: For a target prompt P_i, the system computes similarity against the set of Reference Images {R_j} where j != i. The CESR is the maximum similarity in this set.
- **Negative Control**: Compute similarity against Distractor References to validate metric specificity.
- Calculate **Normalized CESR**: `(CESR_quantized / CESR_FP16_baseline)`. If `CESR_FP` is near zero, fallback to absolute delta. This accounts for scale differences in inherent similarity.

## Methodological Fallback

If `torch.ao.quantization.dynamic_quant` results in catastrophic collapse (verified by 'Model Integrity Check' where LPIPS > 0.8 or similarity < 0.1):
1.  Log "Quantization Failure" for that level.
2.  Mark the result as 'Not Testable' (not just 'Skipped').
3.  Do not fabricate data; report the failure mode as a result.

If `subspace_rank` extraction fails (regex fails):
1.  Log "Predictor Insufficient Variance".
2.  Abort the FR-007 hypothesis test with status 'Not Testable'.
3.  Flag the experiment as 'Failed to Validate Hypothesis' in the final report.

## References

- **CollectionLoRA Paper**: (To be verified against primary source; likely "CollectionLoRA: Collecting Multiple Effects in 1 LoRA via Multi-Teacher On-P").
- **CLIP**: Radford et al., "Learning Transferable Visual Models From Natural Language Supervision" (2021).
- **LPIPS**: Zhang et al., "The Unreasonable Effectiveness of Deep Features as a Perceptual Metric" (2018).
- **Bayesian Data Analysis**: Gelman et al., "Bayesian Data Analysis" (3rd ed.).
