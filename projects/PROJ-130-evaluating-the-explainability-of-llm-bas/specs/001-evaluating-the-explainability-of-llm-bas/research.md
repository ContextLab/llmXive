# Research: Evaluating the Explainability of LLM-Based Bug Fixes

## Research Question

How well do different explainability techniques (attention visualization, code‑diff saliency maps, and generated natural‑language rationales) reflect the actual correctness and safety of bug fixes suggested by large language models for source‑code defects?

## Dataset Strategy

| Dataset | Verified URL | Purpose | Variables Required | Fit Assessment |
|---------|--------------|---------|-------------------|----------------|
| Defects4J v2.0 | https://github.com/rjust/defects4j | Primary bug dataset (OFFICIAL SOURCE) | Buggy files, test suites, commit messages, issue descriptions | ✅ FIT: Official repository contains executable test suite infrastructure required by FR-003 |

**CRITICAL**: Community HuggingFace parquet files (chathuranga-jayanath/*, echodrift/*) are NOT used as primary sources. The official standard bug benchmark GitHub repository is the canonical source to ensure test suite executability (FR-003).

**Dataset-variable fit verification**: Before relying on Defects4J, confirm it contains every variable the analysis needs:
- ✅ Buggy source files (required for patch generation)
- ✅ Test suites (required for correctness labels)
- ✅ Optional reference text: commit messages, issue descriptions (for metadata only, NOT rationale validation)

**Test suite executability verification**: Phase 0 includes explicit verification that the test suite can be executed on a generated patch by running the Defects4J test command on a sample bug. This confirms FR-003 feasibility before proceeding.

**No missing variables identified.** The dataset is appropriate for the planned analysis.

## Model Strategy

| Model | Source | Precision | Compute Requirement | Fit Assessment |
|-------|--------|-----------|-------------------|----------------|
| CodeLlama-7B-Instruct | https://huggingface.co/codellama/CodeLlama-7b-Instruct-hf | 16-bit (default) | CPU-only | ✅ FIT: Runs on GitHub Actions free-tier; 8-bit quantization NOT used (requires CUDA) |

**Decision/Rationale**: CodeLlama-7B-Instruct will run in 16-bit (default) precision on CPU. 8-bit quantization (load_in_8bit, bitsandbytes) will NOT be used as it requires CUDA and is incompatible with the free-tier runner. This is a CPU-tractable approximation of the intended method, documented per compute feasibility requirements.

## Statistical Rigor

### Multiple-Comparison Correction
- **Method**: Bonferroni correction for family-wise error control
- **Number of tests**: 3 techniques × 2 tests (correlation + logistic regression) = 6 comparisons
- **Corrected alpha**: α_corrected = 0.05 / 6 = 0.0083
- **Implementation**: FR-009 applies this correction to all paired t-tests (see SC-005)

### Sample Size / Power Justification
- **Sample size**: 50 bugs from Defects4J v2.0
- **Power analysis**: NOT deferred. Minimum detectable effect sizes specified:
 - For n=50 at [deferred] power: minimum detectable point-biserial correlation r≈0.30
 - For n=85 at [deferred] power: minimum detectable point-biserial correlation r≈0.25
- **Limitation acknowledgment**: This is a feasibility-driven sample size; power limitations will be documented in the final report. Findings with r<0.30 may be underpowered to detect.
- **Impact**: Findings should be interpreted as preliminary; larger samples needed for definitive conclusions

### Causal Inference Assumptions
- **Design**: Observational (no random assignment of patches to bugs)
- **Claim framing**: All findings will be framed as ASSOCIATIONAL, not causal
- **No causal claims**: No claims about explainability techniques causing higher correctness will be made
- **Justification**: Patches are generated for specific bugs based on bug characteristics, not random assignment

### Measurement Validity
- **Defects4J**: Widely-used benchmark for Java bug fixes; validated in prior literature
- **CodeLlama-7B-Instruct**: Standard instruction-tuned LLM for code generation; revision identifier recorded (FR-012)
- **BLEU/ROUGE**: Standard metrics for text similarity; 4-gram configuration with smoothing (see Assumptions)
- **Attention weights**: Direct model output from last decoder layer
  - **CRITICAL LIMITATION**: Attention ≠ explanation (Jain & Wallace; Serrano & Smith). Attention weights measure model focus, not explanation validity. Results are framed as correlation with correctness, NOT as validation of attention as explanation.
- **Integrated Gradients**: Captum implementation; validated in prior interpretability research
- **Rationale coherence**: Measured via internal coherence with code change (REVISED: NOT BLEU/ROUGE against commit messages)

### Predictor Collinearity
- **Attention vs. Saliency**: These metrics may be correlated (both measure token importance)
- **Approach**: Report correlation between attention and saliency scores descriptively
- **Acknowledgment**: Independent effects cannot be claimed if predictors are definitionally related
- **Documentation**: Collinearity acknowledged in statistical analysis (FR-007, FR-008)

### Confound Controls
- **Bug complexity**: Include lines of code, cyclomatic complexity as covariates in regression models
- **Test suite quality**: Flag test suites with known coverage issues; include as stratification variable
- **Model uncertainty**: Record generation confidence scores; include as covariate if available
- **Stratified analysis**: Run separate analyses by bug complexity tier (low/medium/high) to assess robustness

## Success Criteria Alignment

| SC-ID | Measurement | Source/Reference | Target |
|-------|-------------|------------------|--------|
| SC-001 | Point-biserial correlation coefficient (r_pb) | Defects4J ground-truth test suite outcomes | [deferred] |
| SC-002 | Logistic regression AUC-ROC | Defects4J ground-truth test suite outcomes | [deferred] |
| SC-003 | Bonferroni-corrected p-values | α = 0.05 significance threshold | α_corrected = 0.0083 |
| SC-004 | Dataset-variable fit | Defects4J v2.0 schema | All required variables present |
| SC-005 | Multiplicity correction | Number of hypothesis tests (6 comparisons) | Bonferroni adjustment applied |
| SC-006 | Power limitation documentation | Sample size of 50 bugs | Documented as constraint; min detectable r≈0.30 |
| SC-007 | Explainability score ranges | Expected numerical ranges (attention: 0-1, saliency: 0-∞, coherence: 0-1) | Valid output confirmed |

## Compute Feasibility

| Constraint | Requirement | Plan |
|------------|-------------|------|
| CPU | 2 cores | CodeLlama-7B-Instruct runs on CPU in default precision |
| RAM | ~7 GB | Data subset to fit memory; batch processing for test execution |
| Disk | ~14 GB | Defects4J archive stored under data/; explanations/ contains lightweight artifacts |
| GPU | None | No CUDA-dependent libraries (bitsandbytes, quantization) used |
| Runtime | ≤6 h per job | 50 bugs processed end-to-end; sample size reduced if needed |

**Contingency**: If runtime exceeds 6 hours, sample size will be reduced accordingly. This is documented in Assumptions.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Defects4J lacks reference text for some bugs | Rationale coherence cannot be computed | Record as [missing]; exclude from rationale-based analysis |
| CodeLlama-7B-Instruct timeout on CPU | Patch generation fails | Retry up to 3 times; mark as generation_failed after failures |
| Test suite timeout >60 seconds | Correctness label cannot be determined | Enforce timeout; exclude from analysis |
| Model weights too large for 7 GB RAM | OOM error | Use default precision; sample data subset if needed |
| Explainability artifacts too large for 14 GB disk | Storage overflow | Compress visualizations; store saliency as numpy arrays |
| Attention ≠ explanation debate | Results may be misinterpreted | Prominently cite Jain & Wallace (2019), Serrano & Smith (2019); frame as correlation only |
| BLEU/ROUGE against commit messages is invalid | Rationale metric invalid | REVISED: Use coherence against code change instead; document limitation |

## Assumptions

- A bug dataset contains buggy source files and test suites; human-written rationales are NOT available as a standard dataset component. Where reference text is required for rationale evaluation, the system will use **internal coherence with code change** (NOT commit messages or issue descriptions, which describe WHAT changed, not WHY). If no reference text is available for a bug, rationale coherence will be recorded as `[missing]` and that case excluded from rationale-based analysis.
- The design is observational (no random assignment of patches to bugs), so all findings will be framed as ASSOCIATIONAL, not causal; no causal claims about explainability techniques causing higher correctness will be made
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h per job) is sufficient to process 50 bugs end-to-end; if runtime exceeds a predetermined threshold, the sample size will be reduced accordingly.
- CodeLlama-7B-Instruct will run in 16-bit (default) precision on CPU; 8-bit quantization (load_in_8bit, bitsandbytes) will NOT be used as it requires CUDA and is incompatible with the free-tier runner
- The sample size is chosen based on feasibility; minimum detectable effect size is r≈0.30 for n=50 at [deferred] power (documented, not deferred)
- **Attention ≠ explanation**: Attention weights are NOT validated explanations (Jain & Wallace, 2019; Serrano & Smith, 2019). Results are framed as correlation with correctness, not explanation validity.
- BLEU/ROUGE similarity will use the standard 4-gram configuration with smoothing; the threshold of BLEU > 30 for "strong predictor" is based on community-standard interpretation of BLEU scores in code-generation literature
- All statistical tests will use the Bonferroni correction for family-wise error control (α_corrected = 0.05 / 6 = 0.0083 for 6 comparisons)
- The 60-second timeout per test run is based on typical Defects4J test execution times; if a bug's test suite regularly exceeds this, it will be excluded from analysis
- Random seeds are pinned to ensure reproducibility of model inference, data sampling, and statistical resampling operations
- Dataset checksums and model revision identifiers are recorded in output metadata to enable replication and audit of the experimental setup
- **Defects4J source**: Official GitHub repository (https://github.com/rjust/defects4j) is the canonical source; community HuggingFace uploads are NOT used as primary sources

