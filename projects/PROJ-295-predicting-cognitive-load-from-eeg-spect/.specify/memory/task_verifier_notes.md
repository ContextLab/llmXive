# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No directory listing or other evidence was provided to show that the required folders (`code/data`, `code/features`, `code/models`, `tests/unit`, `tests/integration`, `data/raw`, `data/processed`, `results`) were actually created. Without concrete proof of these paths existing, the task cannot be considered completed.
- **T005** — The provided `requirements.txt` lists the required packages but uses open-ended `>=` version specifiers instead of exact pinned versions, and it also includes additional packages not requested. The task explicitly required pinned dependencies, so the artifact does not satisfy the specification.
- **T010** — The `download.py` script correctly downloads the primary dataset and checks for `gaze.tsv`, but when the file is missing it only raises a `FileNotFoundError` and prints a message; it never attempts to automatically download the fallback dataset (`ds003465`) before raising the error, as the task requires. Adding logic to trigger a fallback download in the exception handling path is needed.
- **T009** — The provided `code/data/generate_manifest.py` only re‑exports functions from another module and does not contain any logic to download a tarball, compute its SHA‑256 checksum, or write a manifest file. The existing `data/manifest.yaml` lacks the required top‑level `checksum_sha256` field (and the `url`/`version` fields are nested under `dataset` rather than at the manifest root). Consequently, the task’s specification—producing a manifest with `url`, `version`, and `checksum_sha256`—is not satisfied. The missing implementation and absent checksum field must be added.
- **T042** — declared artifact(s) missing/empty/invalid: code/utils/runtime_profiler.py, results/runtime_profile.json
- **T017** — declared artifact(s) missing/empty/invalid: code/data/preprocess_epoch.py
- **T026** — declared artifact(s) missing/empty/invalid: code/models/split.py
- **T038** — declared artifact(s) missing/empty/invalid: code/models/permutation_test.py, results/permutation_test.json
- **T041** — declared artifact(s) missing/empty/invalid: code/models/baseline.py, results/baseline_comparison.json
