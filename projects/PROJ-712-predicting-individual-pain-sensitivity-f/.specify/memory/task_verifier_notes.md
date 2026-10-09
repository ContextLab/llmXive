# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `requirements.txt` exists and contains all eight required packages, but none of them are pinned or carry version specifiers (only the unrequested `psutil>=5.9` has one), directly contradicting the task's requirement for a "pinned requirements.txt" and its verification criterion that a unit test check "version specifiers" for the listed packages. Fix by adding version pins (e.g., `mne==1.x`, `scikit-learn==1.x`, etc.) for all eight packages.
- **T006** — Requested task execution failed; rerun successfully: scripts/run_test_data_loader.sh exit=2
