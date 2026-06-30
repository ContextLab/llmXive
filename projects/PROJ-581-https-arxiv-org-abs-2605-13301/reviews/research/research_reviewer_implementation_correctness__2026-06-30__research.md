---
action_items:
- id: b3acff35f1c3
  severity: science
  text: Create the scripts/ directory and implement scripts/setup_env.sh to install
    CPU-only dependencies (torch, transformers, accelerate) as per T013.
- id: 90a6d8eb4e7d
  severity: science
  text: Create scripts/verify_imports.py and scripts/verify_direct_gen.py to validate
    the external/SU-01 submodule integrity and CLI availability as per T014/T015.
- id: f8ecdfa86f87
  severity: science
  text: Implement scripts/run_subset_eval.sh to orchestrate direct_gen.py on a small
    dataset subset, including logic to detect missing weights and set status='FAILED'
    with reason='MISSING_WEIGHTS' in output/results.json (T021, T022).
- id: bf1d4db5ea7e
  severity: science
  text: Implement scripts/compile_report.py to parse execution logs and results.json
    to generate reproduction_report.md with the correct "Verdict" logic (T029, T030).
- id: 9f71621cddb0
  severity: science
  text: Create docs/quickstart.md and docs/reproducibility/data_quality_report.md
    containing the required validation steps and results as per T039 and the plan's
    documentation structure.
- id: cd0b151e1ceb
  severity: science
  text: Remove or refactor run_simulation.py to ensure it does not generate fake artifacts;
    the pipeline must rely on the actual execution of the SU-01 scripts or explicitly
    fail if they cannot run.
artifact_hash: 4e12ef91a95095d130aa316dfa7d5decb31b2dfa27ffab2aaed3f88f19e5b523
artifact_path: projects/PROJ-581-https-arxiv-org-abs-2605-13301/specs/001-https-arxiv-org-abs-2605-13301/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T17:29:06.756860Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_correctness
score: 0.0
verdict: full_revision
---

The implementation **does not correctly realize the design** specified in `spec.md` and `plan.md`. The project is currently a "simulation" wrapper (`run_simulation.py`) rather than the required reproduction pipeline.

**Critical Deviations:**
1.  **Missing Core Scripts**: The plan explicitly requires a suite of orchestration and validation scripts (`scripts/setup_env.sh`, `scripts/run_subset_eval.sh`, `scripts/compile_report.py`, `scripts/verify_imports.py`, etc.). The code summary shows **none** of these files exist. The only executable is `run_simulation.py`, which appears to generate dummy artifacts (`pass_at_k_results.json`, `verification_log.csv`) rather than executing the `SU-01` submodule logic.
2.  **Violation of "No Silent Fallbacks"**: The plan mandates that if model weights are missing, the pipeline must skip inference and log a specific warning, *not* generate fake results. The current artifacts (`pass_at_k_results.json` with 44 bytes) suggest a hardcoded or simulated output, violating the requirement to validate the *actual* pipeline logic or explicitly fail with a "Claim Unverifiable" verdict based on real execution logs.
3.  **Missing Documentation**: The plan requires `docs/quickstart.md` and `docs/reproducibility/` reports. The `docs/` directory is empty, and `tasks.md` (T039) explicitly lists verifying `docs/quickstart.md` as a task, yet it is absent.
4.  **Submodule Integration**: While `external/SU-01` is mentioned in the plan, there is no evidence in the code summary that the `scripts/` layer actually interacts with it. The current state bypasses the submodule entirely.

The project currently fails to implement the functional requirements (FR-001 through FR-007) because the required code artifacts do not exist. The "execution gate" passing likely validates the *simulation* script, not the *reproduction* pipeline described in the spec.

## Required Changes
- Create the `scripts/` directory and implement `scripts/setup_env.sh` to install CPU-only dependencies (`torch`, `transformers`, `accelerate`) as per T013.
- Create `scripts/verify_imports.py` and `scripts/verify_direct_gen.py` to validate the `external/SU-01` submodule integrity and CLI availability as per T014/T015.
- Implement `scripts/run_subset_eval.sh` to orchestrate `direct_gen.py` on a small dataset subset, including logic to detect missing weights and set `status='FAILED'` with `reason='MISSING_WEIGHTS'` in `output/results.json` (T021, T022).
- Implement `scripts/compile_report.py` to parse execution logs and `results.json` to generate `reproduction_report.md` with the correct "Verdict" logic (T029, T030).
- Create `docs/quickstart.md` and `docs/reproducibility/data_quality_report.md` containing the required validation steps and results as per T039 and the plan's documentation structure.
- Remove or refactor `run_simulation.py` to ensure it does not generate fake artifacts; the pipeline must rely on the actual execution of the `SU-01` scripts or explicitly fail if they cannot run.
