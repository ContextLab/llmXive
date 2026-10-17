# Implementation Plan: Evaluating LLM Fidelity in Commit-to-Documentation Translation

**Branch**: `001-evaluating-llm-fidelity` | **Date**: 2026-10-17 | **Spec**: [spec.md](../specs/001-evaluating-llm-fidelity/spec.md)  
**Input**: Feature specification from `specs/001-evaluating-llm-fidelity/spec.md`

## Summary
The project builds a reproducible, CPU‑first pipeline (with an optional uniform GPU fallback) that:

1. **Power analysis** to confirm that ≥500 paired samples give ≥80 % power for the Friedman test.  
2. **Data acquisition**: programmatically clone five public Python repositories, extract all commits from the last two years that modify `.md` or `.rst` files, and produce ≥500 validated `(commit_message, doc_diff)` pairs.  
3. **Gold‑standard annotation** of a 50‑sample subset for “technical intent” entities, with inter‑annotator agreement ≥0.6.  
4. **LLM inference** using three open‑source models (Phi‑3‑mini, Gemma‑2‑2b, Llama‑3.2‑3B) in 4‑bit CPU mode; if any model exceeds the 60 s timeout, all models are re‑run on a Kaggle free GPU.  
5. **Entity extraction**: deterministic regex for surface entities; zero‑shot intent classifier calibrated on the gold standard (fallback to rule‑based if κ < 0.6). Surface entities are cross‑checked against the repository codebase via `git grep` **and** AST parsing.  
6. **Fidelity scoring** (precision/recall for intent & surface, hallucination rate).  
7. **Statistical analysis**: normality test → Friedman test (or repeated‑measures ANOVA) with Holm‑Bonferroni correction across three metrics.  
8. **Visualization & reporting**.  
9. **Contract validation** against JSON/YAML schemas.  
10. **CI integration** that runs the full pipeline on every push, caches model weights, and uploads artifacts.

All steps are deterministic, schema‑validated, and respect the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `gitpython`, `datasets`, `transformers`, `bitsandbytes`, `torch>=2.0`, `scikit-learn`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pandas`, `pyyaml`, `tqdm`, `astor`  
- **Storage**: File‑based CSV/JSON under `data/` (raw, intermediate, final)  
- **Testing**: `pytest` with contract tests in `tests/contract/`  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, ~14 GB disk) – **GPU escape hatch** permitted for all models uniformly if needed.  
- **Project Type**: Research pipeline (CLI‑driven)  
- **Performance Goals**: Generation ≤60 s per commit on CPU (NFR‑001).  
- **Constraints**: All models run in 4‑bit quantization on CPU; uniform GPU fallback uses identical quantization.  
- **Scale/Scope**: Minimum 500 paired samples; default CI run samples 200 commits per model to stay within the 6 h wall‑clock limit; a manual workflow can process the full 500‑pair set.

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All scripts are deterministic (seed = 42), data fetched from fixed public URLs, and a single entry point `run_pipeline.py` orchestrates the full workflow. |
| II. Verified Accuracy | All external citations will be validated by the Reference‑Validator before manuscript inclusion (per constitution). |
| III. Data Hygiene | Repository clones are checksum‑verified; each transformation writes a new file with provenance recorded in `data/metadata.yaml`. |
| IV. Single Source of Truth | Every figure, table, and metric references a unique row in `data/processed/fidelity_metrics.csv`. |
| V. Versioning Discipline | All artifacts are hashed; the CI workflow updates `state/projects/PROJ-104-...yaml` after each successful run. |
| VI. Commit-to-Doc Fidelity | Entity taxonomy (surface vs. intent) is defined in `data-model.md` and enforced via `entityset.schema.yaml`. |
| VII. Architectural Fidelity Isolation | Uniform hardware policy: either all models run on CPU or all are re‑run on the same Kaggle GPU, eliminating hardware confounds. |

## Project Structure
```text
specs/001-evaluating-llm-fidelity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── commitpair.schema.yaml
│   ├── generatedoutput.schema.yaml
│   ├── entityset.schema.yaml
│   └── fidelitymetric.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

Source code layout (single‑repo):
```text
src/
├── data_extraction.py
├── gold_annotation.py
├── inference.py
├── entity_extraction.py
├── scoring.py
├── analysis.py
├── utils.py
└── run_pipeline.py

tests/
├── contract/
│   ├── test_commitpair_schema.py
│   ├── test_generatedoutput_schema.py
│   ├── test_entityset_schema.py
│   └── test_fidelity_schema.py
└── unit/
    ├── test_data_extraction.py
    └── test_entity_extraction.py
```

## Phases & Task Mapping (covers all FR/SC)

| Phase | Description | Related FR | Related SC |
|-------|-------------|-----------|------------|
| **0 – Power Analysis** | Monte‑Carlo simulation to estimate power of the Friedman test for 500 pairs. | – | SC‑004 |
| **1 – Data Acquisition & Pairing** | Clone five repos, walk two‑year history, filter commits that modify `.md`/`.rst`, extract diffs, output `data/raw/commit_pairs.csv`. | FR‑001, FR‑007, FR‑008 (gold‑sample) | SC‑001 |
| **2 – Gold‑Standard Annotation** | Randomly sample 50 pairs, produce manual intent annotations (CSV), compute Cohen’s κ; if κ < 0.6, switch to rule‑based intent extraction. | FR‑008 | SC‑001, SC‑003 |
| **3 – Model Inference** | Benchmark each model on a 10‑sample pilot; if any exceeds 60 s timeout, schedule **uniform GPU fallback** on Kaggle; otherwise run on CPU with 4‑bit quantization, generate docs, retry up to 2× on failure. | FR‑002, NFR‑001 | SC‑002 |
| **4 – Entity Extraction** | (a) Surface entities via expanded regexes; (b) Intent entities via zero‑shot classifier (`facebook/bart-large-mnli`) calibrated on gold‑standard; fallback to deterministic keyword heuristic if κ < 0.6; verify surface tokens with `git grep` + AST parsing. | FR‑003, FR‑006 | SC‑003 |
| **5 – Fidelity Scoring** | Compute precision/recall per sample for intent & surface, hallucination rate; aggregate to `data/processed/fidelity_metrics.csv`. | FR‑004 | SC‑003 |
| **6 – Statistical Analysis** | Normality test → Friedman (or repeated‑measures ANOVA) → Holm‑Bonferroni correction across intent precision, surface precision, hallucination rate; report effect sizes. | FR‑005 | SC‑004 |
| **7 – Visualization & Reporting** | Bar chart of intent precision per model, confusion matrix for surface entities, hallucination‑rate plot; save under `results/figures/`; assemble `results/summary.md`. | FR‑005 | SC‑004, SC‑005 |
| **8 – Contract Validation** | Run schema validation against all `contracts/*.schema.yaml`; generate checksum manifest. | – | – |
| **9 – CI Integration** | GitHub Actions workflow (`.github/workflows/research.yml`) runs the full pipeline, caches model weights, uploads artifacts. | – | – |

### Mitigating the T003 Failure
The previous extraction script relied on ad‑hoc `git log` parsing that produced malformed diffs. The revised approach:

- Use **GitPython** to iterate commits (`Repo.iter_commits`) with `max_count=None` and `since=2 years ago`.  
- For each commit, call `commit.diff(commit.parents[0], create_patch=True)` and filter `diff.a_path`/`diff.b_path` ending in `.md` or `.rst`.  
- Store the **unified diff** (`diff.diff.decode('utf-8')`) exactly as produced by Git.  
- Validate each row against `commitpair.schema.yaml` before writing to CSV.  
- If a commit has no documentation diff, it is skipped (fulfills FR‑001 & FR‑007).  

This deterministic pipeline produces a real CSV that can be schema‑validated, satisfying the verifier.

### Mitigating the T004 Failure
The gold‑standard annotation step will now:

- Export the 50 sampled `commit_hash` values to `data/gold/sample_ids.txt`.  
- Provide a **template CSV** (`data/gold/annotation_template.csv`) with columns `commit_hash, intent_entities (semicolon‑separated)`.  
- Annotators fill the template locally; a **checksum** of the completed file is recorded.  
- A small Python script (`gold_annotation.py`) computes Cohen’s κ using `sklearn.metrics.cohen_kappa_score`.  
- If κ < 0.6, the pipeline logs the issue and automatically switches to the rule‑based intent extractor (as described in Phase 4).  

All files are real, version‑controlled, and schema‑validated (`generatedoutput.schema.yaml` for the downstream step), eliminating the earlier failure.

---
