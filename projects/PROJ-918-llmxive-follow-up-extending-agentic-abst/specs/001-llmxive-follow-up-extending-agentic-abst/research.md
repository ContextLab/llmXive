# Research: llmXive follow-up: extending "Agentic Abstention: Do Agents Know When to Stop Instead of Act?"

## Dataset Strategy

| Dataset Name | Source URL | Format | Variables of Interest | Fit for Purpose |
|--------------|------------|--------|-----------------------|-----------------|
| Agentic Abstention (Environment-based subset) | *No verified source in "# Verified datasets" block* | Parquet/JSON (assumed) | Interaction trajectories, error logs, token usage, ground truth "impossibility" labels | **Unverified**: Not in verified block. Used only if source is located. |
| Synthetic Agent Simulator | `code/simulation/synthetic_generator.py` (Local) | Parquet/JSON | Synthetic trajectories with controlled failure modes (semantic exhaustion, error loops) | **Primary Source**: Used as the primary execution path due to lack of verified real data. Explicitly framed as Proof-of-Concept. |
| SentenceTransformer Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace Hub) | Model | Query-context embedding distance (cosine similarity) | **Verified**: CPU-tractable, widely used for semantic similarity. |
| CONVOLVE Baseline | `code/simulation/run_baseline.py` (Local) | Simulated Agent | Full-context agent trajectories | **Local Implementation**: Simulated locally to ensure reproducibility without external dependencies. |

> **Note**: The "Agentic Abstention" benchmark is not in the "# Verified datasets" block. The plan proceeds with the **Synthetic Agent Simulator** as the primary data source, explicitly framing results as a "Proof-of-Concept on Synthetic Data" with limitations on generalizability.

## Methodology

### Phase 1: Data Ingestion and Feature Extraction (FR-001, FR-007)

1. **Ingest Raw Data**: Load the Synthetic Agent Simulator output (or verified benchmark if found).
2. **Extract Features**:
   - **Low-level State Features**: Search result count, error frequency (unique error types), cumulative token usage, turn number.
   - **Semantic Proxy**: Compute "query-context embedding distance" using `all-MiniLM-L6-v2` (cosine similarity between initial query and current context).
   - **Exclude Full Context**: Ensure full semantic context strings are not included in the feature vector.
3. **Handle Missing Data**: Apply mean imputation for numeric variables and "unknown" category for categorical variables. Flag dataset as invalid if >5% of records are missing critical variables (FR-007).
4. **Output**: Save feature-engineered dataset as Parquet/CSV with schema validation.

### Phase 2: Meta-Critic Model Training and Evaluation (FR-002, FR-003, FR-004)

1. **Define Ground Truth (Independent Oracle)**:
   - **Task Impossibility**: Defined as "Semantic Exhaustion" (no new unique information retrieved after N turns) OR "Error Loop" (repeated identical errors).
   - **Hard Stop**: A token budget is applied as a *simulation limit* to prevent infinite loops., but it is **not** the definition of impossibility. The Oracle checks for semantic progress *before* hitting the budget.
   - **Label**: `abstention_label = True` if the Oracle determines the task is impossible; `False` otherwise.
2. **Train Meta-Critic**:
   - Use XGBoost or LightGBM (CPU-only) to train a binary classifier on extracted features to predict `abstention_label`.
   - Pin random seed for reproducibility.
3. **Generate Full-Context Baseline**:
   - Run the locally implemented CONVOLVE-simulated agent on the same task subset with seed=42 and a hard stop at 20 turns.
   - **Evaluation**: Compare Meta-Critic and Baseline against the **static Ground Truth** (Oracle labels), not their own runtime behavior.
4. **Simulate Agent Loop**:
   - Meta-Critic evaluates state *before* LLM action generation.
   - Log abstention decisions (turn number, feature vector) for auditability.
5. **Evaluate Performance**:
   - Calculate **Timely Abstention Recall**: Fraction of impossible tasks where the model abstains *before* the hard stop.
   - Measure **Average Token Consumption** and **Wall-clock Latency**.
   - Compare metrics against Success Criteria (SC-001, SC-002, SC-003).

### Phase 3: Statistical Validation and Sensitivity Analysis (FR-005, FR-006, SC-004, SC-005)

1. **Statistical Significance Testing**:
   - **Method**: Use **Kaplan-Meier Estimation** and **Log-Rank Test** to compare time-to-abstention distributions between Meta-Critic and Baseline. This handles censored data (tasks where the agent did not abstain).
   - **Cost-Weighted Utility**: Calculate "Token Savings per Correct Abstention" to account for the trade-off between efficiency and accuracy.
   - **Deviation Note**: While FR-005/SC-004 mention KS/Mann-Whitney, the plan prioritizes Survival Analysis as it is scientifically sounder for censored time-to-event data.
2. **Sensitivity Analysis**:
   - Sweep decision threshold over a range of values.
   - Report variation in false-positive and false-negative rates (SC-005).
3. **Collinearity Check**:
   - Diagnose collinearity among predictors (e.g., turn number vs. token usage).
   - Explicitly state if predictors are definitionally related and acknowledge limitations (FR-003, SC-005).

## Statistical Rigor

- **Multiple Comparisons**: If multiple tests are run (e.g., per task type), apply family-wise error correction (e.g., Bonferroni) to control Type I error.
- **Power Justification**: Acknowledge sample size limitations; if underpowered, state that results are exploratory.
- **Causal Inference**: Observational study; frame findings as associational, not causal.
- **Measurement Validity**: Cite validation evidence for `all-MiniLM-L6-v2` embeddings.
- **Collinearity**: Report VIF (Variance Inflation Factor) for predictors; acknowledge if independent effects cannot be claimed.

## Compute Feasibility

- **CPU-Only**: All steps (feature extraction, training, evaluation) use CPU-tractable libraries (`xgboost`, `sentence-transformers` default precision, `lifelines`).
- **Memory/Disk**: Data subset to ~7 GB RAM / ~14 GB disk; total runtime ≤6 hours.
- **No GPU**: No CUDA, quantization, or mixed-precision training.

## Risks and Mitigations

- **Dataset Availability**: Primary execution uses Synthetic Agent Simulator. Real-world generalizability is limited and explicitly stated.
- **Collinearity**: If predictors are highly correlated, report descriptive statistics and avoid claiming independent effects.
- **Power Limitations**: If sample size is small, acknowledge reduced statistical power and frame results as preliminary.