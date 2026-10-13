# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The task requires two documentation files (`README.md` and `quickstart.md`) and verification that running `python -m code.generate_networks --topology ER --instances 1 --seed 0` creates both `data/raw/networks/ER_0000.edgelist` and `data/raw/networks/metadata_ER_0000.json` without errors.

**Evidence checked:**

1. **`README.md`** exists (5320 bytes) and contains substantive project documentation. ✓
2. **`quickstart.md`** exists (9145 bytes) and contains the required command `python -m code.generate_networks --topology ER --instances 1 --seed 0`. ✓
3. **Execution log** shows the command ran su
- **T003** — The three utility modules exist and contain substantive implementations, but the task explicitly requires **unit tests that pass**. The evidence shows `tests/unit/` directory exists with test files listed (including `test_checksums.py`, `test_metrics.py`, `test_plotting.py`), but **no test execution evidence is provided**—no pytest output, no passing test logs, no demonstration that `python -c "import code.utils.checksums as c; print(len(c.sha256('README.md')))"` returns 64 as specified in the verification requirement.

The task states: "Each module has a corresponding unit test in `tests/unit
- **T005** — The task requires edge-list files at the path pattern `data/raw/networks/{topology}_{idx}.edgelist`, but the actual files are located in subdirectories: `data/raw/networks/ER/ER_0000.edgelist`, `data/raw/networks/BA/BA_0000.edgelist`, etc. The collector explicitly confirmed "NO MATCHING FILE exists" for the required pattern `data/raw/networks/{topology}_{idx}.edgelist`. While the CSV metadata files are correctly placed at `data/raw/networks/{topology}_metadata.csv` and all 50 instances per topology are generated with node_count == 500 (verified in the CSV and metadata JSON files), the edgelist
- **T007** — The test file exists and is substantive, but it does not use `psutil` as required: on Linux/macOS it uses `resource.getrusage` (ru_maxrss), with psutil only as a Windows fallback, contradicting the task's explicit "uses psutil to monitor peak RAM" requirement. Additionally, there is no execution evidence (no CI/test-run output) that the test actually passes, and the peak-memory logic is weak — it compares `max(initial, final)` after `gc.collect()` rather than measuring true peak during generation, so the assertion may not genuinely verify the 7 GB constraint.
- **T008** — Requested task execution failed; rerun successfully: code/simulate_hk.py exit=1
- **T009** — Requested task execution failed; rerun successfully: code/run_batch.py exit=2
