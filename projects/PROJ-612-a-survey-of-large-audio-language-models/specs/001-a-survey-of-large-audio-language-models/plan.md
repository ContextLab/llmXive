# Implementation Plan: Survey of Large Audio Language Models – Hallucination Analysis

**Branch**: `feature-001-audio-hallucination` | **Date**: 2026-06-25 | **Spec**: `spec.md`

## Summary
This feature implements a reproducible pipeline to evaluate hallucination rates of Large Audio Language Models (LALMs) across three domains (speech, music, environmental sounds) and correlate these rates with estimated domain-specific training data volumes. The approach involves loading CPU-compatible LALMs, processing audio from verified datasets (LibriSpeech, FMA Small, ESC), applying a robust rule-based hallucination detector (fuzzy matching + synonyms), and performing statistical analysis (Kruskal-Wallis for domain differences; descriptive Spearman rank for correlation) within strict CPU-only resource constraints (7GB RAM, 6h runtime).

**Key Revisions**:
- **Datasets**: Switched to verified, metadata-rich alternatives (LibriSpeech for Speech, FMA Small for Music) to ensure ground truth entity availability.
- **Statistics**: Removed invalid p-value/CI claims for N=3 correlation; added Kruskal-Wallis test for domain differences as per Constitution Principle VI.
- **Validation**: Added fuzzy matching and synonym normalization to reduce false positives in hallucination detection.
- **Robustness**: Added runtime guards for sample reduction and checksum verification for data hygiene.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `torch` (CPU-only build), `transformers`, `librosa`, `pandas`, `scikit-learn`, `datasets`, `pyyaml`, `nltk`, `fuzzywuzzy`
**Storage**: Local filesystem (`data/`, `code/`, `results/`), HuggingFace Datasets cache
**Testing**: `pytest` with contract testing against YAML schemas
**Target Platform**: GitHub Actions Free Tier (Linux, 2 CPU, 7GB RAM, No GPU)
**Project Type**: Computational Research Pipeline / CLI
**Performance Goals**: Complete full evaluation (dynamic sample size) + analysis in ≤5 hours; RAM usage <6GB peak.
**Constraints**: No GPU/CUDA; no `bitsandbytes`; strict audio truncation; no causal claims; associative framing only.
**Scale/Scope**: 3 models, 3 domains (dynamic if data missing), target a sufficient number of samples per domain to ensure statistical robustness (total sufficient for analysis), A set of human-annotated samples (redistributed if domains missing).

> Note: All dataset URLs and model references are strictly limited to verified sources or public documentation.

## Constitution Check

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| I. Reproducibility | **Compliant** | Random seeds pinned; `requirements.txt` enforced; datasets fetched via canonical HF links; `code/checksum_data.py` ensures data integrity. |
| II. Verified Accuracy | **Compliant** | Citations in `research.md` map strictly to verified dataset URLs (LibriSpeech, FMA Small, ESC-50); no invented URLs. |
| III. Data Hygiene | **Compliant** | Raw data checksummed via `code/checksum_data.py` and recorded in `state/...yaml`; transformations write new files; no in-place edits. |
| IV. Single Source of Truth | **Compliant** | `hallucination_rates.csv` and `correlation_report.json` are the sole sources for paper stats. |
| V. Versioning Discipline | **Compliant** | Artifact hashes tracked in `state/` YAML; `updated_at` updated on changes. |
| VI. Domain‑Stratified Evaluation | **Compliant** | Pipeline explicitly separates Speech, Music, Env-Sound; metrics computed per domain; **Kruskal-Wallis H-test** added for significance testing. |
| VII. Training‑Data Transparency | **Compliant** | Training data estimates derived from model cards/papers with proxy derivation protocol and stored in `data/training_data_estimates.yaml`. |

## Project Structure

### Documentation (this feature)

```text
specs/feature-001-audio-hallucination/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── hallucination_schema.schema.yaml
│   ├── training_data_schema.schema.yaml
│   └── correlation_output_schema.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-612-a-survey-of-large-audio-language-models/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── checksum_data.py           # NEW: Computes and records SHA-256 checksums
│   ├── load_audio.py
│   ├── run_inference.py
│   ├── detect_hallucination.py    # UPDATED: Fuzzy matching + synonym expansion
│   ├── analyze_correlation.py     # UPDATED: Kruskal-Wallis + Descriptive Spearman
│   ├── retrieve_crowd_judgments.py # NEW: Downloads human labels from platform
│   └── utils.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── manifests/
├── results/
│   ├── hallucination_rates.csv
│   ├── correlation_report.json
│   └── pipeline.log
└── tests/
    ├── unit/
    └── contract/
```

**Structure Decision**: Single project structure with distinct `code/`, `data/`, and `results/` directories to enforce the "Single Source of Truth" and "Data Hygiene" principles. All analysis scripts are modular functions within `code/` to facilitate unit testing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | The plan adheres to CPU constraints and strict data stratification without unnecessary abstraction. |

## Specific Protocols

### Protocol 1: Dataset Selection & Metadata Validation
1. **Speech**: Load `LibriSpeech (dev-clean)` via HuggingFace. Verify presence of `speaker_id` and `text` metadata.
2. **Music**: Load `FMA Small` via HuggingFace. Verify presence of `genres` and `instrument` tags (if available).
3. **Environmental**: Load `ESC-50`. Verify presence of `category` label.
4. **Fallback**: If a dataset lacks required entity metadata for a sample, exclude that sample from the hallucination count but log it. If a domain has <50 valid samples, flag the domain as "Data Limited" and redistribute human validation quota.

### Protocol 2: Hallucination Detection (FR-012)
1. **Lexical Resources**: Use `WordNet` (via NLTK) for synonym expansion and `MusicBrainz` lists for instrument names. These are external, static resources.
2. **Normalization**: Convert both ground truth and caption entities to lowercase, strip whitespace.
3. **Matching**:
   - **Exact Match**: Direct string equality.
   - **Fuzzy Match**: If exact fails, compute Levenshtein distance. If distance < 2 (or similarity > 0.8), treat as match.
   - **Synonym Match**: If entities are synonyms in WordNet, treat as match.
4. **Flagging**: A sample is hallucinated only if a factual entity in the caption contradicts the ground truth AND no match (exact/fuzzy/synonym) is found.

### Protocol 3: Model Exclusion (FR-013)
1. **Keyword List**: Canonical list: `['esc-50', 'esc50', 'musicbench', 'audiobench', 'librispeech']`.
2. **Normalization**: Convert model card text to lowercase, remove punctuation, collapse whitespace.
3. **Fuzzy Matching**: Use `fuzzywuzzy` to compare model card text against keywords. If similarity > 0.8, exclude the model.
4. **Logging**: Log excluded models and the specific keyword match that triggered exclusion.

### Protocol 4: Statistical Analysis
1. **Domain Comparison**: Perform **Kruskal-Wallis H-test** on hallucination rates across domains. Report H-statistic and p-value (if N>=3).
2. **Correlation (Exploratory)**: Compute Spearman's rank correlation between training data volume (ordinal proxy) and hallucination rate.
   - **Constraint**: N=3. **NO p-values or CIs reported**.
   - **Output**: Report coefficient and a descriptive statement (e.g., "Higher data volume associated with lower hallucination rate").
   - **Sensitivity**: Test correlation under three rank assignments (Low=1, Med=2, High=3; and permutations) to check stability.
3. **Human Validation**: Compute Cohen's κ. Flag if < 0.6.

### Protocol 5: Human Validation Sampling (FR-008)
1. **Target**: Exactly 150 samples.
2. **Stratification**:
   - If 3 domains available: a balanced number of samples per domain.
   - If 2 domains available: per domain.
   - If 1 domain available: a representative sample from that domain.
3. **Redistribution**: If a domain is excluded (missing metadata), its quota is redistributed equally to remaining domains.
4. **Crowd Retrieval**: Use `code/retrieve_crowd_judgments.py` to download judgments from platform API/CSV and format as `human_judgments.csv`.

### Protocol 6: Runtime Guard & Data Hygiene
1. **Checksums**: Run `code/checksum_data.py` immediately after data download. Store SHA-256 hashes in `state/...yaml`.
2. **Time Limit**: Monitor elapsed time. If > 4.5 hours, reduce sample size by [deferred] and re-run remaining steps. Log the reduction.
3. **OOM Handling**: If OOM occurs, reduce batch size to 1 and retry. If still fails, abort and log error.