# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T049** — The provided `anomaly_detector.py` file is truncated (ends with `if peak_ram_mb > self.ma`), so the logic that actually checks the limits and aborts the run is missing. Consequently the resource‑validation behavior required by FR‑008 is not fully implemented.
- **T052** — The provided `download_datasets.py` file is truncated and does not show any concrete implementation that actually downloads the required NAB/PhysioNet subsets or the UCI Electricity Load Diagrams and Traffic datasets (e.g., via `ucimlrepo`). Moreover, there is no visible logic checking the outcome of T052b before proceeding. Without the full download code and the conditional guard, the task’s requirements are not satisfied.
