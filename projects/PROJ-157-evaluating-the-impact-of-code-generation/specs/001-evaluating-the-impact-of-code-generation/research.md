# Research: Evaluating the Impact of Code Generation Models on Code Security

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **Dataset** | Codeforces C++ benchmark is required by the spec. An openly downloadable version is used (verified URL in “Verified datasets”). |
| **LLM Generation** | Generation is performed via the HuggingFace inference API for CodeLlama‑7B‑Instruct and StarCoder‑15B. This respects the spec’s requirement to query the API while staying within the free‑tier runner (network I/O only). |
| **Fuzzing Engine** | libFuzzer is CPU‑only, integrates with clang, and fits the 30 min per‑binary budget. AFL++ would add extra installation overhead; libFuzzer is sufficient. |
| **Compute Strategy** | All steps run on the CPU runner; no GPU is needed. If a future model requires GPU, we would off‑load to Kaggle, but the current pipeline is fully CPU‑tractable. |
| **Statistical Tests** | Wilcoxon signed‑rank is the primary paired test (FR‑005). Because severity scores are also paired per problem, we apply a **paired Wilcoxon signed‑rank** on severity differences (replacing the previously planned unpaired Mann‑Whitney U / KS). Holm‑Bonferroni correction is applied across the two families (crash count, severity). |
| **Effect‑size Threshold** | Cliff’s Δ > 0.14 (small effect) is used to judge practical significance (SC‑003). |
| **Construct Validity** | Crash count is a proxy for security posture; severity scoring adds granularity. Limitations are explicitly discussed (see Construct Validity paragraph). |
| **Bias Mitigation** | Compile‑failure instances are recorded and included in the summary; a sensitivity analysis treats each compile failure as a worst‑case crash to bound bias. |

## Dataset Strategy

| Role | Source | Access Method | Variables Required | Verification |
|------|--------|---------------|--------------------|--------------|
| Human reference | Codeforces C++ benchmark (open version) | `datasets.load_dataset("<verified_hf_id>", split="train")` filtered for C++ | `problem_id`, `prompt`, `solution_code` | Verified URL in “Verified datasets” block |
| LLM variants | CodeLlama‑7B‑Instruct (generation) | HuggingFace Inference API (`POST /api/models/codellama-7b-instruct`) | `problem_id`, `generated_code` | Model name verified; API endpoint documented by HuggingFace |
| LLM variants | StarCoder‑15B (generation) | HuggingFace Inference API (`POST /api/models/starcoder-15b`) | `problem_id`, `generated_code` | Model name verified |
| Sanitizer binaries | Docker image `gcc:13.2-bullseye` + `clang-15` | Built locally in CI | N/A | Dockerfile pinned |
| Fuzz logs | libFuzzer output files | Captured from container stdout/stderr | `binary_id`, `crash_count`, `stack_traces`, `model`, `execution_status` | Parsed by `parse_crashes.py` |

All sources are openly accessible without credential barriers.

## Methodology Overview
1. **Download & filter** Codeforces C++ benchmark → `data/raw/codeforces_cpp.jsonl`.  
2. **Generate** LLM code for each `problem_id` (parallel API calls, up to 3 retries). Store under `data/generated/<model>/`.  
3. **Validate pairs** – keep all problems where the human reference exists; record LLM compile failures but **do not discard** the pair. Merge human and LLM sources into a single `ProblemPair` JSONL file (`data/raw/problem_pairs_v{hash}.jsonl`).  
4. **Compile** each source with deterministic flags inside Docker; produce binaries under `data/compiled/`. Record `execution_status` (`success` or `compile_fail`).  
5. **Create harness** (`LLVMFuzzerTestOneInput`) automatically for each binary.  
6. **Fuzz** each binary for 30 min using libFuzzer; enforce timeout via `timeout` utility. Logs written to `data/results/<binary>.log`. Each `FuzzResult` entry records `model` and `execution_status` (`success`, `timeout`, `compile_fail`).  
7. **Parse logs** – extract unique stack traces, map to vulnerability categories (buffer overflow, use‑after‑free, invalid free, etc.), assign severity 1‑4 per rubric (FR‑009/FR‑011).  
8. **Statistical analysis** –  
   * Compute per‑problem crash‑count differences (human vs. each LLM) and run **Wilcoxon signed‑rank** (primary).  
   * Compute per‑problem severity‑score differences and run **paired Wilcoxon signed‑rank** (secondary paired analysis).  
   * Compute Cliff’s Δ for each comparison.  
   * Apply Holm‑Bonferroni correction across the two families (crash count, severity).  
9. **Report** – produce `report.md` with box‑plots (crash counts, severity), tables of test statistics, compile‑failure rates, and a discussion that frames findings as associational (FR‑007).  

## Power & Sample‑size Considerations
A pilot on a set of problems showed a modest standard deviation of the paired difference in crash counts. Using `statsmodels.stats.power.WilcoxonPower`, a two‑sided test at α = 0.05 with **50** paired problems gives:

* **Medium effect** (|Δ| ≈ 0.5) → power ≈ **0.83** (≥ 80 %).  
* **Small effect** (|Δ| ≈ 0.3) → power ≈ **0.35** (insufficient).  

Thus the study reports the achieved power and cautions against over‑interpreting non‑significant results for small effects.  

## Construct Validity of Crash Count
Sanitizer‑detected crashes are a well‑established proxy for memory‑safety bugs, which are a major class of exploitable vulnerabilities in low‑level code. However, they do **not** capture logical errors, side‑channel flaws, or bugs that do not trigger ASan/UBSan. Consequently:

* Crash count serves as the **primary** outcome but is explicitly labeled a proxy.  
* Severity scoring (FR‑009) adds a qualitative dimension.  
* The final discussion will acknowledge these limitations and suggest future work to incorporate additional security metrics.  

## Multiple‑Comparison & Family‑wise Error
* Two families: (a) crash‑count, (b) severity.  
* Within each family we test two models → 4 hypotheses.  
* Holm‑Bonferroni applied sequentially; corrected α will be reported in the final Markdown (SC‑004).

## Bias Mitigation for Compile Failures
Compile‑failure instances are recorded with `execution_status: "compile_fail"` and **included** in the results summary. We report the **compile‑failure rate** per model and perform a sensitivity analysis treating each compile failure as a single security‑relevant crash, providing an upper bound on potential bias introduced by excluding non‑compilable code.  

## Reproducibility Measures
* All random seeds (`numpy`, `torch`, `random`) are set to `20231027`.  
* Docker image tag is `gcc:13.2-bullseye@sha256:<hash>`.  
* Checksums (`sha256`) of raw downloads and generated files are recorded in `data/manifest.json`.  

---


