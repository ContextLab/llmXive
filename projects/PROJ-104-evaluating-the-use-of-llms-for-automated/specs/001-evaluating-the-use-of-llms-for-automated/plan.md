# Implementation Plan: Evaluating LLM Fidelity in Commit-to-Documentation Translation

**Branch**: `001-evaluating-llm-fidelity` | **Date**: 2026-10-16 | **Spec**: [spec.md](../specs/001-evaluating-llm-fidelity/spec.md)  
**Input**: Feature specification from `specs/001-evaluating-llm-fidelity/spec.md`

## Summary
The project builds a reproducible pipeline that (0) **performs a power‑analysis** to confirm that ≥500 paired samples give ≥80 % power for the Friedman test, (1) extracts ≥500 `(commit_message, documentation_diff)` pairs from five popular Python libraries (or a stratified sample of a sufficient number of pairs per model when compute limits apply), (2) generates three candidate documentation updates per commit using Phi‑‑mini, Gemma‑2‑2b, and Llama‑3.2‑3B (CPU‑first 4‑bit inference, with a **uniform GPU escape hatch** if any model exceeds the 60 s budget), (3) parses human and generated diffs into **surface** and **technical‑intent** entities (expanded regexes and AST‑augmented verification), (4) computes precision/recall per entity type, (5) conducts a **power‑analysis** to confirm adequacy of the sample for a Friedman test, (6) performs the Friedman test (or repeated‑measures ANOVA if assumptions met) with **Holm‑Bonferroni correction** across the three metrics, (7) quantifies hallucinations via code‑base verification, (8) visualizes results, and (9) validates all artifacts against schemas (including the newly‑added `entityset.schema.yaml`). All steps are fully automated, deterministic, and respect the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `gitpython`, `datasets`, `transformers`, `bitsandbytes`, `torch>=2.0`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `pandas`, `pyyaml`, `tqdm`, `astor`  
- **Storage**: File‑based CSV/JSON under `data/` (raw, intermediate, final)  
- **Testing**: `pytest` with contract tests in `tests/contract/`  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, ~14 GB disk) – **GPU escape hatch** permitted for all models uniformly if needed.  
- **Performance Goals**: Generation ≤60 s per commit (NFR‑001) on CPU; if any model exceeds, **all** models are re‑executed on a Kaggle free GPU (ensuring hardware parity).  
- **Constraints**: All models run in 4‑bit quantization on CPU; the uniform GPU fallback uses the same quantization and prompts.  
- **Scale/Scope**: Minimum 500 paired samples for full analysis; default CI run uses **200** randomly sampled commits per model (≈ several hundred generation calls) to stay within the a standard CI wall‑clock limit. An optional manual workflow can be triggered for the full 500‑pair set.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Deterministic scripts, seeds pinned, data fetched from public GitHub URLs, single entry point `run_pipeline.py`. |
| II. Verified Accuracy | All external citations will be validated by the Reference‑Validator before manuscript inclusion. |
| III. Data Hygiene | Raw repository clones are checksum‑verified; each transformation writes a new file with provenance recorded in `data/metadata.yaml`. |
| IV. Single Source of Truth | Every figure/table references a unique row in `results/fidelity_metrics.csv`. |
| V. Versioning Discipline | All artifacts are hashed; the CI updates `state/projects/...yaml` after each run. |
| VI. Commit-to-Doc Fidelity | Entity taxonomy (surface vs. intent) defined in `data-model.md` and enforced via `entityset.schema.yaml`. |
| VII. Architectural Fidelity Isolation | **Uniform hardware policy**: either all models run on CPU or all are re‑run on the same Kaggle GPU, eliminating hardware confounds. |

## Project Structure
```text
specs/001-evaluating-llm-fidelity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── commitpair.schema.yaml
│   ├── fidelity.schema.yaml
│   └── entityset.schema.yaml
└── tasks.md   # to be produced by /speckit-tasks later
```

A single‑repo layout (`src/` + `tests/`) suffices for this pure research pipeline.

## Phases & Task Mapping (covers all FR/SC)

| Phase | Description | Related FR | Related SC |
|-------|-------------|-----------|------------|
| **0 – Power Analysis** | Monte‑Carlo simulation (a large number of replicates) to estimate power of the Friedman test for detecting a medium effect (Cohen’s d suggests a medium effect size.) with 500 pairs; if power < 0.8, flag results as exploratory. | – | SC‑004 |
| **1 – Data Acquisition & Pairing** | Clone five repos, walk commit history (last 2 years), filter commits that modify `.md`/`.rst` files, extract diffs, output `data/raw/commit_pairs.csv`. | FR‑001, FR‑007, FR‑008 (gold‑standard sampling) | SC‑001 |
| **2 – Gold‑Standard Annotation** | Randomly sample an appropriate number of pairs., produce manual annotations for intent entities, compute inter‑annotator Cohen’s κ; if κ < 0.6, pipeline automatically switches to rule‑based intent extraction (see Phase 4). | FR‑008 | SC‑001, SC‑003 |
| **3 – Model Inference** | **Pre‑inference benchmark**: run a small pilot on CPU; if **any** model exceeds the 60 s timeout, **all** models are scheduled to run on a Kaggle free GPU (uniform fallback). Load each LLM in 4‑bit CPU mode (`device="cpu"`). For each commit, construct a fixed prompt (`<commit_message>\n<pre‑change doc context>`), generate documentation update, enforce max‑tokens = 200, timeout = 60 s, retry up to 2 ×. Store outputs in `data/generated/<model_id>/`. | FR‑002, NFR‑001 | SC‑002 |
| **4 – Entity Extraction** | **Surface Entities** – Expanded regex patterns: <br>• File paths: `r"[a-zA-Z0-9_./-]+\.(py|md|rst)"` <br>• Function signatures: `r"def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\("` <br>• Version numbers: `r"\d+\.\d+\.\d+"` <br>• Class names: `r"class\s+[A-Z][a-zA-Z0-9_]*"` <br>• Variable assignments: `r"[a-zA-Z_][a-zA-Z0-9_]*\s*="` <br>• Import statements: `r"(import|from)\s+[a-zA-Z0-9_.]+"` <br>**Technical Intent** – Zero‑shot classifier (`facebook/bart-large-mnli`) **threshold calibrated** on the 50‑sample gold‑standard to achieve κ ≥ 0.6; confidence threshold is set adaptively. If κ < 0.6, fallback to deterministic rule‑based heuristic (keyword + noun‑phrase). <br>**Verification** – Surface tokens are cross‑checked via `git grep -w` **and** AST parsing of the repository’s Python files (using `ast` module) to catch renamed/aliased symbols. Absence after both checks ⇒ hallucination. Produce `EntitySet` JSON per sample. | FR‑003, FR‑006 | SC‑003 |
| **5 – Fidelity Scoring** | Compute precision/recall per sample for intent and surface categories using human diff as ground truth (or gold‑standard for intent). Aggregate per model → `data/processed/fidelity_metrics.csv`. | FR‑004 | SC‑003 |
| **6 – Statistical Analysis** | Test normality (Shapiro‑Wilk). If non‑normal → Friedman test (`scipy.stats.friedmanchisquare`) on paired intent‑precision scores. If normal → repeated‑measures ANOVA (`statsmodels`). **Apply Holm‑Bonferroni correction** across the three metrics (intent precision, surface precision, hallucination rate). Record p‑values `[deferred]`. | FR‑005 | SC‑004 |
| **7 – Hallucination Quantification** | Using the AST‑augmented verification, flag generated surface entities absent from the codebase as hallucinations; compute `hallucination_rate` per sample and add to metrics. | FR‑006 | SC‑005 |
| **8 – Visualization & Reporting** | Bar chart of intent precision per model, confusion matrix of surface entity preservation, hallucination‑rate plot. Save figures under `results/figures/`. Assemble a markdown summary (`results/summary.md`). | FR‑005 | SC‑004, SC‑005 |
| **9 – Contract Validation** | Run contract tests against schemas in `contracts/` (**including `entityset.schema.yaml`**) and ensure dataset checksums are recorded. | – | – |
| **10 – CI Integration** | Add GitHub Actions workflow (`.github/workflows/research.yml`) that runs the full pipeline, caches model weights, and uploads artifacts. | – | – |

All phases respect the compute budget: phases 1‑5 stream Git data (≤ 7 GB RAM), model inference runs on CPU; if the uniform GPU fallback triggers, the entire batch runs on a Kaggle free GPU within the Multi‑hour limit. The default CI run uses **200** randomly sampled commits per model (≈ a few hundred generation calls) to stay well within the 6‑hour GitHub Actions wall‑clock limit; a separate manual workflow can be triggered for the full 500‑pair analysis.

---


