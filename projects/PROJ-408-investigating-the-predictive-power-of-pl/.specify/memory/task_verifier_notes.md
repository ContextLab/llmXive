# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — The only artifact is the `scripts/setup_project.py` source file; there is no evidence that the script was actually run (e.g., execution logs, created directory listings, or a timestamped marker). Without proof that the repository structure was initialized, the task requirement is not satisfied.
- **T002** — The provided `requirements.txt` contains all required package names, but it does not pin them to specific versions (e.g., `biopython==1.79`). The task explicitly calls for “pinned Python dependencies,” so version specifications are missing. Adding exact version numbers for each package is needed to satisfy the requirement.
- **T002a** — No installation logs, command outputs, or scripts are present to demonstrate that `mafft` and `fasttree` (or the fallback `fasttree-mt`) were installed via `apt-get` and that their versions were verified in the PATH. Without such artifacts, the requirement cannot be confirmed.
- **T003** — The provided `pyproject.toml` config includes `F401` but does not list `ANN001`, and there is no `ruff.toml` file at all. Consequently the required enforcement of both `F401` and `ANN001` is not satisfied. Adding `ANN001` to the `select` list (or creating a `ruff.toml` with both codes) is needed.
- **T008** — declared artifact(s) missing/empty/invalid: code/validate_env.py
- **T009** — declared artifact(s) missing/empty/invalid: data/raw/species_list.txt, scripts/fetch_species_list.py
- **T011a** — declared artifact(s) missing/empty/invalid: data/raw/test_species_10.txt
- **T011b** — declared artifact(s) missing/empty/invalid: data/raw/test_species_10.txt, data/processed/test_tree.newick
- **T037a** — declared artifact(s) missing/empty/invalid: data/processed/runtime_metrics.json
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/phylo_dist_matrix.csv, data/processed/climate_dist_matrix.csv, data/processed/partial_mantel_results.json
- **T030** — declared artifact(s) missing/empty/invalid: code/viz.py
- **T031** — declared artifact(s) missing/empty/invalid: code/viz.py
- **T029** — declared artifact(s) missing/empty/invalid: tests/contract/baselines/phylo_metabolite_heatmap.png
- **T034a** — declared artifact(s) missing/empty/invalid: docs/README.md
- **T034b** — declared artifact(s) missing/empty/invalid: docs/quickstart.md
