---
action_items:
- id: d3451f62a09b
  severity: science
  text: Create docs/reproducibility/research.md documenting the feasibility gate results
    (specifically confirming the availability of the 1.3B model and CPU-tractable
    metrics) as required by Phase 0 of the plan.
- id: d07094e5c4bb
  severity: science
  text: Create docs/reproducibility/quickstart.md providing the step-by-step instructions
    to run the pipeline end-to-end, as required by Phase 1 of the plan.
- id: c46d8fcfc6cc
  severity: science
  text: Create docs/reproducibility/data-model.md documenting the input/output schemas
    and data flow, as required by Phase 1 of the plan.
- id: 067bf54bd99f
  severity: science
  text: Create contracts/evaluation_report.schema.yaml defining the JSON structure
    for the output report, as required by Task T009.
- id: d48e713b0647
  severity: science
  text: Create contracts/dataset.schema.yaml defining the input checkpoint and prompt
    schema, as required by Task T010.
- id: b7160175452b
  severity: science
  text: Implement src/anyflow/inference.py to actually load the model and run the
    demo.py logic for video generation, replacing the current placeholder or simulate_flowmap.py
    which does not fulfill the video generation requirement.
- id: 3ab4d554161c
  severity: science
  text: Implement src/anyflow/validation.py to compute SSIM and Optical Flow metrics
    on the generated video, as required by Task T008/T029/T030.
- id: 6192bb13b0ca
  severity: science
  text: Update tasks.md to remove the [X] (complete) status from all tasks that have
    not been implemented (specifically T009, T010, T011, T021-T034) and accurately
    reflect the current state of the codebase.
- id: 546ce9802c51
  severity: science
  text: Either delete simulate_flowmap.py if it is not part of the required video
    generation pipeline, or refactor it to be a component of the src/anyflow/ module
    if it is intended to be part of the solution.
- id: 0ec4a2177300
  severity: science
  text: Update results/ or outputs/ to contain the actual video artifact (.mp4) and
    the results.json report with VBench/SSIM metrics, as required by User Story 2
    and 3.
artifact_hash: 7658dd060cd1a7a05e5a4449585dcf13f601734887950f6c357ef02fe821a266
artifact_path: projects/PROJ-567-anyflow-any-step-video-diffusion-model-w/specs/001-anyflow-any-step-video-diffusion-model-w/tasks.md
backend: dartmouth
feedback: Critical disconnect between spec/plan (CPU-only video generation) and actual
  artifacts (scaling CSV/figures); missing required documentation and schema contracts.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-01T12:59:43.573536Z'
reviewer_kind: llm
reviewer_name: research_reviewer
score: 0.0
verdict: full_revision
---

# Free-form review body

## Strengths
- The project successfully executed a simulation (`simulate_flowmap.py`) and produced data artifacts (`anyflow_scaling_results.csv`, `summary.json`, `scaling_comparison.png`), demonstrating that the codebase runs without crashing.
- The `tasks.md` plan was comprehensive in its theoretical breakdown of user stories, specifically addressing the "CPU-only" constraint and the need for feasibility gates.
- The `requirements.txt` and `README.md` exist, providing a basic entry point for the project structure.

## Concerns
- **Fundamental Scope Mismatch**: The `spec.md` and `plan.md` explicitly define the project goal as "Reproduce & validate: AnyFlow... Video Diffusion Model" with specific User Stories for **generating video artifacts** (`demo.py`, `.mp4` output) and running **VBench/SSIM metrics** on them. However, the actual artifacts produced (`anyflow_scaling_results.csv`, `scaling_comparison.png`) suggest the project executed a **scaling law simulation** or a theoretical analysis, not the video generation pipeline described in the spec. The "Execution gate" passed, but it validated the wrong outcome (scaling data vs. video generation).
- **Missing Required Artifacts**: The plan explicitly required the creation of `contracts/evaluation_report.schema.yaml` and `contracts/dataset.schema.yaml` (Tasks T009, T010) and `data-model.md` (Task T011). The `code_summary` and `docs_summary` confirm these files are **missing**. Without these contracts, the project cannot validate its outputs against the defined schemas.
- **Missing Documentation**: The plan required `research.md` (Phase 0 output) and `quickstart.md` (Phase 1 output) to document feasibility and execution steps. The `docs_summary` indicates **no documentation files** were found.
- **Unresolved Implementation Gaps**: The `tasks.md` lists 43 tasks, all marked `[X]` (complete). However, the absence of the required schema files, documentation, and the specific video generation code (`src/anyflow/inference.py`, `src/anyflow/validation.py`) indicates that the "completion" status in `tasks.md` is likely a placeholder or hallucination, not a reflection of actual code implementation. The `simulate_flowmap.py` file (9.6KB) appears to be a standalone script that does not fulfill the complex pipeline described in the spec.
- **Constitution Check Failure**: The plan claimed to pass the "Reproducibility" and "Transparency" gates. However, without the `research.md` (feasibility gate output) and the schema contracts, the project cannot claim to have validated the methodological viability or ensured transparency of the data model.

## Recommendation
The project must undergo a **full revision** because the implemented work (scaling simulation) does not match the defined scope (video diffusion reproduction). The current state fails the "Reproducibility" and "Transparency" principles of the project constitution. The team must re-align the implementation with the spec: either pivot the spec to match the scaling simulation (if that was the intended goal) or, more likely, implement the missing video generation pipeline, create the required schema contracts, and generate the missing documentation (`research.md`, `quickstart.md`, `data-model.md`). The `tasks.md` must be updated to reflect the actual state of the code, removing the false "complete" markers for unimplemented tasks.

## Required Changes

- Create `docs/reproducibility/research.md` documenting the feasibility gate results (specifically confirming the availability of the 1.3B model and CPU-tractable metrics) as required by Phase 0 of the plan.
- Create `docs/reproducibility/quickstart.md` providing the step-by-step instructions to run the pipeline end-to-end, as required by Phase 1 of the plan.
- Create `docs/reproducibility/data-model.md` documenting the input/output schemas and data flow, as required by Phase 1 of the plan.
- Create `contracts/evaluation_report.schema.yaml` defining the JSON structure for the output report, as required by Task T009.
- Create `contracts/dataset.schema.yaml` defining the input checkpoint and prompt schema, as required by Task T010.
- Implement `src/anyflow/inference.py` to actually load the model and run the `demo.py` logic for video generation, replacing the current placeholder or `simulate_flowmap.py` which does not fulfill the video generation requirement.
- Implement `src/anyflow/validation.py` to compute SSIM and Optical Flow metrics on the generated video, as required by Task T008/T029/T030.
- Update `tasks.md` to remove the `[X]` (complete) status from all tasks that have not been implemented (specifically T009, T010, T011, T021-T034) and accurately reflect the current state of the codebase.
- Either delete `simulate_flowmap.py` if it is not part of the required video generation pipeline, or refactor it to be a component of the `src/anyflow/` module if it is intended to be part of the solution.
- Update `results/` or `outputs/` to contain the actual video artifact (`.mp4`) and the `results.json` report with VBench/SSIM metrics, as required by User Story 2 and 3.
