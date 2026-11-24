# Research: llmXive follow-up: extending "ResearchStudio-Idea"

*(In-place revision; Sections 1–6 preserved, with dataset strategy corrected to cite only verified sources, claim scope narrowed, corpus role clarified, and compute feasibility clarified per the revision concerns.)*

## 1. Research Question & Hypothesis

**Question**: Do the 'ideation patterns' derived from top-tier ML conferences generalize to improve the quality of research proposals in resource-constrained, non-ML domains (public health, climate adaptation), or are these patterns specific artifacts of ML research culture?

**Hypothesis** (scoped — see §4 confound limitation):
- **H1 (Generalization, scoped)**: Proposals generated with ML-pattern structural constraints receive significantly higher expert scores in "contextual alignment" (primary) and "feasibility" than proposals generated with a generic unstructured prompt. **Note**: because the baseline is an unstructured prompt, this comparison tests *structured (ML-pattern) prompting vs. unstructured prompting*; it cannot by itself isolate the ML-origin of the structure (see §4).
- **H0 (Null)**: No significant difference between the two conditions.

## 2. Dataset Strategy

**Corpora required**:
1. **ML Corpus**: accepted abstracts (ML conference culture reference).
2. **Non-ML Corpus**: accepted and rejected abstracts from public-health and climate-adaptation venues.

**Corpus role (methodological, clarified)**: the corpus is the **source of the non-ML problem statements** and the ML reference context for the pattern cards. `acceptance_status` is recorded for provenance and FR-001 ingestion hygiene (balancing) but is **not used in any statistical analysis**; no corpus-level accepted-vs-rejected comparison is performed. The paired-proposal experiment is the entire study.

**Verified sources (the ONLY dataset URLs citable here)**: The verified-datasets block for this project contains only `all-MiniLM-L6-v2` embedding parquet files:
- https://huggingface.co/datasets/lsb/simplewiki2023-all-minilm-l6-v2-embedding/resolve/main/data/train-00000-of-00002-3dabc2a2d6e3d70d.parquet
- https://huggingface.co/datasets/lsb/openwebtext-all-minilm-l6-v2-embedding/resolve/main/data/train-00000-of-00105-5fb99383dece10fd.parquet
- 

These are pre-computed embedding corpora, **not** abstract corpora with acceptance metadata. **Therefore no verified, directly-downloadable abstract dataset (ML or non-ML, with accepted/rejected labels) is currently available for this project.** This is stated explicitly rather than fabricating a URL. **Consequently the research question is UNANSWERABLE until a verified labeled corpus and real expert ratings are added; current deliverables are pipeline validation only.** Consequences for the plan:

- `code/01_data_acquisition.py` (T011) is implemented with the full download/pagination/balancing/fallback architecture against configurable source endpoints, and MUST fail gracefully with a per-venue error log and non-zero exit when a configured source is inaccessible (per the spec's edge case) rather than proceeding with incomplete data. The deterministic fixture is produced only via an explicit `--dry-run` flag.
- The pipeline's dry-run path uses a small, clearly-labeled deterministic fixture corpus (fixed seed, `mock=true` metadata) so all downstream logic (embedding, generation, blinding, statistics) is exercised and tested end-to-end. The final report (T037) MUST label results as dry-run/fixture-based and MUST NOT present them as answering the research question.
- **Scope gap flagged**: obtaining a real, open, labeled abstract corpus (e.g., an open-review or PubMed-OA mirror with acceptance labels) requires a verified source added to the spec's dataset list before real-data conclusions can be drawn. This is surfaced for scope revision, not silently worked around.

**Data flow**: download/fixture → `data/raw/corpus_raw.jsonl` (checksummed) → validate/balance → `data/processed/corpus_clean.jsonl`.

## 3. Methodology

### 3.1 Pattern Mapping (FR-002)
- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (quantized/dynamic-quantized on CPU).
- **Fallback (spec edge case)**: if the configured model fails to load under memory constraints, the system falls back to a smaller, lighter model (configured in `utils/config.py`) and **logs the switch** with reason and both model names.
- **Process**: encode 15 pattern cards; encode non-ML problem statements; cosine similarity; select top-3 patterns with score ≥ 0.6 (retrieval mechanism only, not a validity metric — SC-004 note preserved).

### 3.2 Proposal Generation (FR-003)
- **Experimental group**: problem statement + top-3 similarity-selected patterns as structural constraints in the prompt.
- **Baseline group**: same problem statement + generic "be creative" instruction, no pattern-derived structure.
- Exactly one pattern-guided and one baseline proposal per problem statement (valid pairing, 50 pairs).
- **Claim scope**: because the baseline is unstructured, any significant difference is attributable at most to *structured (ML-pattern) prompting vs. unstructured prompting*; a third arm with non-ML structural scaffolding would be needed to isolate the ML-origin of the patterns — flagged as a spec gap, not added (see §4).
- **Model**: Hugging Face Inference API (primary); Ollama with quantized Mistral-7B-Instruct (4-bit) fallback. Both are CPU/API-feasible; no fake CPU imitation of a GPU-only computation is planned (none is needed — API inference offloads compute; local 4-bit inference fits the runner).
- **Batching + covariates**: record `token_count`, `generation_time` per proposal.
- **Runtime**: 100 proposals within 4 hours (FR-003), measured against the ≤6 h runner budget (SC-003).

### 3.3 Expert Evaluation (FR-004)
- **Blind protocol**: `04_evaluation_loader.py` strips generation metadata and writes `data/results/blinded_batches.csv` (T059a).
- **Alignment rubric (anti-circularity)**: experts rate "contextual alignment" as the degree to which the proposal addresses the **problem statement and its domain context** (public health / climate adaptation). Pattern cards are never shown, described, or inferable from the instructions; the full rubric text is embedded in the `instructions` field of `blinded_batches.csv` (T059a). This prevents the primary outcome from being partially determined by the manipulation.
- **Dry-run**: deterministic mock ratings (fixed seed, labeled) written to `data/results/ratings_filled.csv` (T059b) to verify statistical logic only.
- **Real ratings**: ingested via the same loader; experts verified via ORCID and ≥5 years domain experience; ≥3 independent experts per proposal.
- **IRR gate**: Krippendorff's alpha ≥ 0.6 computed on RAW ratings BEFORE any outlier removal or cleaning (T055 runs before T033). If alpha < 0.6, halt with recruitment guidance.

### 3.4 Statistical Analysis (FR-005, FR-006)
- **Power config (T024b)**: read n (pairs) from `data/results/generated_proposals.jsonl`; write `data/results/power_analysis_config.json` (α = 0.05, target d = 0.5, achieved power `[deferred]`); the limitation text references the **0.8 power convention** so the achieved estimate (expected ≈0.70 for n=50, d=0.5, two-sided paired t) is interpretable against it.
- **Tests**: Shapiro-Wilk normality check on paired mean-score differences → paired t-test or Wilcoxon signed-rank (automatic selection).
- **Correction**: Benjamini-Hochberg across the 3 metrics (feasibility, bottleneck, alignment).
- **Outliers**: sensitivity re-run with extreme ratings removed (spec edge case).
- **Validity (T036)**: `calculate_validity_improvement()` computes the alignment-score difference from expert mean scores (SC-004) → `data/results/validity_metrics.json`. SC-004 is treated as a **testable outcome** evaluated against the null of no difference — no presupposed direction or significance.
- **Report (T037)**: `data/results/analysis_report.md` generated from result files; MUST contain "associational, not causal" in the conclusion, enforced by a parser assertion; conclusions scoped to structured-vs-unstructured prompting.

## 4. Statistical Rigor & Limitations

- **Multiple comparisons**: BH correction across 3 metrics (FR-005, SC-002).
- **Power**: n = 50 pairs at d = 0.5, α = 0.05 (two-sided paired t) yields achieved power of roughly 0.70 — **below the 0.8 convention**; the power config (T024b) reports the achieved estimate against the 0.8 reference and the report acknowledges this as an explicit limitation.
- **Confound (structured vs. unstructured prompting)**: the two-arm design cannot distinguish "ML-derived patterns generalize" from "any structured prompt outperforms an unstructured one". All claims are therefore framed as **structured (ML-pattern) vs. unstructured prompting**; a third arm (non-ML structural scaffolding) is flagged as a spec gap for scope revision.
- **Causal framing**: patterns are selected by similarity, not randomized; all claims framed as **associational, not causal** (FR-006).
- **Measurement validity**: expert judgment with IRR gate as prerequisite; alignment rubric anchored to the problem statement/domain (not patterns), preventing circularity; no internal model metrics used as quality proxies (Principle VII).

## 5. Compute Feasibility (CPU-first)

- **Embedding**: `all-MiniLM-L6-v2` runs on CPU within 7 GB RAM (verified assumption in spec); lighter fallback model with logged switch if loading fails.
- **Generation**: HF Inference API (offloaded) primary; local 4-bit Ollama fallback fits the box. No GPU escape hatch needed.
- **Analysis**: `statsmodels`/`scipy`/`krippendorff` are lightweight.
- **Time**: full pipeline within ≤6 h; generation within 4 h (SC-003).

## 6. Decision/Rationale

| Component | Choice | Rationale |
| :--- | :--- | :--- |
| Embedding model | `all-MiniLM-L6-v2` (quantized), lighter fallback w/ logged switch | CPU-tractable, fits 7 GB RAM, spec-mandated; fallback per spec edge case |
| LLM generation | HF Inference API / Ollama 4-bit fallback | Real generation, feasible on the free runner |
| Statistical test | Paired t / Wilcoxon (auto-selected) | Spec-mandated (FR-005) |
| Correction | Benjamini-Hochberg | Controls FDR for 3 tests |
| Data source | Configurable endpoints + labeled deterministic fixture for dry-run (`--dry-run` only; fail-first otherwise) | No verified open abstract corpus exists in the verified block; no URL is fabricated; real-data conclusions blocked until a verified source is added |
| Evaluation | Blind expert ratings, problem-statement-anchored alignment rubric, IRR gate on raw data | Principle VII; anti-circularity; T055-before-T033 ordering enforced |
| Claim scope | Structured (ML-pattern) vs. unstructured prompting | Two-arm design cannot isolate ML-origin of structure; third arm flagged as spec gap |
| Compute | All CPU / API | No GPU-requiring method in the pipeline |