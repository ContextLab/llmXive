# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `generate_clips.py` script correctly creates `.npz` files containing the required `states`, `actions`, and `observations` arrays, but the `data/raw/` directory currently holds 100 clip files (including duplicates like `clip_0000.npz`, `clip_0010.npz`, etc.) instead of the required 50. The task’s verification condition “`ls data/raw/ | wc -l` equals 50” is therefore not met. The directory must be cleaned to contain exactly the 50 reproducible clips (`clip_000.npz` … `clip_049.npz`).
- **T003** — Requested task execution failed; rerun successfully: src/pipeline/extract_descriptors.py exit=1
