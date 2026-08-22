# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T070** — No `specs/001-evaluating-llm-generated-c/research.md` file containing the statistical methodology appendix is present, nor is there any signed‑off version placed in the `data/` directory as a pre‑registered protocol. The required documentation and its inclusion are missing.
- **T021a** — The repository contains a partially implemented `calculate_cyclomatic_complexity` function, but there is no code that iterates over candidate repositories, writes the results to `data/raw/repo_cc_raw.json`, nor does the file `data/raw/repo_cc_raw.json` exist. Consequently the required output file is missing and the task is not fulfilled.
- **T021b** — The repository lacks any implementation that runs `cloc --json` and writes results to `data/raw/repo_loc_raw.json`, and the expected output file is absent. Consequently the required LOC collection and verification are not present.
- **T021c** — The repository lacks the required `data/raw/doc_quality_scores.json` file, and the shown `code/validation.py` does not contain any function that computes the binary presence of Setup, API, and Architecture sections or writes those scores to the specified JSON output. The task’s core functionality and output are therefore missing.
- **T021f** — declared artifact(s) missing/empty/invalid: data/raw/repo_loc_raw.json, data/raw/repo_cc_raw.json, data/raw/repo_selection_rubric.json, data/raw/repo_matching_report.json
- **T016** — declared artifact(s) missing/empty/invalid: data/raw/participant_logs.json
- **T018** — declared artifact(s) missing/empty/invalid: data/raw/participant_logs.json
- **T019** — The required output file `data/raw/participant_logs.json` is missing, so no evidence exists that incomplete records were handled, dropout counts calculated, or status flags were added. The task’s core artifact is absent.
- **T020** — declared artifact(s) missing/empty/invalid: data/raw/participant_logs.json
- **T028** — No code, configuration, or logs were provided that implement the required fallback to the local CPU‑optimized phi (int4) model, pin it to a specific HuggingFace commit, or record generation config and checksums. The evidence consists only of the task description and spec excerpt, which does not satisfy the implementation requirement.
- **T030a** — declared artifact(s) missing/empty/invalid: data/raw/schema_temp.json
