# Research: Evaluating the Impact of Code Generation Models on Code Vulnerability Density

## Dataset Strategy

| Dataset | Source | Verified URL | Usage | Notes |
|---------|--------|--------------|-------|-------|
| HumanEval | HuggingFace | ` | Benchmark tasks, human solutions | Downloaded via `datasets.load_dataset("openai/openai_humaneval", split="test")` |
| MBPP | HuggingFace | ` | Benchmark tasks, human solutions | Downloaded via `datasets.load_dataset("google-research-datasets/mbpp", split="train")` |
| StarCoder | HuggingFace | `https://huggingface.co/bigcode/starcoder` | LLM for code generation | Loaded via `transformers` with `load_in_8bit=True` for CPU feasibility |
| CodeGen | HuggingFace | `https://huggingface.co/Salesforce/codegen-2B-mono` | LLM for code generation | Loaded via `transformers` with `load_in_8bit=True` for CPU feasibility |

**Dataset Fit Verification**:
- **HumanEval/MBPP**: Contain `task_id`, `prompt`, `canonical_solution`, `test` (entry point). Matches required variables for generation and validation.
- **StarCoder/CodeGen**: Pre-trained code models. No variables needed from dataset; used for generation.
- **No Missing Variables**: All required predictors (model type, benchmark) and outcomes (vulnerability count) are obtainable from the pipeline.

## Statistical Rigor

- **Primary Method**: **Permutation Test** on raw vulnerability counts. Chosen for robustness with small samples (n=64) and high zero-inflation where ZINB may fail.
- **Multiple Comparison Correction**: Benjamini-Hochberg (FDR) applied to p-values when testing across vulnerability categories (FR-007).
- **Power Analysis**: Post-hoc power calculated using `statsmodels.stats.power.tt_ind_solve_power` (alpha=0.05, effect_size=0.5, observed n). Dataset flagged as 'under-powered' if power < 0.80 (FR-009).
- **Causal Inference**: Observational study; claims framed as associational differences, not causal. No randomization; identification strategy is comparative analysis of groups.
- **Measurement Validity**: Bandit (static analysis) validated against known vulnerability patterns. **FPR Adjustment**: A rule-based heuristic estimates FPR, but this is a **sensitivity analysis only** and **not** validated against a gold standard (manual audit). The primary conclusion is drawn from raw counts.
- **Collinearity**: The FPR adjustment applies a group-level scalar to individual samples, inducing collinearity. This is why the adjusted metric is **excluded** from the primary test.
- **Selection Bias**: Mean code complexity (Cyclomatic Complexity) is calculated for both groups. If significantly different, a stratified analysis by complexity bins is performed.

## Compute Feasibility

- **CPU-First**: All methods (generation, static analysis, statistical tests) designed for CPU execution.
- **Model Quantization**: StarCoder/CodeGen loaded with `load_in_8bit=True` to fit in 7GB RAM. If OOM, fallback to smaller model variant (e.g., `starcoderbase-1b`).
- **Streaming**: Benchmarks loaded via `datasets.load_dataset(..., streaming=True)` to avoid full dataset in memory.
- **GPU Escape Hatch**: If CPU inference fails (OOM), pipeline auto-offloads to Kaggle GPU (scaled down: 8-bit, fewer tasks).
- **No Fabrication**: No synthetic stand-ins; real data streamed or sampled (first-N rows) if full dataset too large.

## Decision/Rationale

- **Why Permutation Test?**: ZINB requires larger samples for convergence. Permutation test is robust and distribution-free, suitable for n=64.
- **Why FPR Sensitivity Only?**: The rule-based heuristic lacks a ground-truth validation. Using it for the primary metric would introduce unquantifiable bias.
- **Why Quantization?**: Full-precision models exceed 7GB RAM. Quantization is necessary for CPU execution, but introduces a known bias (acknowledged in limitations).
- **Why Fixed Task List?**: To prevent time-based sampling bias (where 'hard' tasks are excluded). A fixed list of tasks is selected before generation.
- **Why Complexity Control?**: To mitigate selection bias introduced by the 'valid code' filter (FR-002).

## Dataset Strategy (Detailed)

1. **HumanEval/MBPP Download**:
 - Use `datasets.load_dataset("openai/openai_humaneval", split="test")` and `datasets.load_dataset("google-research-datasets/mbpp", split="train")`.
 - Persist to `data/raw/humaneval.parquet` and `data/raw/mbpp.parquet`.
 - Checksum recorded in `state/`.

2. **Model Loading**:
 - Load StarCoder/CodeGen via `transformers.AutoModelForCausalLM.from_pretrained(..., load_in_8bit=True, device_map="cpu")`.
 - If OOM, switch to `starcoderbase-1b` or `codegen-2B-mono` (smaller variant).

3. **Generation Loop**:
 - **Fixed Task List**: Select the first N tasks (e.g., 128) from the benchmark.
 - Iterate tasks; generate code until a sufficient number of valid samples (passing tests) are obtained or a maximum attempt limit is reached.
 - Log failures; exclude invalid samples.
 - If a predefined time limit is reached, stop and report 'completed tasks' (a random prefix of the fixed list).

4. **Static Analysis**:
 - Run Bandit on all valid samples; extract CWE IDs, counts.
 - Map CWEs to categories (e.g., SQLi, XSS).

5. **Complexity Measurement**:
 - Calculate Cyclomatic Complexity for all samples.
 - Compare means between LLM and Human groups.

6. **FPR Estimation (Sensitivity)**:
 - Run Reference-Validator Agent on stratified sample (n=20 per group).
 - Calculate group-specific FPR; adjust counts: `adjusted_count = raw_count * (1 - group_FPR)`.
 - **Note**: This metric is for sensitivity analysis only.

7. **Statistical Analysis**:
 - **Primary**: Permutation Test on raw counts (LLM vs Human).
 - **Secondary**: Stratified tests by CWE category (if n≥5 per group); apply FDR correction.
 - **Cross-Benchmark**: Separate tests for HumanEval and MBPP.
 - **Cross-Model**: Separate test for StarCoder vs CodeGen.
 - **Power Analysis**: Calculate and flag if power < 0.80.

8. **Visualization & Reporting**:
 - Boxplots (LLM vs Human); bar charts (top 5 CWEs).
 - Generate `results/summary.md` with stats, images, and sensitivity metrics.
 - Report explicitly states that primary conclusion is based on raw counts.

## Assumptions & Limitations

- **Bandit Accuracy**: Assumes Bandit detects ≥90% of vulnerabilities; FPR adjustment is a proxy, not ground truth.
- **Sample Size**: 64 samples per model/benchmark may be under-powered for small effect sizes; power analysis will flag this.
- **Model Compatibility**: StarCoder/CodeGen assumed compatible with CPU; if not, smaller variants used.
- **Observational Nature**: Findings are associational; no causal claims about model security.
- **Quantization Bias**: 8-bit quantization introduces numerical noise, altering model behavior compared to full precision. This is a known systematic bias.
- **FPR Validity**: The rule-based heuristic for FPR estimation is not validated against a manual audit. It is a proxy, and the sensitivity analysis shows the range of possible outcomes, not a corrected truth.
- **Selection Bias**: Passing benchmark tests does not guarantee absence of vulnerabilities. Complexity control is used to assess this bias.