# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The required `data/raw/uci_citation_verified.json` file does not exist, and the YAML file updates the wrong key (`citation_verification` instead of `uci_citation_verified`) and lack the required URL field. There is also no evidence that the Reference-Validator Agent was used. The task therefore fails to meet the specified artifacts and schema.
- **T001** — I looked for the required directory tree and the `tree_manifest.json` file that should contain a JSON list of absolute paths, but no such directories or manifest file are present in the provided evidence. The task’s core deliverable is missing.
- **T007** — No evidence of the three required directories (`data/raw/`, `data/simulated/`, `data/results/`) or the `.gitkeep` placeholder files is provided; without visible artifacts the task’s requirement is not satisfied.
- **T017** — The required `data/results/simulation.log` file does not exist, and the YAML project state file lacks the `artifact_hashes` entry with a SHA‑256 checksum for the log. Consequently the logging output and checksum recording mandated by the task are missing.
