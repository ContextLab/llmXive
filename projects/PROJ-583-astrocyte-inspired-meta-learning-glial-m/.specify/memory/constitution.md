# Astrocyte-Inspired Meta-Learning: Glial Modulation of Neural Networks — Research Project Constitution

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
project's `state/projects/PROJ-583-astrocyte-inspired-meta-learning-glial-m.yaml` `updated_at` timestamp.

### VI. Biologically-Grounded Regularization Integrity

The implementation of the astrocyte-inspired homeostatic module MUST strictly
adhere to the calcium-wave ODE formulation (Eq. 1-3) defined in the cited
neural-astrocytic architecture (Polykretis et al., 2018). The multiplicative
homeostatic factor $h_t = f(Ca_t)$ applied to the MAML inner-loop gradient
updates MUST be derived directly from the simulated calcium concentration
$Ca_t$ without heuristic simplification, ensuring the biological mechanism
remains the sole source of the stability-plasticity regularization effect.
This principle is grounded in the **Methodology sketch** section of the idea,
which explicitly mandates implementing the specific ODE and coupling it to
neuron learning rates, and the **Motivation** section, which identifies the
lack of translation from astrocyte-derived homeostatic mechanisms to
meta-learning algorithms as the primary research gap.

### VII. Statistical Rigor in Stability-Plasticity Evaluation

Performance claims regarding the stability-plasticity trade-off MUST be
validated using paired-sample t-tests (p < 0.05) comparing the
astrocyte-modulated MAML against a vanilla MAML baseline across a minimum of
five random seeds. The evaluation MUST explicitly report both the **plasticity
metric** (accuracy on the current task after 1, 5, and 10 inner-loop updates)
and the **stability metric** (accuracy on the previous task after training on
the current task) as defined in the **Training protocol**. This principle is
grounded in the **Expected results** section, which anticipates statistically
significant differences between the modulated model and baseline, and the
**Methodology sketch**, which specifies the exact metrics and statistical
tests required to confirm or refute the hypothesis.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-583-astrocyte-inspired-meta-learning-glial-m/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-583-astrocyte-inspired-meta-learning-glial-m.yaml` `artifact_hashes` map.
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
**1.0.0** — ratified 2026-07-03.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-583-astrocyte-inspired-meta-learning-glial-m | **Field**: neuroscience | **Ratified**: 2026-07-03
