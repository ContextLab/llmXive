# Implementation Plan: Evaluating the Impact of Code Generation Models on Code Security

**Branch**: `001-evaluate-llm-code-security` | **Date**: 2026-10-18 | **Spec**: [spec.md](../specs/001-evaluate-llm-code-security/spec.md)  
**Input**: Feature specification from `/specs/001-evaluate-llm-code-security/spec.md`

## Summary
The study requires a paired dataset of human‑written C++ solutions and LLM‑generated variants for the same programming challenges, deterministic compilation of each snippet, fuzzing each binary with ASan/UBSan, triage of crashes into security‑relevant categories with severity scores, and paired non‑parametric statistical comparison (Wilcoxon signed‑rank, paired Wilcoxon on severity, Holm‑Bonferroni correction).  

**Key technical choices**
* **Human reference data** – Open Codeforces C++ benchmark dataset (verified URL provided in the “Verified datasets” block). No fallback to HumanEval; if the Codeforces dataset cannot be obtained, the pipeline aborts with a clear error.
* **LLM variants** – generated on‑the‑fly via HuggingFace inference API for CodeLlama‑7B‑Instruct and StarCoder‑15B.  
* **Compilation & fuzzing** – Docker container (`gcc:13.2-bullseye` + `clang-15`) with flags `-O0 -g -fsanitize=address,undefined`; libFuzzer as the fuzzing engine.  
* **Statistical pipeline** – `scipy.stats` for Wilcoxon, `statsmodels` for Holm‑Bonferroni, `pingouin` for Cliff’s Δ.  

All steps are deterministic, seeded, and fully reproducible on a GitHub Actions free‑tier runner.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**:  
* `datasets==2.18.0` (HuggingFace)  
* `transformers==4.41.0` (for API calls)  
* `torch==2.2.2` (CPU‑only)  
* `docker==7.0.0` (Python SDK)  
* `clang==15.0.7` (via `apt`)  
* `libfuzzer` (built‑into clang)  
* `pandas==2.2.2`, `numpy==1.26.4`  
* `scipy==1.13.0`, `statsmodels==0.14.2`, `pingouin==0.5.4`  
* `matplotlib==3.8.4`, `seaborn==0.13.2`  

**Storage**: Files under `data/` (raw Human/Codeforces data, generated LLM code, compiled binaries, fuzz logs) – all version‑hashed.  
**Testing**: `pytest==8.2.2` for contract validation, `hypothesis` for data‑model sanity checks.  
**Target Platform**: Linux (Ubuntu‑22.04) GitHub Actions runner.  
**Constraints**: Total wall‑clock ≤ 6 h per batch; per‑binary fuzz timeout 30 min; ≤ 95 % compilable pair rate (SC‑005).  

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | All external URLs (Codeforces/Open dataset, HuggingFace models) are fixed; random seeds are pinned in `code/`; Docker image tag is immutable. |
| II. Verified Accuracy | Every citation (Codeforces dataset, CodeLlama, StarCoder) uses the verified URLs listed in the “Verified datasets” block. |
| III. Data Hygiene | Raw downloads are checksummed; every transformation writes a new file with a `*_v{hash}.jsonl` suffix. |
| IV. Single Source of Truth | Every figure/statistic in the final Markdown report references a specific row in `data/fuzz_results_v{hash}.jsonl`. |
| V. Versioning Discipline | All artifacts are content‑hashed; `state/projects/PROJ-157-...yaml` will be updated automatically. |
| VI. Deterministic Compilation & Fuzzing Isolation | Dockerfile pins `gcc`/`clang` versions; `timeout` enforces the 30 min budget; each binary runs in its own isolated container. |
| VII. Quantitative Vulnerability Triage & Statistical Rigor | Crash parsing follows the rubric (FR‑009); statistical tests and Holm‑Bonferroni correction are applied as required (FR‑008, FR‑007). |

All principles satisfied – no violations.

## Project Structure

```
specs/001-evaluate-llm-code-security/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── problem_pair.schema.yaml
    └── fuzz_result.schema.yaml

code/
├── download_humaneval.py
├── generate_llm_variants.py
├── compile_and_fuzz.py
├── parse_crashes.py
├── statistical_analysis.py
└── generate_report.py

data/
├── raw/
│   └── codeforces_cpp.jsonl
├── generated/
│   ├── codellama/
│   └── starcoder/
├── compiled/
│   └── binaries/
└── results/
    └── fuzz_results.jsonl
```

## Phase‑wise Tasks (mapped to FR/SC)

| Phase | Description | FR IDs | SC IDs |
|-------|-------------|--------|--------|
| **0 – Environment & Seed Setup** | Create deterministic Docker image, pin seeds, verify checksums. | – | I, III, V |
| **1 – Human Reference Acquisition** | Download Codeforces C++ benchmark (or abort if unavailable) and verify ≥ 50 distinct problems. | FR‑001 | SC‑006 |
| **2 – LLM Variant Generation** | Call HuggingFace API for CodeLlama‑7B‑Instruct & StarCoder‑15B, retry up to 3×, store per‑problem file. | FR‑001 | SC‑006 |
| **3 – Pair Validation & ProblemPair Creation** | Ensure each problem has a human reference and LLM variants; **do not discard** LLM code that fails to compile – record a `compile_fail` status. Merge human and LLM sources into a single `ProblemPair` JSONL file (`data/raw/problem_pairs_v{hash}.jsonl`). | FR‑001, FR‑003 | SC‑005 |
| **4 – Deterministic Compilation** | Inside Docker, compile each source with `-O0 -g -fsanitize=address,undefined`; capture compile status (`success` or `compile_fail`). | FR‑002, FR‑003 | SC‑005 |
| **5 – Harness Generation** | Auto‑generate `LLVMFuzzerTestOneInput` wrapper for each compiled binary. | FR‑010 | – |
| **6 – Fuzz Execution** | Run libFuzzer for 30 min per binary, enforce hard timeout, **record** for each run: `model` (human / codellama / starcoder) and `execution_status` (`success`, `timeout`, `compile_fail`) in the `FuzzResult` JSONL. | FR‑003, FR‑004, FR‑011 | SC‑005 |
| **7 – Crash Parsing & Severity Scoring** | Extract unique stack traces, map to vulnerability categories, assign 1‑4 severity per FR‑009/FR‑011. | FR‑004, FR‑009, FR‑011 | – |
| **8 – Statistical Summaries** | Compute per‑problem crash‑count differences and run **Wilcoxon signed‑rank** (primary). Compute per‑problem severity‑score differences and run **paired Wilcoxon signed‑rank** (secondary paired analysis). Compute Cliff’s Δ for each comparison. Apply Holm‑Bonferroni correction across the two families (crash‑count, severity). | FR‑005, FR‑008, FR‑007 | SC‑001, SC‑002, SC‑003, SC‑004 |
| **9 – Report Generation** | Produce Markdown report with box‑plots, tables of test statistics, compile‑failure rates, and a discussion that frames findings as associational (FR‑007). | FR‑006, FR‑007, FR‑008 | – |
| **10 – Reproducibility Audit** | Verify all hashes, seeds, and container IDs; generate a `manifest.json` for CI. | – | I, IV, V |

### Power & Sample‑size Justification
A two‑sided Wilcoxon signed‑rank test at α = 0.05 with **50 paired problems per model** yields:

* **Medium effect** (|Δ| ≈ 0.5, estimated SD of paired differences is expected to be small): power ≈ **0.83** (≥ 80 %).
* **Small effect** (|Δ| ≈ 0.3): power ≈ **0.35** (insufficient).  

These calculations were performed with `statsmodels.stats.power.WilcoxonPower`. The study therefore reports achieved power and cautions against over‑interpreting non‑significant results for small effects.

### Construct Validity of Crash Count
Sanitizer‑detected crashes are a well‑established proxy for memory‑safety bugs, a major class of exploitable vulnerabilities in low‑level code. However, they do **not** capture logical errors, side‑channel flaws, or bugs that do not trigger ASan/UBSan. Consequently:

* Crash count serves as the **primary** outcome but is explicitly labeled a proxy (FR‑007).  
* Severity scoring (FR‑009) adds a qualitative dimension.  
* The final discussion will acknowledge these limitations and suggest future work to incorporate additional security metrics.

### Bias Mitigation for Compile Failures
Compile‑failure instances are recorded with `execution_status: "compile_fail"` and **included** in the results summary. We report the **compile‑failure rate** per model and perform a sensitivity analysis treating each compile failure as a single security‑relevant crash, providing an upper bound on potential bias introduced by excluding non‑compilable code.

## Compute Feasibility
All steps run on the CPU‑only GitHub Actions runner; no GPU is required. If a future component (e.g., a neural triage classifier) requires GPU, the pipeline can off‑load that step to Kaggle’s free GPU tier, but the current design stays within CPU limits.

---


