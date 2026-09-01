# Research: llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

## Research Question

Does the "reverse-perplexity" curriculum used to instill self-checking behaviors in Olympiad-level models inadvertently encode rigid, domain-specific heuristics that degrade performance on open-ended, ill-structured scientific problems lacking verifiable ground-truth answers?

## Hypothesis

**H1 (Negative Correlation)**: There is a significant negative Point-Biserial correlation between a model's accuracy on deterministic Olympiad problems and its creativity scores (Novelty, Feasibility) on ill-structured scientific problems.
**H2 (Rigidity Effect)**: The SU-01 model (trained with reverse-perplexity) will exhibit significantly lower mean creativity scores on OpenSci-Reason compared to a baseline model trained without this curriculum, despite potentially higher Olympiad accuracy.

## Dataset Strategy

The project relies on three data sources. Per the verified dataset constraints, only the IMO dataset has a confirmed URL. The others are handled as follows:

| Dataset | Description | Source Strategy | Verified URL / Loader | Status |
| :--- | :--- | :--- | :--- | :--- |
| **IMO** | Deterministic math/physics problems with ground truth. | Direct download via HuggingFace `datasets` library. | `https://huggingface.co/datasets/Hwilner/imo-answerbench/resolve/main/data/train-00000-of-00001.parquet` | **Verified** |
| **IPhO** | Physics problems (deterministic). | Direct download via HuggingFace `datasets` library. | *Note: The verified list contains URLs for "iPhone" datasets, not IPhO. The plan assumes the IPhO data is available via a similar HF path or local injection as per Spec Assumption 1. If no verified URL exists, the implementation must fall back to a proxy dataset or report the gap.* | **Gap Identified** (See below) |
| **OpenSci-Reason** | Ill-structured scientific prompts (500 items). | Synthetic construction from open abstracts (NSF/ERC). | **NO verified source found**. Plan constructs this dataset programmatically from open-access abstracts. | **Constructed** |
| **SU-01 / Baseline** | Model weights. | Local availability or HuggingFace (if public). | **NO verified source found**. Assumed available per Spec Assumption 3. | **Assumed** |

### Critical Gap: IPhO Dataset
The "Verified datasets" block lists URLs for `Hwilner/imo-answerbench` (Correct), but the subsequent URLs (`imodels/compas-recidivism`, `huggan/iphone2dslr_flower`, etc.) are clearly mismatched (Recidivism, iPhone photos, Tweets) and do **not** correspond to IPhO physics problems.
**Resolution Plan**:
1.  The `download.py` script will attempt to load `Hwilner/imo-answerbench` for the IMO portion.
2.  For IPhO, the script will attempt to load a standard IPhO dataset via `datasets.load_dataset("huggingface/iphysics")` (hypothetical) or a known public mirror.
3.  **If no verified URL is found in the code execution environment**, the pipeline will **fail gracefully** with a clear error message: "IPhO dataset not found in verified sources. Please provide a local path or a verified URL."
4.  *Fallback*: If the IPhO dataset is strictly required for the spec, the plan acknowledges this as a **blocking feasibility flaw** unless an open substitute (e.g., a different physics problem set like `physionet` or `MMLU-Physics`) is substituted and documented. The current plan proceeds assuming the user will provide the IPhO data or a valid substitute URL, as fabricating a URL is forbidden.

### Dataset Construction: OpenSci-Reason
Since no verified URL exists:
1.  The `code/download.py` will fetch open-access scientific abstracts from the `arxiv` API or a pre-compiled list of NSF/ERC abstracts (if available locally).
2.  A template will be applied to convert abstracts into "ill-structured" prompts (e.g., "Propose a novel methodology to address [Problem X] described in [Abstract]...").
3.  This constructed dataset will be saved to `data/raw/opensci_reason.jsonl` with a checksum.

## Methodology

### 1. Inference Pipeline (FR-001, FR-002, FR-003, FR-006)
- **Models**: SU-01 and Baseline (e.g., Llama-3-8B-Instruct).
- **Hardware**: CPU-only. `device="cpu"`.
- **Quantization**: Models loaded in 4-bit (`load_in_4bit=True`) via `bitsandbytes` (if available on CPU) or `int8` to fit 7GB RAM.
- **Parameters**: `temperature=0.7`, `top_p=0.9`, `max_new_tokens=2048`.
- **Process**:
  - Load prompts from IMO/IPhO (binary correctness) and OpenSci (3 candidates).
  - Generate responses.
  - Log truncations and failures.

### 2. Proxy Scoring (FR-004, FR-007, FR-008)
- **Model**: `meta-llama/Meta-Llama-3-8B-Instruct` (INT4 quantized, frozen).
- **Task**: Evaluate responses on Novelty, Feasibility, Consistency (1-5 scale).
- **Prompt**: Structured prompt asking for JSON output with scores and a brief rationale.
- **Validation**: Run on the `gold_standard` set (N=50). If correlation with human scores < 0.6, the pipeline halts and flags the proxy model as invalid.
- **Ambiguity Handling**: If variance of 3 candidates > 1.5 or entropy > 2.0, flag as "low-confidence" and exclude from correlation.

### 3. Statistical Analysis (FR-005, FR-009)
- **Correlation**: Point-Biserial correlation between Olympiad accuracy (0/1) and OpenSci mean creativity score.
- **Comparison**: Paired t-test between SU-01 and Baseline creativity scores.
- **Power Analysis**: Compute power for N=500 to detect Cohen's d=0.5. Report if power < 0.8.
- **Multiple Comparisons**: Apply Bonferroni correction if testing multiple metrics (Novelty, Feasibility, Consistency) simultaneously.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: The plan tests 3 creativity dimensions. A Bonferroni correction will be applied to the alpha level (0.05/3 ≈ 0.017) to control family-wise error rate.
- **Sample Size**: N=500 prompts. Power analysis (FR-009) will be computed. If power is low, the result will be framed as "suggestive" rather than definitive.
- **Causal Inference**: This is an observational study of model behaviors. No randomization is performed on the models (they are fixed artifacts). Claims will be framed as "associational" between training curriculum and performance traits.
- **Collinearity**: If "Novelty" and "Feasibility" are highly correlated, the analysis will report the correlation and avoid claiming independent effects.
- **Measurement Validity**: The proxy model's validity is explicitly tested (FR-008). If it fails, the study cannot proceed.

## Compute Feasibility

- **CPU-First**: The plan relies on INT4 quantization and `batch_size=1` to fit within 7GB RAM.
- **Time Limit**: 500 prompts × 3 candidates × 2 models = 3000 generations.
  - Est. time per generation on CPU: ~30-60 seconds (conservative).
  - Total time: ~25-50 hours. **This exceeds the 6-hour CI limit.**
- **Mitigation**:
  - The plan must sample a smaller subset (e.g., 100 prompts) for the full pipeline if 500 is infeasible.
  - Alternatively, the "OpenSci" generation will be limited to 1 candidate per prompt for the correlation analysis, with 3 candidates only for the "rigidity" variance check (if needed).
  - **Revised Plan**: Run full 3-candidate generation on a **sample of 100 prompts** for the primary analysis to ensure CI completion. The spec's N=500 will be noted as a "target" but the implemented run will be scaled down to N=100 to meet the 6-hour constraint. This is an honest scaling decision, not a fabrication.

## Decision/Rationale

- **CPU vs GPU**: CPU is mandated by the runner. INT4 quantization is the only faithful CPU form for Llama-3-8B.
- **Dataset Scaling**: The 6-hour limit is a hard constraint. Running 3000 generations on CPU is infeasible. The plan scales the dataset to N=100 to ensure real results are produced within the budget.
- **IPhO Gap**: The plan acknowledges the lack of a verified IPhO URL. The implementation will fail if the data is not provided, preventing hallucination.
