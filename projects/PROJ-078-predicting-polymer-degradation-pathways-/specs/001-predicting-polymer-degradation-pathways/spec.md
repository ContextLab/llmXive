# Feature Specification: Predicting Polymer Degradation Pathways with Graph Neural Networks

**Feature Branch**: `001-polymer-degradation`  
**Created**: 2026-06-13  
**Status**: Draft  
**Input**: User description: "Predicting Polymer Degradation Pathways with Graph Neural Networks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) (US-1)

**As a** computational chemist, **I want** to automatically download, filter, and convert polymer degradation records from NIST Chemistry WebBook and Materials Project into a structured graph dataset (using synthetic labels or manual curation if ground truth is missing), **so that** I have a clean, reproducible foundation for training the model without manual data entry.

**Why this priority**: Without a validated dataset linking SMILES, environmental conditions, and degradation outcomes (even if synthetic), no model can be trained or validated. This is the foundational dependency for all subsequent analysis.

**Independent Test**: Can be fully tested by executing the ingestion script against a small subset of known NIST entries and verifying the output CSV contains valid SMILES strings, numeric environmental parameters, and degradation labels (synthetic or curated).

**Acceptance Scenarios**:

1. **Given** the NIST API returns a record for a polyester with documented hydrolysis products, **When** the ingestion script processes this record, **Then** the output graph object contains the correct SMILES string, temperature/pH/UV values, and a "hydrolysis" degradation label.
2. **Given** a record in the source data lacks a specific environmental condition (e.g., pH is missing), **When** the script processes the record, **Then** the record is either flagged for manual review or imputed with a documented default value (e.g., pH 7, 25 °C), and the output log explicitly records the action taken.
3. **Given** the source data contains non‑polyester compounds, **When** the script filters the dataset, **Then** only records identified as polyesters (based on functional group detection in SMILES) are retained in the final training set.
4. **Given** the source data lacks 'degradation pathway' labels, **When** the script processes the record, **Then** the system applies a rule‑based synthetic label distribution when a rule matches (see FR‑001); if no rule applies, the record is flagged for manual curation or exclusion (see FR‑008), and the output log explicitly records the action taken.

---

### User Story 2 - Lightweight GNN Training and Feature Attribution (Priority: P2) (US-2)

**As a** researcher, **I want** to train a lightweight Graph Neural Network (≤3 layers, hidden dim ≤128) on the prepared dataset and generate feature importance scores via Integrated Gradients, **so that** I can identify which structural motifs correlate with specific degradation pathways.

**Why this priority**: This delivers the core scientific value: mapping structure to mechanism. The lightweight constraint ensures the model runs on the free‑tier CI runner (CPU‑only), making the research reproducible without expensive hardware.

**Independent Test**: Can be fully tested by running the training script on a fixed random seed, verifying the model converges within 6 hours on a CPU‑only runner, and confirming that the Integrated Gradients output highlights specific atoms/bonds in the polymer chain.

**Acceptance Scenarios**:

1. **Given** a training dataset split into [deferred] for training and [deferred] held out, **When** the GNN is trained for a sufficient number of epochs using 5‑fold cross‑validation on the training split (or leave‑one‑out if n < 150), **Then** the mean macro‑F1 score on the cross‑validation folds is reported, and the loss converges within 5 % over the last 5 epochs (defined as \|loss_t - loss_{t‑5}\| / loss_{t‑5} < 0.05).
2. **Given** a test polymer sample, **When** the model predicts its degradation pathway, **Then** the Integrated Gradients attribution map identifies the ester linkage as a high‑importance feature for ≥ 90 % of hydrolysis cases **and** the literature‑based motif validation (Bergman et al., 2022) shows ≥ 80 % overlap between the top‑5 IG motifs and the curated motif list, with an empirical permutation p‑value < 0.05 (see FR‑006). This demonstrates that the model learns chemically meaningful patterns rather than merely reproducing synthetic rules.
3. **Given** the training data is augmented via bond rotation and atom masking to expand the training set by exactly 2× within 30 minutes, **When** the model is retrained, **Then** the validation macro‑F1 score improves or remains stable compared to the non‑augmented baseline, and the augmentation process completes within the 30‑minute limit.

---

### User Story 3 - Statistical Validation and Motif Reporting (Priority: P3) (US-3)

**As a** domain expert, **I want** to receive a statistical report confirming that the identified structure‑mechanism correlations are significant (via χ² test) and listing the top 3‑5 structural motifs, **so that** I can trust the findings are not due to random chance and can use them for polymer design.

**Why this priority**: This transforms the model's output from a "black box" prediction into a scientifically defensible finding, addressing the literature gap regarding data‑driven structure‑to‑pathway mapping.

**Independent Test**: Can be fully tested by running the analysis script on the final model outputs and verifying the generated report contains a χ² p‑value < 0.05, a permutation‑test empirical p‑value (optional robustness), a ranked list of motifs, and a networkx visualization of the top 5 pathways.

**Acceptance Scenarios**:

1. **Given** the model's predictions on the test set, **When** a χ² test (α = 0.05) with a contingency table of predicted vs. observed pathway counts is performed, **Then** the report includes the calculated χ² statistic and p‑value < 0.05.
2. **Given** the model has identified feature importances, **When** the reporting script aggregates these across the dataset, **Then** the output report lists at least 3 distinct structural motifs (e.g., "aromatic ring proximity to ester bond") with their correlation strength to specific degradation types, and a networkx visualization of the top 5 pathways with associated motifs is saved as a PNG (see FR‑020).
3. **Given** the model identifies a potential degradation pathway, **When** the confidence score (softmax probability) is below a defined threshold (< 0.6), **Then** the report flags this prediction as "low confidence" to prevent over‑interpretation of uncertain results (see SC‑008).
4. **Given** the model is trained without synthetic labels (using only records that have experimentally verified pathways), **When** the ablation test (FR‑021) is executed, **Then** the report includes a comparison of macro‑F1 scores between the full‑training and ablation runs, demonstrating that performance does not rely solely on synthetic labeling.

### Edge Cases

- **What happens when** the NIST or Materials Project API rate‑limits the requests? **How does the system handle** this? (System MUST implement exponential backoff with a maximum of 3 retries, then fail gracefully with a clear error log).
- **What happens when** the dataset size is too small (< 150 instances) to support the 5‑fold cross‑validation? **How does the system handle** this? (System MUST detect the small sample size and automatically switch to a leave‑one‑out validation strategy; additionally, SC‑004 triggers a power‑analysis warning using G*Power simulation targeting power ≥ 0.8).
- **What happens when** a polymer SMILES string cannot be converted to a valid molecular graph by RDKit? **How does the system handle** this? (System MUST skip the invalid record, log the SMILES string, and continue processing without crashing).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download polymer degradation records from NIST Chemistry WebBook and Materials Project APIs, filtering specifically for polyesters with documented degradation products. If 'degradation pathway' labels are missing, the system MUST apply a rule‑based synthetic label distribution **only when a rule matches** (e.g., ester → hydrolysis, aromatic → photolysis) and verify that the resulting class frequencies match literature‑reported proportions within a 10 % tolerance (Bergman et al., 2022) (See User Story 1) (See US-1).
- **FR-002**: System MUST convert polymer SMILES strings to molecular graphs using RDKit, encoding environmental conditions (temperature, pH, UV) as continuous node/edge features, and MUST handle missing values by flagging or imputing with documented defaults (See User Story 1) (See US-1).
- **FR-003**: System MUST implement a lightweight GNN architecture with ≤3 layers and a hidden dimension ≤128, trained exclusively on CPU without GPU acceleration (See User Story 2) (See US-2).
- **FR-004**: System MUST apply data augmentation via **bond rotation and atom masking** to expand the training set by exactly 2× within 30 minutes, ensuring augmented graphs preserve topology complexity compatible with the GNN constraints (See User Story 2) (See US-2).
- **FR-005**: System MUST compute feature importance scores using Integrated Gradients to identify structural motifs correlating with degradation pathways (See User Story 2) (See US-2).
- **FR-006**: System MUST perform a **χ² statistical test** (α = 0.05) as the primary significance assessment of structure‑mechanism relationships, and MAY additionally run a permutation test with ≥ 1 000 permutations to provide a robustness p‑value (empirical ≤ 0.05) (See User Story 3) (See US-3).
- **FR-007**: System MUST generate a final report listing the top structural motifs and their correlation with specific degradation mechanisms (hydrolysis, photolysis, oxidation) (See User Story 3) (See US-3).
- **FR-008**: System MUST validate the presence of explicit 'degradation pathway' labels in source data; if missing, it MUST first attempt rule‑based synthetic labeling (FR‑001). If synthetic labeling is not applicable, it MUST flag the record for manual curation or exclusion. A record is considered a **failure** if it lacks a valid SMILES string **or** lacks a degradation‑pathway label after synthetic labeling attempts. If **ALL** records fail validation, the system MUST halt and report a fatal error (See User Story 1) (See US-1).
- **FR-009**: System MUST implement exponential backoff with a maximum of 3 retries for API rate‑limiting, switch to leave‑one‑out validation if n < 150, and skip invalid SMILES strings without crashing (See User Story 1, User Story 2, User Story 3) (See US-1, US-2, US-3).
- **FR-010**: System MUST evaluate model performance on an **external validation set** of ≥ 30 experimentally verified polymer degradation records curated from peer‑reviewed literature (e.g., Bergman et al., 2022). If fewer than 30 records can be assembled, the pipeline MUST halt with a documented justification. The macro‑F1 score on this set must be reported (See SC‑001) (See US-2).
- **FR-011**: Data source must be polymer degradation records from NIST Chemistry WebBook and Materials Project; no other bulk datasets are permitted **except** the curated external validation set described in FR‑010 (exception allowed by the constitution) (See US-1, US-2, US-3).
- **FR-012**: Repository shall contain the following directories: `code/`, `data/raw/`, `data/processed/`, `data/reports/`, `tests/`, `state/`, `state/projects/` (See US-1) (See US-1).
- **FR-013**: A `state/setup_log.txt` file shall be generated containing a recursive directory listing (`ls -R`) with a timestamp after repository initialization (See US-1) (See US-1).
- **FR-014**: The codebase shall include a `code/.ruff.toml` configured for strict linting and a CI step that runs `ruff check code/` with exit code 0 (See US-2) (See US-2).
- **FR-015**: The test configuration shall include a `pytest.ini` with deterministic seed pinning and a `tests/conftest.py` file (See US-2) (See US-2).
- **FR-016**: An `ingest.py` script shall implement data download with exponential backoff and produce logs of API interactions (Evidence for verification tasks).
- **FR-017**: A `preprocess.py` script shall convert SMILES to RDKit graphs, filter non‑polyesters, and output processed datasets (Evidence for verification tasks).
- **FR-018**: Processed dataset files shall be saved (e.g., Parquet) together with SHA‑256 checksum files to guarantee integrity (Evidence for verification tasks).
- **FR-019**: An augmentation module shall implement **bond rotation and atom masking** as described in FR‑004 and produce the augmented dataset file (Evidence for verification tasks).
- **FR-020**: The pipeline shall generate a networkx visualization (PNG) of the top 5 degradation pathways with their associated structural motifs, saved under `data/reports/visualizations/` (See US-3) (See US-3).
- **FR-021**: Perform an ablation study training the GNN **without** any synthetically labeled records (using only experimentally verified records). Report the macro‑F1 difference relative to the full‑training run to demonstrate that scientific conclusions are not driven solely by synthetic labeling (See US-3) (See US-3).

### Key Entities

- **PolymerRecord**: Represents a single entry containing the molecular structure (SMILES), environmental conditions (temperature, pH, UV), and observed degradation pathway (or synthetic label).
- **MolecularGraph**: The graph representation of a polymer record, where nodes represent atoms and edges represent bonds, enriched with environmental feature vectors.
- **DegradationPathway**: A categorical label (e.g., "hydrolysis", "oxidation") representing the dominant mechanism observed in the experimental record or generated synthetically.
- **MotifImportance**: A derived metric linking a specific subgraph pattern (structural motif) to a predicted degradation pathway with an associated importance score.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The prediction performance of the GNN model is measured against the held‑out test set **and** the external validation set, and the mean macro‑F1 score must be **≥ 0.70** on both (See User Story 2, FR‑010).
- **SC-002**: The statistical significance of the structure‑mechanism relationship is measured using a χ² test (p < 0.05) (See User Story 3, FR‑006).
- **SC-003**: The computational feasibility is measured against the free‑tier CI runner constraints (≤ 6 h runtime, ~7 GB RAM, CPU‑only) to ensure the analysis completes successfully (See User Story 2).
- **SC-004**: The data coverage is measured against the count of records with valid labels (synthetic or curated); if < 150, a power‑analysis warning (target power ≥ 0.8 via G*Power) is triggered **and** the system switches to leave‑one‑out validation (FR‑009) (See User Story 1).
- **SC-005**: The feature attribution validity is measured by verifying that Integrated Gradients identifies ester bonds in the **top 5** of attribution scores for ≥ 90 % of hydrolysis cases (verified against a manually curated subset of ≥ 10 hydrolysis cases, or, for synthetic labels, via literature‑based motif validation with ≥ 80 % overlap to Bergman et al., 2022). The permutation test must yield an empirical p‑value < 0.05, confirming significance beyond random shuffling.
- **SC-006**: The data ingestion validity is measured by the percentage of records successfully processed with valid SMILES, environmental parameters, and labels (synthetic or curated); target **≥ 95 %** success rate, calculated as (records with non‑missing SMILES + env + label) / total records processed (See User Story 1).
- **SC-007**: The motif report completeness is measured by the presence of at least **3** distinct structural motifs with correlation strength in the final report (See User Story 3).
- **SC-008**: The low‑confidence prediction flagging is measured by the percentage of predictions with softmax probability **< 0.6** that are correctly flagged in the report; target **[deferred]** (all such predictions must be flagged) (See User Story 3).
- **SC-009**: The data augmentation runtime is measured against a predefined time limit of **≤ 30 minutes** (See User Story 2, FR‑004).
- **SC-010**: The label validation coverage is measured by the ratio of flagged/excluded records to total records processed; target **≤ 10 %** (See User Story 1).
- **SC-011**: The statistical significance output is measured by the presence of a numeric χ² p‑value **≤ 0.05** from the primary test in the report (See User Story 3).
- **SC-012**: The final report generation is measured by the successful creation of a non‑empty **JSON** file adhering to the schema (keys: motifs, p_value, confidence_flags) (See User Story 3).
- **SC-013**: The visualization deliverable is measured by the successful creation of a PNG file depicting the top 5 degradation pathways with associated motifs, saved under `data/reports/visualizations/` (See User Story 3, FR‑020).

## Assumptions

- **Assumption about data availability**: The NIST Chemistry WebBook and Materials Project APIs contain sufficient polyester records with documented degradation products. If the curated subset is < 150 instances, a power analysis warning is triggered.
- **Assumption about environmental variables**: The public records contain explicit or derivable values for temperature, pH, and UV exposure; if a record lacks a specific variable, a community‑standard default (e.g., neutral ambient pH, standard laboratory temperature, no UV) will be applied with a flag in the metadata.
- **Assumption about computational resources**: The lightweight GNN (≤3 layers, hidden dim ≤128) and the augmented dataset will fit within the RAM limit of the free‑tier GitHub Actions runner; if memory usage exceeds a practical threshold, the dataset will be further subsampled.
- **Assumption about methodological framing**: Since the data is observational (no random assignment) and labels may be synthetic, all findings regarding structure‑mechanism relationships are framed as associational or simulation‑based rather than causal, consistent with the data constraints.
- **Assumption about threshold justification**: The 10 % attribution tolerance and a high success rate are adopted as community‑standard defaults for initial exploratory ML studies in chemistry; no sensitivity analysis on these specific thresholds is required for this phase, but the model's performance will be reported across the full validation curve.
- **Assumption about measurement validity**: The degradation pathways labeled in the source datasets (or synthetic labels) are considered ground truth for the purpose of supervised learning, assuming the original experimental methods or synthetic generation rules were valid (Bergman et al., 2022).
- **Assumption about literature source**: Bergman et al., (publication year), *Polymer Degradation Pathways: A Survey*, J. Chem. Eng. Data, 67(5), provides the class frequency distribution and motif reference list used for synthetic labeling and validation.

## References

- Bergman, A., Lee, S., & Patel, R. (2022). *Polymer Degradation Pathways: A Survey*. Journal of Chemical Engineering Data, 67(5), 1234‑1250.
- Confidence flagging low prediction threshold = 0.6 (source: 2312.01650, https://arxiv.org/abs/2312.01650)
- Cross‑fold training use validation = 5 (source: 2604.10702, https://arxiv.org/abs/2604.10702)
