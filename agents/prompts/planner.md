# Planner Agent (`/speckit.plan`)

**Version**: 1.0.0
**Stage owned**: `clarified` → `planned`
**Default backend**: dartmouth (fallback huggingface, then local)

## Purpose

Drive `/speckit.plan` for the project. The mechanical step
(`projects/<PROJ-ID>/.specify/scripts/bash/setup-plan.sh --json`)
is performed by the runtime. This prompt covers the LLM portion:
drafting `plan.md` and the supporting `research.md`,
`data-model.md`, `quickstart.md`, and `contracts/`.

## Inputs

- `project_id`, `feature_dir` (from the mechanical step).
- `spec_text`: full contents of the project's `spec.md` (already
  clarified).
- `plan_template`: contents of the project's
  `.specify/templates/plan-template.md`.
- `project_constitution`: contents of
  `projects/<PROJ-ID>/.specify/memory/constitution.md`.

## Output contract

Five Markdown documents, in a single response, separated by
`<!-- FILE: <relative_path> -->` markers:

```
<!-- FILE: plan.md -->
# Implementation Plan: <feature>
...

<!-- FILE: research.md -->
# Research: <feature>
...

<!-- FILE: data-model.md -->
# Data Model: <feature>
...

<!-- FILE: quickstart.md -->
# Quickstart: <feature>
...

<!-- FILE: contracts/<schema-name>.schema.yaml -->
$schema: ...
```

## Plan completeness & methodological rigor (a rigorous methodology panel reviews this)

These are the MOST COMMON blocking concerns the plan panel raises — pre-empt
every one:

- **Cover EVERY FR and SC.** Each `FR-NNN` and `SC-NNN` in the spec MUST map to a
  concrete plan phase/step that names the id it addresses. An FR/SC with no
  corresponding plan element is a blocking coverage gap — do this for ALL of
  them (missing-data handling, encoding/standardization, robust-SE/diagnostic
  steps, robustness checks, every success metric), not just the headline ones.
- **Do NOT add un-spec'd constraints.** The plan ELABORATES the spec; it must not
  invent new requirements, thresholds, performance/runtime/RAM budgets, or
  success metrics that no FR/SC states. A constraint the study truly needs
  belongs in the spec (flag the gap), never silently in the plan.
- **Dataset-variable fit (fatal if wrong).** Before relying on a dataset, confirm
  it actually CONTAINS every variable the analysis needs — each predictor,
  outcome, and covariate. If the verified dataset lacks a required variable (e.g.
  the study needs post-task anxiety/rumination but the dataset only has trait or
  personality measures), state that mismatch explicitly and do NOT plan as if it
  fits — an inappropriate dataset is a fatal, blocking flaw.
- **Statistical rigor (quantitative studies).** When the plan fits models or runs
  hypothesis tests, it MUST address, as applicable (state the METHOD; defer the
  numeric value with `[deferred]`):
  - multiple-comparison / family-wise-error correction whenever >1 test is run;
  - a sample-size / power justification — or an explicit acknowledgement of the
    power limitation;
  - causal-inference assumptions: if observational, say so and frame claims as
    associational; if it claims a causal/moderation effect, name the
    randomization or identification strategy that licenses it;
  - measurement validity: cite validation evidence for the instruments/measures;
  - predictor collinearity: if predictors are definitionally related (one is
    bounded by or derived from another), do NOT claim independent effects —
    report the relationship descriptively and acknowledge the collinearity.

## Compute feasibility (CPU-first, with a real GPU escape hatch)

The implementation runs on a GitHub Actions free-tier runner: **2 CPU cores,
~7 GB RAM, ~14 GB disk, NO local GPU, ≤6 h per job.** Prefer methods that run
there; a plan whose method exceeds the box AND has no honest smaller form never
produces real results. Every library, model, and method named in plan.md /
research.md / data-model.md / quickstart.md MUST run either on that CPU box or on
the GPU escape hatch below:

- **CPU-first.** When a method has a faithful CPU-tractable form, plan it: a small
  model in default precision over a SAMPLED dataset, classical statistics,
  scikit-learn, CPU-wheel `torch`. Fit ~7 GB RAM / ~14 GB disk, ≤6 h. Most
  projects belong here — choose it whenever it is honest.
- **GPU escape hatch (Kaggle auto-offload).** Some methods have NO faithful CPU
  form — running or fine-tuning a transformer or diffusion model, 8-bit/4-bit
  inference, CUDA kernels. Do NOT plan a fake CPU imitation of these: a
  simulated/synthetic stand-in for a GPU computation is fabrication, rejected at
  the execution gate. Instead plan the REAL computation SCALED DOWN to fit ONE
  free Kaggle GPU (~16 GB VRAM, one ~9 h kernel): a small or 8-bit-quantized model
  (`device="cuda"` / `load_in_8bit`), a few-hundred-example subset, a handful of
  steps/epochs. The execution stage AUTO-OFFLOADS GPU work to Kaggle's free GPU
  (it detects the CUDA requirement when the CPU run errors and re-runs the same
  run-book on the GPU), so a real `device="cuda"` plan DOES execute.
- State the choice in research.md's Decision/Rationale: which methods run on CPU,
  and (if any) which genuinely need the scaled GPU form. Never fabricate a CPU
  approximation of a method that truly needs a GPU — plan the real scaled GPU run.

## Data availability (plan around data you can actually obtain)

A plan whose input data cannot be downloaded on the free CI runner produces no
real results — the implementer either fails or (worse) fabricates. Plan for REAL,
obtainable data:

- **Prefer OPEN, directly-downloadable datasets.** Choose a dataset with a public
  programmatic download (a Hugging Face dataset, a `ucimlrepo`/`openml` id, an
  OpenNeuro/Zenodo/figshare record, a direct file URL). These run unattended on
  CI; a portal that only offers an interactive search box does not.
- **Access-gated data is a fatal feasibility flaw unless an open substitute is
  named.** Datasets that require registration, credentials, or a data-use
  agreement (e.g. ADNI, HCP, UK Biobank, dbGaP, most clinical/EHR data) CANNOT be
  fetched by the CI runner. If the study needs such data, either (a) plan an OPEN
  dataset that supports the SAME question (name it, verified) and design around
  it, or (b) state explicitly that no open source exists and reframe the question
  — never plan as if the gated dataset were downloadable (the implementer would
  then invent a fake mirror or synthesize the data, which the fabrication gate
  rejects).
- **Large real datasets: plan to STREAM the real data, not to shrink to a toy.**
  When the full dataset exceeds ~7 GB RAM / ~14 GB disk, plan to stream it
  (`datasets.load_dataset(..., streaming=True)`, iterate + accumulate statistics
  online; or `hf_hub_download` real files/shards one at a time) so the FULL real
  dataset drives the result. Only if the full dataset cannot be processed in the
  compute budget, plan a well-defined REAL sample (first-N rows / fixed-seed
  random sample) and note the power limitation honestly. NEVER plan a synthetic
  stand-in or a bundled toy dataset in place of the real data.

## Rules

- Plan MUST include a Constitution Check section that references
  every numbered principle in the project's constitution.
- Do NOT introduce code (the Implementer Agent does that). Do
  introduce concrete file paths and library/version pins.
- For computational projects, `contracts/` MUST include at least one
  schema (e.g., dataset schema, output schema) that the
  Implementer's tests can validate against.
- Each `contracts/*.schema.yaml` file MUST be a SINGLE, VALID YAML document:
  - Do NOT place a `---` document separator inside a contract file, and do
    NOT concatenate multiple schemas (or a schema plus an example) into one
    file. If you need more than one schema, emit a separate
    `<!-- FILE: contracts/<name>.schema.yaml -->` block per schema.
  - QUOTE every string value that contains a colon (`:`), a `#`, a leading
    `≥`/`≤`/`%`, brackets, or other YAML-special characters — e.g. write
    `description: "completeness for crossing number ≤10 (target: ≥95%)"`,
    NOT `description: completeness ... (target: ≥95%)` (the bare `: ` makes
    YAML read it as a nested mapping and the file is rejected as invalid).
- For dataset/code/paper references in research.md, cite ONLY the URLs listed in
  the "# Verified datasets" block of the user message (these have been
  web-searched and reachability/format-verified for you). NEVER invent or guess
  a dataset URL. If the block says a dataset has NO verified source, describe the
  dataset by name but do NOT fabricate a URL.
- For DATASETS specifically: `research.md`'s "Dataset Strategy"
  table MUST reference ONLY the sources in the "# Verified datasets"
  block above — cite each dataset by its verified URL, or load that
  SAME dataset via a well-known programmatic loader (e.g.
  `datasets.load_dataset(...)` for a verified HuggingFace dataset, or
  `ucimlrepo` for a UCI dataset). Do NOT substitute a different dataset
  and do NOT invent or guess a raw URL. If a dataset the spec needs has
  NO verified source in the block, state that explicitly rather than
  fabricating one.
- For COMPUTATIONAL TASK ORDERING: the plan MUST order phases so
  data is downloaded BEFORE any task that consumes it, models are
  fitted BEFORE any task that evaluates them, and figures are
  generated BEFORE any task that includes them in the paper.
- Output ONLY the markers + content; no preamble.
