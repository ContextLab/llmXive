---
action_items:
- id: 2439a050e145
  severity: writing
  text: 'Update docs/reproducibility/quickstart.md to correct all file paths: change
    code/requirements.txt to requirements.txt (or src/requirements.txt if moved),
    and change code/long_context_proxy.py to the correct entry point src/eval/run_cpu_eval.py
    (or long_context_proxy.py if that is the intended root-level entry, but ensure
    consistency with plan.md).'
- id: 80720c9c3047
  severity: writing
  text: Update docs/reproducibility/quickstart.md to reflect the correct data loading
    procedure as defined in plan.md (Phase 0), removing instructions for manual file
    placement and instead referencing the automated datasets.load_dataset call or
    the correct script that performs this action.
- id: feb36ed16a80
  severity: writing
  text: Update docs/reproducibility/quickstart.md to reference the correct output
    artifacts (results/sample_results.json, results/evaluation_run.json) as defined
    in plan.md (Phase 1) instead of data/metrics_summary.json, or clarify the relationship
    between these files if metrics_summary.json is a derived summary.
- id: ab89c5831bd4
  severity: writing
  text: Ensure the README.md (if it contains similar instructions) is also updated
    to match the corrected paths and entry points.
artifact_hash: 7b0e27a4ac0f1aa353bdac696a1c6e023d0477744711767339afb0f126c666f3
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/specs/001-training-long-context-vision-language-mo/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T16:55:06.349297Z'
reviewer_kind: llm
reviewer_name: research_reviewer_filesystem_hygiene
score: 0.0
verdict: minor_revision
---

The project exhibits critical filesystem hygiene defects that break the "reproducibility from a clean checkout" requirement. The `docs/reproducibility/quickstart.md` file contains instructions that are inconsistent with the actual project structure and file locations, rendering the reproduction guide non-functional.

**Specific Defects:**

1.  **Incorrect Directory Paths in Quickstart**: The `docs/reproducibility/quickstart.md` file instructs the user to run `pip install -r code/requirements.txt` and `python code/long_context_proxy.py`. However, the `code/` directory does not exist in the project root. The actual files are located at the root level (`requirements.txt`, `long_context_proxy.py`) or within `src/` (e.g., `src/eval/run_cpu_eval.py` as per `plan.md`). This discrepancy prevents a user from following the guide successfully.

2.  **Entry Point Mismatch**: The quickstart guide directs execution to `code/long_context_proxy.py`. While `long_context_proxy.py` exists at the root, the `plan.md` and `tasks.md` explicitly define `src/eval/run_cpu_eval.py` as the primary entry point for the CPU evaluation pipeline (Task T012). The guide fails to reference the correct, spec-compliant entry point, leading to potential confusion and execution of a potentially incomplete or proxy script instead of the main evaluation logic.

3.  **Inconsistent Data Path Instructions**: The quickstart guide states, "Ensure the dataset files are downloaded and placed there [data/ directory]." While `data/` exists, the `plan.md` (Phase 0) specifies using `datasets.load_dataset` to fetch data into a local cache, not manual placement. The guide's instruction implies a manual process that contradicts the automated data loading strategy defined in the plan, potentially causing the script to fail if the user attempts to manually place files that the script expects to be in a specific cache format or location.

4.  **Missing Artifact Path Verification**: The guide claims to reproduce metrics found in `data/metrics_summary.json`. While this file exists, the `plan.md` (Phase 1) specifies outputting to `results/sample_results.json` and `results/evaluation_run.json`. The guide references a file (`metrics_summary.json`) that appears to be an intermediate or legacy artifact, not the primary output defined in the design documents. This creates ambiguity about which file represents the "official" result.

These defects constitute a blocking issue for filesystem hygiene because they prevent the project from being reproducible via its own documentation. The paths and entry points must be aligned with the actual file structure and the design specifications.

## Required Changes

- Update `docs/reproducibility/quickstart.md` to correct all file paths: change `code/requirements.txt` to `requirements.txt` (or `src/requirements.txt` if moved), and change `code/long_context_proxy.py` to the correct entry point `src/eval/run_cpu_eval.py` (or `long_context_proxy.py` if that is the intended root-level entry, but ensure consistency with `plan.md`).
- Update `docs/reproducibility/quickstart.md` to reflect the correct data loading procedure as defined in `plan.md` (Phase 0), removing instructions for manual file placement and instead referencing the automated `datasets.load_dataset` call or the correct script that performs this action.
- Update `docs/reproducibility/quickstart.md` to reference the correct output artifacts (`results/sample_results.json`, `results/evaluation_run.json`) as defined in `plan.md` (Phase 1) instead of `data/metrics_summary.json`, or clarify the relationship between these files if `metrics_summary.json` is a derived summary.
- Ensure the `README.md` (if it contains similar instructions) is also updated to match the corrected paths and entry points.
