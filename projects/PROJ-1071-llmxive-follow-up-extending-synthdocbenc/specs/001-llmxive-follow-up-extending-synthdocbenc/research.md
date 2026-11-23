# Research: llmXive follow-up: extending "SynthDocBench" with Decoupled Retrieval

## Overview

This research phase investigates the "middle-third" bias in long-context Visual Language Models (VLMs) by decoupling retrieval from visual attention. The study compares a static-image baseline against a retrieval-augmented condition to determine if injecting relevant text snippets eliminates positional accuracy degradation.

## Verified datasets

**No external datasets are used.** The study relies entirely on locally generated synthetic documents to ensure precise control over "middle-third" definitions and to avoid the availability issues of existing benchmarks.

- **Synthetic Long Documents (Local Generation)**:
  - **Source**: `code/doc_generator.py`
  - **Format**: Parquet (with base64-encoded images) and PDF.
  - **Relevance**: Generated to contain specific "middle-third" regions with ground-truth answers, ensuring the dataset-variable fit for the hypothesis.

*Note: The previously cited HuggingFace SynthDocBench chart dataset was removed as it does not contain the required long-form positional metadata.*

## Dataset Strategy

| Dataset | Source/URL | Loading Method | Variables Used | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Synthetic Long Documents** | Local (`data/raw/generated_docs.parquet`) | `pandas.read_parquet` | `doc_id`, `page_image`, `question`, `answer`, `page_number`, `doc_length`, `question_position` | Generated locally. `question_position` is derived from `page_number` and `doc_length`. |
| **OCR Text Index** | Derived from Synthetic Docs (via Tesseract) | In-memory FAISS index | `page_text`, `page_number`, `doc_id` | Generated locally; not a pre-existing dataset. |

*Dataset-variable fit confirmation*: The locally generated dataset explicitly includes `page_image` (visual input), `question` (query), `answer` (ground truth), and `page_number` (positional metadata). These variables are sufficient to define the "middle-third" region and compute the accuracy delta. No external data sources are needed.

## Methodology

### Phase 1: Baseline Reproduction (Static Image)
1. **Data Preparation**: Run `code/doc_generator.py` to create 200 synthetic documents. Filter for documents with length ≥ 100 pages to ensure "middle-third" definition is meaningful.
2. **OCR & Indexing (Pre-computation)**: Run Tesseract on all pages to generate a text index. Store page-level text and coordinates. *Note: This step is computationally intensive but CPU-tractable.*
3. **Baseline Inference**: For each of the 7 selected VLMs:
   - Load the model in CPU mode (quantized if necessary).
   - Present the full document image (or a sliding window if context limits prohibit full image) with the question.
   - Record the generated answer and compute accuracy against ground truth.
   - Stratify results by question position (First, Middle, Last third).

### Phase 2: Retrieval-Augmented Inference
1. **Query Generation**: For each question, generate a search query (e.g., using the question text directly).
2. **Retrieval**: Query the FAISS index (CPU) to retrieve the top-k relevant text snippets.
   - **Ground Truth Definition**: A retrieval is considered a "True Positive" if the retrieved snippet contains the ground-truth answer text OR has a semantic similarity score ≥ 0.85 (cosine similarity) to the ground-truth answer. This is independent of the question's positional metadata.
   - **Constraint**: Enforce a strict token limit (≤ 2048 tokens) for injected text.
   - **Metric**: Measure retrieval precision/recall against the ground-truth answer text.
3. **Augmented Inference**: Present the original document image + retrieved text snippets + question to the VLM.
   - **Constraint**: Ensure total token count (image tokens + text tokens) does not exceed model limits.
   - Record accuracy for "middle-third" questions.

### Phase 3: Statistical Analysis
1. **Delta Calculation**: Compute `Accuracy_Retrieval - Accuracy_Baseline` for "middle-third" questions per model.
2. **Correlation Analysis**:
   - Variable X: Model's native context window size (varying token capacities).
   - Variable Y: Accuracy recovery delta.
   - Test: Spearman rank correlation (non-parametric).
   - **Hypothesis**: Smaller context models show greater recovery (negative correlation).
   - **Limitation**: With N=7 models, statistical power for correlation is extremely low. The result is reported as an **exploratory descriptive trend**, not a statistically significant generalizable claim. No p-value threshold is claimed for generalizability.
3. **Control Check**: Verify accuracy on "First/Last" thirds to ensure retrieval does not degrade performance on well-attended regions.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Since we are testing 7 models across 2 conditions, we will apply a Bonferroni correction or False Discovery Rate (FDR) control if performing individual hypothesis tests per model. The primary claim relies on the aggregate correlation, which is a single descriptive metric.
- **Power Justification**: The study uses up to 200 documents. However, the correlation analysis is performed across only 7 models (N=7). **Statistical power for correlation is determined by N=7, not the document count.** With N=7, the power to detect a significant correlation is low. The analysis is reframed as **exploratory**; any observed trend is descriptive, and no claim of statistical significance (p < 0.05) is made for the correlation coefficient itself.
- **Causal Framing**: This is an observational study of model behavior under two input conditions. Claims about "attentional bottlenecks" will be framed as associational findings derived from the intervention, not causal proofs of internal architecture.
- **Measurement Validity**: The "middle-third" definition is fixed by the generation protocol (pages 34-66 of a 100-page doc). No sensitivity analysis is planned as the definition is standard.
- **Collinearity & Confounding**: Context window size and model architecture are confounded. Smaller models may be less capable generally, not just due to context limits.
  - **Mitigation**: We will stratify the descriptive analysis by model family (e.g., Llama-based vs. others) where possible to partially control for architecture. However, the limitation remains that context size is a proxy for architectural differences.
- **Retrieval Ground Truth**: To avoid circularity, retrieval precision/recall is measured against the **semantic similarity to the answer text**, not the page number. This ensures the retrieval system is evaluated on finding the *content*, not the *location*.

## Feasibility & Sample Size Strategy

- **CPU-First Strategy**:
  - **Retrieval**: `faiss-cpu` is highly efficient and fits within 7 GB RAM.
  - **VLM Inference**: Models will be selected/quantized to run on CPU.
 - **Time Limit**: The full pipeline (a large corpus × 7 models × 2 conditions) is estimated to take [deferred] on CPU, exceeding the 6-hour limit.
  - **Dynamic Sampling**: The pipeline will first run a pilot on a small set of documents to measure per-document runtime. Based on this, the maximum feasible sample size (N) will be calculated to fit within 6 hours.
  - **Reporting**: If N < 200, the reduced sample size and its impact on the power to detect the "middle-third" bias will be explicitly reported as a limitation. The 6-hour limit applies to the *feasible* sample size, not the theoretical full set.
- **No GPU Escape Hatch**: To maintain the integrity of the "Resource-Constrained Evaluation" (Constitution Principle VI), the GPU escape hatch is **not** used for the main hypothesis test. The sample size is reduced to fit CPU constraints.

## Risks & Mitigations

- **Risk**: OCR fails on complex layouts.
  - **Mitigation**: Skip retrieval for affected pages; fallback to empty string. Log failure rate.
- **Risk**: VLM hallucinates despite correct context.
  - **Mitigation**: Strict exact-match or semantic similarity scoring against ground truth.
- **Risk**: Token overflow in augmented input.
  - **Mitigation**: Enforce strict truncation of retrieved text to ≤ 2048 tokens.
- **Risk**: Low statistical power due to N=7 models.
  - **Mitigation**: Frame results as exploratory trends; avoid inferential claims.