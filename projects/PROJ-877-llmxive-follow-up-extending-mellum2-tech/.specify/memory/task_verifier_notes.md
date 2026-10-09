# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided evidence only includes `pyproject.toml`, `requirements.txt`, and `ruff.toml`; the required `.gitignore`, `README.md`, `.env.template` files and the full directory hierarchy are missing. Moreover, the configuration values do not match the task specifications (`ruff.toml` targets Python 3.10 instead of 3.11, and `pyproject.toml` requires Python >=3.9 rather than >=3.11). The implementer must add the missing files/directories and correct the config values.
- **T002** — The provided `requirements.txt` lists the required packages but does not include exact version numbers for any of them, contrary to the task’s specification. Additionally, it contains extra packages not requested, but the critical failure is the absence of pinned versions.
- **T018a** — declared artifact(s) missing/empty/invalid: code/data/ngram.py, data/processed/kenlm_model_python.arpa
- **T018b** — declared artifact(s) missing/empty/invalid: code/data/ngram.py, data/processed/kenlm_model_java.arpa
- **T027** — declared artifact(s) missing/empty/invalid: data/results/us2_threshold_report.md
- **T029** — declared artifact(s) missing/empty/invalid: code/analysis/stats.py, data/results/us3_permutation_pvalue.json
- **T030** — declared artifact(s) missing/empty/invalid: data/results/us3_corrected_pvalues.json
- **T031** — declared artifact(s) missing/empty/invalid: data/results/us3_validation_result.json, data/results/us3_limitation_report.md
- **T032b** — declared artifact(s) missing/empty/invalid: docs/api.md
- **T035** — declared artifact(s) missing/empty/invalid: tests/unit/test_edge_cases.py
