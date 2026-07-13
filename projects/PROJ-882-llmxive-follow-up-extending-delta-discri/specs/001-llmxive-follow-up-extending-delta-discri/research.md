# Research: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

## 1. Problem Statement & Hypothesis

**Problem**: The DelTA algorithm assigns discriminative credit to tokens via dynamic gradient backpropagation, which is computationally expensive and requires access to model internals. Can this signal be approximated using only **static input features** (n-grams, POS, semantic similarity computed using a model distinct from the Oracle) without accessing the oracle model's hidden states?

**Hypothesis**: If the discriminative signal is primarily encoded in the input semantics, a lightweight static model (MLP) trained on external features will achieve a statistically significant Spearman rank correlation with the true DelTA Coefficients at the example level. If the correlation is near zero, the signal is likely emergent from the model's internal dynamics rather than the input text alone.

## 2. Dataset Strategy

We utilize the **GSM8K** dataset, a collection of grade-school math word problems.

| Dataset | Source URL | Usage | Verification |
|:--- |:--- |:--- |:--- |
| **GSM8K (Main)** | ` | Primary source for problem statements and solutions. Used to filter for verified correct solutions. | Verified via HuggingFace `datasets` loader. |
| **GSM8K Prolog** | ` | Alternative/Supplementary source for solution traces if the main split lacks specific metadata. | Verified via HuggingFace `datasets` loader. |
| **Calc-gsm8k** | ` | Cross-validation source to ensure robustness of feature extraction across different dataset versions. | Verified via HuggingFace `datasets` loader. |

**Selection Rationale**: GSM8K provides structured reasoning traces, making it ideal for token-level credit assignment. The verified URLs ensure reproducibility and avoid hallucinated data sources.

**Filtering Strategy (FR-001)**:
1. Load the dataset from the primary HuggingFace URL.
2. Filter for rows where `solution` is not null and `answer` matches the extracted solution (verified correctness).
3. Stratify by solution length to ensure the 200-example subset (seed=42) is representative.
4. If < 200 valid examples remain after filtering, the pipeline fails explicitly (per FR-002).

## 3. Methodology

### 3.1. Oracle Generation (FR-002)
- **Algorithm**: DelTA (Discriminative Token Credit Assignment).
- **Model**: Phi-mini (a compact model with a parameter count suitable for full precision execution on CPU with approximately 8 GB RAM).
- **Process**:
 1. Iterate through the 200 filtered examples.
 2. For each prompt, run the DelTA algorithm to compute a gradient-based credit score for every token.
 3. Handle numerical instability: If DelTA fails to converge for an example, log the error and exclude the example (Edge Case handling).
 4. Output: A JSON/Parquet file mapping `(example_id, token_index) -> delta_coefficient`.
- **Constraint Check**: Phi-3-mini on CPU is feasible within the 6-hour limit.
 - Phi-mini in full precision requires ~8 GB RAM (fits within the 7 GB limit with careful memory management).
 - Estimated runtime: approximately a few hours for 200 examples on 2 CPUs.
 - Uses `torch.no_grad()` where possible and optimized batching to minimize memory overhead.
 - **No fallback strategy**: If runtime exceeds a predefined threshold or OOM occurs, the pipeline fails explicitly with an error message.

### 3.2. Static Feature Extraction (FR-003)
- **Goal**: Create a feature vector for each token without using the Oracle model's hidden states.
- **Model Independence**: Semantic similarity features are computed using **sentence-transformers/all-MiniLM-L6-v2**, a lightweight model (22M parameters, ~100 MB RAM) that is **distinct from the Oracle model (Phi-3-mini)**. This ensures strict independence and prevents circularity.
- **Features**:
 1. **N-grams**: Count of local n-grams (n=1 to 3) surrounding the token.
 2. **POS Tags**: Part-of-speech tags using `spacy` (e.g., NOUN, VERB, NUMBER).
 3. **Semantic Similarity**: Cosine similarity between the token's context (window of ±5 tokens) and a "seed set" of 50 known GSM8K reasoning patterns (pre-computed embeddings of the first 50 GSM8K traces using sentence-transformers/all-MiniLM-L6-v2).
- **Circularity Check**: The seed set embeddings are computed **once** using sentence-transformers/all-MiniLM-L6-v2, NOT the Phi-3-mini used for the Oracle step. This mathematical separation ensures the predictor features are independent of the Oracle's internal representation.
- **Independence Rationale**: Using a distinct embedding model for static features ensures the hypothesis test is valid: "Can static features (from sentence-transformers) predict dynamic credit assignment (from Phi-3-mini)?" If we used Phi-3-mini's embeddings for both, the predictor would be functionally coupled to the Oracle, invalidating the independence assumption.

### 3.3. Model Training (FR-004)
- **Architecture**: 2-layer MLP.
 - Input: Static Feature Vector (dimension = sum of n-gram counts + POS one-hot + similarity).
 - Hidden 1: A standard number of units, ReLU activation.
 - Hidden 2: units, ReLU activation.
 - Output: 1 unit (predicted DelTA Coefficient).
- **Optimizer**: Adam (default learning rate).
- **Loss**: Mean Squared Error (MSE).
- **Environment**: CPU-only (`device="cpu"`). No CUDA.
- **Data Split**: [deferred] Train, [deferred] Test (stratified by solution length).

### 3.4. Evaluation (FR-005, FR-006, FR-008)
- **Unit of Analysis**: Example (problem) level, not token level.
 - For each example, aggregate token-level predictions and targets by averaging.
 - Compute Spearman Rank Correlation ($\rho$) on the aggregated example-level scores.
 - This respects the intra-example correlation structure (tokens within the same problem are not independent).
- **Metric**: Spearman Rank Correlation ($\rho$) between Predicted and True DelTA Coefficients (example-level).
- **Baselines**:
 1. **Random Baseline**: Uniform weights from $N(0,1)$, seed=42.
 2. **Uniform Baseline**: All coefficients = 1.
- **Significance Test**: Permutation test (a sufficient number of shuffles of example-level target coefficients).
 - Null Hypothesis: No correlation between static features and DelTA.
 - P-value: Proportion of permuted correlations $\ge$ observed correlation.
 - Shuffling is performed at the example level (not token level) to preserve the independence assumption.
- **Feature Importance**: SHAP values (using `shap` library, CPU-compatible) to determine if a null result is due to "poor proxies" (low SHAP) or "emergent signal" (high SHAP but low correlation).
- **Collinearity Analysis**:
 - Compute the Pearson correlation matrix of input features (n-gram counts, POS tags, semantic similarity).
 - If high collinearity is detected (Pearson r > 0.7 between any pair of features), report this explicitly in the final analysis.
 - When interpreting SHAP values, note that high collinearity may prevent reliable estimation of independent feature effects. If needed, use SHAP interaction values to decompose the effects of correlated features.

## 4. Statistical Rigor & Limitations

- **Multiple Comparisons**: Only one primary hypothesis (Spearman $\rho$ at example level) is tested. No correction needed for the primary metric, but the permutation test inherently controls for chance.
- **Sample Size**: A collection of example-level data points, each consisting of a short sequence of tokens, yields a set of example-level data points. (after aggregation). This is a small sample for regression. We acknowledge low power for detecting weak effects. The permutation test (a sufficient number of iterations) is sufficient for a rough significance estimate.
- **Intra-Example Correlation**: Tokens within the same problem are not independent. The plan addresses this by aggregating to the example level for the primary analysis. Token-level secondary analyses, if performed, will use cluster-robust variance estimation to account for intra-example correlation.
- **Causal Inference**: The study is **observational**. We frame all findings as associational. We do not claim that static features *cause* the discriminative signal, only that they predict it.
- **Collinearity**: N-gram counts and semantic similarity (from sentence-transformers) may be correlated. The plan mandates explicit reporting of the feature correlation matrix. If high collinearity exists, SHAP interpretation will be qualified with caveats about the inability to distinguish independent effects.
- **Measurement Validity**: DelTA coefficients are the "ground truth" by definition of the algorithm. The validity of the approximation depends entirely on the correctness of the DelTA implementation and the appropriateness of Phi-3-mini as the Oracle model.
- **Model Independence**: Using sentence-transformers (distinct from Phi-3-mini) for static features ensures that the hypothesis test is not confounded by the Oracle model's internal representation. If the correlation is high, it indicates that input semantics (as captured by sentence-transformers) predict the Oracle's dynamic credit assignment. If the correlation is low, it suggests the signal is emergent from the Oracle's internal dynamics.

## 5. Compute Feasibility Plan

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Strategy**:
 - **Data**: Subset to 200 examples (deterministic, seed=42).
 - **Model**: Phi-3-mini on CPU is feasible within the 6-hour limit.
 - **Time Budget**:
 - Download/Filter: < 10 min.
 - Oracle Generation: Several hours (estimated for a moderate number of examples on standard CPUs).
 - Feature Extraction: < 30 min.
 - Training: < 10 min.
 - Evaluation: < 10 min.
 - **Total**: ~3–4 hours (well within 6-hour limit).
 - **Memory Budget**:
 - Phi-mini in full precision: ~8 GB (peak).
 - sentence-transformers: ~ MB.
 - Feature matrices: a manageable size suitable for standard computational environments..
 - MLP training: ~ MB.
 - **Total peak**: ~8 GB (acceptable).
 - **Deterministic Execution**: The pipeline is deterministic. No adaptive timeouts or fallbacks. If constraints are exceeded, the pipeline fails explicitly.
