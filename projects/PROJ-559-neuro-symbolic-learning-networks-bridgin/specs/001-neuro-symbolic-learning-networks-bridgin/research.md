# Research: Neuro‑Symbolic Learning Networks

## Background

Neuro‑symbolic AI combines neural network pattern recognition with symbolic reasoning's interpretability and logical structure. In educational contexts, this hybrid approach aims to generate explanations that are both fluent (neural) and logically verifiable (symbolic). The research question is whether neuro‑symbolic explanations are associated with improved student reasoning accuracy, response time, and self‑reported comprehension compared to neural‑only or symbolic‑only explanations.

**Causal Framing Note**: This is an observational/comparative study (simulated students). All claims must be framed as associational unless randomization of explanation condition assignment is explicitly implemented. Results are correlational; causal claims require randomization.

## Dataset Strategy

| Dataset | Purpose | Source (verified URL) | Variables Needed | Variables Available | Fit Status |
|---------|---------|----------------------|------------------|---------------------|------------|
| ASSISTments (skill_builder) | Problem statements and solution metadata | https://huggingface.co/datasets/OloriBern/assistments-dataset/resolve/main/skill_builder_data_corrected.csv | problem_id, prompt_text, solution, difficulty | problem_id, skill_id, correct, hint_count | **PARTIAL** - prompt_text and solution fields must be verified during download phase |
| ASSISTments (item_mapping) | Item metadata | https://huggingface.co/datasets/OloriBern/assistments-classic-recommender/resolve/main/item_mapping.csv | problem_id, item attributes | item_id, skill_id, correct_rate | **PARTIAL** - links to skill_builder for full problem text |
| ASSISTments | Additional problem data | https://huggingface.co/datasets/Atomi/ASSISTments2009/resolve/main/data/train-00000-of-00001.parquet | problem_id, student interactions | multiple columns for student responses | **PARTIAL** - may contain interaction logs for validation |
| **Khan Academy** | Additional problem source | **NO VERIFIED SOURCE FOUND** | problem_id, prompt_text, solution, difficulty | **NO URL AVAILABLE** | **BLOCKING GAP** - spec assumes Khan Academy dataset but no verified source exists; plan proceeds with ASSISTments only, FR-001 scope reduced accordingly |
| Human pilot dataset | BKT calibration (≥50 participants) | **NO VERIFIED SOURCE FOUND** | problem_id, condition, correct, rt_seconds, comprehension_rating | **NO URL AVAILABLE** | **BLOCKING GAP** - FR-010 requires ≥50 human participants; must be collected via IRB‑approved study BEFORE simulation |
| Real student dataset | Final analysis (≥200 participants) | **NO VERIFIED SOURCE FOUND** | problem_id, condition, correct, rt_seconds, comprehension_rating | **NO URL AVAILABLE** | **BLOCKING GAP** - FR-011 requires ≥200 human participants; must be collected via IRB‑approved study for final analysis |

**Dataset Fit Concerns**:
1. **Khan Academy gap**: The spec references Khan Academy but the verified datasets block shows "NO verified source found" for FR-001. The plan proceeds with ASSISTments only and notes this as a scope reduction.
2. **Human data gap**: FR-010 and FR-011 require human participant data (≥50 for calibration, ≥200 for final analysis) with no verified source. This data must be collected via IRB‑approved study before simulation can proceed.
3. **Problem text availability**: ASSISTments CSV may not contain full `prompt_text` and `solution` fields needed for explanation generation; these must be verified during the download phase (pre-simulation gate).

## Technical Approach

### Explanation Generation

| Condition | Method | Library | CPU Feasibility |
|-----------|--------|---------|-----------------|
| Neural-only | Fine‑tuned distilled LLM (≤300M parameters) | `transformers` + `torch` (CPU) | **FEASIBLE** - 300M parameter model should generate within 2s per problem on CPU |
| Symbolic-only | Rule‑based symbolic trace generator | Custom Python (no ML) | **FEASIBLE** - deterministic, minimal compute |
| Neuro‑symbolic | Neural narrative + symbolic trace fusion | Custom Python + LLM | **FEASIBLE** - depends on neural component feasibility |

**Compute Feasibility Decision**: The spec originally assumed a 1B‑parameter LLM could generate explanations in ≤2 seconds on CPU. This is optimistic; the plan commits to ≤300M parameter models (e.g., distilbert-base-uncased or similar) to ensure CI feasibility within 6h budget.

### Student Simulation

**BKT Model**: The spec references a BKT‑based student simulator but the verified datasets block shows "NO verified source found" for BKT. The plan must:
1. Implement BKT from first principles (standard parameters: P(L0), P(T), P(S), P(G))
2. Calibrate against human pilot data (≥50 participants) before full simulation (FR-010)
3. Document the calibration methodology and success criteria (RMSE ≤0.15, no systematic bias)
4. **Validation Methodology**: External validity assessed via hold-out human data (separate from calibration set) with cross-validation to ensure independence

### Statistical Analysis

**Mixed‑Effects Regression** (FR-006, Constitution Principle VI):
- **Fixed effects**: explanation_condition (neural/symbolic/neuro‑symbolic), prior_knowledge_score, problem_difficulty, data_source (simulated/real)
- **Random intercepts**: problem_id, student_id
- **Effect sizes**: Cohen's d with 95% confidence intervals for pairwise comparisons
- **Multiple comparison correction**: Apply family‑wise error correction (Bonferroni or Holm) when testing >1 pairwise comparison
- **Power justification**: ≥6,000 simulated interactions (2,000 per condition) supports power ≥0.80 for effect size ≥0.1 (educational research convention); **power claims limited to what calibration data supports**
- **CI Width Validation**: SC-003 requires effect-size 95% CI width ≤0.20; this will be computed and validated in analysis output

**Causal Assumptions**: This is an observational/comparative study (simulated students). Claims must be framed as associational unless randomization is explicitly implemented. Results are correlational; causal claims require randomization of explanation condition assignment.

**Measurement Validity**: The multi-point Likert scale for comprehension uses a validated instrument per educational research methodology (standard comprehension rating scales; see e.g., Pintrich et al. for MSLQ validation). The plan notes: "Comprehension rating uses a validated multi-point Likert scale per educational research methodology."

**Collinearity Check**: Prior to regression, compute Variance Inflation Factor (VIF) for predictors. If VIF ≥ 5 for any predictor (e.g., prior_knowledge_score and problem_difficulty may be definitionally related), report effects descriptively rather than claiming independent effects.

**Data Source Weighting**: Human data (≥200) and simulated data (≥6,000) will be analyzed with appropriate interaction terms for data_source. Combined analysis includes data_source as fixed effect to assess whether condition effects differ by data source.

## Decision / Rationale

| Decision | Rationale |
|----------|-----------|
| Proceed with ASSISTments only (Khan Academy gap) | No verified source exists for Khan Academy; proceeding with ASSISTments alone is feasible but limits generalizability; FR-001 scope reduced |
| Use distilled ≤300M parameter LLM for neural explanations | 1B parameter model likely exceeds 2s per problem on CPU; 300M ensures CI feasibility |
| Sample a representative subset of problems for full explanation generation | Full dataset may exceed the allocated CI budget; sampling ensures pipeline completion while maintaining statistical power |
| Implement BKT from first principles | No verified BKT source exists; standard BKT parameters are well‑documented in educational literature |
| Calibrate BKT before full simulation (FR-010) | Required to avoid circularity; calibration must precede simulation per spec |
| Separate calibration data from validation data | Required to avoid circular validation; no overlap between pilot (≥50) and validation datasets |
| Collect human pilot data (≥50) + real student data (≥200) | Required by FR-010 and FR-011 for scientific validity; simulation alone cannot support generalizable claims |
| Apply family‑wise error correction | Required for statistical rigor when testing multiple pairwise comparisons (SC-003) |
| Add VIF collinearity check | Required to verify predictor independence before claiming regression coefficients |
| Reframe study as simulation-based with limitations | Human data is external dependency; study can proceed with explicit generalizability limitations |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset download timeout (FR-007) | Pipeline failure | Implement 300s timeout with clear error message (SC-008) |
| LLM inference exceeds time limit | CI job timeout | Use ≤300M parameter model; sample problems; document trade‑off |
| Human data collection delays | Research incomplete | Plan must flag this as external dependency; simulation can proceed with synthetic calibration if human data unavailable (with limitation note) |
| Memory exceeds a substantial threshold | CI job failure | Subset data; stream processing; monitor memory (SC-006) |
| BKT calibration fails (RMSE >0.15) | Invalid simulation results | Iterate calibration parameters; document failure if persistent; use synthetic calibration with limitation |
| Multiple comparison inflation | False positives | Apply Bonferroni or Holm correction; report adjusted p‑values |
| Predictor collinearity | Unstable coefficients | VIF < 5 check before regression; report descriptively if violated |
| CI width too large (SC-003) | Insufficient precision | Increase sample size or document limitation |

## References (Verified Sources Only)

**Datasets**:
- ASSISTments skill_builder: https://huggingface.co/datasets/OloriBern/assistments-dataset/resolve/main/skill_builder_data_corrected.csv
- ASSISTments item_mapping: https://huggingface.co/datasets/OloriBern/assistments-classic-recommender/resolve/main/item_mapping.csv
- ASSISTments2009: https://huggingface.co/datasets/Atomi/ASSISTments2009/resolve/main/data/train-00000-of-00001.parquet

**NO VERIFIED SOURCE** for:
- Khan Academy dataset (FR-001 gap; plan proceeds with ASSISTments only)
- BKT simulator implementation
- Human pilot dataset (≥50 participants; IRB-approved study required)
- Real student dataset (≥200 participants; IRB-approved study required)

**Validation References**:
- Likert scale validation: Pintrich, P. R., Smith, D. A., Garcia, T., & McKeachie, W. J. (1991). A manual for the use of the Motivated Strategies for Learning Questionnaire (MSLQ). National Center for Research to Improve Postsecondary Teaching and Learning.