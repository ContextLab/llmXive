# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T047** — No SHA‑256 hash values, no logs of two pipeline runs, and no `data/` or `state/` directories with identical files are present. The required evidence that the pipeline was executed twice with the same seed and that all output hashes match is missing.
- **T049** — No audit artifacts (e.g., file inventory, generation logs, or verification scripts) are present to demonstrate that `data/raw/` contains only generated files and that `data/processed/` and `data/results/` are derived exclusively from `data/raw/`. The required evidence is missing.
- **T051** — No `state/projects/PROJ-866-...yaml` file (or its contents) was provided, and thus there is no evidence that the required `reproducibility_hash` and `final_verification_timestamp` fields were added. The implementer must supply the updated YAML file with those entries.
- **T057** — The required output file `data/results/vif_report.json` does not exist, and the provided `tradeoff_model.py` snippet ends before any code that actually computes VIF and writes the JSON report, so the task’s reporting requirement is not fulfilled.
