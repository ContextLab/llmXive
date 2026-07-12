# llmXive follow-up: extending "CiteVQA: Benchmarking Evidence Attribution for Trustworthy Document In" — Research Project Constitution

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
project's `state/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc.yaml` `updated_at` timestamp.

### VI. Cross-Modal Attribution Fidelity

The project's primary evaluation metric, Strict Attributed Accuracy (SAA),
MUST be computed as the strict intersection of answer correctness (exact match
or semantic similarity > 0.85) and bounding box Intersection-over-Union (IoU)
> 0.5. This principle mandates that text-only models (specifically Phi-3-mini
in the decomposed pipeline) are evaluated against the specific failure mode
of "Attribution Hallucination" by verifying that predicted text chunks map to
the correct visual coordinates in the CiteVQA dataset. Any claim regarding
model performance is invalid unless it explicitly reports the SAA score derived
from this dual-constraint evaluation, ensuring that high retrieval accuracy
does not mask a failure in spatial localization.

### VII. Modality-Decoupled Experimental Control

To isolate the causal impact of visual pre-training, the project MUST maintain
strict separation between the Text-Only Baseline and the Visual-Only Control
experiment. The Text-Only Baseline (using `all-MiniLM-L6-v2` and Phi-3-mini)
MUST rely exclusively on retrieved text chunks and predicted chunk IDs without
access to raw pixel data during the reasoning phase. Conversely, the Visual-Only
Control MUST receive only the cropped image regions derived from the predicted
chunk IDs, excluding textual context. This structural separation is required
to validate the hypothesis that text-only reasoning fails to utilize low-level
structural cues (e.g., layout proximity, font hierarchy) necessary for precise
spatial localization, as defined in the methodology sketch.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-12.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-832-llmxive-follow-up-extending-citevqa-benc | **Field**: linguistics | **Ratified**: 2026-07-12
