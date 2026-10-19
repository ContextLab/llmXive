# Research: Quantifying Hallucination in LLM‑Generated API Documentation

## Research Question
*Do intrinsic code characteristics (function length, identifier entropy, cyclomatic complexity, naming style) correlate with the HallucinationIndex of CPU‑only LLM‑generated API descriptions?*  
All findings are framed as **associational** (“correlation observed”) in accordance with the observational nature of the study (Principle VII).

## Dataset Strategy

| Dataset | Source / URL | Variables Extracted | Verification Status |
|---------|--------------|--------------------|---------------------|
| **CodeSearchNet (Python)** | `https://huggingface.co/datasets/kejian/codesearchnet-python-raw/resolve/main/data/train-00000-of-00002-022fcdc5658ecd68.parquet` (train) and `https://huggingface.co/datasets/kejian/codesearchnet-python-pep8-v1/resolve/main/data/test-00000-of-00001.parquet` (test) | `source_code`, `reference_docstring`, `func_name` | **Verified** – direct HuggingFace parquet download |
| **LLM Weights** | `Salesforce/codegen-350M` (via `transformers`) and `bigcode/starcoderbase-1b` (via `transformers`) | N/A (model inference) | **Verified** – available on HuggingFace, CPU‑compatible |
| **Human Validation Subset** | Generated locally by `validate.py` (no external URL) | `human_score_raw`, `annotator_id`, `entity_f1_human`, `semantic_similarity_human` | **Verified** – produced by the pipeline itself |

*No external gated datasets are required; all inputs are programmatically downloadable.*

## Methodology

### 1. Data Ingestion & Pre‑processing
1. Download the two parquet files (train + test) using `datasets.load_dataset(..., streaming=False)`.
2. Filter out rows where `reference_docstring` is empty (`missing_docstring=True` – FR‑015) and compute:
   - **Source token count** (`token_count_source`) via a `tiktoken`‑compatible tokenizer.
   - **Identifier entropy**: Shannon entropy of tokenized identifier strings.
   - **Naming style**: regex classification (`snake_case`, `camelCase`, `other`).
   - **Cyclomatic complexity** via `radon` (NaN & `radon_parse_failure=True` flagged per FR‑016).

### 2. Generation Pipeline (FR‑002)
- Load `codegen-350M` in 16‑bit (`torch.float16`) and `starcoderbase-1b` quantized to 4‑bit (`bitsandbytes` `load_in_4bit=True`).
- Prompt: `"Describe the function {func_name} in one sentence based on the code."`
- Enforce one‑sentence constraint:
  * If a sentence delimiter (`.`, `!`, `?`) appears, truncate after the first delimiter.
  * If none, truncate to the first **64 tokens**.
- Record provenance (`generation_id`, `timestamp`, `model_name`, `input_function_hash`) for every row (FR‑018).

### 3. Hallucination Metric (FR‑003, FR‑020)
- **Entity extraction**: Use spaCy (`en_core_web_sm`) to pull parameter names and return types from both the source AST and the generated description.
- **Precision Hallucination** = *invented entities / total generated entities*.
- **Recall Omission** = *missing entities / total ground‑truth entities*.
- **Entity‑F1** = harmonic mean of precision and recall.
- **Semantic similarity**: SBERT (`sentence‑transformers/all-MiniLM-L6-v2`) cosine similarity between generated description and reference docstring, scaled to `[0,1]`.
- **HallucinationIndex** = `0.5 * (1 - entity_f1) + 0.5 * (1 - semantic_similarity)` (bounds `[0,1]`).

#### Semantic‑Similarity Validation (FR‑020)
1. From the stratified validation subset (see §4) randomly select **≥ 5 %** of generated descriptions.
2. Human annotators rate semantic similarity on a 0‑1 Likert scale.
3. Compute Pearson r between automated SBERT similarity scores and human ratings. Require **r ≥ 0.7**; otherwise, flag the component for review (recorded as `semantic_validation_flag`).

### 4. Manual Validation Subset (FR‑009, FR‑011, FR‑013, FR‑017)
- **Stratified Sampling**: Sample **≥ 5 %** of functions (≥ 50 items) using a **joint stratification** on HallucinationIndex quartiles **and** source token‑count deciles to ensure coverage across difficulty and length.
- **Annotation Template**: `validate.py --generate-template` produces `annotation_template.csv` with rows for each selected function.
- **Human Annotation**: Three independent annotators label each function:
  * **Behavioral Consistency** rubric (0‑3) → `human_score_raw`.
  * **Entity‑F1** (0‑1) → `entity_f1_human`.
  * **Semantic Similarity** (0‑1) → `semantic_similarity_human`.
- **Aggregation**: Compute median factual score, median entity‑F1, Krippendorff’s α for the factual scores; if α < 0.7 or score spread > 1.0, invoke the senior reviewer (FR‑017) to adjudicate and produce a final adjudicated score.
- **Calibration Checks**:
  * Pearson r between automated `entity_f1` and median manual `entity_f1`; flag “needs review” if **r < 0.7**, report 95 % CI (FR‑011).
  * Semantic‑similarity validation as described in §3 (FR‑020).

### 5. Statistical Analysis (FR‑004 – FR‑008)
1. **Partial Spearman** (FR‑019):
   - Rank all variables.
   - Regress ranked HallucinationIndex on ranked **generated description length** to obtain residuals.
   - Compute Spearman ρ between each predictor’s ranked values and the residuals from step (b). This controls for description length without using it as a predictor.
2. **Multiple Linear Regression** (FR‑008):
   - Model **per model**: `HallucinationIndex ~ token_count_source + identifier_entropy + cyclomatic_complexity`.
   - Report β‑coefficients with 95 % CI and VIF scores.
   - **DescriptionLength is NOT included** as a predictor (Principle VII).
3. **Multiple‑Comparison Correction** (FR‑005):
   - Apply Bonferroni correction to the three correlation p‑values.
4. **Model Comparison** (FR‑010):
   - After fitting separate regressions for each model, compute the absolute difference of each coefficient; assert **≤ 0.15** (SC‑006).
5. **Mixed‑Effects Model** (optional, T015):
   - Fit a linear mixed‑effects model with `model` as a fixed effect and source‑code predictors as random effects to verify that model‑specific variance does not confound the relationships.

### 6. Robustness & Sensitivity (FR‑006 – FR‑011)
- **Threshold sweep**: `{0.01, 0.05, 0.1}` → proportion of functions where `HallucinationIndex ≥ threshold` (SC‑004).
- **Manual validation correlation** (FR‑011) already described.
- **Bonferroni‑adjusted p‑values** for the three correlation tests (SC‑005).
- **Disclaimer**: All results are reported with the phrase `"correlation observed"` to satisfy SC‑007.

### 7. Power Analysis (T016)
- Using the `pwr` package we compute that detecting a Spearman ρ = 0.1 with α = 0.05 and power = 0.8 requires **≈ 825** samples. Processing **1 000** functions satisfies this requirement; the calculation is saved in `results/power_analysis.json`. (Addresses SC‑001.)

### 8. Reporting (FR‑007)
- Final JSON (`results/final_report.json`) contains:
  * Partial Spearman ρ and Bonferroni‑adjusted p‑values for each predictor (per model).
  * Multiple linear regression coefficients with 95 % CI (per model) and VIF scores.
  * Sensitivity‑analysis table.
  * Manual validation Pearson r, Krippendorff’s α, and validation flag.
  * Semantic‑similarity validation Pearson r and `semantic_validation_flag`.
  * Model‑comparison table (absolute coefficient differences).
  * Disclaimer string `"correlation observed"`.

## Decision Rationale: Compute Feasibility
- **CPU‑first**: Both models fit within 7 GB RAM on CPU (codegen‑[large‑scale] ≈ 2 GB, starcoder model occupies on the order of a few gigabytes after 4‑bit quantization.). Batch size 1 ensures memory stays < 5 GB.
- **No GPU Escape Hatch**: All required operations (tokenization, inference, SBERT similarity) have faithful CPU implementations; therefore we stay on the free‑tier runner.
- **Data Size**: The full Python subset is on the order of a few gigabytes when compressed; we download the parquet files directly, streaming is unnecessary because the total size fits the disk quota. If future scaling exceeds RAM, we would switch to `datasets.load_dataset(..., streaming=True)`.

## Statistical Rigor & Limitations
- **Multiple comparisons**: Bonferroni correction applied (FR‑005).
- **Power**: With 1 000 functions, we have > 0.8 power to detect a Spearman ρ > 0.1 (as assumed in the specification). Smaller effects may be under‑powered (acknowledged).
- **Observational**: No causal claims; all results are framed as associations (Principle VII).
- **Metric validity**: Automated HallucinationIndex is validated against an independent human behavioral rubric (FR‑020). If calibration fails (r < 0.7), the index is flagged for review (FR‑011).
- **Collinearity**: VIF checks guard against inflated standard errors; predictors with VIF > 5 would be examined.
- **Categorical predictor**: Naming style is analyzed with Mann‑Whitney U (non‑parametric) rather than Spearman, respecting its nominal nature.
- **Success Criterion SC‑003**: The manual validation workflow (FR‑009, FR‑011) directly satisfies SC‑003; the pipeline reports the Pearson r and Krippendorff’s α, and flags any failure per the criterion.

---

