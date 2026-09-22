# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or other evidence of the requested folder hierarchy are provided; the claim alone does not prove that the `src/...`, `data/...`, and `tests/...` directories were actually created. The implementer must supply a manifest (e.g., `tree` output or a list of created paths) showing that all specified directories exist.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, or similar) are present in the provided evidence, nor any scripts or documentation showing that ruff and black have been set up. Without these artifacts, the requirement to configure linting and formatting tools is not satisfied.
- **T003b** — No updated `spec.md` content is provided; the claim that FR-003 has been changed and the Llama-3-8B exclusion removed cannot be verified without the actual file showing those edits. The required artifact (the modified specification) is missing.
- **T004a** — declared artifact(s) missing/empty/invalid: data/results/ground_truth_validation.json
- **T005** — The provided `src/utils/verify_citations.py` is truncated (ends mid‑function without closing braces, error handling, iteration over DOIs, or JSON writing) and no `data/results/citation_report.json` file was generated. The required end‑to‑end citation verification and report output are therefore missing.
- **T007** — declared artifact(s) missing/empty/invalid: src/utils/resource_monitor.py
- **T008** — declared artifact(s) missing/empty/invalid: src/utils/hash_artifacts.py
- **T016b** — declared artifact(s) missing/empty/invalid: data/results/extraction_memory_log.json
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/features.jsonl
- **T018** — The required output file `data/results/distinctiveness_stats.csv` is missing, so no Mann‑Whitney U test results, corrections, or significance flags have been logged. The implementer must generate the CSV with the specified columns and apply the appropriate multiple‑testing correction.
- **T018b** — declared artifact(s) missing/empty/invalid: data/results/distinctiveness_report.md
- **T021a** — declared artifact(s) missing/empty/invalid: data/processed/error_schema.json
- **T021b** — The `src/modeling/oracle.py` file exists but its content is truncated and we cannot see the full implementation that writes the validation report. Moreover, the required output file `data/results/oracle_validation.json` is missing, so the script has not produced the mandated validation report. The task’s core requirement is therefore not satisfied.
- **T022** — declared artifact(s) missing/empty/invalid: src/modeling/dataset.py, data/processed/triplets.jsonl
