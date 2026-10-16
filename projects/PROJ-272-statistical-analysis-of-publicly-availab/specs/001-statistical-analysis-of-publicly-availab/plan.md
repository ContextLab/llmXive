# Implementation Plan: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

**Branch**: `001-statistical-cognitive-decline` | **Date**: 2026-10-15 | **Spec**: `specs/001-statistical-cognitive-decline/spec.md`  
**Input**: Feature specification from `/specs/001-statistical-cognitive-decline/spec.md`

## Summary
The pipeline will ingest the **ADReSS Challenge** dataset. Because a verified public source for the raw transcripts is not available, the plan uses **pre‑computed sentence embeddings** (verified Hugging Face source) and treats **semantic coherence**—the average pairwise cosine similarity of those embeddings—as a proxy linguistic marker for cognitive decline. This proxy is supported by literature linking reduced semantic coherence to Alzheimer’s disease (e.g., *[semantic coherence & AD]*). The use of embeddings is a **constrained approach**; the limitation that raw text is unavailable is explicitly documented (see FR‑001 limitation). The study also adjusts for demographic covariates (age, education, gender) to mitigate confounding. All steps are CPU‑only and fit within the GitHub Actions free‑tier constraints.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `sentence-transformers` (CPU‑only `all-MiniLM-L6-v2`), `pyyaml`, `tqdm`, `pytest`  
- **Storage**: Local file system under `data/` (raw, interim, processed)  
- **Testing**: `pytest` (unit, contract, integration)  
- **Target Platform**: Linux (`ubuntu-latest` GitHub Actions)  
- **Performance Goals**: Total runtime ≤ 6 h, peak RAM ≤ 6 GB  
- **Constraints**: CPU‑only; no synthetic data; all external URLs verified; strict reproducibility  

## Constitution Check
| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Fixed random seeds in `code/config.py`; all dependencies pinned in `requirements.txt`; dataset fetched from the verified Hugging Face URL each run. |
| **II. Verified Accuracy** | Only the ADReSS embeddings URL (verified) is cited; no unverified sources. |
| **III. Data Hygiene** | Raw embeddings file stored with SHA‑256 checksum; transformations write new files; no PII present. |
| **IV. Single Source of Truth** | Every statistic in the eventual paper is generated directly from the JSON/CSV artifacts produced by the pipeline. |
| **V. Versioning Discipline** | Content hashes recorded in `state/projects/PROJ-272...yaml`; any artifact change updates the hash. |
| **VI. Linguistic Feature Transparency** | Semantic similarity computed in `code/features.py` using the exact `sentence-transformers` model version `all-MiniLM-L6-v2`. |
| **VII. Clinical Ground Truth Independence** | Labels come from ADReSS clinical assessments; features derived solely from embeddings, ensuring independence. |
| **VIII. FR‑001 Limitation** | Raw transcripts are not publicly available; the plan proceeds with embeddings as a proxy and documents this limitation explicitly. |

## Project Structure
### Documentation (this feature)
```
specs/001-statistical-cognitive-decline/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── feature.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

### Source Code
```
code/
├── __init__.py
├── config.py            # seeds, paths, constants
├── ingestion.py         # download & verify ADReSS embeddings, create cleaned CSV with empty text field
├── features.py          # compute semantic similarity (named `sentence_embedding_cosine_similarity`)
├── stats.py             # Mann‑Whitney U, Bonferroni, Cohen's d, rank‑biserial
├── modeling.py          # LR & RF with covariates, nested CV (adaptive if dataset is small)
├── utils.py             # logging, checksum helpers
└── main.py              # orchestrates the full pipeline
```

### Data Layout
```
data/
├── raw/
│   └── adress_embeddings.parquet   # verified source
├── interim/
│   ├── cleaned_adress.csv          # participant_id, label, text (empty), embedding_path
│   └── exclusions.log              # records of dropped records
├── processed/
│   ├── features.csv                # participant_id, label, sentence_embedding_cosine_similarity, lexical/syntactic fields = null
│   ├── stats_results.json
│   └── model_results.json
└── results/
    ├── raw_record_count.json
    ├── group_counts.json
    └── metadata.json
```

## Mapping of Functional & Success Criteria to Plan Phases
| US / SC | Description | Plan Phase / Task |
|---------|-------------|-------------------|
| **US1** (Data Ingestion & Preprocessing) | Download embeddings, verify checksum, create `cleaned_adress.csv` with empty `text` field. | Phase 3 – `code/ingestion.py`. |
| **US2** (Feature Extraction & Statistical Testing) | Compute semantic similarity; perform Mann‑Whitney U tests (Control vs AD, Control vs MCI) with Bonferroni correction; report Cohen's d and rank‑biserial effect sizes. | Phase 4 – `code/features.py` & `code/stats.py`. |
| **US3** (Predictive Modeling & Validation) | Stratified split; train Logistic Regression and Random Forest with age/education/gender covariates; nested 5‑fold outer CV, 3‑fold inner CV; report mean AUC ± SD. | Phase 5 – `code/modeling.py`. |
| **SC‑Power** | Provide power analysis for Mann‑Whitney U (detectable effect size of approximately small‑to‑medium magnitude at [deferred] power). | Added to research.md and referenced in plan.md. |
| **SC‑Covariates** | Adjust for age, education, gender in models and report adjusted effect sizes. | Described in research.md; implemented in `modeling.py`. |
| **Contract Validation** | Run `pytest tests/contract/` after artifact creation to ensure schema compliance. | Phase 7 – added as final step. |

## Detailed Phase Tasks
1. **Phase 3 – Ingestion**
   - Download `adress_embeddings.parquet` from the verified Hugging Face URL.
   - Verify SHA‑256 checksum (recorded in project state).
   - Generate `data/interim/cleaned_adress.csv` with columns: `participant_id`, `label`, `text` (empty string), `embedding_path`.
   - Log excluded records (missing labels or insufficient length) to `data/interim/exclusions.log`.

2. **Phase 4 – Feature Extraction**
   - Load each participant’s embedding array.
   - Compute `sentence_embedding_cosine_similarity` = mean pairwise cosine similarity.
   - Populate `features.csv` with this column; lexical/syntactic columns set to `null`.

3. **Phase 5 – Statistical Testing**
   - Perform Mann‑Whitney U tests for Control vs AD and Control vs MCI.
   - Apply Bonferroni correction (α = 0.05/2).
   - Compute **Cohen's d** and **rank‑biserial correlation** as effect sizes.
   - Save results to `stats_results.json`.

4. **Phase 6 – Modeling**
   - Load demographic covariates (age, education, gender) if present.
   - Stratified train/validation/test split (70/30) with fixed seed.
   - Nested CV (outer 5‑fold, inner 3‑fold) for hyper‑parameter tuning.
   - Fit Logistic Regression (L2) and Random Forest.
   - Record mean AUC ± SD, plus accuracy/F1, in `model_results.json`.

5. **Phase 7 – Contract Validation & Metadata**
   - Execute `pytest tests/contract/` to validate `cleaned_adress.csv`, `features.csv`, and JSON outputs against the schemas.
   - Generate `metadata.json` containing checksums, timestamps, and data‑hygiene metadata.

## Compute Feasibility
- **Memory**: Embedding parquet of approximately a few hundred megabytes.; processing in batches ≤ 1 GB.  
- **Runtime**: End‑to‑end < 30 min on the GitHub Actions CPU runner.  
- **GPU**: Not required.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Raw transcripts unavailable → lexical/syntactic features missing | Explicitly document omission; use empty `text` field; focus analysis on semantic similarity; note limitation in manuscript. |
| Embedding file corrupted or checksum mismatch | Abort pipeline with clear error; checksum recorded in project state. |
| Class imbalance (AD vs Control) | Use stratified CV; report class‑wise metrics. |
| Single‑sentence transcript (no pairwise similarity) | Record similarity as `null` and exclude from tests (count reported). |
| Limited power for Control vs MCI | Provide power analysis; label findings exploratory. |
| Potential confounding by demographics | Include age, education, gender as covariates in models and report adjusted effect sizes. |