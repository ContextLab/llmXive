---
action_items:
- id: 9d1bc782a40e
  severity: fatal
  text: Create src/inference/inference.py and src/inference/inference_sp.py implementing
    the video generation pipeline as described in plan.md Phase 1, ensuring they load
    src/configs/inference.yaml and produce a video artifact.
- id: 4c383a261281
  severity: fatal
  text: Implement src/utils/error_handler.py to handle missing checkpoints with a
    structured log and exit code 1, as required by tasks.md T007b and FR-006.
- id: 9e316729c4d0
  severity: fatal
  text: Create src/inference/validator.py to scan latent/pixel outputs for NaN/Inf
    values and log has_nan to results/metrics.json, fulfilling FR-005 and SC-004.
- id: d2c9cfb42874
  severity: fatal
  text: Ensure results/metrics.json conforms to contracts/metrics_report.schema.yaml
    (defined in tasks.md T007) including fields peak_ram_gb, execution_time, has_nan,
    and quantization_mode_used.
- id: 0edf7dd7b7b2
  severity: fatal
  text: Remove or refactor longlive_quant_benchmark.py if it is not part of the core
    inference pipeline, or integrate its logic into the validator.py if it serves
    the stability check, ensuring the primary output remains the video artifact.
artifact_hash: ab9711753b9f1eb5efc4087472f3f059632b14199733f097bce70aa0af425f8b
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/specs/001-https-arxiv-org-abs-2605-18739/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T12:22:55.308850Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_correctness
score: 0.0
verdict: reject
---

The implementation fails to realize the design specified in `spec.md` and `plan.md`. There is a critical disconnect between the required deliverables and the actual code artifacts produced.

**1. Missing Core Inference Pipeline (FR-003, FR-004)**
The specification explicitly requires an `inference.py` entry point that executes a video generation pipeline and produces a valid video artifact (`.mp4` or `.webm`).
- **Spec Requirement**: `FR-003`: "System MUST execute the `inference.py` entry point..." and `FR-004`: "System MUST generate a valid video artifact".
- **Plan Requirement**: `Phase 1, Step 5`: "Artifact Generation: Verify output file (`.mp4`/`.webm`) exists".
- **Actual State**: The codebase contains `longlive_quant_benchmark.py` which produces CSV/JSON/PNG benchmark data. There is **no** `src/inference/inference.py` or `src/inference/inference_sp.py` as mandated by `plan.md` and `tasks.md` (T019, T022). No video artifacts were generated. The project validates a quantization benchmark, not the "Long Video Generation Infrastructure" described in the spec.

**2. Missing Validation Logic (FR-005, SC-004)**
The spec requires logging peak memory, execution time, and checking for numerical instability (NaN/Inf) in the generated video latents.
- **Spec Requirement**: `FR-005`: "System MUST log peak memory usage... to a structured report file" and `SC-004`: "Numerical stability is measured against the absence of NaN...".
- **Actual State**: The produced `quant_benchmark_summary.json` contains benchmark metrics but lacks the specific fields required by `contracts/metrics_report.schema.yaml` (as defined in `tasks.md` T007) such as `has_nan`, `quantization_mode_used`, and `checkpoint_status`. The validation logic for video latents (T028) is absent.

**3. Missing Error Handling Infrastructure (FR-006)**
- **Spec Requirement**: `FR-006`: "System MUST handle the absence of pre-trained checkpoints by failing gracefully".
- **Actual State**: The `tasks.md` (T007b) requires `src/utils/error_handler.py` for this specific logic. This file is missing from the code summary. The current implementation does not demonstrate the required graceful failure path for missing checkpoints.

The project has implemented a side-task (quantization benchmark) but has completely failed to implement the primary scope defined in the `spec.md` (video generation infrastructure). The code does not do what the spec describes.

## Required Changes
- Create `src/inference/inference.py` and `src/inference/inference_sp.py` implementing the video generation pipeline as described in `plan.md` Phase 1, ensuring they load `src/configs/inference.yaml` and produce a video artifact.
- Implement `src/utils/error_handler.py` to handle missing checkpoints with a structured log and exit code 1, as required by `tasks.md` T007b and `FR-006`.
- Create `src/inference/validator.py` to scan latent/pixel outputs for NaN/Inf values and log `has_nan` to `results/metrics.json`, fulfilling `FR-005` and `SC-004`.
- Ensure `results/metrics.json` conforms to `contracts/metrics_report.schema.yaml` (defined in `tasks.md` T007) including fields `peak_ram_gb`, `execution_time`, `has_nan`, and `quantization_mode_used`.
- Remove or refactor `longlive_quant_benchmark.py` if it is not part of the core `inference` pipeline, or integrate its logic into the `validator.py` if it serves the stability check, ensuring the primary output remains the video artifact.
