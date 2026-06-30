---
action_items:
- id: 1f032ccbba57
  severity: science
  text: Create the directory structure src/inference/, src/utils/, src/configs/, src/scripts/,
    and contracts/ as defined in plan.md.
- id: 14e400c589b4
  severity: science
  text: Implement src/inference/inference.py and src/inference/inference_sp.py to
    handle the video generation pipeline, including checkpoint validation (FR-006)
    and pre-flight memory estimation (Plan Phase 1, Step 3).
- id: f11653cd58df
  severity: science
  text: Implement src/inference/validator.py to scan latent/pixel frames for NaN/Inf
    values and log metrics to results/metrics.json conforming to contracts/metrics_report.schema.yaml.
- id: 8481e22c89aa
  severity: science
  text: Create src/configs/inference.yaml and src/configs/inference_nvfp4.yaml with
    the required parameters for synthetic data generation and quantization modes.
- id: c5e93caa3d6c
  severity: science
  text: Create contracts/inference_output.schema.yaml and contracts/metrics_report.schema.yaml
    to define the validation schemas for artifacts and metrics.
- id: fbae4161dc21
  severity: science
  text: Implement src/utils/error_handler.py to handle missing checkpoints gracefully
    (FR-006) and log structured errors.
- id: aab8e8a5fb4d
  severity: science
  text: Remove or refactor longlive_quant_benchmark.py to integrate with the new modular
    structure, ensuring it does not duplicate logic or bypass the required configuration
    and validation steps.
artifact_hash: ab9711753b9f1eb5efc4087472f3f059632b14199733f097bce70aa0af425f8b
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/specs/001-https-arxiv-org-abs-2605-18739/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T12:23:32.930853Z'
reviewer_kind: llm
reviewer_name: research_reviewer_code_quality_research
score: 0.0
verdict: full_revision
---

The project exhibits a critical structural disconnect between the implementation plan and the actual code artifacts, rendering the research un-reproducible and the codebase non-compliant with the spec.

**1. Missing Core Implementation Modules**
The `spec.md` and `plan.md` explicitly mandate the creation of `src/inference/inference.py`, `src/inference/inference_sp.py`, `src/inference/validator.py`, and `src/utils/error_handler.py` to handle the video generation pipeline, sequence parallelism, and numerical stability checks. The provided code summary lists only `longlive_quant_benchmark.py` (7.8KB) and `requirements.txt`. The absence of the entire `src/` directory structure defined in `plan.md` (Phase 1, Phase 2, Phase 3 tasks) means the core scientific method (video generation infrastructure validation) has not been implemented. The existing `longlive_quant_benchmark.py` appears to be a standalone script that does not integrate with the required configuration management, checkpoint handling, or artifact generation logic described in the spec.

**2. Truncation and Incomplete File Structure**
The single file `longlive_quant_benchmark.py` (7806 bytes) is insufficient to contain the logic for environment initialization, pre-flight memory estimation, sequence parallelism fallback, and video artifact generation required by User Stories 1, 2, and 3. If this file was intended to be a monolithic implementation, it is severely truncated or incomplete, as it lacks the necessary imports, class definitions, and control flow for the specified pipeline. The plan explicitly calls for splitting logic into `inference.py`, `inference_sp.py`, and `validator.py` to manage complexity and memory; the current state fails to reflect this decomposition.

**3. Missing Configuration and Contract Artifacts**
The spec requires `src/configs/inference.yaml`, `src/configs/inference_nvfp4.yaml`, and contract schemas in `contracts/`. The code summary shows no `src/` or `contracts/` directories. Without these configuration files, the system cannot be parameterized for the "synthetic video prompt" or "NVFP4 fallback" scenarios required for reproducibility. The `quant_benchmark_results.csv` and `quant_benchmark_summary.json` in the `data/` directory do not conform to the `contracts/metrics_report.schema.yaml` defined in the plan (which requires `peak_ram_gb`, `has_nan`, `quantization_mode_used`), indicating a failure to implement the required data contracts.

**4. Reproducibility Failure**
A clean checkout of this repository would fail to run the `inference.py` entry point or the `setup_env.sh` script because the referenced files do not exist. The project cannot be reproduced on a CPU-only runner as the necessary infrastructure code is missing.

## Required Changes
- Create the directory structure `src/inference/`, `src/utils/`, `src/configs/`, `src/scripts/`, and `contracts/` as defined in `plan.md`.
- Implement `src/inference/inference.py` and `src/inference/inference_sp.py` to handle the video generation pipeline, including checkpoint validation (FR-006) and pre-flight memory estimation (Plan Phase 1, Step 3).
- Implement `src/inference/validator.py` to scan latent/pixel frames for NaN/Inf values and log metrics to `results/metrics.json` conforming to `contracts/metrics_report.schema.yaml`.
- Create `src/configs/inference.yaml` and `src/configs/inference_nvfp4.yaml` with the required parameters for synthetic data generation and quantization modes.
- Create `contracts/inference_output.schema.yaml` and `contracts/metrics_report.schema.yaml` to define the validation schemas for artifacts and metrics.
- Implement `src/utils/error_handler.py` to handle missing checkpoints gracefully (FR-006) and log structured errors.
- Remove or refactor `longlive_quant_benchmark.py` to integrate with the new modular structure, ensuring it does not duplicate logic or bypass the required configuration and validation steps.
