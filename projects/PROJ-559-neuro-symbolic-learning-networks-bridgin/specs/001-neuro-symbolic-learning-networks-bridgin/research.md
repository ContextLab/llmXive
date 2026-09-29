# Research: Neuro-Symbolic Learning Networks

## Research Question

Does a neuro-symbolic explanation approach (combining neural narrative with symbolic trace) improve student reasoning accuracy, response time, and self-reported comprehension compared to neural-only or symbolic-only explanations in mathematics education **within the ASSISTments domain**?

## Background & Motivation

Educational research increasingly explores the "black box" of AI tutors. While Large Language Models (LLMs) provide fluent explanations (System 1 intuition), they often lack logical rigor. Conversely, symbolic solvers provide exact traces (System 2 reasoning) but can be opaque to learners. This project investigates whether bridging these modes yields superior pedagogical outcomes.

## Verified Datasets

The following datasets are verified and used for this project. **Only these sources are cited.**

| Dataset | Purpose | Verified Source URL |
| :--- | :--- | :--- |
| **ASSISTments** | Source of math/logic problems for generation and simulation. | https://huggingface.co/datasets/OloriBern/assistments-dataset/resolve/main/skill_builder_data_corrected.csv |
| **Khan Academy** | Secondary source of problems to ensure diversity (if available via open proxy). | *No direct verified URL for full Khan dataset in block; using ASSISTments as primary with partial ingestion.* |
| **Human Pilot Data** | Calibration data for BKT simulator (≥50 participants). | *Collected via mock survey interface (T030b) or existing public dataset if available.* |
| **Real Student Data** | Final analysis data (≥200 participants). | *Collected via mock survey interface (T030b) or existing public dataset if available.* |

*Note: The spec mentions Khan Academy, but the `# Verified datasets` block does not contain a verified, direct-download URL for the full Khan Academy dataset. The plan relies on the ASSISTments dataset (verified) as the primary source. If Khan data is strictly required, the pipeline proceeds with ASSISTments only and logs the failure to meet the dual-source requirement (FR-001 partial).*

## Dataset Strategy

### Primary Data Source: ASSISTments
The `skill_builder_data_corrected.csv` from the verified Hugging Face source will be used.
- **Ingestion**: Downloaded via `code/data/download_assistments.py` with a A timeout of several minutes will be applied. (FR-007).
- **Validation**: Schema validated against `contracts/problem.schema.yaml` (T012a).
- **Subset**: A representative subset of problems (e.g., algebra, geometry) will be selected to ensure the dataset contains the necessary variables (problem text, solution steps, difficulty).

### Secondary Data Source: Khan Academy (Optional)
- **Ingestion**: Attempted via `code/data/download_khan.py`.
- **Failure Handling**: If the download fails (timeout or missing URL), the pipeline logs `ERROR: Failed to download Khan Academy within 300 seconds – aborting pipeline` for the Khan step, but **proceeds** with ASSISTments data only. The final report will note that FR-001 was partially met (single source).
- **Scope Reduction Protocol**: **If only ASSISTments data is available, the study's external validity is explicitly limited to the ASSISTments domain.** The final report will state: "Findings are generalizable only to the ASSISTments corpus; claims regarding broader mathematics education are not supported due to single-dataset constraints."

### Human Data Acquisition Protocol (T030b)
- **Method**: Real human pilot data (≥50) and real student data (≥200) are collected via a mock survey interface (e.,g., Google Forms/Qualtrics) or ingested from a verified public dataset (e.g., OpenML Human Learning).
- **Fallback**: If real human data is unavailable after 48 hours, the project triggers the **Scope Reduction Protocol**: the study is reclassified as a "Simulation Feasibility Study," and all claims about "real student performance" are disabled. The BKT simulator is not calibrated, and the comparative analysis is limited to the simulated environment only.

### Data Limitations & Mitigation
- **Missing Variables**: If the ASSISTments dataset lacks specific metadata (e.g., explicit "difficulty" scores), these will be inferred via a lightweight heuristic or derived from problem length/complexity, documented in `research.md`.
- **Dataset Size**: The full dataset may exceed RAM. Streaming (`datasets.load_dataset(..., streaming=True)`) will be used to process problems in batches.

## Methodological Rigor & Statistical Plan

### Experimental Design
A **between-subjects design** where each simulated student is assigned to exactly one explanation condition per problem.
1.  **Neural-Only**: LLM-generated narrative.
2.  **Symbolic-Only**: Rule-based step-by-step trace.
3.  **Neuro-Symbolic**: Hybrid of both.

*Constraint*: A `student_id` cannot appear for the same `problem_id` in multiple conditions. This prevents carryover effects (learning from the first explanation invalidating the second).

### Statistical Analysis
- **Model**: Linear Mixed-Effects Model (LMM) using `statsmodels` (Python) or `lme4` (R).
  - **Fixed Effects**: `explanation_condition`, `prior_knowledge` (derived), `problem_difficulty`, `data_source` (simulated vs. real).
  - **Random Effects**: Random intercepts for `problem_id` and `student_id`.
- **Multiple Comparison Correction**: Bonferroni or Holm-Bonferroni correction applied for pairwise comparisons (Neuro-Symbolic vs. Neural, etc.) to control family-wise error rate.
- **Power Analysis**: Sample size of [deferred] students per condition ([deferred] total) is targeted to achieve power ≥ 0.80 for effect sizes ≥ 0.1 (FR-009).
- **Causal Inference**: As this is a simulation, claims are framed as "associational" unless the simulation explicitly models a causal mechanism. The inclusion of `data_source` (simulated vs. real) as a fixed effect controls for potential biases (FR-011). **Crucially, if real human pilot data (T030b) is missing, the study is scope-reduced to "Simulation Feasibility" and no causal claims about real learners are made.**

### Measurement Validity
- **Response Time**: Simulated based on BKT probability of knowledge and explanation complexity.
- **Comprehension**: Likert scale (1-5) derived from a logistic function of **knowledge_gap** (student's current knowledge vs. problem difficulty) and **explanation_complexity**. This avoids circularity by not deriving comprehension from correctness.
- **Collinearity**: If "difficulty" and "response time" are definitionally related, they will be reported descriptively, and collinearity acknowledged in the model diagnostics.

## Compute Feasibility

### CPU-First Strategy
- **LLM Inference**: A **B-parameter model** (e.g., `TinyLlama-1.1B-Chat-v1.0` in 4-bit precision) will be used to fit within 7 GB RAM on the -core CPU runner. This is a conservative choice to ensure stability.
- **Simulation**: The BKT model is purely algorithmic (matrix operations) and runs efficiently on CPU.
- **Analysis**: `statsmodels` mixed-effects models are optimized for CPU and can handle the target sample size (6k rows) within the -hour window.

### GPU Escape Hatch
- If the LLM inference fails due to memory constraints on the CPU runner, the pipeline will automatically detect the failure and re-run the generation step on a **Kaggle GPU** (GB VRAM) using the same code with `device="cuda"`.
- The plan does **not** fabricate a CPU approximation for a GPU-only task; it relies on the auto-offload mechanism for genuine GPU requirements.

## Decision/Rationale

- **Why ASSISTments?** It is the only math/education dataset with a verified, direct-download URL in the provided block.
- **Why Partial Ingestion?** To satisfy FR-001's "attempt" requirement while avoiding a total pipeline abort if Khan Academy is unavailable. **Scope Reduction Protocol limits generalizability claims if only one dataset is used.**
- **Why Mixed-Effects?** Accounts for the hierarchical nature of the data (students nested within problems) and controls for problem difficulty.
- **Why Human-Only Calibration?** To avoid circular validation (synthetic pilot tuning) and ensure the BKT model approximates real cognitive processes.
- **Why 0.5B Model?** To guarantee CPU feasibility on the 7GB RAM runner, avoiding the high risk of OOM with 1B+ models.