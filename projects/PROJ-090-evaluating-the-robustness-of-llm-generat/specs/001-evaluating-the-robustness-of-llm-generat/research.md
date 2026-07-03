# Research: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

## Executive Summary

This research plan details the methodology for evaluating the robustness of StarCoder2-3B code generation against semantically-preserving input perturbations. The study leverages the HumanEval dataset, generates perturbed prompts via rule-based transformations, validates semantic equivalence using `sentence-transformers/all-MiniLM-L6-v2`, and executes generated code in a sandboxed CPU environment. Statistical analysis includes McNemar's test with Bonferroni correction, Mixed-Effects Logistic Regression, and sensitivity analysis on the semantic similarity threshold. The entire pipeline is designed to run within the constraints of a free-tier GitHub Actions runner (2 CPU, 7 GB RAM, 6h runtime).

## Dataset Strategy

| Dataset | Source URL | Loading Method | Usage | Notes |
|---------|------------|----------------|-------|-------|
| HumanEval | https://huggingface.co/datasets/openai/openai_humaneval/resolve/main/openai_humaneval/test-00000-of-00001.parquet | `datasets.load_dataset("openai_humaneval")` | Primary evaluation benchmark | Contains 164 Python programming tasks with function signatures, docstrings, and unit tests. |
| Sentence-Transformers Embeddings | (Model weights, not dataset) | `sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')` | Semantic similarity validation | Used to compute cosine similarity between original and perturbed prompts. |
| StarCoder2-3B | (Model weights) | `transformers.AutoModelForCausalLM.from_pretrained(..., load_in_4bit=True)` | Code generation | CPU-optimized 4-bit quantized model for inference. |

**Data Acquisition Plan**:
1. Download HumanEval parquet file from the verified HuggingFace URL.
2. Verify checksum against recorded hash in `state/`.
3. Load into pandas DataFrame for processing.
4. Split into original prompts and generate perturbed variants.

**Semantic Similarity Validation**:
- Use `sentence-transformers/all-MiniLM-L6-v2` to encode original and perturbed prompts.
- Compute cosine similarity.
- Retain perturbations with similarity > 0.95 for primary analysis.
- Store raw scores for all candidates for sensitivity analysis.

## Model & Methodology

### Perturbation Generation
Three rule-based transformations applied to HumanEval prompt descriptions:
1. **Synonym Substitution**: Replace non-keyword tokens with synonyms from WordNet, ensuring no change in programming semantics.
2. **Typo Injection**: Randomly inject character typos (e.g., missing letters, swapped characters) in function descriptions.
3. **Syntactic Rephrasing**: Rephrase problem statements using predefined syntactic patterns (e.g., active to passive voice, clause reordering).

*Constraint*: Up to 3 variants per task, prioritized by semantic similarity score.

### Inference & Execution
- **Model**: StarCoder2-3B loaded with 4-bit quantization (`bitsandbytes` CPU build).
- **Hardware**: CPU-only (no CUDA).
- **Timeouts**: 30s for generation, 10s per test case execution.
- **Sandbox**: Docker container with `--network none` and `--cap-drop ALL`.
- **Error Handling**: Log OOM, timeout, and execution errors; skip failed samples.

### Statistical Analysis
1. **Pass@1 Calculation**: Compute pass rates for original and each perturbation type.
2. **McNemar's Test**: Paired comparison of original vs. perturbed pass/fail outcomes per perturbation type.
3. **Bonferroni Correction**: Adjust alpha level for 3 comparisons (α = 0.05 / 3).
4. **Mixed-Effects Logistic Regression**: Model pass/fail as function of perturbation type with 'task' as random effect to account for clustering.
5. **Sensitivity Analysis**: Re-score all candidates with thresholds {0.85, 0.90, 0.95, 0.99} and report pass@1 variation.

## Statistical Rigor & Feasibility

### Multiple Comparisons
- **Method**: Bonferroni correction applied to McNemar's test p-values.
- **Rationale**: Three perturbation types tested; family-wise error rate controlled at 0.05.

### Sample Size & Power
- **Limitation**: HumanEval has 164 tasks; with up to 3 perturbations per task, total samples ~650.
- **Acknowledgement**: Power for McNemar's test may be limited for small effect sizes; results interpreted with caution.
- **Mitigation**: Mixed-Effects model accounts for task-level clustering, improving efficiency.

### Causal Inference Assumptions
- **Observational**: Study is observational; perturbations are applied deterministically but not randomized across tasks.
- **Claim Framing**: Results framed as associational (perturbation type associated with pass rate change), not causal.
- **Identification Strategy**: Paired design (original vs. perturbed for same task) controls for task difficulty.

### Measurement Validity
- **Semantic Similarity**: `all-MiniLM-L6-v2` validated on STS benchmarks; threshold 0.95 ensures high-fidelity perturbations.
- **Code Correctness**: HumanEval unit tests are standard benchmark for code generation; pass/fail is binary and objective.

### Predictor Collinearity
- **Acknowledgement**: Perturbation types are mutually exclusive by design; no collinearity in fixed effects.
- **Random Effect**: 'task' random effect accounts for within-task correlation of perturbations.

## Compute Feasibility

### Resource Constraints
- **RAM**: 7 GB limit.
- **Disk**: 14 GB limit.
- **Runtime**: 6 hours.
- **CPU**: 2 cores.

### Mitigations
- **Model Quantization**: 4-bit StarCoder2-3B reduces memory footprint to ~3-4 GB.
- **Batching**: Process tasks sequentially or in small batches to avoid OOM.
- **Timeouts**: Strict 30s generation and 10s execution timeouts prevent hanging processes.
- **Data Subset**: If full 164 tasks exceed runtime, prioritize a stratified random sample (e.g., 100 tasks) with documented reduction.

### Library Compatibility
- **CPU-Only**: `transformers`, `sentence-transformers`, `scikit-learn`, `statsmodels` all have CPU wheels.
- **bitsandbytes**: Use CPU-optimized build (`bitsandbytes-cpu`).
- **No GPU Dependencies**: No CUDA, no mixed-precision training.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| 4-bit Quantization | Required to fit StarCoder2-3B in 7 GB RAM on CPU. |
| Semantic Threshold 0.95 | High-fidelity perturbations ensure surface changes, not intent changes. |
| McNemar's Test | Paired design controls for task difficulty; appropriate for binary outcomes. |
| Mixed-Effects Model | Accounts for clustering of perturbations within tasks. |
| Bonferroni Correction | Controls family-wise error rate for 3 comparisons. |
| CPU-Only Pipeline | Mandatory for free-tier GitHub Actions; avoids GPU dependency. |
