# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No artifact showing a `data/raw/` directory was provided; the evidence section contains no files or directory listings to confirm that the required folder exists. Without concrete proof of the directory’s creation, the task cannot be considered fulfilled.
- **T001b** — No evidence of a `data/processed/` directory was provided; the artifact list is empty, so the required data directory has not been demonstrated as existing. The implementer must create the directory (or show its presence) to satisfy task T001b.
- **T001c** — No evidence was provided that a `data/results/` directory actually exists on disk (e.g., a directory listing, screenshot, or command output). Without such proof, we cannot confirm the required artifact was created.
- **T001d** — Only `code/__init__.py` is present, and it contains documentation and a version string rather than being an empty placeholder. The required `tests/__init__.py` and `README.md` files are absent entirely. The task is not fully satisfied.
- **T001e** — No evidence of a `data/stimuli/` directory (or any files within it) is provided; the claim lacks the required artifact to confirm the stimuli directory was created.
- **T002** — No `requirements.txt` file was presented, and thus there is no evidence of a list containing the required packages with pinned version numbers. The implementer must supply a non‑empty `requirements.txt` that pins pandas, scipy, statsmodels, numpy, pyyaml, openml, datasets, and requests.
