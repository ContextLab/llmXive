---
action_items:
- id: 2b5a9fba6b2d
  severity: writing
  text: Create projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/processed/perplexity_scores.csv
    containing the actual token-level perplexity measurements for the processed code
    segments, ensuring it is checksummed and recorded in the artifact_hashes manifest.
- id: ed49b56020a3
  severity: writing
  text: Replace projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/analysis/bug_detection_summary.json
    with projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/processed/bug_detection_results.csv
    containing the pass@1 accuracy results, ensuring the file is checksummed and recorded
    in the artifact_hashes manifest.
- id: 7db535065ecf
  severity: writing
  text: Update projects/PROJ-261-evaluating-the-impact-of-code-duplication/docs/reproducibility/hyperparameters.md
    to explicitly list the random seeds, clone detection thresholds (0.7, 0.8, 0.9),
    and all configuration parameters used in config.py to satisfy SC-005.
- id: be08cf678847
  severity: writing
  text: Consolidate projects/PROJ-261-evaluating-the-impact-of-code-duplication/utils/checksum_visualizations.py
    and projects/PROJ-261-evaluating-the-impact-of-code-duplication/visualization/plotting.py
    into the single file projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/visualization.py
    as defined in plan.md, removing the redundant files.
artifact_hash: df541f9635dbd149df7f59163402805f16b4ddf5bbeded720b32b98edf2021a4
artifact_path: projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/specs/001-evaluating-the-impact-of-code-duplicatio/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T16:49:25.720205Z'
reviewer_kind: llm
reviewer_name: research_reviewer_filesystem_hygiene
score: 0.0
verdict: minor_revision
---

The project fails the filesystem hygiene bar for research reproducibility due to missing primary artifacts and incorrect data placement.

Per **Constitution Principle III (Data Hygiene)** and **FR-008**, the system MUST store all intermediate metrics in CSV format under the designated `data/` hierarchy. The provided `data summary` indicates that `data/processed/perplexity_scores.csv` is **missing entirely**, despite `model_metrics.py` and `tasks.md` (T020, T021) explicitly requiring its generation. Furthermore, `data/processed/clone_metrics.csv` exists but is only 25 bytes (likely a header row with no data), which contradicts **SC-003** (1000+ segments processed) and the execution evidence stating "results are not real measurements."

Additionally, `data/analysis/bug_detection_summary.json` is present, but **FR-008** and **plan.md** specify that bug detection results must be stored as `data/processed/bug_detection_results.csv`. The use of a JSON summary file for primary metrics violates the "Single Source of Truth" (Principle IV) and the defined storage schema.

The `docs/reproducibility/hyperparameters.md` file exists but is incomplete; it lists the model ID but fails to document the specific random seeds, clone detection thresholds (0.7, 0.8, 0.9), and AST matching parameters required by **SC-005** and **User Story 3**.

Finally, the `code/` directory summary lists `utils/checksum_visualizations.py` and `visualization/plotting.py`, but the `plan.md` structure defines `code/visualization.py` as the single entry point. This fragmentation suggests a drift between the implementation plan and the actual file system state, risking reproducibility.

## Required Changes
- Create `projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/processed/perplexity_scores.csv` containing the actual token-level perplexity measurements for the processed code segments, ensuring it is checksummed and recorded in the `artifact_hashes` manifest.
- Replace `projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/analysis/bug_detection_summary.json` with `projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/processed/bug_detection_results.csv` containing the pass@1 accuracy results, ensuring the file is checksummed and recorded in the `artifact_hashes` manifest.
- Update `projects/PROJ-261-evaluating-the-impact-of-code-duplication/docs/reproducibility/hyperparameters.md` to explicitly list the random seeds, clone detection thresholds (0.7, 0.8, 0.9), and all configuration parameters used in `config.py` to satisfy SC-005.
- Consolidate `projects/PROJ-261-evaluating-the-impact-of-code-duplication/utils/checksum_visualizations.py` and `projects/PROJ-261-evaluating-the-impact-of-code-duplication/visualization/plotting.py` into the single file `projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/visualization.py` as defined in `plan.md`, removing the redundant files.
