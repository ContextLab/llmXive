# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — The provided `code/power_analysis.py` is truncated and does not contain the full logic for fetching species from both NPPN/MGB3 and TRY, computing the sample size with `FTestPower`, nor halting with the required error when N < 55. Additionally, the required output file `state/power_analysis_report.yaml` is absent. Both the implementation and the deliverable report are missing.
- **T015** — declared artifact(s) missing/empty/invalid: data/derived/rsametrics.csv
- **T024a** — The required output file `data/derived/phylogenetic_tree.newick` does not exist, so the script’s primary deliverable is missing. Consequently the task’s requirement is not satisfied.
- **T024b** — The repository lacks a `fit_pgl()` implementation in `code/models.py` (the file is truncated and does not contain the required function), and the required input file `data/derived/phylogenetic_tree.newick` is missing. Both the core function and its necessary data are absent, so the task is not satisfied.
- **T026** — declared artifact(s) missing/empty/invalid: data/derived/model_results.csv
- **T026b** — The repository contains `code/generate_report.py` with functions to load VIF results and generate framing text, but the file never writes the required `state/vif_compliance_check.yaml`. Moreover, that YAML file is missing from the project, so the required output artifact does not exist. The task’s requirement to record VIF status and suppression actions in `state/vif_compliance_check.yaml` is therefore unmet.
