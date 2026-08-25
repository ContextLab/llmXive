# Research: llmXive follow-up: extending "ResearchStudio-Idea"

## 1. Research Question & Hypothesis

**Question**: Do the 15 'ideation patterns' derived from top-tier ML conferences generalize to improve the quality of research proposals in resource-constrained, non-ML domains (public health, climate adaptation), or are these patterns specific artifacts of ML research culture?

**Hypothesis**:
*   **H1 (Generalization)**: Pattern-guided proposals (selected by semantic similarity) will receive significantly higher scores in "contextual alignment" and "feasibility" than both the Baseline (generic prompt) and the Random-Pattern (randomly selected patterns) groups.
*   **H0 (Null)**: No significant difference exists between the three groups.

## 2. Dataset Strategy

**Strategy**: The study requires two distinct corpora:
1.  **ML Corpus**: 200 accepted abstracts (source: verified ML dataset).
2.  **Non-ML Corpus**: 200 accepted and 200 rejected abstracts from *Nature Climate Change* and *Health Affairs*.

**Constraint Check & Fallback**:
*   **FR-001** mandates downloading 600 abstracts.
*   **Feasibility**: The spec assumes these are "publicly accessible via direct URL."
*   **Risk**: Many high-impact journals (Nature, Health Affairs) are paywalled.
*   **Mitigation (Fallback)**: If the primary venues return 403/404, the pipeline **automatically switches** to verified open-access alternatives:
    *   **Climate**: `arxiv` dataset (filter by `cs.CY` or `q-bio.QM`), or `pubmed` (Open Access subset).
    *   **Public Health**: `pubmed` (Open Access subset) or `arxiv` (cs.HC).
    *   **Implementation**: `code/01_data_acquisition.py` will attempt the primary source first. If it fails, it logs "Primary source inaccessible, switching to fallback: [Dataset ID]" and proceeds with the open dataset. This ensures the study remains feasible on the free CI tier.

**Verified Datasets**:
*   **ML Corpus**: `huggingface/datasets` (e.g., `bigscience/mt-bench` or similar open ML abstracts).
*   **Non-ML Fallback**: `arxiv` (via Hugging Face), `pubmed` (via Hugging Face).
*   **Action**: The implementation will verify the availability of the fallback datasets. If no open dataset exists, the plan acknowledges this as a **fatal feasibility flaw** and halts.

**Data Flow**:
1.  Download raw JSON/CSV (Primary or Fallback).
2.  Parse and validate (non-empty abstract).
3.  Filter to exactly 200 accepted/200 rejected (non-ML) and 200 (ML).
4.  Store as `data/processed/corpus.jsonl`.

## 3. Methodology

### 3.1 Pattern Mapping (FR-002)
*   **Model**: `sentence-transformers/all-MiniLM-L6-v2` (Quantized).
*   **Reasoning**: Fits within 7 GB RAM on CPU. Provides sufficient semantic similarity for pattern retrieval.
*   **Process**:
    1.  Encode the 15 ML Pattern Cards.
    2.  Encode non-ML problem statements.
    3.  Compute cosine similarity.
    4.  Select top-3 patterns with score ≥ 0.6.

#### 3.1.1 Pattern Mapping Validation (New)
*   **Purpose**: To verify that semantic similarity correlates with *applicability* of the pattern.
*   **Method**: Before full generation, select a hold-out set of 10 problem statements.
*   **Action**: A domain expert manually reviews a representative subset of the top retrieved patterns for each statement.
*   **Gate**: If < 70% of the retrieved patterns are deemed "applicable" by the experts, the pipeline halts and flags the embedding model as unsuitable. This prevents the generation of noise-based proposals.

### 3.2 Proposal Generation (FR-003)
*   **Approach**:
    *   **Experimental Group (Pattern-Guided)**: Prompt LLM with problem statement + top-3 patterns (selected by similarity).
    *   **Control Group 1 (Random-Pattern)**: Prompt LLM with problem statement + **3 randomly selected patterns** (no similarity filter). This decouples "relevance" from "structural utility."
    *   **Control Group 2 (Baseline)**: Prompt LLM with problem statement + "be creative" generic instruction.
*   **Constraints**:
    *   Must generate multiple sets of proposals (including Pattern, Random, and Baseline categories) to ensure sufficient data for analysis.
    *   Must run within 4 hours on CPU.
    *   **Model Choice**:
        *   **Primary**: Hugging Face Inference API (free tier).
        *   **Fallback**: If API rate-limited, switch to **Ollama** running a quantized `Mistral-7B-Instruct-v0.1` (4-bit) via a local Docker container.
        *   **Logic**: `code/03_proposal_generation.py` checks API quota. If exceeded, it spawns the Ollama container and switches endpoints automatically.
    *   **Batching**: Process in batches to manage memory and rate limits.
    *   **Covariate Collection**: Record `token_count` and `generation_time` for every proposal.

### 3.3 Expert Evaluation (FR-004)
*   **Protocol**:
    *   **Blind**: Strip generation metadata.
    *   **Raters**: **Recruit 15 domain experts** (public health/climate) via **Prolific** (or academic networks).
        *   **Budget**: Pre-approved budget of $X (calculated at $Y/hour for 30 mins per expert).
        *   **Inclusion**: ORCID + ≥5 years of domain experience.
    *   **Metrics**: Feasibility, Bottleneck Identification, Contextual Alignment (1-5 Likert).
    *   **Recruitment Mechanism**: The pipeline includes a `code/utils/recruit_experts.py` script that generates the Prolific study link and instructions. The CI pipeline runs in "Dry-Run" mode (validates logic) or "Live" mode (waits for the `ratings.csv` file uploaded by the user after recruitment).
    *   **Inter-Rater Reliability (IRR) Gate**:
        *   **Requirement**: The study design requires recruiting **until** Krippendorff's alpha ≥ 0.6 is achieved for each metric.
        *   **Action**: `code/05_statistical_analysis.py` calculates alpha. If alpha < 0.6, the pipeline halts and outputs "Recruit More Experts" with specific guidance, rather than rejecting the data post-hoc.

### 3.4 Statistical Analysis (FR-005, FR-006)
*   **Tests**:
    *   **Model**: Linear Mixed-Effects Model (LMM) or Paired Test with Covariates.
    *   **Formula**: `Score ~ Group + Token_Count + (1|Problem_Statement)`.
        *   `Group`: Categorical (Pattern, Random, Baseline).
        *   `Token_Count`: Covariate to control for generation artifacts (length bias).
    *   **Normality**: Shapiro-Wilk on residuals.
    *   **Correction**: Benjamini-Hochberg for 3 metrics (Feasibility, Bottleneck, Alignment).
    *   **Effect Size**: Cohen's d (or partial eta-squared for LMM).
*   **Rhetoric**: Explicitly state "associational, not causal" in the conclusion.

## 4. Statistical Rigor & Limitations

*   **Multiple Comparisons**: Addressed via FWER/FDR correction (FR-005).
*   **Power**: N=50 problem statements (paired). Assumed power is sufficient for medium effect (d=0.5) at α=0.05, accounting for inter-rater variance. *Limitation*: Small sample size for creative evaluation; results are preliminary.
*   **Causal Claims**: The study is observational/experimental in design but lacks randomization of the *problem statements* to the *patterns* (patterns are selected by similarity). Claims will be framed as **associational**.
*   **Collinearity**: Patterns are not independent. The analysis treats them as a composite "pattern-guided" condition, but the "Random-Pattern" control isolates the structural effect.
*   **Measurement Validity**: Relies on expert judgment. Inter-rater reliability (Krippendorff's alpha) is a **prerequisite** for analysis (IRR Gate).

## 5. Compute Feasibility (CPU-First)

*   **Embedding**: `all-MiniLM-L6-v2` runs comfortably on CPU (2 cores, 7 GB RAM).
*   **Generation**:
    *   **Option A (API)**: Hugging Face Inference API (Free Tier). Preferred. Offloads compute.
    *   **Option B (Local Fallback)**: Ollama + Mistral-7B (4-bit). Used if API rate-limited. Fits in available RAM.
*   **Analysis**: `statsmodels` and `scipy` are lightweight.
*   **Memory**: 7 GB limit is tight for LLM inference. Batching and the API fallback ensure feasibility.
*   **Time**: A reasonable time limit is sufficient for a sufficient number of generations if API is used. Local fallback may take longer but is within the standard Kaggle time window if offloaded.

## 6. Decision/Rationale

| Component | Choice | Rationale |
| :--- | :--- | :--- |
| **Embedding Model** | `all-MiniLM-L6-v2` (Quantized) | CPU-tractable, fits 7 GB RAM, standard for semantic similarity. |
| **Pattern Control** | **Random-Pattern Group** (No similarity filter) | Decouples semantic relevance from structural utility. |
| **LLM for Generation** | Hugging Face API (Primary) / Ollama (Fallback) | API ensures feasibility. Ollama fallback guarantees execution if API fails. |
| **Statistical Test** | LMM with `Token_Count` covariate | Controls for generation artifacts (length bias). |
| **Correction** | Benjamini-Hochberg | Controls FDR, less conservative than Bonferroni for 3 tests. |
| **Data Source** | Primary (Paywalled) -> Fallback (arXiv/PubMed) | Ensures feasibility on free CI tier. |
| **Evaluation** | Real Experts (Prolific) + IRR Gate | Validates hypothesis with real data. IRR gate ensures quality. |