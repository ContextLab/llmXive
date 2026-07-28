# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure (`code/`, `data/`, `tests/`, `data/raw/`, `data/processed/`, `data/stimuli/`, `data/ethics/`) is present or described in the provided artifacts; the implementer only supplied a textual specification without creating any of the required folders or files.
- **T003** — No linting or formatting configuration artifacts (e.g., .flake8, pyproject.toml, or pre‑commit setup) were provided; the evidence consists only of a unrelated feature specification, so the requirement to configure flake8 and black is not satisfied.
- **T012** — No stimulus‑generation script, CSV files, or randomisation code were supplied; consequently there is no evidence that “Partner” and “Tool” vignettes are produced from a controlled template, nor that participants are assigned to conditions with the required 50/50 split. The implementer must provide the actual script(s) and example output files to satisfy the task.
- **T016** — declared artifact(s) missing/empty/invalid: data/stimuli/vignettes_partner.csv, data/stimuli/vignettes_tool.csv
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/randomization_log.json
- **T025** — The required file `data/processed/pilot_validation_report.json` does not exist, so no validation results have been logged as the task demands. The implementer must generate the pilot study validation output and save it at the specified path.
- **T021** — No code, script, or data file was provided that implements or demonstrates the `manipulation_check_failed` boolean logic. Without an artifact showing the flagging mechanism, the requirement is not satisfied.
- **T022** — No code, script, configuration file, or documentation was provided that shows logic for detecting and removing partial responses from the dataset. The only material present is the original feature specification; there is no artifact demonstrating the required exclusion functionality.
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_responses.csv
