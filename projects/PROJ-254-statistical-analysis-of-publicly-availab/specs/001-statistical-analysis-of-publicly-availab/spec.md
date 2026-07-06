# Feature Specification: Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution

**Feature Branch**: `001-genre-evolution`  
**Created**: 2026-07-06  
**Status**: Draft  
**Input**: User description: “Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution”  

## User Scenarios & Testing *(mandatory)*  

### User Story 1 – Generate Yearly Genre Embeddings (Priority: P1)  

A researcher wants to create reproducible yearly genre embeddings from large‑scale streaming logs so that downstream temporal analyses can be performed.  

**Why this priority**: Without reliable embeddings the entire investigation collapses; this is the foundational data‑processing step.  

**Independent Test**: Run the ingestion‑pre‑processing pipeline on a sample of the MPD and Last.fm datasets and verify that a set of genre‑level vectors is produced for each calendar year.  

**Acceptance Scenarios**:  

1. **Given** the raw MPD and Last.fm 1‑Billion Listening Events files are present, **When** the pipeline executes the metadata extraction and Word2Vec training modules, **Then** a folder `yearly_embeddings/` contains a `.npy` file for every year in the study period, each with a dimension‑100 vector per canonical MusicBrainz genre.  
2. **Given** a year with fewer than 5 000 track‑play sequences, **When** the training step runs, **Then** the system logs a warning but still outputs a genre‑vector file (with missing genres filled with zero vectors).  

---  

### User Story 2 – Compute & Visualize Temporal Similarity (Priority: P2)  

A researcher wants to quantify how genre boundaries shift over time and produce visual artefacts that communicate the trend.  

**Why this priority**: The similarity metrics and visualisations are the primary evidence for the research question and are needed before statistical testing.  

**Independent Test**: Execute the similarity‑calculation script on the embeddings generated in US‑1 and confirm that the mean off‑diagonal cosine similarity per year and corresponding heatmaps are saved.  

**Acceptance Scenarios**:  

1. **Given** the yearly genre‑vector files, **When** the similarity module runs, **Then** a CSV `yearly_similarity.csv` lists each year with its mean off‑diagonal cosine similarity and intra‑genre variance.  
2. **Given** the CSV output, **When** the visualization module runs, **Then** a PNG `similarity_trend.png` and an HTML heatmap `genre_similarity_heatmap.html` are created without errors.  

---  

### User Story 3 – Statistically Test Trend & Perform Sensitivity Checks (Priority: P3)  

A researcher wants to assess whether the observed similarity trend is statistically significant and verify robustness to threshold choices.  

**Why this priority**: The claim about genre blurring or tightening hinges on a defensible statistical inference; this story validates the scientific conclusion.  

**Independent Test**: Run the linear regression script on the similarity CSV and verify that (a) a slope estimate with 95 % CI and p-value is reported, and (b) a sensitivity report for three similarity-change thresholds is produced.  

**Acceptance Scenarios**:  

1. **Given** `yearly_similarity.csv`, **When** the linear regression analysis executes, **Then** the console prints the fixed-effect coefficient for `year`, its 95 % CI, and a p-value (α = 0.05).  
2. **Given** the same CSV, **When** the sensitivity module sweeps thresholds {0.005, 0.01, 0.02}, **Then** a table `sensitivity_report.csv` shows the slope and p-value for each threshold, demonstrating whether significance persists.  

---  

### Edge Cases  

- What happens when a track has no MusicBrainz genre tag? → The system logs the omission and excludes the track from genre‑averaging; if > 20 % of tracks in a year are missing, a warning is raised.  
- How does the system handle API rate‑limit errors from MusicBrainz or AcousticBrainz? → It implements exponential back‑off and retries up to three times; persistent failures abort the pipeline with a clear error message.  
- What if a year contains fewer than 1 000 unique tracks after filtering? → The year is flagged as “low‑coverage” and excluded from the linear regression; the exclusion is recorded in `pipeline_log.txt`.  

## Requirements *(mandatory)*  

### Functional Requirements  

- **FR-001**: The system MUST ingest the Million Playlist Dataset and Last.fm 1‑Billion Listening Events files, extract track IDs, release years, and genre tags via the MusicBrainz API, and store a normalized metadata table. *(See US-1)*  
- **FR-002**: The system MUST map each track to one or more canonical MusicBrainz genre labels, handling multi‑genre assignments by creating separate genre‑track links. *(See US-1)*  
- **FR-003**: The system MUST train a skip‑gram Word2Vec model (gensim, dim = 100, window = 10, negative = 5, epochs = 5) and produce a yearly genre‑embedding matrix by averaging track vectors within each genre. *(See US-1)*  
- **FR-004**: The system MUST compute pairwise cosine similarity between all genre vectors for each year, summarise the mean off‑diagonal similarity and intra‑genre variance, and output a CSV `yearly_similarity.csv`. *(See US-2)*  
- **FR-005**: The system MUST fit a linear regression model with `year` as the independent variable and `mean_off_diagonal_similarity` as the dependent variable, using robust standard errors to account for low degrees of freedom (N=20), output the slope, 95 % CI, and an uncorrected p-value for the fixed effect. *(See US-3)*  
- **FR-006**: The system MUST perform a sensitivity analysis by re‑computing the linear regression slope for each threshold in a set {0.005, 0.01, 0.02}, where for each threshold the system filters the dataset to include only years where the absolute year-over-year delta in similarity exceeds that threshold, and record the resulting uncorrected p-values in `sensitivity_report.csv`. *(See US-3)*  
- **FR-007**: The system MUST generate visualisations: (a) a line plot of mean similarity over years with 95 % CI bands, and (b) a yearly similarity heatmap, exporting them as PNG and interactive HTML respectively. *(See US-2)*  
- **FR-008**: The system MUST log all pipeline stages, parameters, and any warnings/errors to `pipeline_log.txt` to ensure reproducibility. *(General)*  
- **FR-009**: The system MUST join Last.fm data with MusicBrainz metadata to resolve release years; tracks that cannot be matched to a release year in MusicBrainz after a reasonable number of retry attempts are excluded. from the temporal analysis. *(See US-1)*  
- **FR-010**: The system MUST implement a fuzzy-matching fallback for missing MusicBrainz IDs: if a direct ID is missing, the system attempts to match by (artist, track title, album) tuple; if no match is found after 3 attempts, the track is excluded, and the exclusion rate is logged (warning if >20%). *(See US-1)*  
- **FR-011**: The system MUST enforce a maximum RAM usage of ≤ 6 GB by implementing batched vector loading and discarding intermediate vectors immediately after aggregation; if memory usage approaches a critical threshold, the system MUST trigger a garbage collection cycle and log a warning. *(See US-1)*  

### Key Entities  

- **Metadata Table**: rows = tracks; columns = track ID, release year, MusicBrainz genre(s), play count per year.  
- **Yearly Embedding Matrix**: rows = canonical genres; columns = 100‑dimensional embedding vectors for a given calendar year.  

## Success Criteria *(mandatory)*  

### Measurable Outcomes  

- **SC-001**: ≥ 90 % of tracks that possess a MusicBrainz genre tag are successfully represented in the yearly embedding matrices (See US-1).  
- **SC-002**: The linear regression model converges and reports a slope estimate with 95 % CI and an uncorrected p-value for the year effect (See US-3).  
- **SC-003**: The sensitivity analysis reports p-values for all three thresholds {0.005, 0.01, 0.02} in `sensitivity_report.csv` (See US-3).  
- **SC-004**: All visual artefacts (`similarity_trend.png`, `genre_similarity_heatmap.html`) are generated without runtime errors and match the schema defined in the documentation (See US-2).  

## Assumptions  

- The MPD and Last.fm datasets contain reliable release‑year metadata for the majority of tracks; tracks lacking a year are excluded.  
- MusicBrainz provides a stable, curated genre taxonomy that can be treated as the ground‑truth categorical variable.  
- Listening‑event logs span a multi-year period from the mid‑2000s to 2024. with sufficient density to train Word2Vec models on a sampled subset of ≤ 1 M sequences per year, keeping compute within free‑CPU limits.  
- All statistical inference is observational; therefore, findings are framed as **associational** (no causal language).  
- No GPU or CUDA libraries are used; all model training and inference rely on CPU‑only implementations (gensim, statsmodels).  
- The cosine‑similarity threshold for “meaningful change” is justified by prior music‑information‑retrieval literature that treats a Δcosine ≥ 0.01 as a perceptible shift; the sensitivity sweep (0.005‑0.02) tests robustness around this community‑standard.  
- The hardware constraints (CPU-only, ≤6GB RAM) are assumed based on the availability of free-tier compute resources for this research project.