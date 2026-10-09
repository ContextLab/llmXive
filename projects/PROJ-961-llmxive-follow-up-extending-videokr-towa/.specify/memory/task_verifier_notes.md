# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The provided `code/utils/config.py` file exists and contains seed and path utilities, but it does **not** define a `sensitivity_thresholds` variable (list of integers defaulting to `[2, 3, 4]`) as required by the task specification. Adding this variable (and optionally exposing it via the config) is needed to satisfy the requirement.
- **T007** — The provided `code/utils/entity_linker.py` defines an `EntityLinker` with simple string‑based similarity, but it never inspects an input dataset for a `node_id` or `entity_id` column nor skips linking when such columns exist. The `main()` function is empty, and no function accepts a DataFrame to perform the required conditional logic. Consequently, the script does not fulfill the task’s core requirement.
- **T009** — The provided `checksum.py` defines helper functions but its `main()` is empty, so it cannot be invoked as a utility script, and `verify_all_raw_data` expects a list of checksum entries yet `generate_checksum_file` writes a single dict, causing a runtime error. The script therefore does not fulfill the requirement of a runnable integrity‑verification utility.
- **T013b** — declared artifact(s) missing/empty/invalid: data/processed/annotated_videokr.csv, data/processed/annotation_coverage.tmp.json, data/processed/annotation_coverage.json
- **T031c** — declared artifact(s) missing/empty/invalid: mypy.ini
- **T031a** — declared artifact(s) missing/empty/invalid: data/processed/lint_log.txt
- **T031b** — declared artifact(s) missing/empty/invalid: data/processed/type_log.txt
- **T038** — declared artifact(s) missing/empty/invalid: code/analysis/generate_narrative.py, data/processed/threshold_results.json, data/processed/stability_metric.json, data/processed/sensitivity_summary.md, data/processed/final_report.md, data/processed/narrative.md
