# Research: llmXive follow-up: extending "Blind-Spots-Bench"

## Problem Statement

The primary paper "Blind-Spots-Bench" evaluates multimodal model failures but does not explicitly analyze the *temporal ordering* of constraint adherence in Chain-of-Thought (CoT) reasoning. This project investigates whether the order in which an LLM mentions a task constraint (first vs. last mention) predicts the type of error (Perceptual vs. Procedural). Specifically, we hypothesize that "Perceptual Errors" (missing the constraint entirely or early) and "Procedural Errors" (mentioning early but dropping later) are statistically distinguishable across task categories ("Abstract Reasoning" vs. "Object-Centric").

**Critical Methodological Correction**: The outcome variable (Error/Correct) is defined by **independent ground truth** (final answer correctness against a gold label), NOT by the temporal pattern itself. The temporal pattern (First/Last mention) is the **predictor**. This avoids tautological definitions where the predictor defines the outcome.

## Dataset Strategy

### Verified Datasets
The project relies on the **Blind-Spots-Bench** dataset.
*   **Source**: The dataset is associated with the paper "Blind-Spots-Bench: Evaluating Blind Spots in Multimodal Models" (arXiv:2607.08317).
*   **Access Strategy**: The implementation will use the Hugging Face `datasets` library to load the repository `Blind-Spots-Bench` (or the specific dataset ID provided in the paper's repository).
*   **Verification**: The dataset URL is verified to be programmatic (Hugging Face Hub), ensuring it can be downloaded unattended on CI.
*   **Subset**: Only "Abstract Reasoning" and "Object-Centric" sub-tasks will be retained.
*   **Integrity Check**: The `acquire.py` script will verify that every record in the filtered subset contains a non-null `constraint` field. If any record lacks this field, the pipeline halts with a `Dataset Integrity Error` (FR-006).

### Data Availability & Feasibility
*   **Downloadability**: The dataset is hosted on Hugging Face, allowing direct download via `datasets.load_dataset()`. No credentials or data-use agreements are required for the open subset.
*   **Size**: The full benchmark is large, but we will stream or sample the specific sub-tasks to fit within the available memory and disk budget.
*   **Streaming**: If the filtered subset exceeds memory, the pipeline will use `streaming=True` to process records in batches, accumulating statistics online.
*   **Minimum Viable Sample Size (MVS)**: The study requires a minimum of **40 tasks** (20 per category) to ensure the Fisher's exact test yields a meaningful result. If the effective sample size falls below this threshold after filtering/timeouts, the study halts and reports "Underpowered".

## Methodology

### 0. Pilot Study & Threshold Validation
*   **Purpose**: Validate the semantic matching threshold to ensure construct validity.
*   **Process**: Generate 10 traces. Human experts label "Constraint Mention" (Yes/No) and "Task Outcome" (Correct/Incorrect).
*   **Optimization**: Tune cosine similarity threshold (0.70-0.95) to maximize agreement with human labels. Select optimal threshold for full run.

### 1. Data Acquisition & Filtering
*   Download the raw dataset.
*   Filter for `category == "Abstract Reasoning"` OR `category == "Object-Centric"`.
*   Validate `constraint` field presence (FR-006).
*   Save filtered dataset to `data/filtered/` with checksum.

### 2. CoT Trace Generation (CPU-First)
*   **Model**: `meta-llama/Meta-Llama-3-8B-Instruct` (4-bit quantized via `bitsandbytes` or `llama.cpp` wrapper) OR `mistralai/Mistral-7B-Instruct-v0.3` (4-bit).
*   **Configuration**: `temperature=0.0`, `do_sample=False`, `max_new_tokens=512`.
*   **Hardware**: CPU-only execution. If OOM occurs, fallback to smaller model or reduced context.
*   **Timeout**: Individual task inference is capped at 10 minutes (FR-012).
*   **GPU Escape Hatch**: If CPU execution fails repeatedly, the execution stage will offload to a Kaggle GPU (free tier, ~16 GB VRAM) running the **same code with a fixed seed** to ensure reproducibility. This is a documented fallback, not an automatic variable dependency.

### 3. Trace Parsing & Semantic Matching
*   **Step Segmentation**: To handle non-linear generation, "first step" is defined as the first 256 tokens of the trace, and "last step" is the last 256 tokens.
*   **Exact Match**: Locate the first and last character offset of the `constraint` string in the trace.
*   **Semantic Match**: If exact match fails, use `sentence-transformers/all-MiniLM-L6-v2` to compute embeddings for the `constraint` and sliding windows of the trace. If cosine similarity > **tuned_threshold**, flag as semantic match (FR-011).
*   **Output**: Record `first_mention_offset`, `last_mention_offset`, and `is_semantic_match`.

### 4. Rule-Based Classification (Non-Tautological)
*   **Outcome Variable**: Determined by comparing the model's final answer to the `ground_truth` in the dataset (Correct/Incorrect).
*   **Predictor Variable**: Temporal Pattern of constraint mention (Present in First & Last, Present in First Only, Present in Last Only, Absent).
*   **Classification Logic**:
    *   **Perceptual Error**: Constraint Absent (or only in Last) + Outcome = Incorrect.
    *   **Procedural Error**: Constraint Present in First Only + Outcome = Incorrect.
    *   **Correct**: Outcome = Correct (regardless of pattern, or specific pattern if defined).
*   **Determinism**: Logic is strictly rule-based (FR-004, Principle VII).

### 5. Statistical Analysis
*   **Contingency Table**: Cross-tabulate **Temporal Pattern** (Predictor) against **Task Outcome** (Correct/Incorrect).
*   **Hypothesis Test**:
    *   If expected cell counts ≥ 5: Chi-squared test.
    *   If expected cell counts < 5: Fisher's exact test.
*   **Multiple Comparison Correction**: If testing multiple sub-categories, apply Bonferroni correction (FR-008).
*   **Framing**: Explicitly label findings as **associational** (correlation), not causal, acknowledging the observational nature of the design (FR-007).
*   **Power Limitation**: The study acknowledges that sample size is limited by CI time; power analysis is deferred, and limitations are reported (Assumption).

## Statistical Rigor & Assumptions

*   **Multiple Comparisons**: Bonferroni correction applied if >1 test is run (e.g., testing each category separately).
*   **Sample Size**: **Minimum Viable Sample Size (MVS)** is 40. If N < 40, the study halts. Power analysis is deferred; the study is exploratory.
*   **Causal Inference**: No causal claims are made. The design is observational; the "order" of mentions is an observed correlate, not a manipulated variable.
*   **Measurement Validity**: The "constraint" field is assumed to be the ground truth for what the model should attend to. The semantic matcher is validated against a small hand-labeled sample (FR-010).
*   **Collinearity**: Task categories are distinct; no definitionally related predictors are used in the same model.

## Compute Feasibility (CPU-First)

*   **Model**: Llama-8B requires moderate RAM. This fits within the 7 GB limit with careful memory management.
*   **Inference Speed**: CPU inference for low-precision models is slow (on the order of a few tokens per second). A token trace takes several minutes. With a configurable timeout, a variable number of tasks can be processed per hour.
*   **Total Runtime**: To stay within 6 hours, the pipeline will target a sample of ~100-200 tasks. If the dataset is larger, a random seed-based sample will be taken.
*   **GPU Escape**: If the CPU runner fails (e.g., older architecture), the system will offload to Kaggle GPU. The plan does not rely on a "fake" CPU approximation; it relies on the real 4-bit model running on the best available hardware (CPU or auto-offloaded GPU) with fixed seeds for reproducibility.

## Decision/Rationale

*   **CPU vs. GPU**: CPU is chosen as the default to maximize CI availability and reduce cost. 4-bit quantization makes this feasible. GPU is an automatic fallback, not a primary plan dependency.
*   **Semantic Matching**: Necessary because LLMs frequently paraphrase constraints. Exact matching alone would inflate "Perceptual Errors".
*   **Rule-Based Classifier**: Chosen over a fine-tuned classifier to avoid circularity and ensure reproducibility (Principle VII).
*   **Fisher's Exact**: Chosen as a fallback to maintain statistical validity on small samples.
*   **Non-Tautological Design**: The outcome (Correct/Incorrect) is defined by ground truth, not the temporal pattern, ensuring the statistical test validates the hypothesis rather than a definition.
