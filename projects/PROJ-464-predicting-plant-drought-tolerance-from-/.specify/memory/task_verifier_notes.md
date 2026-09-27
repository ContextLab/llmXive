# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — No schema files or validation code were provided in a `contracts/` directory; the only material shown is a feature specification and user stories, which do not constitute the required data validation schema checks. The deliverable is missing.
- **T024b** — The `fit_pgl` function in `code/models.py` is still a placeholder that raises `NotImplementedError`, and the required output file `data/derived/pgls_results.csv` (as well as the input tree file `data/derived/phylogenetic_tree.newick`) are missing. The task’s core implementation and deliverables have not been provided.
- **T026** — declared artifact(s) missing/empty/invalid: data/derived/model_results.csv
- **T026b** — The repository lacks the required `state/vif_compliance_check.yaml` file, so the VIF compliance check output is missing. Moreover, the provided `generate_report.py` is truncated and does not demonstrate the implementation of the framing logic that suppresses independent effect claims when VIF > 5. Both the artifact and the required behavior are absent.
- **T030** — declared artifact(s) missing/empty/invalid: state/vif_compliance_check.yaml
- **T029** — declared artifact(s) missing/empty/invalid: data/derived/sensitivity_report.md
- **T032a** — No README.md content was provided; there is no evidence that the file was created or updated to include Installation, Usage, and Results sections as required. The implementer must supply the updated README.md showing those sections.
- **T032b** — No evidence of any files under `docs/` was provided; the implementer did not supply an API documentation file or a quickstart guide, so the required documentation update is missing.
- **T033** — No code, commit logs, diff, or documentation showing that any cleanup or refactoring was performed are present; the only artifacts described relate to functional user stories, not to the required code‑quality improvements. Consequently, there is no evidence that the “code cleanup and refactoring” task was actually completed.
