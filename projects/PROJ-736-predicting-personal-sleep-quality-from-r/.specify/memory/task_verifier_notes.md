# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — The required output file `data/raw/behavioral/hcp1200_behavioral_data.csv` does not exist, and the provided `download_hcp.py` contains only placeholder logic (e.g., a stub URL, comments about missing credentials, and no implemented checksum verification or CIFTI download). Hence the task’s requirements are not met.
- **T006** — The provided `code/data/preprocess.py` is truncated and contains placeholder logic: `load_cifti` deliberately raises a RuntimeError instead of loading data, `apply_schaefer_parcellation` ends abruptly with an unfinished line, and there are no implementations for nuisance regression or the 0.01‑0.1 Hz band‑pass filter. Consequently the required functionality is not present.
