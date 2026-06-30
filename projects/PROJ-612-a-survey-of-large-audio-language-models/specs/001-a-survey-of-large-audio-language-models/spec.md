# Feature Specification: Survey of Large Audio Language Models – Hallucination Analysis

**Feature Branch**: `[feature-001-audio-hallucination]`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: “A Survey of Large Audio Language Models: Generalization, Trustworthiness, and Outlook – evaluate hallucination rates across speech, music, and environmental‑sound domains and relate them to domain‑specific training data volume.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Automated Domain‑wise Hallucination Evaluation (Priority: P1)

**As a** researcher, **I want** an end‑to‑end pipeline that loads selected open‑source LALMs, runs them on a representative set of audio samples per domain (speech, music, environmental sounds), and outputs per‑domain hallucination rates, **so that** I can obtain a baseline trustworthiness profile for each model.

**Why this priority**: Provides the core empirical evidence required to answer the primary research question; without it no further analysis is possible.

**Independent Test**: Execute the pipeline on a fresh GitHub Actions runner and verify that it produces a CSV file containing three rows (one per domain) with hallucination‑rate values and 95 % Wilson‑score confidence intervals.

**Acceptance Scenarios**:

1. **Given** the pipeline configuration (model list, dataset paths, 500 samples per domain), **when** the pipeline is invoked, **then** it completes without error and writes a `hallucination_rates.csv` file with the required columns.  
2. **Given** a sample that exceeds the 10‑second duration limit, **when** the pipeline processes it, **then** the sample is skipped, logged, and does not affect the reported rates.

---

### User Story 2 – Correlation of Training‑Data Volume with Hallucination (Priority: P2)

**As a** researcher, **I want** the system to estimate the amount of domain‑specific pre‑training data used for each model and compute a statistical correlation (Spearman’s rank correlation) with the observed hallucination rates, **so that** I can explore whether data availability explains domain differences.

**Why this priority**: Directly addresses the secondary hypothesis about data scarcity driving hallucinations; essential for interpreting the domain‑wise results.

**Independent Test**: Run the analysis script on the `hallucination_rates.csv` produced by US‑1 and verify that it outputs a report containing (a) estimated training‑data volumes per domain, (b) a correlation coefficient, and (c) a statement of the correlation direction and strength.

**Acceptance Scenarios**:

1. **Given** valid hallucination rates and training‑data estimates, **when** the correlation analysis is executed, **then** it produces a Spearman correlation coefficient with a 95 % confidence interval and a descriptive statement.  
2. **Given** missing training‑data estimates for a domain, **when** the analysis runs, **then** it derives a proxy or flags the value as 'unknown' and continues.

---

### User Story 3 – Human Validation of Hallucination Labels (Priority: P3)

**As a** researcher, **I want** a subset (exactly 150 samples) of the automatically generated captions to be reviewed by human annotators, with inter‑annotator agreement reported, **so that** I can assess the reliability of the rule‑based hallucination detector.

**Why this priority**: Guarantees external validity of the automated metric; required for publication‑grade evidence.

**Independent Test**: Submit the selected representative set of audio‑caption pairs to a public crowdsourcing platform, collect binary hallucination judgments from at least two independent annotators per item, compute Cohen’s κ, and verify that the system correctly calculates and reports the value.

**Acceptance Scenarios**:

1. **Given** the set of 150 samples, **when** the annotation job is launched, **then** the system records the annotation IDs and later retrieves the judgments without loss.  
2. **Given** the collected judgments, **when** the agreement computation runs, **then** it outputs a κ statistic and flags if κ < 0.6.

---

### Edge Cases

- **What happens when an audio file is longer than 10 seconds?**  
  The preprocessing step rejects the file, logs a warning, and excludes it from the hallucination count.

- **How does the system handle a model that fails to load due to memory constraints?**  
  The pipeline aborts gracefully, logs the failure, and reports which model(s) could not be evaluated.

- **What if the training‑data volume information is unavailable for a model?**  
  The analysis step derives a relative volume proxy from available metadata (e.g., token counts) or flags the value as 'unknown' and proceeds, rather than halting.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load each specified LALM (≤ 2 B parameters) using CPU‑only execution without invoking GPU‑specific libraries. *(See US‑1)*
- **FR-002**: System MUST resample all audio to 16 kHz and truncate or discard samples longer than 10 seconds, logging any discards. *(See US‑1)*
- **FR-003**: System MUST generate a caption for every retained audio sample using a standardized prompting template and store the raw text output. *(See US‑1)*
- **FR-004**: System MUST apply a rule‑based hallucination detector that flags a sample as hallucinated if any factual element (e.g., speaker identity, instrument name, animal species) in the caption contradicts the ground‑truth metadata, using exact string match on normalized (lowercased, stripped) entity names. *(See US‑1)*
- **FR-005**: System MUST compute per‑domain hallucination rates with Wilson‑score confidence intervals at a 95 % confidence level and write them to `hallucination_rates.csv`. *(See US‑1)*
- **FR-006**: System MUST retrieve or estimate domain-specific pre-training data estimates for each model from published documentation or dataset papers by parsing JSON/YAML model cards or extracting text from PDFs of technical reports. If exact counts are unavailable, the system MUST derive a relative volume proxy (e.g., hours of audio or token counts) cited from the primary source. The analysis MUST treat these values as estimates with documented uncertainty bounds. *(See US‑2)*
- **FR-007**: System MUST perform a Spearman’s rank correlation between training‑data volume and hallucination rates across the three domains, report the correlation coefficient and 95 % confidence interval, and frame the result as exploratory due to the small sample size (N=3). *(See US‑2)*
- **FR-008**: System MUST select exactly 150 samples from the evaluated captions, submit them to a public crowdsourcing platform compliant with local minimum wage laws (e.g., ≥ $13.00/hr in the US), and retrieve binary hallucination judgments. *(See US‑3)*
- **FR-009**: System MUST compute Cohen’s κ for the human annotations and flag if κ < 0.6. *(See US‑3)*
- **FR‑010**: System MUST log all processing steps, resource usage, and any errors to a reproducible `pipeline.log` file. *(General)*
- **FR‑011**: System MUST enforce that all statistical inference is framed as associative (no causal language) because the design is observational. *(Methodological)*
- **FR‑012**: System MUST ensure that the rule‑based detector’s factual checks are based on validated lexical resources (e.g., instrument taxonomies, entity lists, knowledge graphs) that are distinct from the training data of the evaluated models. *(Measurement validity)*
- **FR‑013**: System MUST exclude any model from the analysis if its training data includes the specific test datasets (ESC-50, MusicBench, AudioBench) used for hallucination evaluation, to prevent tautological validation. *(Scientific Soundness)*

### Key Entities

- **AudioSample**: Represents a single audio clip with attributes `domain`, `duration`, `metadata` (ground‑truth labels).  
- **ModelInstance**: Represents a loaded LALM with attributes `name`, `parameter_count`, `training_data_estimates`.  
- **Caption**: Text output generated by a ModelInstance for an AudioSample.  
- **HallucinationLabel**: Binary flag (`true` = hallucinated) produced by the rule‑based detector or human annotator.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The full evaluation pipeline (US‑1) completes in ≤ 5 hours on a GitHub Actions free‑tier runner (Multiple CPU cores, 7 GB RAM). *(See US‑1)*
- **SC-002**: The system calculates and reports the width of each domain’s hallucination‑rate confidence interval. *(See US‑1)*
- **SC-003**: The Spearman correlation analysis (US‑2) yields a descriptive report of the correlation coefficient and direction. *(See US‑2)*
- **SC-004**: Human annotation agreement (Cohen’s κ) is calculated and reported, with a flag if κ < 0.6. *(See US‑3)*
- **SC-005**: All statistical analyses are framed as associative and exploratory where appropriate. *(Methodological)*
- **SC-006**: No GPU‑specific libraries (e.g., `bitsandbytes`, `torch.cuda`) are imported or executed during the run. *(Compute feasibility)*

## Assumptions

- All three LALMs are publicly available on HuggingFace and can be loaded with ≤ 2 B parameters on CPU within the RAM budget.  
- Public benchmarks (AudioBench speech subset, MusicBench, ESC‑50) provide reliable ground‑truth metadata for factual comparison.  
- The rule‑based hallucination detector can rely on existing lexical resources (instrument lists, speaker‑ID name databases) that are freely downloadable.  
- Approximate domain‑specific training‑data volumes can be extracted from model cards or associated papers; exact counts are not required for correlation analysis.  
- Human annotation will be performed via a public crowdsourcing service (e.g., Amazon Mechanical Turk, Prolific, or similar) that allows 150 items without exceeding budget limits.  
- All statistical analyses are associative; no causal claims will be made about training data causing hallucinations.  
- The free‑tier CI environment provides at least 7 GB RAM and 14 GB disk; datasets will be streamed or subsampled to stay within these limits.  
- No GPU or CUDA‑based acceleration will be used; all code must be compatible with pure CPU execution.  
- The models selected for evaluation do not have training data that overlaps with the specific test datasets (ESC-50, MusicBench, AudioBench) used for hallucination evaluation.