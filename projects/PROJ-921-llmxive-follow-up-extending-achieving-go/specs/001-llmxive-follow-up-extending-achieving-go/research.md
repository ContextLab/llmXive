# Research: llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

## Research Question & Hypothesis

**Question**: Does the "reverse-perplexity" curriculum used to instill self-checking behaviors in Olympiad-level models inadvertently encode rigid, domain-specific heuristics that degrade performance on open-ended, ill-structured scientific problems lacking verifiable ground-truth answers?

**Hypothesis**: The SU-01 model, optimized for deterministic correctness on Olympiad tasks, will exhibit a statistically significant negative interaction effect between 'Model Type' and 'Domain' in a Linear Mixed Effects model, indicating that higher Olympiad accuracy correlates with lower creativity scores on ill-structured problems compared to a baseline model.

## Dataset Strategy

The study relies on two distinct data sources. All datasets are verified as open and programmatically accessible to ensure CI feasibility.

| Dataset | Purpose | Source/Loader | Verified URL | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **IMO Bench** | Deterministic Olympiad reasoning (SU-01 vs Baseline accuracy) | `datasets.load_dataset` | https://huggingface.co/datasets/nvidia/Nemotron-IMO-Bench/resolve/main/data/test.jsonl | JSONL format; contains math/physics problems with verifiable answers. |
| **ScienceQA** | Ill-structured scientific problems (Creativity scoring) | `datasets.load_dataset` | https://huggingface.co/datasets/bigscience/ScienceQA/resolve/main/data/train-00000-of-00001.parquet | Parquet format; contains multiple-choice science questions. **Strategy**: Prompts are converted to open-ended by removing options and asking for a generated solution. |
| **Gold Standard** | Proxy model validation (N=50) | Local JSONL (Curated) | N/A | Manually curated set of responses with human expert scores. |

**Dataset Fit & Feasibility Analysis**:
- **IMO Bench**: The verified URL provides a JSONL file suitable for text generation. The content is verified to be Olympiad-style problems.
- **IPhO Bench**: The verified URL provided (`huggan/iphone2dslr_flower`) points to an image dataset. **Critical Decision**: The IPhO component is **excluded** from the active pipeline. The 'Olympiad' construct is now restricted to 'Math Olympiad' (IMO) only. The hypothesis is reframed to reflect this limitation (Math-only generalizability).
- **ScienceQA (OpenSci-Reason)**: The verified URL (`bigscience/ScienceQA`) provides a parquet file of science questions. **Modality Mismatch Resolution**: The dataset is primarily multiple-choice. The plan explicitly defines a **Prompt Engineering Strategy** to convert these into open-ended challenges: "Given the question and context, generate a detailed solution without relying on the multiple-choice options." This creates the 'ill-structured' prompt required for the hypothesis.
- **SU-01 Model**: No verified source URL exists. The plan assumes the weights are available via HuggingFace or a local path as per the `Assumptions` in `spec.md`. If not available, the pipeline will fail with a clear error, preventing fabrication.

## Methodology

### Phase 1: Data Ingestion & Preprocessing
1.  **Download**: Fetch datasets from verified URLs using `datasets.load_dataset`.
2.  **Validation**: Compute checksums. Verify text content in IMO/ScienceQA files.
3.  **Prompt Engineering**: Convert ScienceQA MCQs to open-ended prompts by stripping options and appending "Generate a detailed solution."
4.  **Formatting**: Convert all prompts to a unified JSONL structure: `{"prompt_id", "text", "domain", "source", "is_ill_structured"}`.
5.  **Gold Standard**: Load the N=50 human-rated set.

### Phase 2: Inference (CPU-Only)
1.  **Models**: Load SU-01 and Baseline models. Use `device="cpu"`, `torch_dtype=torch.float32`.
2.  **Parameters**: `batch_size=1`, `temperature=0.7`, `max_new_tokens=2048` (hard limit).
3.  **Token Limit Enforcement (FR-006)**:
    -   **Task**: Explicitly check token count after generation.
    -   **Logic**: If `len(tokens) > 2048`, truncate to 2048, set `truncated=True`, and log to `audit_log.jsonl`.
4.  **Generation**:
    -   Run on IMO: Generate 1 response per prompt.
    -   Run on ScienceQA: Generate multiple distinct responses per prompt.
5.  **Response Completeness Check (FR-003)**:
    -   **Task**: Count valid responses per prompt.
    -   **Logic**: If count < 3, flag prompt as `incomplete` and log to `audit_log.jsonl`. Exclude from analysis.
6.  **Failure Handling**: Log truncations (token limit) and OOMs. Exclude incomplete prompts from analysis.

### Phase 3: Automated Scoring (Proxy Model)
1.  **Proxy Model Verification (FR-004)**:
    -   **Task**: Check for a fine-tuned variant of `meta-llama/Meta-Llama-3-8B-Instruct` on HuggingFace.
    -   **Logic**: If found, load it. If not, load the base model and flag the limitation in the audit log.
2.  **Model**: Load the verified model at INT4 quantization (`load_in_4bit=True`).
3.  **Prompt**: "Score the following response on Novelty, Feasibility, and Logical Consistency using a qualitative assessment scale. Output JSON with rationale."
4.  **Execution**: Score all ScienceQA responses.
5.  **Ambiguity Check**: Calculate variance of 3 scores per prompt. Flag if variance > 1.5 or entropy > 2.0.
6.  **Dimension Independence Check**:
    -   **Task**: Calculate correlation between 'Consistency' and 'Novelty/Feasibility' scores.
    -   **Logic**: If correlation > 0.8, flag 'Halo Effect' and trigger multi-rater ensemble (3 distinct models) if feasible.
7.  **Validation**: Compare proxy scores against the N=50 Gold Standard. Compute Pearson correlation. If r < 0.6, flag the proxy model as invalid.

### Phase 4: Statistical Analysis
1.  **Pre-Study Power Justification (FR-009)**:
    -   **Task**: Calculate required N for Cohen's d=0.5, alpha=0.025 (Bonferroni corrected).
    -   **Logic**: Confirm N=500 is sufficient. If not, state limitation.
2.  **Linear Mixed Effects (LME) Model**:
    -   **Formula**: `Creativity_Score ~ Model_Type * Domain + (1 | Prompt_ID)`
    -   **Fixed Effects**: Model Type (SU-01 vs Baseline), Domain (Olympiad vs OpenSci).
    -   **Random Effects**: Prompt_ID (to account for nested structure).
    -   **Goal**: Test the interaction term `Model_Type:Domain` for significance.
3.  **Power Analysis (Conditional)**:
    -   **Task**: Calculate power for the observed effect size.
    -   **Condition**: Only valid if Proxy Model Validation (r > 0.6) passes.
4.  **Sensitivity**: Re-run LME excluding low-confidence prompts.

## Statistical Rigor & Constraints

-   **Multiple Comparisons**: The study tests the interaction effect and dimension independence. A Bonferroni correction will be applied to the alpha level (0.05 / 2 = 0.025).
-   **Sample Size / Power**: N=500 prompts is planned. A pre-study justification is performed. If power < 0.8, the limitation will be explicitly stated.
-   **Causal Inference**: This is an observational study of model behaviors. Claims will be framed as "associational" (e.g., "models with higher Olympiad accuracy tend to have lower creativity scores") rather than causal.
-   **Measurement Validity**: The proxy model is validated against human experts (FR-008). If correlation < 0.6, the results are considered invalid.
-   **Collinearity**: The 'Novelty' and 'Feasibility' scores may be correlated. Multicollinearity will be checked (VIF) if used in a combined metric.
-   **Compute Feasibility**:
    -   **CPU-First**: All inference uses CPU.
    -   **RAM Limit**: INT4 quantization for the scoring model is critical to fit within 7GB RAM.
    -   **GPU Escape Hatch**: If the SU-01 model requires GPU for *any* reason (e.g., architecture incompatibility), the plan will fail on CPU. No synthetic GPU approximation is planned. The "escape hatch" is the Kaggle GPU runner, but the spec explicitly requires CPU-only for the primary pipeline. If the SU-01 model *cannot* run on CPU, the project will report a "Compute Infeasibility" rather than fabricating a GPU run.

## Risk Mitigation

-   **Dataset Mismatch**: IPhO is excluded; analysis relies on IMO (Math-only). This is documented as a limitation.
-   **Modality Mismatch**: ScienceQA MCQs are converted to open-ended prompts. This is documented as a prompt engineering strategy.
-   **Proxy Model Bias**: The N=50 validation set and Dimension Independence Check ensure the scoring model is not hallucinating or exhibiting halo effects. If it fails, the project halts.
-   **Timeouts**: Hard token limits prevent CI job hangs. Truncated responses are excluded.
-   **Model Availability**: If SU-01 weights are not found, the pipeline fails with a clear error, preventing data fabrication.


## projects/PROJ-921-llmxive-follow-up-extending-achieving-go/specs/001-llmxive-follow-up-extending-achieving-go/data-model.md