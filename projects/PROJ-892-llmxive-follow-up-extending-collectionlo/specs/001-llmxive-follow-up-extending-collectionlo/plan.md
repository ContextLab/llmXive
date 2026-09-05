# Implementation Plan: Quantization Robustness of Multi-Effect LoRA Adapters

**Branch**: `001-lora-quantization-robustness` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-collectionlo/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-collectionlo/spec.md`

## Summary

This project evaluates the robustness of "CollectionLoRA" (a synthesized multi-effect LoRA adapter) against post-training quantization (INT8, INT4). The primary requirement is to measure concept adherence (via CLIP cosine similarity) and pixel fidelity (via LPIPS) degradation when quantizing weights without re-distillation. The technical approach involves **synthesizing** a valid multi-effect adapter from verified single-effect LoRAs (or procedural generation if none are found), performing zero-shot quantization on a CPU-only runner, and analyzing the results using Bayesian hierarchical models. 

**Key Methodological Update**: The correlation analysis between subspace rank and bleeding is now **descriptive/exploratory** only, as N=5 effects is insufficient for statistical significance. The primary inference focuses on the quantization effect (N=50). The CESR metric is **normalized** against a distractor baseline to isolate bleeding from general fidelity loss.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `torch` (CPU-only quantization), `diffusers`, `transformers`, `scipy` (SVD), `pymc` (Bayesian analysis), `lpips`, `clip` (or `open-clip`), `datasets` (for prompt management).  
**Storage**: Local file system (`data/`, `state/`); no external DB.  
**Testing**: `pytest` (unit), `pytest-cov` (coverage), custom integration tests for quantization integrity.  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU-first, 2 cores, ~7-16GB RAM).  
**Project Type**: Research Pipeline / CLI Tool.  
**Performance Goals**: Complete generation and analysis within ≤6 hours; memory usage <14GB.  
**Constraints**: Must run on CPU without CUDA; must handle OOM (Exit 137) gracefully; must synthesize adapter if public source fails.  
**Scale/Scope**: A set of distinct prompts × multiple quantization levels (FP, INT8, INT4) × 5 seeds (approx. 150 images); Multiple distinct effects in the adapter.

> **Note on Dataset/Model Availability**: The `stabilityai/collection-lora` repository does not exist. The plan **explicitly implements** a Synthetic Adapter Construction phase (Phase 0) using verified single-effect LoRAs or procedural generation to satisfy FR-001 and FR-010.

## Constitution Check

| Principle | Compliance Status | Evidence / Plan Element |
|-----------|-------------------|-------------------------|
| **I. Reproducibility** | **Compliant** | `code/` contains pinned `requirements.txt`; random seeds defined in `code/config.yaml`; data fetched via programmatic loaders or procedural generation. |
| **II. Verified Accuracy** | **Compliant** | All citations (CLIP, LPIPS, Bayesian methods) reference standard literature; dataset URLs are specific, verified HuggingFace IDs or procedural. |
| **III. Data Hygiene** | **Compliant** | `state/` YAML records SHA-256 hashes for all weights, images, and results; raw data is never modified in place. |
| **IV. Single Source of Truth** | **Compliant** | `data/results.csv` is the sole source for statistical claims; figures in the paper will be generated directly from this CSV. |
| **V. Versioning Discipline** | **Compliant** | **Every** artifact (images, CSVs, JSONs, weights) carries a content hash recorded in `state/artifacts.yaml`. |
| **VI. Quantization Noise Isolation** | **Compliant** | Zero-shot quantization via `torch.ao.quantization` (no fine-tuning); comparison against FP16 baseline isolates noise. |
| **VII. Low-Rank Subspace Fidelity** | **Compliant** | SVD rank computed on **pre-merge** source matrices (independent of merge logic); correlation is descriptive (N=5 effects) with explicit 'Underpowered' flagging. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-collectionlo/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── analysis_results.schema.yaml
    ├── generation_result.schema.yaml
    └── state.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.yaml          # Prompts, seeds, paths
├── data_loader.py       # Model loading, SVD, quantization, merging
├── generator.py         # Image generation loop
├── metrics.py           # CLIP, LPIPS, CESR (Normalized) calculation
├── statistical_analysis.py # Bayesian modeling
├── main.py              # Orchestration
└── utils.py             # Hashing, error handling

data/
├── models/              # Downloaded/synthesized adapters
├── generated/           # Output images
├── references/          # FP16 Reference Images & Distractor Images
├── results.csv          # Aggregated metrics
└── subspace_ranks.json  # SVD results (source ranks)

state/
└── artifacts.yaml       # Hashes and timestamps

tests/
├── unit/
├── integration/
└── contract/
```

**Structure Decision**: A single `code/` directory containing modular scripts is chosen to minimize overhead and ensure all steps run sequentially on the CPU runner. The `data/` directory is strictly for artifacts; `state/` tracks provenance.

## Phases & Tasks

### Phase 0: Adapter Synthesis & Verification
*Goal: Construct a valid multi-effect adapter and compute intrinsic source ranks.*

- **T001: Load & Verify Source LoRAs**
  - Load a set of verified single-effect LoRAs. (e.g., `lykon/dreamshaper-lora`, `cagliostrolab/animagine-xl`, etc.) OR generate procedural low-rank matrices if none are available.
  - **Compatibility Check (T001b)**: Verify all sources share the same base model architecture and rank. If incompatible, fallback to procedural generation.
  - **SVD Rank (T001c)**: Compute SVD rank on each **pre-merge** source matrix with tolerance `1e-5`. Record as `SourceRank` (independent of merge).
  - **Output**: `data/subspace_ranks.json` (source ranks), `data/models/source_loras/`.

- **T002: Merge into CollectionLoRA**
  - Apply **Weighted Linear Addition with Orthogonal Projection (WLA-OP)** to merge source matrices into a single adapter.
  - **Protocol**: Project each source matrix onto an orthogonal basis before addition to minimize cross-talk.
  - **Output**: `data/models/collection_lora.safetensors`.

### Phase 1: Generation & Metric Calculation
*Goal: Generate images and compute normalized metrics.*

- **T003: Generate Baseline (FP16)**
  - Generate a set of images (multiple prompts × multiple seeds) using an FP16 adapter.
  - **Output**: `data/generated/baseline/`, `data/references/baseline_embeddings.json`.

- **T004: Generate Distractor References (T012)**
  - Generate 10 images using the **same** FP16 adapter but with **unrelated** prompts (Distractors) to establish a random semantic distance floor.
  - **Output**: `data/references/distractor_embeddings.json`.

- **T005: Generate Quantized Outputs (INT8, INT4)**
  - Apply `torch.ao.quantization` to create INT8 and INT4 adapters.
  - Generate multiple images for each level.
  - **Model Integrity Check (T015)**: If LPIPS > 0.8 or Similarity < 0.1, flag as 'CatastrophicCollapse' and skip. If `torch.ao.quantization` fails, flag as 'BackendUnavailable' and skip.
  - **Output**: `data/generated/int8/`, `data/generated/int4/`, `data/results/quantized_metrics.csv`.

- **T006: Compute Normalized CESR (T013)**
  - Calculate `CESR_raw` (similarity to other effect references).
  - Calculate `CESR_baseline` (mean similarity to Distractor References from T004).
  - Compute `CESR_normalized = CESR_raw - CESR_baseline`.
  - **Output**: `data/results.csv` (includes `cesr_baseline`, `cesr_normalized`).

### Phase 2: Statistical Analysis
*Goal: Perform Bayesian analysis and descriptive correlation.*

- **T007: Bayesian Hierarchical Model**
  - Model `similarity_score` ~ Normal(μ, σ) with `μ` ~ Effect(quantization_level).
  - Test for significant differences in adherence across levels.
  - **Output**: `data/analysis_results.json` (quantization effects).

- **T008: Descriptive Correlation (T021)**
  - Aggregate `CESR_normalized` to the **effect level** (mean per effect).
  - Correlate aggregated bleeding with `SourceRank` (from T001).
  - **Note**: N=5 effects is **underpowered** for significance. This is a **descriptive** trend analysis.
  - **Output**: `data/analysis_results.json` (correlation coefficient, CI).

- **T009: Power & Stability Check (T022)**
  - Calculate ESS for correlation coefficient.
  - **Flag**: If ESS < 200 (expected for N=5), set `status` = 'Underpowered'.
  - **Output**: `data/analysis_results.json` (power_flag).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Synthetic Adapter Construction** | Public `stabilityai/collection-lora` does not exist. | Using a single-effect LoRA would fail FR-007 (correlation across effects) and FR-011 (CESR). Merging 5 verified open LoRAs or procedural generation is the only way to satisfy the multi-effect requirement. |
| **Bayesian Hierarchical Model** | N=10 prompts is too small for ANOVA. | Frequentist ANOVA would lack power; Bayesian approach with informative priors (FR-012) allows valid inference with small N. |
| **CPU-First Quantization** | No GPU available on free-tier runner. | Running on a local GPU is not reproducible by CI; `torch.ao.quantization` on CPU is the only reproducible path. |
| **Normalized CESR** | Raw CESR confounds bleeding with general fidelity loss. | Distractor baseline (T004) isolates specific cross-effect interference. |
| **Descriptive Correlation** | N=5 effects is statistically insufficient for significance. | Acknowledging the 'Underpowered' flag (T009) is more honest than forcing a false significance test. |

## Execution Order & Resource Constraints

- **Sequential Dependencies**:
  - T001 (Load/SVD) → T002 (Merge) → T003 (Baseline) → T004 (Distractors) → T005 (Quantization).
  - **Critical Note for T005 (Quantization)**: T005 **must** execute after T001c and T002 are complete. The quantization process (`torch.ao.quantization`) requires the merged adapter to be fully loaded and the SVD ranks to be computed. Attempting to run T005 before T002 may result in OOM errors or invalid weight matrices. The `[Foundational]` tag on T005 does not imply parallel execution with T002; it implies T005 is a foundational step for the *analysis*, but it is **sequentially dependent** on Phase 0 completion.