# Implementation Plan: llmXive follow-up: extending "Visual Generation in the New Era: An Evolution from Atomic Mapping to "

**Branch**: `001-llmxive-followup` | **Date**: 2026-07-11 | **Spec**: `spec.md`

## Summary
This project implements a CPU-tractable experimental pipeline to evaluate whether "Symbolic-Physics" prompts improve **2D Geometric Coherence** (defined as adherence to machine-generated 2D projection constraints) in diffusion model generations. The system simulates basic physics using `pymunk` on a single CPU core to generate JSON constraints (bounding boxes, collision rules), appends natural language descriptors to text prompts, and generates images using a distilled CPU-optimized diffusion model (LCM-LoRA). The study compares three groups: () Text-only Baseline, (2) Text + Physics Descriptors (Experimental), and (3) Text + Random Noise (Length-Matched Control). Evaluation uses `YOLOvn` to measure the alignment between generated 2D bounding boxes and the `pymunk`-derived ground truth. The primary outcome is "Prompt Adherence Rate" (1 - Violation Rate), analyzed via two-proportion z-test.

*Note: This study measures **Instruction Adherence** relative to a 2D projection ground truth, not 3D physical reality. The metric is explicitly defined as "2D Geometric Coherence" to acknowledge the limitations of 2D detection against 3D generation.*

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymunk`, `diffusers` (CPU-compatible), `torch` (CPU-only), `ultralytics` (YOLOv8n), `scikit-learn`, `pandas`, `numpy`, `pyyaml`  
**Storage**: Local file system with explicit sub-structure:
- `data/raw/`: Input scene descriptions (immutable).
- `data/derived/`: Intermediate artifacts (physics JSON, prompts, images, evaluation results).
- `data/processed/`: Final aggregated statistics.
**Testing**: `pytest` (unit/contract tests), manual verification of JSON schema and image generation.  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 CPU, ~7GB RAM, No GPU, ≤6h).  
**Project Type**: Computational Research Pipeline / CLI  
**Performance Goals**: Complete N=100 per group (300 total generations) within 6 hours on CPU; memory usage < 6.5 GB.  
**Constraints**: No CUDA/GPU; no quantization requiring `bitsandbytes`; strict seed locking; deterministic evaluation.  
**Scale/Scope**: A fixed number of scenes per group (a defined total of generations), a corresponding set of JSON constraints, and images. (N=500 is deferred to paid compute).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/`; `requirements.txt` pins versions; data fetched from local `data/` or canonical sources; no global state. |
| **II. Verified Accuracy** | **Compliant** | All citations (datasets, models) will be validated against primary sources; no hallucinated URLs in `research.md`. |
| **III. Data Hygiene** | **Compliant** | Raw data (scene descriptions) preserved; derivations (physics JSON, images) written to new files; checksums recorded in state. |
| **IV. Single Source of Truth** | **Compliant** | Final statistics trace to `data/` CSV/JSON; no hand-typed numbers in reports; `code/` is the sole generator of results. |
| **V. Versioning Discipline** | **Compliant** | **Workflow**: A post-processing script `code/utils/update_state.py` runs after each pipeline phase. It calculates SHA-256 hashes of all artifacts in `data/derived/` and `data/processed/`, updates the `artifact_hashes` map in `state/...yaml`, and sets the `updated_at` timestamp. |
| **VI. Symbolic Physics Grounding** | **Compliant** | Physics constraints generated strictly by `pymunk` (JSON); natural language descriptors are deterministic translations of JSON fields. |
| **VII. Deterministic Geometric Evaluation** | **Compliant** | Evaluation uses `YOLOv8n` + rule-based comparison against JSON; no subjective human judgment or model-internal state reliance. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── physics-constraint.schema.yaml
│   └── evaluation-result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-820-llmxive-follow-up-extending-visual-gener/
├── data/
│   ├── raw/
│   │   └── scene_descriptions.csv      # Input: A set of scene descriptions
│   ├── derived/
│   │   ├── physics_constraints/        # Output: A set of JSON files
│   │   ├── prompts/                    # Output: A set of prompt files organized into three groups.
│   │   ├── generated_images/           # Output: A set of images (3 groups)
│   │   └── evaluation_results/         # Output: A dataset of JSON/CSV records documenting violations
│   └── processed/
│       └── final_analysis.csv          # Output: Aggregated stats for paper
├── code/
│   ├── __init__.py
│   ├── simulation/
│   │   ├── __init__.py
│   │   └── physics_engine.py           # pymunk logic, JSON generation
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── prompt_engine.py            # Prompt construction (Baseline/Exp/Control)
│   │   └── diffusion_runner.py         # CPU-optimized model inference
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── detector.py                 # YOLOv8n wrapper, violation logic
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── statistics.py               # Z-test, power analysis
│   ├── utils/
│   │   └── update_state.py             # Versioning workflow script
│   └── main.py                         # Orchestration script
├── tests/
│   ├── contract/
│   │   └── test_schemas.py             # Validates JSON against contracts
│   ├── integration/
│   │   └── test_pipeline.py            # End-to-end small run
│   └── unit/
│       └── test_physics_logic.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with modular `code/` subdirectories (`simulation`, `generation`, `evaluation`, `analysis`) to separate concerns and facilitate independent testing of the physics engine, diffusion runner, and detector. This aligns with the computational pipeline nature of the research.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Matched Control Group** | To isolate the effect of physics content from prompt length/complexity. | A simple text-only baseline confounds prompt length with content. |
| **LCM-LoRA** | Required to meet 6h CPU deadline for N=100. Standard SD is too slow. | Standard SD-2.1 would exceed the 6h limit even for N=100. |
| **2D Coherence Metric** | Only feasible automated metric for CPU pipeline. | Multi-view reconstruction is computationally intractable for this scale. |
| **N=100** | Feasible within 6h on Free Tier. | N=500 exceeds free-tier compute limits. |