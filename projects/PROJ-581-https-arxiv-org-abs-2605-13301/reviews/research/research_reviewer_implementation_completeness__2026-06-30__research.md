---
action_items:
- id: 03a4df11f76f
  severity: science
  text: Create the external/ directory structure and initialize the external/SU-01
    git submodule as per FR-001, ensuring the su01-eval and su01-train-slime directories
    are present.
- id: 8284c4993585
  severity: science
  text: Implement scripts/setup_env.sh to install CPU-only dependencies (torch, transformers,
    accelerate) and verify no CUDA imports occur, replacing the current simulation
    approach.
- id: caf04855fc8d
  severity: science
  text: Implement scripts/run_subset_eval.sh to orchestrate the inference on a 2-problem
    subset, including the logic to check for model weights and set status='FAILED'
    with reason='MISSING_WEIGHTS' if absent (per T022).
- id: b8d8b49ec5b7
  severity: science
  text: Implement scripts/compile_report.py to parse execution logs and results.json
    to generate reproduction_report.md with the required "Verdict" field (per T029,
    T030).
- id: ffd4625c4873
  severity: science
  text: Create docs/quickstart.md and docs/reproducibility/data_quality_report.md
    containing the pipeline validation steps and results, as required by T039 and
    the plan's documentation structure.
- id: 9e3aae8b2b6c
  severity: science
  text: Remove run_simulation.py and replace it with the actual pipeline scripts,
    ensuring the output/ directory is populated by real execution artifacts rather
    than static placeholders.
artifact_hash: 4e12ef91a95095d130aa316dfa7d5decb31b2dfa27ffab2aaed3f88f19e5b523
artifact_path: projects/PROJ-581-https-arxiv-org-abs-2605-13301/specs/001-https-arxiv-org-abs-2605-13301/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T17:29:44.211526Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_completeness
score: 0.0
verdict: full_revision
---

The implementation is **incomplete** relative to the claimed scope in `spec.md` and `plan.md`. The project currently consists of a single simulation script (`run_simulation.py`) and placeholder data files, but it lacks the entire orchestration layer required to validate the SU-01 pipeline as specified.

**Critical Missing Components:**
1.  **Orchestration Scripts**: The plan explicitly requires `scripts/setup_env.sh`, `scripts/run_subset_eval.sh`, `scripts/compile_report.py`, `scripts/verify_imports.py`, and `scripts/fetch_sample_dataset.py`. None of these exist. The current `run_simulation.py` appears to be a mock/simulation rather than the actual pipeline integration required by FR-001 through FR-007.
2.  **Submodule Integration**: `spec.md` (FR-001) and `plan.md` require the initialization of the `external/SU-01` git submodule. The `code_summary` shows no `external/` directory, meaning the core codebase to be validated is missing.
3.  **Documentation Artifacts**: `plan.md` and `tasks.md` (T039) require `docs/quickstart.md` and a `docs/reproducibility/` directory with specific reports. The `docs/` directory is empty.
4.  **Verification Logic**: The plan mandates specific logic to detect missing model weights and set `status='FAILED'` with `reason='MISSING_WEIGHTS'` (T022, T030). This logic is absent; the current artifacts (`pass_at_k_results.json`) are static placeholders (44 bytes) and do not reflect a dynamic evaluation pipeline.

The advisory comment correctly identifies that the implementation does not match the design. The project is currently a "simulation" of the result, not an implementation of the reproduction pipeline. To meet the research-stage bar, the actual scripts must be written to attempt the submodule fetch, environment setup, and conditional execution flow described in the plan.

## Required Changes

- Create the `external/` directory structure and initialize the `external/SU-01` git submodule as per FR-001, ensuring the `su01-eval` and `su01-train-slime` directories are present.
- Implement `scripts/setup_env.sh` to install CPU-only dependencies (`torch`, `transformers`, `accelerate`) and verify no CUDA imports occur, replacing the current simulation approach.
- Implement `scripts/run_subset_eval.sh` to orchestrate the inference on a 2-problem subset, including the logic to check for model weights and set `status='FAILED'` with `reason='MISSING_WEIGHTS'` if absent (per T022).
- Implement `scripts/compile_report.py` to parse execution logs and `results.json` to generate `reproduction_report.md` with the required "Verdict" field (per T029, T030).
- Create `docs/quickstart.md` and `docs/reproducibility/data_quality_report.md` containing the pipeline validation steps and results, as required by T039 and the plan's documentation structure.
- Remove `run_simulation.py` and replace it with the actual pipeline scripts, ensuring the `output/` directory is populated by real execution artifacts rather than static placeholders.
