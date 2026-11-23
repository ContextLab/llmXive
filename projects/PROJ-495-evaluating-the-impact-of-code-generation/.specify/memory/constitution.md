# Evaluating the Impact of Code Generation on Code Vulnerability Density — Research Project Constitution

## Core Principles

### I. Reproducibility (NON-NEGOTIABLE)

Every result reported in this project MUST be reproducible by re-running the
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
`code/`. Derived numbers MUST NOT be hand-typed into the paper.

### V. Versioning Discipline

Every artifact under this project carries a content hash. The
Advancement-Evaluator Agent invalidates stale review records when the
hashed artifact changes. Every research-stage artifact change updates this
project's `state/projects/PROJ-495-evaluating-the-impact-of-code-generation.yaml` `updated_at` timestamp.

### VI. Static Analysis Fidelity

All vulnerability counts MUST be derived exclusively from the configured static analysis pipeline (Bandit, Semgrep, SonarQube) applied to the raw code artifacts. Manual counting or heuristic estimation of vulnerability density is prohibited. This principle is grounded in the methodology sketch which mandates running a "static analysis pipeline using Bandit (Python), Semgrep (multi-language), and SonarQube Community Edition on all code samples" to extract "vulnerability counts per file," ensuring that the comparison between LLM-generated and human-written code relies on consistent, tool-based detection rather than subjective assessment.

### VII. Vulnerability Taxonomy Compliance

Every identified vulnerability MUST be classified using the Common Weakness Enumeration (CWE) taxonomy. The project MUST report vulnerability density broken down by specific CWE classes (e.g., injection, XSS, buffer overflow). This requirement is grounded in the methodology sketch which explicitly states the need to "Classify vulnerabilities by type (injection, XSS, buffer overflow, authentication) using CWE taxonomy" to enable the statistical comparison of specific vulnerability patterns between code sources.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-495-evaluating-the-impact-of-code-generation/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-495-evaluating-the-impact-of-code-generation.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-09-03.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-495-evaluating-the-impact-of-code-generation | **Field**: computer science | **Ratified**: 2026-09-03
