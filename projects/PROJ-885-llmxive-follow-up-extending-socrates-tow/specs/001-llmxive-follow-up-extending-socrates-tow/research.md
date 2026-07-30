# Research: llmXive Follow-up: Dynamic Socio-Cognitive State Injection

## 1. Research Question
Does the explicit injection of dynamically inferred socio-cognitive state signals into an LLM mediator's context significantly increase consensus gap closure in high-emotion, culturally diverse conflict scenarios compared to static prompting?

## 2. Dataset Strategy

### Verified Datasets
The study relies on the **SoCRATES** evaluation suite and its associated prompts.

| Dataset Name | Source URL | Variables Needed | Fit Verification |
| :--- | :--- | :--- | :--- |
| **SoCRATES Evaluation Suite** | `https://huggingface.co/datasets/SoCRATES/socrates-eval` (Verified via HuggingFace API) | `conflict_type`, `ideal_resolution`, `dialogue_prompts` | **Verified**: The suite provides the prompts and ideal resolutions. **Derivation**: Trajectories with `emotional_reactivity` and `cultural_identity` metadata are *synthesized* by running the SoCRATES prompts with specific seed attributes to generate the required dialogue history and metadata tags. |

*Note: No access-gated data is used. All data is programmatically downloadable or derivable via `datasets.load_dataset` and local generation scripts.*

### Dataset Variables & Mapping
- **emotional_reactivity**: Generated metadata (0.0-1.0) used for FR-001 oversampling (>40% high reactivity).
- **cultural_identity**: Generated metadata (tags) used for FR-001 oversampling (>40% diverse identity).
- **dialogue_history**: Generated dialogue text, input for FR-002 (State Classifier) and FR-003 (Injection).
- **ideal_resolution**: Ground truth summary from SoCRATES, used for FR-005 (Consensus Gap Score).

### Data Availability & Feasibility
- **Download Method**: `datasets.load_dataset("SoCRATES/socrates-eval", streaming=True)` for prompts.
- **Synthesis**: A local script `src/data/generate_trajectories.py` uses the prompts to generate dialogue trajectories with injected metadata (emotional_reactivity, cultural_identity) to satisfy FR-001.
- **Storage**: Raw prompts in `data/raw/socrates_prompts.parquet`; Derived trajectories in `data/processed/filtered_trajectories.jsonl` (checksummed).
- **Sample Size**: Target N=500 trajectories. **Design**: Repeated Measures (each trajectory evaluated by all LLMs). This ensures N=500 per comparison, maintaining power for a medium effect size (Cohen's d is expected to be moderate.) at α=0.05, power=0.80.

## 3. Methodology

### 3.1 Data Generation (FR-001)
- **Process**: Use SoCRATES prompts to generate dialogue trajectories. Inject metadata tags (`emotional_reactivity`, `cultural_identity`) based on seed parameters to ensure >40% of the final dataset falls into high-difficulty categories.
- **Output**: `data/processed/filtered_trajectories.jsonl`.

### 3.2 State Classifier (FR-002) - *Feature Isolation & Validity*
- **Model**: Logistic Regression (scikit-learn).
- **Input Features**: **Dynamic text features only**. TF-IDF or Bag-of-Words extracted from the *last N turns* of the `dialogue_history`.
  - *Exclusion*: `emotional_reactivity` and `cultural_identity` metadata are **NOT** used as features for prediction. They are used *only* for oversampling (FR-001) and ground truth labeling (if derived from metadata).
- **Training Labels**: Derived from the `conflict_type` metadata (if available) or a rule-based proxy that maps dialogue patterns to states (e.g., "escalating", "cultural-friction").
- **Feature Isolation**: The classifier uses **surface text features** (TF-IDF). The evaluator (Section 3.4) uses **semantic embeddings** (sentence-transformers). These feature spaces are mathematically distinct, preventing circular validation.
- **Threshold**: Confidence threshold (e.g., 0.7) determines injection. Low confidence -> "neutral-monitoring".

### 3.3 Experiment Execution (FR-003, FR-004) - *Repeated Measures*
- **Models**: 8 LLMs (e.g., `llama-3-8b`, `mistral-7b`, etc.) running via `transformers` with `device="cpu"` and -bit/8-bit quantization.
- **Conditions**:
  - **Static**: Base system prompt + `ideal_resolution` hint.
  - **Adapter**: Base prompt + Dynamic State Instruction (e.g., "De-escalate: Participant A is showing high reactivity").
- **Execution**: **Repeated Measures**. Every trajectory (N=500) is run through **all 8 LLMs** under both conditions. This ensures N=500 per statistical comparison, preserving power.
- **Timeout Handling**: Retry mechanism (a limited number of attempts, exponential backoff). Skipped samples logged.

### 3.4 Evaluation (FR-005) - *CPU-Compatible Metric*
- **Metric**: Consensus Gap Closure = 1 - CosineSimilarity(Embedding(LLM_Output), Embedding(Ideal_Resolution)).
- **Evaluator**: **Sentence-Transformers** (`all-MiniLM-L6-v2`). This model is CPU-compatible, lightweight, and provides a semantic distance metric.
- **Independence**: The evaluator uses **semantic embeddings** of the full resolution text. The classifier uses **surface text features** of the dialogue history. These are orthogonal. The evaluator does **not** use the state labels injected.

### 3.5 Statistical Analysis (FR-006, FR-007) - *Bounded Data Handling*
- **Data Transformation**: Consensus Gap scores are bounded [0, 1]. A **logit transformation** is applied to the gap scores before testing to handle skewness. If transformation fails or data is too sparse, **Wilcoxon signed-rank test** is used.
- **Normality Check**: Shapiro-Wilk test on difference scores (Adapter - Static). **Record p-value** in report.
- **Test Selection**:
  - If Normal (p > 0.05): Paired t-test on logit-transformed data.
  - If Non-Normal (p <= 0.05): Wilcoxon signed-rank test.
- **Correction**: Holm-Bonferroni correction applied across the multiple LLM comparisons.
- **Analysis Population**:
  - **Primary**: Full Adapter set (including 'neutral-monitoring' injections) to reflect real-world deployment.
  - **Sensitivity**: Separate analysis for 'High-Confidence Adapter' vs. 'Static' to check for dilution bias.
- **Significance**: p < 0.05 (corrected) flags `is_significant: true`.

## 4. Compute Feasibility & Rationale

| Method | Platform | Rationale |
| :--- | :--- | :--- |
| **Logistic Regression** | CPU | Trivial for moderate RAM capacity.; fits within 30s. |
| **LLM Inference** | CPU (GGUF/Quantized) | Low-bit quantization of large-scale models fits in ~6GB RAM.. If a model fails, it is excluded (Assumption 2). No GPU required. |
| **Sentence-Transformers** | CPU | `all-MiniLM-L6-v2` is lightweight and runs efficiently on CPU. |
| **Statistical Tests** | CPU | `scipy.stats` runs instantly on N=500. |
| **Data Streaming** | CPU | `streaming=True` avoids loading full dataset into RAM. |

**Decision**: All methods are CPU-first. No GPU escape hatch is needed as the study design (8-bit quantization, sentence-transformers, N=500) fits within the GitHub Actions free tier constraints.

## 5. Assumptions & Limitations
- **Assumption**: The SoCRATES prompts can be used to generate valid conflict trajectories with the required metadata.
- **Assumption**: 8-bit quantized models provide sufficient quality for mediation tasks.
- **Limitation**: If N < 200 after filtering, power may be insufficient for small effects. This will be reported honestly (Assumption 4).
- **Limitation**: Synthetic data may not fully capture real-world cultural nuances.
- **Limitation**: The 'neutral-monitoring' state may dilute the effect size in the primary analysis; sensitivity analysis addresses this.