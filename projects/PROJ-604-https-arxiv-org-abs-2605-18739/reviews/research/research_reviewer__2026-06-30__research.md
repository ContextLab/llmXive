---
action_items:
- id: a9b553ef0e8a
  severity: science
  text: Create src/inference/inference.py implementing the end-to-end video generation
    pipeline that loads a text prompt, executes the diffusion model (with NVFP4 fallback
    if applicable), and writes a valid .mp4 or .webm file to outputs/.
- id: e38514b8f2cd
  severity: science
  text: Create src/inference/inference_sp.py implementing the sequence parallelism
    fallback to handle memory constraints on the 7GB RAM limit, as required by FR-007.
- id: 06e23d9d2d3e
  severity: science
  text: Create src/inference/validator.py to scan latent and pixel outputs for NaN/Inf
    values and generate the results/metrics.json file conforming to contracts/metrics_report.schema.yaml.
- id: 48f7e8bf3815
  severity: science
  text: Create docs/reproducibility/validation_report.md documenting the hardware
    constraints (CPU vs. Blackwell), the specific sequence length used (2-4 frames),
    and the explicit limitation that "Long Video" claims are unverified, as mandated
    by the plan's "Limitations" section.
- id: 2461492059d4
  severity: science
  text: Update tasks.md to reflect the actual implementation status or re-assign the
    missing tasks (inference.py, inference_sp.py, validator.py) to the implementer
    for immediate execution.
artifact_hash: ab9711753b9f1eb5efc4087472f3f059632b14199733f097bce70aa0af425f8b
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/specs/001-https-arxiv-org-abs-2605-18739/tasks.md
backend: dartmouth
feedback: Critical mismatch between spec (LongLive-2.0 video inference) and implementation
  (quantization benchmark); missing required artifacts and documentation.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T12:21:43.910869Z'
reviewer_kind: llm
reviewer_name: research_reviewer
score: 0.0
verdict: full_revision
---

# Free-form review body

## Strengths
- The project successfully executed a code path (`longlive_quant_benchmark.py`) and produced numerical artifacts (CSV, JSON, PNG), demonstrating that the environment is functional and the code runs without crashing.
- The `requirements.txt` and basic project structure appear to be in place, satisfying the initial environment setup requirements.

## Concerns
- **Fundamental Scope Mismatch**: The `spec.md` and `plan.md` explicitly define a project to "Reproduce & Validate LongLive-2.0 NVFP4 **Infrastructure**" for **Long Video Generation**. The requirements (FR-003, FR-004) mandate an `inference.py` script that generates a video artifact (`.mp4`/`.webm`) from a text prompt. The actual implementation (`longlive_quant_benchmark.py`) and outputs (`quant_benchmark_results.csv`, `quant_benchmark_comparison.png`) are limited to a **quantization benchmark** (likely comparing precision modes) and do not perform video generation.
- **Missing Core Artifacts**: The project failed to produce the primary deliverable defined in the spec: a generated video file. The `results/` directory contains benchmark data, not the `metrics.json` or video artifacts required by `User Story 2` and `User Story 3`.
- **Missing Documentation**: The `plan.md` explicitly requires the creation of `docs/reproducibility/` files (e.g., `data_quality_report.md`, `hyperbolic_volume_validation.md` or equivalent validation reports) to satisfy the "Constitution Check" and "Reproducibility" gates. The `docs summary` indicates no documentation files were found.
- **Plan vs. Execution Gap**: The `tasks.md` lists specific tasks for `inference.py`, `inference_sp.py`, and `validator.py` (T019, T022, T028). None of these files appear in the `code summary`. The implementation appears to have skipped the entire "Inference Pipeline" and "Validation" phases, focusing only on a preliminary benchmark.

## Recommendation
The project must undergo a **full revision**. The current implementation validates a side-effect (quantization math) but fails to address the core research question: the ability to run the LongLive-2.0 infrastructure for video generation. The spec requires a video generation pipeline, sequence parallelism handling, and specific validation reports, none of which are present. The team must re-implement the `inference.py` and `inference_sp.py` scripts, generate the required video artifacts, and produce the missing reproducibility documentation before the project can be considered for acceptance.

## Required Changes

- Create `src/inference/inference.py` implementing the end-to-end video generation pipeline that loads a text prompt, executes the diffusion model (with NVFP4 fallback if applicable), and writes a valid `.mp4` or `.webm` file to `outputs/`.
- Create `src/inference/inference_sp.py` implementing the sequence parallelism fallback to handle memory constraints on the 7GB RAM limit, as required by `FR-007`.
- Create `src/inference/validator.py` to scan latent and pixel outputs for NaN/Inf values and generate the `results/metrics.json` file conforming to `contracts/metrics_report.schema.yaml`.
- Create `docs/reproducibility/validation_report.md` documenting the hardware constraints (CPU vs. Blackwell), the specific sequence length used (2-4 frames), and the explicit limitation that "Long Video" claims are unverified, as mandated by the plan's "Limitations" section.
- Update `tasks.md` to reflect the actual implementation status or re-assign the missing tasks (`inference.py`, `inference_sp.py`, `validator.py`) to the implementer for immediate execution.
