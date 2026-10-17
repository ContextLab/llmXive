# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The smoke-test command itself works (`--sample 5` exited 0 in 0.1s and wrote `data/generated/phi3-mini/sample_test.txt`), but the required verification `pytest tests/quickstart_test.py` does NOT pass: the recorded run timed out after 600s (exit -1), almost certainly because `test_full_pipeline_smoke` invokes `--full`, which triggers the slow repo-cloning data-extraction stage — the quickstart test must complete quickly, not hang. Additionally, `quickstart.md` contains broken install commands (`python -m venv.venv` and `source.venv/bin/activate` are missing spaces), so the documented setup step
- **T003** — Requested task execution failed; rerun successfully: code/data_extraction.py exit=1
- **T004** — Requested task execution failed; rerun successfully: code/gold_annotation.py exit=1
