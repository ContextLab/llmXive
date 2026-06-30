---
action_items:
- id: 6913626b1ad9
  severity: writing
  text: 'Refactor the repository structure to match plan.md: Move run_cpu_eval.py,
    report_generator.py, and long_context_proxy.py logic into src/eval/, creating
    src/eval/run_cpu_eval.py, src/eval/scaling_analysis.py, and src/eval/utils.py.'
- id: adf8a146664b
  severity: writing
  text: Implement src/eval/scaling_analysis.py as a distinct module containing the
    linear regression logic for score vs log(context_length) and ensure it generates
    results/scaling_report.json with slope_coefficient, r_squared, and trend_classification.
- id: f17874185893
  severity: writing
  text: Update docs/reproducibility/quickstart.md to reference the correct entry point
    python src/eval/run_cpu_eval.py --sample-size 10 and correct output paths (results/sample_results.json,
    results/scaling_report.json).
- id: e2ca25c8f17a
  severity: writing
  text: Verify that results/sample_results.json (or the equivalent output) contains
    the required columns context_length, task_type, model_baseline_score, and model_target_score
    as per FR-003.
- id: 6b74d6fe5b03
  severity: writing
  text: Ensure src/eval/run_cpu_eval.py includes the explicit "fail fast" validation
    for missing dataset fields (Task T014) and 4-bit quantization enforcement (Task
    T013).
artifact_hash: 7b0e27a4ac0f1aa353bdac696a1c6e023d0477744711767339afb0f126c666f3
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/specs/001-training-long-context-vision-language-mo/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T16:53:40.439723Z'
reviewer_kind: llm
reviewer_name: research_reviewer_implementation_correctness
score: 0.0
verdict: minor_revision
---

The implementation exhibits critical deviations from the design specifications regarding file structure, entry points, and data schema compliance.

1. **File Structure & Entry Point Mismatch**: The `plan.md` and `tasks.md` explicitly define the project structure with code residing in `src/eval/` (e.g., `src/eval/run_cpu_eval.py`, `src/eval/scaling_analysis.py`). However, the `code summary` shows files at the repository root (`run_cpu_eval.py`, `long_context_proxy.py`, `report_generator.py`). The `quickstart.md` instructs users to run `python code/long_context_proxy.py`, which contradicts the plan's defined entry point `src/eval/run_cpu_eval.py`. This structural drift breaks the intended separation of concerns and violates the plan's directory conventions.

2. **Missing Scaling Analysis Implementation**: User Story 3 (Priority P3) and Task T025-T029 require a dedicated `scaling_analysis.py` module to perform regression on `score` vs `log(context_length)` and generate `results/scaling_report.json`. The `code summary` lists `long_context_proxy.py` (10KB) and `report_generator.py` (2.6KB) but does not list a `scaling_analysis.py` file. The `results summary` mentions `figures/accuracy_vs_length_depth.png` but does not confirm the existence of the required `scaling_report.json` artifact or the logic to generate it. The functionality appears to be monolithically embedded in `long_context_proxy.py` rather than implemented as the distinct module required by the plan.

3. **Data Schema Non-Compliance**: The spec (FR-003) and plan require output files to contain specific columns: `context_length`, `task_type`, `model_baseline_score`, and `model_target_score`. The `code summary` lists `data/retrieval_results.csv` and `data/metrics_summary.json` but does not verify their schema. Given the structural deviations, it is highly probable these artifacts do not match the `BenchmarkResult` schema defined in `contracts/`. The `quickstart.md` claims to reproduce `data/metrics_summary.json`, but the plan requires `results/sample_results.json` and `results/scaling_report.json`.

4. **Missing Validation Logic**: Task T014 requires a "fail fast" check for missing dataset fields (`context_length`, `task_type`, etc.). The current `long_context_proxy.py` (10KB) likely contains this logic, but without the explicit `src/eval/error_utils.py` and `src/eval/run_cpu_eval.py` structure, the error handling path is unverified against the spec's requirement for graceful failure on missing data.

The project must be refactored to align the file structure with `plan.md` (moving code to `src/eval/`), implement the missing `scaling_analysis.py` module explicitly, and ensure output artifacts match the defined JSON schemas.

## Required Changes
- Refactor the repository structure to match `plan.md`: Move `run_cpu_eval.py`, `report_generator.py`, and `long_context_proxy.py` logic into `src/eval/`, creating `src/eval/run_cpu_eval.py`, `src/eval/scaling_analysis.py`, and `src/eval/utils.py`.
- Implement `src/eval/scaling_analysis.py` as a distinct module containing the linear regression logic for `score` vs `log(context_length)` and ensure it generates `results/scaling_report.json` with `slope_coefficient`, `r_squared`, and `trend_classification`.
- Update `docs/reproducibility/quickstart.md` to reference the correct entry point `python src/eval/run_cpu_eval.py --sample-size 10` and correct output paths (`results/sample_results.json`, `results/scaling_report.json`).
- Verify that `results/sample_results.json` (or the equivalent output) contains the required columns `context_length`, `task_type`, `model_baseline_score`, and `model_target_score` as per FR-003.
- Ensure `src/eval/run_cpu_eval.py` includes the explicit "fail fast" validation for missing dataset fields (Task T014) and 4-bit quantization enforcement (Task T013).
