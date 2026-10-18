# Tasks: Evaluating the Impact of Code Generation Models on Code Security

**Inputs**: `spec.md`, `plan.md`, existing research idea, and reviewer feedback.  
All tasks are unchecked; each includes the artifact paths it creates or modifies and the verification steps required to satisfy the corresponding functional and success‑criteria requirements.

---

- [ ] **T001** [P1] [US1] Acquire human reference C++ solutions from the Codeforces benchmark.  
  *Implementation*: `code/download_human.py` – downloads the verified Codeforces dataset (URL fixed in `plan.md`) and writes a newline‑delimited JSON file `data/raw/codeforces_cpp.jsonl`.  
  *Verification*:  
  &nbsp;&nbsp;· Run the script and check that at least **50** distinct `problem_id`s are present.  
  &nbsp;&nbsp;· Verify the SHA‑256 checksum of the downloaded archive matches the value recorded in `plan.md`.  
  &nbsp;&nbsp;· Confirm each entry contains a compilable C++ source string (`human_code`).  

- [ ] **T002** [P1] [US2] Generate LLM variants for each problem using CodeLlama‑7B‑Instruct and StarCoder‑15B via the HuggingFace inference API.  
  *Implementation*: `code/generate_llm_variants.py` – iterates over `data/raw/codeforces_cpp.jsonl`, calls the two models, retries up to three times on failure, and writes per‑model JSONL files `data/generated/codellama/variants.jsonl` and `data/generated/starcoder/variants.jsonl`.  
  *Verification*:  
  &nbsp;&nbsp;· For every `problem_id` that succeeded, the corresponding entry contains a non‑empty source string under `llm_code["codellama"]` / `llm_code["starcoder"]`.  
  &nbsp;&nbsp;· Log all failed generations (`log/llm_generation_fail.log`) and ensure they are excluded from the final paired dataset.  

- [ ] **T003** [P1] [US3] Consolidate human and LLM sources into a validated `ProblemPair` collection.  
  *Implementation*: `code/create_problem_pairs.py` – merges the human file and the two LLM variant files, producing `data/raw/problem_pairs_v{hash}.jsonl` that conforms to `contracts/problem_pair.schema.yaml`.  
  *Verification*:  
  &nbsp;&nbsp;· Run schema validation (`pytest tests/test_problem_pair_schema.py`).  
  &nbsp;&nbsp;· Count that each retained `ProblemPair` has a `human_code` field and **both** LLM fields (or records a `generation_failed` flag).  
  &nbsp;&nbsp;· Ensure the pair‑integrity rate ≥ 95 % (SC‑005).  

- [ ] **T004** [P2] [US4] Deterministically compile every source (human and LLM) with ASan + UBSan inside a Docker container and record compilation status.  
  *Implementation*: `code/compile_and_fuzz.py` – for each `ProblemPair`, creates a temporary Docker image `gcc:13.2-bullseye` (pinned), compiles with flags `-O0 -g -fsanitize=address,undefined`, and writes compilation metadata to `data/compiled/compile_status_v{hash}.jsonl`. Successful binaries are saved under `data/compiled/binaries/`.  
  *Verification*:  
  &nbsp;&nbsp;· All entries have `execution_status` either `"success"` or `"compile_fail"` (FR‑002, FR‑003).  
  &nbsp;&nbsp;· The overall compile‑failure rate ≤ 5 % (SC‑005).  

- [ ] **T005** [P2] [US5] Auto‑generate a libFuzzer harness (`LLVMFuzzerTestOneInput`) for each compiled binary and rebuild the instrumented binary.  
  *Implementation*: `code/generate_fuzz_harness.py` – reads the list of successful binaries, injects a wrapper source file, recompiles, and stores the final fuzzable binaries under `data/compiled/fuzz_binaries/`.  
  *Verification*:  
  &nbsp;&nbsp;· Each binary runs `./binary -runs=0` without immediate crash (sanity check).  
  &nbsp;&nbsp;· The harness source files are saved in `code/harness_templates/`.  

- [ ] **T006** [P2] [US6] Execute the fuzzing harness on each binary for a hard‑capped 30‑minute budget, capturing crash logs and timeout events.  
  *Implementation*: `code/run_fuzzing.py` – launches each binary inside its own Docker container, uses `timeout 1800s`, and writes a `FuzzResult` JSON line to `data/results/fuzz_results_v{hash}.jsonl`.  
  *Verification*:  
  &nbsp;&nbsp;· Every `FuzzResult` contains fields required by `contracts/fuzz_result.schema.yaml`.  
  &nbsp;&nbsp;· Execution statuses are one of `"success"`, `"timeout"`, `"compile_fail"` (FR‑003, FR‑011).  

- [ ] **T007** [P2] [US7] Parse ASan/UBSan crash logs, map stack traces to vulnerability categories, and assign severity scores (1‑4) per FR‑009.  
  *Implementation*: `code/parse_crashes.py` – reads the raw fuzzer logs, extracts unique stack traces, applies the rubric table (included in `docs/rubric.md`), and appends `severity_scores` to each `FuzzResult`. Updated results are written to `data/results/fuzz_results_parsed_v{hash}.jsonl`.  
  *Verification*:  
  &nbsp;&nbsp;· For each security‑relevant crash, a severity integer between 1 and 4 is present.  
  &nbsp;&nbsp;· Non‑security crashes are flagged but **not** counted in `crash_count`.  

- [ ] **T008** [P3] [US8] Perform paired statistical analyses (Wilcoxon signed‑rank) on crash‑count differences and on severity‑score differences for each LLM model versus human code. Compute Cliff’s Δ effect sizes and apply Holm‑Bonferroni correction across the two metric families.  
  *Implementation*: `code/statistical_analysis.py` – loads `fuzz_results_parsed_v{hash}.jsonl`, builds per‑problem paired vectors, runs `scipy.stats.wilcoxon`, `pingouin.compute_effsize`, and `statsmodels.stats.multitest.multipletests` (method=`holm`). Results are saved to `data/analysis/stat_summary_v{hash}.jsonl`.  
  *Verification*:  
  &nbsp;&nbsp;· The summary file contains for each model: `p_value`, `effect_size`, `corrected_alpha`, and a human‑readable `conclusion_text`.  
  &nbsp;&nbsp;· All p‑values are reported with the Holm‑Bonferroni adjusted α = 0.05 (FR‑008).  

- [ ] **T009** [P3] [US9] Generate the final Markdown report with visualizations (box‑plots of crash counts, severity distributions, compile‑failure statistics) and a discussion that frames findings as associational (FR‑007).  
  *Implementation*: `code/generate_report.py` – creates `paper/report.md`, embeds figures from `figures/` (produced by the analysis script), and includes tables linking each statistic to the exact row in `data/analysis/...`.  
  *Verification*:  
  &nbsp;&nbsp;· The report contains a reproducibility section citing the content‑hashed artifact IDs.  
  &nbsp;&nbsp;· All required visualizations are present and render without errors (`pytest tests/test_report_render.py`).  

- [ ] **T010** [P3] [US10] Conduct a reproducibility audit: verify that all random seeds, Docker image digests, and file hashes are recorded in `manifest.json`; re‑run the entire pipeline from `quickstart.md` on a fresh runner and confirm identical hashes.  
  *Implementation*: `code/audit_reproducibility.py` – gathers `numpy.random.seed`, `torch.manual_seed`, Docker image SHA, and writes `manifest.json` under `data/`.  
  *Verification*:  
  &nbsp;&nbsp;· A fresh CI run produces the same `manifest.json` (bit‑wise identical).  
  &nbsp;&nbsp;· The audit script exits with status 0 only if all checks pass.  

- [ ] **T011** [P3] [US11] Document the full experimental protocol (data acquisition, LLM generation parameters, compilation flags, fuzzing budget, statistical methods) in `docs/methodology.md` and link it from the report.  
  *Implementation*: Write a concise but complete protocol file referencing the exact script versions and parameter values used.  
  *Verification*:  
  &nbsp;&nbsp;· The methodology file is cross‑referenced from `paper/report.md`.  
  &nbsp;&nbsp;· Reviewers can locate every script and configuration via the hyperlinks.  

- [ ] **T012** [P3] [US12] Create a CI test suite that validates schema compliance, ensures the minimum dataset size (≥ 50 problem pairs per model), and checks that the statistical summary meets the success criteria (p‑value reporting, effect‑size calculation).  
  *Implementation*: Add tests under `code/tests/` (e.g., `test_schema.py`, `test_dataset_size.py`, `test_statistics.py`).  
  *Verification*:  
  &nbsp;&nbsp;· All tests pass on the CI runner (`pytest -q`).  
  &nbsp;&nbsp;· Failures surface as pipeline errors, preventing progression to the paper hand‑off.  

---  

### Dependencies and Requirement Coverage

| Requirement | Satisfied by Task(s) |
|-------------|----------------------|
| **FR‑001** | T001, T002, T003 |
| **FR‑002** | T004 |
| **FR‑003** | T004, T006 |
| **FR‑004** | T007 |
| **FR‑005** | T008 |
| **FR‑006** | T009 |
| **FR‑007** | T009 |
| **FR‑008** | T008 |
| **FR‑009** | T007 |
| **FR‑010** | T005 |
| **FR‑011** | T006, T007 |
| **SC‑001** – **SC‑006** | T001–T010 (as indicated in verification steps) |

All tasks respect the data‑flow ordering: acquisition → generation → pair creation → compilation → harness → fuzzing → parsing → analysis → reporting → audit. No task writes outside the `data/`, `code/`, `figures/`, or `paper/` directories.
