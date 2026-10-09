# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure or file listing is provided as evidence; without seeing the created folders (e.g., `code/01_data_collection`, `data/raw/human_samples`, etc.) we cannot confirm the required project layout exists. The implementer must supply a manifest or screenshot showing the directories have been created.
- **T004** — The `code/utils/config.py` file does not define or export a `FALSE_POSITIVE_THRESHOLD` constant, nor does it expose a `RANDOM_SEED` variable (it only provides a `get_random_seed()` function and a `"random_seed"` entry in `DEFAULT_CONFIG`). The required pinned reference set SHA is also absent. These missing definitions mean the task’s verification criteria are not satisfied.
- **T022.5** — declared artifact(s) missing/empty/invalid: code/02_static_analysis/generate_reference_set.py, data/raw/reference_set/, state/projects/PROJ-514-evaluating-the-impact-of-code-generation.yaml
- **T012.5** — declared artifact(s) missing/empty/invalid: code/01_data_collection/export_task_descriptions.py, data/raw/api_logs.json, data/raw/human_samples/, data/intermediate/tasks.json
- **T042** — declared artifact(s) missing/empty/invalid: code/utils/fail_loud_loader.py
- **T045** — declared artifact(s) missing/empty/invalid: tests/unit/test_bonferroni_correction.py, data/intermediate/stat_results.json
- **T046** — declared artifact(s) missing/empty/invalid: tests/contract/test_pmd_ruleset_validation.py
