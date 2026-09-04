# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory listings, `os.path.isdir` checks, or other concrete evidence of the required folders (`projects/PROJ-268-the-impact-of-network-centrality-on-neur/` and its sub‑directories) were provided. Without visible proof that these paths exist, the task requirement is not satisfied.
- **T001c** — The required file `projects/PROJ-268-the-impact-of-network-centrality-on-neur/code/requirements.txt` does not exist, and there is no evidence that `pip install -r requirements.txt` was run or succeeded. The task’s core deliverable is therefore missing.
- **T001d** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or Black settings) or related setup scripts are present in `projects/PROJ-268-the-impact-of-network-centrality-on-neur/code/`. Without these artifacts, the task of configuring ruff/flake8 and Black has not been demonstrated.
- **T006** — declared artifact(s) missing/empty/invalid: data/results/processing.log
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No code, configuration file, or documentation was provided showing that error handling has been added to raise fatal errors when a “Data Gap” or “Storage Limit Exceeded” condition occurs. The claim lacks any tangible artifact (e.g., updated script, settings file, or test demonstrating the behavior).
- **T012b** — No preprocessing script, pipeline code, or generated 400 × 400 structural and functional connectivity matrices are present. The claim provides only a textual description; there is no evidence of raw NIfTI detection, Schaefer‑atlas parcellation, or any output files in `data/processed`. The required artifacts are missing, so the task is not satisfied.
- **T017** — declared artifact(s) missing/empty/invalid: data/results/processing_summary.json
- **T023** — No CSV files named `centrality_<subject_id>.csv` or `synchrony_<subject_id>.csv` are present in the `data/processed` directory, nor any evidence (e.g., file listings, content snippets) that such per‑subject outputs were generated. The required artifacts are missing.
- **T024** — No code, test, or documentation was presented that adds a dimension‑matching check for structural (SC) and functional (FC) connectivity matrices, nor any error handling that halts execution on mismatch. The required validation artifact is missing.
