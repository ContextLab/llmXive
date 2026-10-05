# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — No `run_inference.py` file or modifications are presented, and there is no evidence of added error‑handling logic, logging of CodeCarbon failures, or prompt‑skipping behavior. The required artifact is missing, so the task is not satisfied.
- **T013** — declared artifact(s) missing/empty/invalid: data/raw/codexglue_sample.json
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/llm_inference_results.json
- **T015** — No code, test files, or documentation were presented showing that validation logic was added to filter out failed or empty‑string code generations, nor any test coverage confirming this behavior. The required artifact (implementation and its tests) is missing.
- **T018** — The required `data/processed/llm_inference_results.json` file is missing, so the joining logic cannot be executed, and no evidence of a completed `calculate_emissions.py` implementation is provided. The task therefore does not meet its stated requirement.
- **T019** — No evidence of a modified `calculate_emissions.py` containing LOC‑counting logic is present; the claim provides no code, diff, or file content to verify that the required functionality was implemented. The required artifact is missing.
- **T020** — No `calculate_emissions.py` file or code snippet was provided, and there is no evidence that the human baseline CO₂ calculation (using the mean of the reported time range and a standard laptop power model) has been implemented. The required artifact is missing, so the task is not satisfied.
- **T021** — No code, script, or data file implementing the normalization step was supplied, nor any generated table containing `prompt_id`, `loc_count`, `llm_co2_per_loc`, and `human_co2_per_loc`. Without these artifacts, we cannot confirm that the required `co2_per_loc` calculations for both LLM and human baselines have been implemented. The next implementer must add the normalization logic and provide the resulting output artifact.
