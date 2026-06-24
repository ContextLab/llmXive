# Evaluating the Impact of Code Style on LLM Code Generation Diversity — Research Project Constitution

## Core Principles

### I. Reproducibility (NON-NEGOTIABLE)

Every result reported in this project MUST be reproducible by re‑running the
project's `code/` against the project's `data/` on a fresh GitHub Actions
runner. Random seeds MUST be pinned in `code/`. External datasets MUST be
fetched from the same canonical source on every run.

### II. Verified Accuracy (inherits parent Principle II)

Every external citation in `idea/`, `technical-design/`,
`implementation-plan/`, or `paper/` MUST be verified by the
Reference-Validator Agent against the primary source before contributing
review points. Title-token-overlap with the cited source MUST be ≥
`CITATION_TITLE_OVERLAP_THRESHOLD` (default 0.7).

### III. Data Hygiene

Datasets MUST be checksummed and the checksum recorded under `data/`. No
data may be modified in place; every transformation MUST produce a new file
with a documented derivation. Personally identifying information MUST NOT
appear in committed data.

### IV. Single Source of Truth (inherits parent Principle I)

Every figure, statistic, or interpretation in the paper MUST trace back to
exactly one row in this project's `data/` and one block in this project's
`code/`. Derived numbers MUST NOT be hand‑typed into the paper.

### V. Versioning Discipline

Every artifact under this project carries a content hash. The
Advancement-Evaluator Agent invalidates stale review records when the
hashed artifact changes. Every research‑stage artifact change updates this
project's `state/projects/PROJ-466-evaluating-the-impact-of-code-style-on-l.yaml` `updated_at` timestamp.

### VI. Style‑Aware Evaluation (domain‑specific)

All prompt variants that encode explicit style constraints (neutral, strict
PEP8, aggressive minification) **must** be stored as separate files under
`code/prompts/` and referenced by name in any experiment configuration.
The generation pipeline must record which style variant was used for each
sample, ensuring that diversity metrics can be traced back to the exact
style conditioning described in the methodology sketch (HumanEval tasks,
CodeGen‑350M‑mono model). No experiment may omit this provenance metadata.

### VII. Statistical Rigor in Diversity Analysis (domain‑specific)

Diversity measurements (token n‑gram overlap, AST edit distance) **must** be
computed using the same versioned analysis scripts located in
`code/analysis/`. Any statistical test, such as the Kruskal‑Wallis H‑test
used to compare style groups, must be executed with a fixed random seed and
its parameters (e.g., significance threshold) declared in a
`config/analysis.yaml` file. Results reported in the paper must include the
exact script version hash and the configuration snapshot that produced
them.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-466-evaluating-the-impact-of-code-style-on-l/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end‑to‑end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-466-evaluating-the-impact-of-code-style-on-l.yaml` `artifact_hashes` map.
- Raw data is preserved unchanged; derivations are written to new
  filenames.
- No commits are accepted that fail the Repository-Hygiene Agent's PII
  scan.

## Verified Accuracy Gate

The Reference-Validator Agent runs at three points:

1. On every artifact write that introduces or modifies citations.
2. Inside the Advancement-Evaluator before awarding any review point.
3. As a blocking gate on the `research_review` → `research_accepted`
   transition.

A reviewer's score MUST be set to 0.0 if the reviewed artifact has any
citation in `unreachable` or `mismatch` status.

## Versioning

This constitution carries its own semver. Initial version:
**1.0.0** — ratified 2026-06-24.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-466-evaluating-the-impact-of-code-style-on-l | **Field**: computer science | **Ratified**: 2026-06-24

# Idea summary (for context)

---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Code Style on LLM Code Generation Diversity

**Field**: Computer Science

## Research question

To what extent do explicit code style constraints in prompts modulate the structural diversity of solutions generated by small-scale open-weight code Large Language Models (LLMs)?

## Motivation

Understanding how stylistic conditioning influences LLM output variability is critical for deploying code assistants that balance readability with solution exploration. If strict style guidelines inadvertently collapse the search space of viable solutions, models may fail to discover alternative, potentially more efficient implementations. This project addresses the gap in evaluating LLM robustness to stylistic variation beyond standard functional correctness metrics.

## Literature gap analysis

### What we searched

Queries targeted "LLM code generation style," "code style constraints LLM," and "diversity of generated code" across Semantic Scholar and arXiv using the provided literature block. The search yielded four results, none of which directly isolate code style as an independent variable affecting generation diversity.

### What is known

- [SIMCOPILOT: Evaluating Large Language Models for Copilot-Style Code Generation (2025)](http://arxiv.org/abs/2505.21514v1) — Establishes benchmarks for interactive coding assistants but does not vary style constraints as a parameter.
- [Evaluating Code Generation of LLMs in Advanced Computer Science Problems (2025)](http://arxiv.org/abs/2504.14964v1) — Focuses on educational utility and functional correctness in student contexts without analyzing stylistic conditioning effects.

### What is NOT known

No published work has quantified how specific formatting rules (indentation, naming conventions, bracing) impact the entropy or structural variance of generated code. Existing evaluations prioritize pass rates over the diversity of acceptable solutions under stylistic constraints.

### Why this gap matters

Developers rely on LLMs to propose multiple alternatives; if style constraints reduce diversity, users lose access to novel implementation strategies. Filling this gap informs prompt engineering guidelines for maintaining creative flexibility while adhering to team style guides.

### How this project addresses the gap

The methodology explicitly manipulates style constraints in prompts and measures output diversity using AST-based metrics, directly isolating the causal link between style conditioning and solution variance.

## Expected results

We expect strict style constraints (e.g., minified or rigid PEP8) to reduce structural diversity compared to neutral prompts, measurable via lower n‑gram entropy and reduced AST edit distances. Confirming this would imply that style prompting acts as a regularization mechanism, potentially limiting exploration of alternative algorithms.

## Methodology sketch

- **Data acquisition**: Download the HumanEval benchmark subset (publicly available on HuggingFace) containing 164 programming tasks.
- **Model selection**: Load a small open-weight model (e.g., Salesforce/CodeGen-350M-mono) via `transformers` on CPU to ensure compliance with 7GB RAM limits.
- **Prompt engineering**: Create three style variants for each task: (1) Neutral, (2) Strict PEP8, (3) Aggressive Minification.
- **Generation**: For each task and style, generate 5 code samples using temperature sampling (T=0.7) to capture variability.
- **Metric computation**: Calculate token n‑gram overlap and Abstract Syntax Tree (AST) edit distance between generated samples within each style group.
- **Statistical analysis**: Apply a Kruskal‑Wallis H‑test to compare diversity score distributions across the three style groups.
- **Validation**: Ensure all generated code compiles (where possible) to filter non‑functional noise before diversity analysis.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None identified.
- Verdict: NOT a duplicate
