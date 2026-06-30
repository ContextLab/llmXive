---
action_items:
- id: a1e0dc7ffa60
  severity: science
  text: Create src/inference/inference.py implementing the end-to-end video generation
    pipeline as defined in spec.md User Story 2, ensuring it accepts a text prompt
    and outputs a valid .mp4 or .webm file.
- id: abe1314d82ac
  severity: science
  text: Create src/inference/inference_sp.py implementing sequence parallelism logic
    to manage memory usage within the 7GB RAM limit, as required by spec.md FR-007.
- id: 1ce38d97fff4
  severity: science
  text: Implement checkpoint validation logic in src/inference/inference.py that raises
    a structured FileNotFoundError and logs to logs/error.log if pre-trained weights
    are missing, fulfilling spec.md FR-006.
- id: 2d86fbeb6f24
  severity: science
  text: Create src/inference/validator.py to scan latent and pixel outputs for NaN/Inf
    values and log peak_ram_gb, execution_time, and has_nan to results/metrics.json
    conforming to contracts/metrics_report.schema.yaml.
- id: 537b7e95cab1
  severity: science
  text: Remove or refactor longlive_quant_benchmark.py to serve strictly as a utility
    within the new pipeline, ensuring the primary entry point is the video generation
    script, not a static benchmark.
artifact_hash: ab9711753b9f1eb5efc4087472f3f059632b14199733f097bce70aa0af425f8b
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/specs/001-https-arxiv-org-abs-2605-18739/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T12:23:11.961003Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_completeness
score: 0.0
verdict: full_revision
---

The implementation is **incomplete** relative to the claimed scope defined in `spec.md` and `plan.md`. The project claims to reproduce the "LongLive-2.0 NVFP4 Infrastructure for Long Video Generation," yet the delivered code (`longlive_quant_benchmark.py`) and artifacts (`quant_benchmark_results.csv`, `quant_benchmark_comparison.png`) only perform a static quantization benchmark.

The following critical components mandated by the specification are entirely missing:
1.  **Inference Pipeline**: `spec.md` (User Story 2, FR-003, FR-004) requires an `inference.py` script that executes an end-to-end pipeline to generate a video artifact (`.mp4`/`.webm`). The current codebase lacks this script and the associated video generation logic.
2.  **Sequence Parallelism**: `spec.md` (FR-007) and `plan.md` (Phase 1, Step 4) require `inference_sp.py` to handle memory constraints on the 7GB runner. This file is absent.
3.  **Validation Logic**: `spec.md` (User Story 3, FR-005) requires logging peak memory, execution time, and NaN checks to `results/metrics.json`. The current `quant_benchmark_summary.json` does not conform to this requirement, nor does it validate the *generation* pipeline.
4.  **Error Handling**: `spec.md` (FR-006) requires explicit handling for missing checkpoints. The current implementation does not demonstrate this path.

The advisory comment correctly identifies a "Fundamental Scope Mismatch." The current work validates a *component* (quantization math) but fails to implement the *system* (video generation infrastructure) described in the spec. The project cannot advance until the full inference pipeline, including video artifact generation and memory management, is implemented.

## Required Changes
- Create `src/inference/inference.py` implementing the end-to-end video generation pipeline as defined in `spec.md` User Story 2, ensuring it accepts a text prompt and outputs a valid `.mp4` or `.webm` file.
- Create `src/inference/inference_sp.py` implementing sequence parallelism logic to manage memory usage within the 7GB RAM limit, as required by `spec.md` FR-007.
- Implement checkpoint validation logic in `src/inference/inference.py` that raises a structured `FileNotFoundError` and logs to `logs/error.log` if pre-trained weights are missing, fulfilling `spec.md` FR-006.
- Create `src/inference/validator.py` to scan latent and pixel outputs for NaN/Inf values and log `peak_ram_gb`, `execution_time`, and `has_nan` to `results/metrics.json` conforming to `contracts/metrics_report.schema.yaml`.
- Remove or refactor `longlive_quant_benchmark.py` to serve strictly as a utility within the new pipeline, ensuring the primary entry point is the video generation script, not a static benchmark.
