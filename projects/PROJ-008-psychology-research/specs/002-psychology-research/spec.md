# Feature Specification: Mindfulness Components and Delivery Formats in ASD Social Skills

## User Stories

### US1: Data Collection and Cleaning Pipeline (P1) (See SC-001, SC-005)
**As a** researcher,
**I want** to collect study data from ClinicalTrials.gov, OSF, and PubMed-indexed full‑text articles,
**so that** I can extract standardized variables for meta‑analysis.

**Acceptance Criteria**:
- [ ] Studies are retrieved from ClinicalTrials.gov, OSF, and PubMed only (Constitution Principle VI)
- [ ] Inclusion criteria: age 6‑12, ASD diagnosis, social skill outcomes, **randomized controlled trial design** (RCT) (see scientific soundness‑1e8349cb)  
  *Rationale*: Quasi‑experimental designs introduce selection bias; restricting to RCTs preserves causal validity while still allowing a moderator analysis for any accidental quasi‑experimental records.
- [ ] Study design type (RCT vs. quasi‑experimental) is recorded as `design_type` and will be used as a moderator in meta‑analysis (FR-017)
- [ ] Multi‑arm studies are combined using Cochrane’s recommended inverse‑variance weighting method (FR-018) **instead of proportional control splitting** (see FR-008 revision)
- [ ] Output: `data/processed/cleaned_studies.csv` and `data/raw/excluded_studies.log`
- [ ] DOI for each study is validated via Crossref API (FR-015)
- [ ] Registry URLs are also validated for correctness (FR-032)

### US2: Effect Size Calculation and Meta‑Analysis (P2) (See SC-002, SC-006)
**As a** researcher,
**I want** to calculate Hedges' g effect sizes and perform random‑effects meta‑analysis,
**so that** I can quantify intervention efficacy and heterogeneity.

**Acceptance Criteria**:
- [ ] Hedges' g calculated with small‑sample correction; when baseline means/SDs are available, compute change‑score g (FR-026); otherwise use post‑score g and note limitation (FR-033).
- [ ] Random‑effects model uses REML estimator and Hartung–Knapp adjustment (FR-022)
- [ ] Subgroup analysis for mindfulness components, delivery formats, social‑skill domains, and follow‑up duration (FR-016, FR-010, FR-011, FR-012)
- [ ] Power analysis performed **for each subgroup** (α = 0.05, power = 0.80, expected g = 0.5) and documented (FR-019); reports required number of studies per subgroup.
- [ ] If total number of studies N < 10, switch to descriptive synthesis (no meta‑regression)

### US3: Visualization and Publication‑Bias Assessment (P3) (See SC-003, SC-004)
**As a** researcher,
**I want** to generate forest plots and funnel plots,
**so that** I can visualize results and assess publication bias.

**Acceptance Criteria**:
- [ ] Forest plot shows study‑specific CIs and pooled effect diamond for all analyses
- [ ] Funnel plot and Egger's test are generated **only if N ≥ 10** (FR-006)
- [ ] Synthetic dataset fixture containing at least ten studies is available for testing the conditional branch (testability‑d6626563)
- [ ] Final report includes all plots and narrative synthesis

## Functional Requirements

- **FR-001**: Data collector must support ClinicalTrials.gov, OSF, and PubMed APIs (See US1)
- **FR-002**: Rate‑limiting and exponential backoff for API calls
- **FR-003**: Extract intervention components and delivery formats using regex patterns (See US2, FR-016)
- **FR-004**: Calculate Hedges' g with small‑sample correction; retain `n_treatment` and `n_control` in output (FR-024)
- **FR-005**: Random‑effects meta‑analysis with heterogeneity statistics using REML and Hartung–Knapp (FR-022)
- **FR-006**: Generate forest plot for all analyses; generate funnel plot and Egger's test **only if N ≥ 10** (see US3)
- **FR-007**: Validate data against schema contracts
- **FR-008**: **Combine multi‑arm studies by applying Cochrane’s inverse‑variance weighting to merge treatment arms into a single contrast against a shared control.**  
  *Algorithm*:  
  1. Compute each arm’s effect size (Hedges’ g) and variance.  
  2. Derive weights = 1/variance.  
  3. Weighted‑average effect = Σ(w_i · g_i) / Σ w_i.  
  4. Combined variance = 1 / Σ w_i.  
  5. Output a single record with `n_treatment` = Σ n_treatment_i, `n_control` unchanged, and the combined effect/variance fields.  
  **Unit‑test fixture**: `tests/fixtures/multi_arm_split.yaml` demonstrates input with two treatment arms (n=30, n=25) sharing a control (n=55) and the expected combined row.
- **FR-009**: Abstract‑only text extraction fallback (no full‑text OCR); flag records where extraction relied solely on abstract for manual review (FR‑020)
- **FR-010**: Extract social skill domains (communication, peer interaction, etc.) and store in `social_skill_domain` (See Data Model)
- **FR-011**: Subgroup analysis by social skill domain
- **FR-012**: Follow‑up duration subgroup analysis
- **FR-013**: Effect size calculation from summary statistics (post‑score or change‑score as per FR‑026/FR‑033)
- **FR-014**: Conditional logic: suppress meta‑regression if N < 10
- **FR-015**: Validate DOI existence for each study via Crossref API (Constitution Principle II)
- **FR-016**: Extract delivery_format (caregiver‑mediated vs. child‑led) and store in `delivery_format` (See Data Model)
- **FR-017**: Record study design type (`design_type`) and use as moderator in meta‑analysis
- **FR-018**: Combine multiple treatment arms using Cochrane’s inverse‑variance method (replaces proportional splitting)
- **FR-019**: Perform **subgroup‑specific** power calculations (α = 0.05, power = 0.80, expected g = 0.5) and report required number of studies per subgroup (components, formats, skill domains, follow‑up)
- **FR-020**: Flag studies where component/delivery‑format extraction relied on abstract‑only data for manual verification
- **FR-021**: Extract risk‑of‑bias rating per Cochrane RoB2 and store in `rob_score`
- **FR-022**: Use REML estimator for τ² and apply Hartung–Knapp adjustment
- **FR-023**: If registry entries lack means/SDs, retrieve full‑text article via PubMed and extract required statistics
- **FR-024**: EffectSize CSV must include columns `n_treatment` and `n_control`
- **FR-025**: Update `contracts/cleaned_study.schema.yaml` to require `social_skill_domain`
- **FR-027**: Update `contracts/cleaned_study.schema.yaml` to require `delivery_format`
- **FR-028**: Exclude records flagged by FR‑020 from subgroup analyses unless manually verified; otherwise report sensitivity analysis with and without those records.
- **FR-030**: Incorporate risk‑of‑bias (`rob_score`) as a weighting factor in meta‑analysis and provide a sensitivity analysis stratified by RoB2 categories.
- **FR-031**: Supplement registry‑only data with PubMed‑indexed full‑text articles to obtain missing means/SDs; log source provenance for each extracted statistic.
- **FR-032**: Validate both registry URLs and DOIs for correctness and existence (Crossref for DOIs, HTTP HEAD for URLs).
- **FR-033**: When baseline (pre‑intervention) means/SDs are available, compute change‑score Hedges' g; otherwise compute post‑score g and annotate the effect size record with `baseline_used: false`.

## Non‑Functional Requirements

- **SC-001**: Data collection reproducibility – CI pipeline must complete without error on a fresh GitHub Actions runner and produce identical SHA‑256 hashes for `cleaned_studies.csv` and `excluded_studies.log` across two independent runs (See US1)
- **SC-002**: Effect‑size calculation correctness – Hedges' g values must match those produced by the metafor R package within a suitably small tolerance for a benchmark dataset of five studies. (See US2)
- **SC-003**: Plot generation – Forest and funnel plot PNG files must be generated; their SHA‑256 checksums must match expected values for the synthetic dataset of ≥10 studies (See US3)
- **SC-004**: Risk‑of‑bias extraction – `rob_score` column must be present for all studies and contain a valid RoB2 categorical value (low, some concerns, high) (See FR‑021)
- **SC-005**: Reproducibility on fresh runner – CI pipeline must complete all steps without error and produce identical SHA‑256 hashes for all output artifacts on a fresh GitHub Actions runner (See US1)
- **SC-006**: Power analysis reporting – Power analysis report must state the minimum number of studies required for each subgroup to achieve 80 % power at α = 0.05 (See FR‑019)

## Data Models

- **Study**: `id`, `title`, `registry`, `population`, `intervention`, `control`, `outcomes`, `follow_up`, `social_skill_domain`, `delivery_format`, `design_type`, `rob_score`
- **EffectSize**: `study_id`, `hedges_g`, `se`, `ci_lower`, `ci_upper`, `n_treatment`, `n_control`, `baseline_used`
- **MetaAnalysisResult**: `pooled_g`, `se`, `ci`, `i2`, `q_statistic`, `p_value`, `n_studies`

## Schema Contracts

- `contracts/cleaned_study.schema.yaml` (must require `social_skill_domain` and `delivery_format`; updated per FR‑025 & FR‑027)
- `contracts/effect_size.schema.yaml`

## Test Fixtures

- `tests/fixtures/multi_arm_split.yaml` – YAML file describing a synthetic multi‑arm study with two treatment arms and a shared control; expected combined record after applying FR‑008 algorithm. Used by the unit‑test suite to verify correct arm‑combination logic.
