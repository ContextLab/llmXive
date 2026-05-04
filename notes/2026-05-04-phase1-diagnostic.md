# Phase 1 (Idea Lifecycle) Diagnostic Report

**Date range**: 2026-05-04 – _<TBD on report finalize>_
**Spec**: [specs/003-phase1-idea-lifecycle-testing/spec.md](../specs/003-phase1-idea-lifecycle-testing/spec.md)
**Tracker**: [#107](https://github.com/ContextLab/llmXive/issues/107)
**Branch**: `003-phase1-idea-lifecycle-testing`
**Final commit at report time**: _<TBD; updated by T053>_
**Backend**: Dartmouth Chat (`is_paid: false` per `agents/registry.yaml`)

---

## Section 2: Executive summary

_(To be filled in T043 after Sections 3-7 are populated.)_

### What worked well

_(3-5 bullets, each citing a specific Section 3+ subsection by anchor link.)_

### What needs improvement

_(3-5 bullets, severity tag inline.)_

### What's broken

_(CRITICAL/HIGH defects only, each with file:line pointer.)_

**Carry-forward verdict**: _<N> projects carried forward to spec 004 (see Section 8 / `carry-forward.yaml`)._

---

## Section 3: Per-agent runs

### Brainstorm

_(One subsection per cohort. Quote state YAML before/after, idea artifact verbatim, run-log entry verbatim, acceptance-criteria evaluation per FR-009.)_

#### Cohort 1 (commit `f2dcf9f`)

**Prompt version under test**: `1.1.0` (`agents/prompts/brainstorm.md` at commit `be4bee0`, FR-003a-tightened)
**Backend / model**: dartmouth / `google.gemma-3-27b-it` (per registry default for the brainstorm agent)
**Generation command** (corrected — see defect D0 below): `python -m llmxive brainstorm --count 8`
**Cohort members** (8 projects):

1. PROJ-261-evaluating-the-impact-of-code-duplicatio
2. PROJ-262-predicting-molecular-dipole-moments-with
3. PROJ-263-assessing-the-validity-of-frequentist-co
4. PROJ-264-assessing-the-stability-of-statistical-m
5. PROJ-265-assessing-the-impact-of-data-ordering-on
6. PROJ-266-exploring-the-correlation-between-molecu
7. PROJ-267-predicting-plant-stress-response-from-pu
8. PROJ-268-the-impact-of-network-centrality-on-neur

##### Idea artifacts (verbatim, FR-006)

###### PROJ-261 — Evaluating the Impact of Code Duplication on LLM Code Understanding

```markdown
---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Code Duplication on LLM Code Understanding

**Field**: computer science

Code duplication is a common phenomenon in software development, often arising from copy-pasting. While the impact of code duplication on human maintainability is well-studied, its effect on Large Language Model (LLM) understanding of code remains largely unexplored. This research proposes to investigate how the presence of duplicated code blocks influences an LLM's ability to accurately predict the next token, generate code summaries, or identify bugs. We will analyze a large corpus of open-source Python code, quantifying code duplication using established metrics (e.g., JPlag) and then evaluating the performance of a pre-trained LLM (e.g., CodeGen, StarCoder) on tasks related to understanding duplicated versus non-duplicated code segments.  The results could inform strategies for reducing code duplication to improve LLM-assisted software engineering tools.
```

###### PROJ-262 — Predicting Molecular Dipole Moments with Graph Neural Networks

```markdown
---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Predicting Molecular Dipole Moments with Graph Neural Networks

**Field**: chemistry

Can graph neural networks (GNNs) accurately predict molecular dipole moments directly from SMILES strings, bypassing computationally expensive quantum chemical calculations? Accurate dipole moment prediction is crucial for understanding intermolecular interactions and predicting material properties, but traditional methods are often slow. This project proposes training and evaluating a GNN model on a publicly available dataset of molecular structures and their corresponding dipole moments (e.g., from the Open Quantum Chemistry Database). The model's performance will be assessed by comparing its predictions to experimental values or high-level ab initio calculations, focusing on diverse organic molecules. Success would provide a rapid and cost-effective method for estimating dipole moments, accelerating materials discovery and chemical simulations.
```

###### PROJ-263 — Assessing the Validity of Frequentist Confidence Intervals with Small Sample Sizes

```markdown
---
field: statistics
submitter: google.gemma-3-27b-it
---

# Assessing the Validity of Frequentist Confidence Intervals with Small Sample Sizes

**Field**: statistics

Small sample sizes frequently encountered in real-world applications can lead to inaccurate frequentist confidence intervals. This project investigates the extent to which standard confidence interval calculations (e.g., t-intervals, z-intervals) deviate from their nominal coverage probabilities when applied to datasets with n < 30, using publicly available datasets from the UCI Machine Learning Repository. The approach involves simulating repeated sampling from these datasets, calculating confidence intervals for a key parameter (e.g., mean, difference of means), and empirically estimating the actual coverage rate. This will provide insights into the reliability of frequentist inference in small-sample scenarios and potentially motivate the use of alternative interval estimation methods.
```

###### PROJ-264 — Assessing the Stability of Statistical Model Performance Across Data Subsets

```markdown
---
field: statistics
submitter: google.gemma-3-27b-it
---

# Assessing the Stability of Statistical Model Performance Across Data Subsets

**Field**: statistics

Recent advances in machine learning and statistical modeling often rely on large, publicly available datasets. However, the performance of these models can vary significantly depending on the specific subset of data used for evaluation. This research proposes to investigate the stability of statistical model performance across different subsets of a publicly available dataset (e.g., from OpenML or UCI), quantifying the variance in key metrics like accuracy, precision, and recall. The approach will involve partitioning the dataset into multiple random subsets, training and evaluating a pre-defined set of statistical models on each subset, and then analyzing the distribution of performance metrics. This will provide insights into the robustness of these models and identify potential biases introduced by data selection.
```

###### PROJ-265 — Assessing the Impact of Data Ordering on Bootstrapping Results

```markdown
---
field: statistics
submitter: google.gemma-3-27b-it
---

# Assessing the Impact of Data Ordering on Bootstrapping Results

**Field**: statistics

Bootstrapping is a widely used resampling technique for estimating the sampling distribution of a statistic. However, the order of samples in the original dataset can potentially influence the results of bootstrapping, especially when dealing with non-independent and identically distributed data. This project proposes to investigate the sensitivity of bootstrapping results to data ordering by applying bootstrapping to several publicly available time series datasets (e.g., stock prices, weather data) and comparing the resulting confidence intervals and p-values when the data is presented in its original order, reversed order, and randomly shuffled order. The analysis will focus on quantifying the discrepancy in statistical inferences caused by data ordering, and identifying dataset characteristics that exacerbate this effect, offering guidance for more robust bootstrapping applications.
```

###### PROJ-266 — Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes

```markdown
---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes

**Field**: chemistry

Can molecular flexibility, quantified through internal coordinate analysis or normal mode analysis, be correlated with experimentally measured permeability coefficients for a diverse set of drug-like molecules across biological cell membranes? This research proposes a computational screening of publicly available permeability data (e.g., from Caco-2 cell assays) alongside molecular dynamics simulations to calculate flexibility metrics. A statistical model will then be trained to predict permeability based on these flexibility descriptors, potentially identifying key structural features that enhance or hinder drug transport. Understanding this relationship could aid in the rational design of drug candidates with improved bioavailability.
```

###### PROJ-267 — Predicting Plant Stress Response from Publicly Available Proteomic Data

```markdown
---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Plant Stress Response from Publicly Available Proteomic Data

**Field**: biology

Can publicly available proteomic datasets from plants subjected to various abiotic stresses (drought, salinity, heat) be used to predict the expression levels of stress-responsive genes in novel, unseen conditions? This research will leverage existing datasets from resources like NCBI GEO and ProteomeXchange to train machine learning models (e.g., random forests, support vector regression) to map proteomic profiles to gene expression changes. The success of this approach could provide a valuable, rapid method for assessing plant stress resilience without requiring costly and time-consuming experimental validation, ultimately informing crop improvement strategies in the face of climate change.
```

###### PROJ-268 — The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI

```markdown
---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI

**Field**: neuroscience

Can measures of network centrality—degree, betweenness, and eigenvector centrality—predict the degree of functional synchrony between brain regions during resting-state fMRI? Existing work demonstrates that brain regions exhibit coordinated activity, but less is known about how the structural organization of the brain's network influences this synchrony. This project will leverage publicly available Human Connectome Project data to calculate network centrality metrics for each brain region and correlate them with pairwise functional connectivity values derived from resting-state fMRI scans. We hypothesize that regions with higher centrality will exhibit greater functional synchrony with other regions, reflecting their role as hubs in information integration. This analysis could offer insights into the neural mechanisms underlying efficient brain communication and inform models of cognitive function and dysfunction.
```

##### State YAML quotes (verbatim, FR-007)

All 8 state YAMLs share the same shape — quoting one representative (PROJ-261) and noting the per-project differences below:

```yaml
artifact_hashes: {}
assigned_agent: null
created_at: '2026-05-04T17:52:52.287155Z'
current_stage: brainstormed
failed_stage: null
field: computer science
human_escalation_reason: null
id: PROJ-261-evaluating-the-impact-of-code-duplicatio
last_run_id: null
last_run_status: null
points_paper: {}
points_research: {}
revision_round: 0
speckit_paper_dir: null
speckit_research_dir: null
title: Evaluating the Impact of Code Duplication on LLM Code Understanding
updated_at: '2026-05-04T17:52:52.287155Z'
```

Per-project field mapping (only `id`, `field`, `title`, and `created_at`/`updated_at` differ):

| Project | Field | Title |
|-|-|-|
| PROJ-261 | computer science | Evaluating the Impact of Code Duplication on LLM Code Understanding |
| PROJ-262 | chemistry | Predicting Molecular Dipole Moments with Graph Neural Networks |
| PROJ-263 | statistics | Assessing the Validity of Frequentist Confidence Intervals with Small Sample Sizes |
| PROJ-264 | statistics | Assessing the Stability of Statistical Model Performance Across Data Subsets |
| PROJ-265 | statistics | Assessing the Impact of Data Ordering on Bootstrapping Results |
| PROJ-266 | chemistry | Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes |
| PROJ-267 | biology | Predicting Plant Stress Response from Publicly Available Proteomic Data |
| PROJ-268 | neuroscience | The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI |

##### Run-log entries (verbatim, FR-007)

**Finding (defect D1, HIGH)**: the `python -m llmxive brainstorm` subcommand wrote ZERO run-log entries for any of PROJ-261..268. Confirmed by `grep -l "PROJ-26[1-8]" state/run-log/2026-05/*.jsonl` returning no matches. The only run-log entry written during this cohort step is for an unrelated `flesh_out` invocation on PROJ-258 (resulting from defect D0 below):

```json
{"agent_name": "flesh_out", "backend": "dartmouth", "cost_estimate_usd": 0.0, "ended_at": "2026-05-04T17:52:26.343862Z", "entry_id": "2d9e5eb0-e2ac-40c2-9ad6-5d8c07b86463", "failure_reason": null, "inputs": ["projects/PROJ-258-the-effect-of-simulated-social-rejection/idea/the-effect-of-simulated-social-rejection.md"], "model_name": "qwen.qwen3.5-122b", "outcome": "success", "outputs": ["projects/PROJ-258-the-effect-of-simulated-social-rejection/idea/the-effect-of-simulated-social-rejection.md"], "parent_entry_id": null, "project_id": "PROJ-258-the-effect-of-simulated-social-rejection", "prompt_version": "1.0.0", "run_id": "00785382-122d-4f72-ae6d-4540130756ac", "started_at": "2026-05-04T17:51:51.103465Z", "task_id": "d2cc7bd5-4f98-4312-aa1f-1be68b6b4d74"}
```

This violates FR-007 ("System MUST capture … the run-log JSONL entry … for every agent invocation") and Constitution principle III (real-call testing must produce loggable signal). See defect D1 in Section 6.

##### Acceptance-criteria evaluation (FR-009)

Issue [#59](https://github.com/ContextLab/llmXive/issues/59) acceptance criteria:

| # | Criterion | 261 | 262 | 263 | 264 | 265 | 266 | 267 | 268 |
|-|-|-|-|-|-|-|-|-|-|
| 1 | Outputs a seed.md / idea.md with non-empty title + field + idea body | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2 | The idea is in scope for 8h GHA cron (no special hardware, no datasets > 1GB) | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| 3 | Does NOT make claims about prior work | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ⚠️ |
| 4 | Stays under wall_clock_budget_seconds=300 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

FR-003a scope filter:

| # | Criterion | 261 | 262 | 263 | 264 | 265 | 266 | 267 | 268 |
|-|-|-|-|-|-|-|-|-|-|
| 5 | In-scope idea-type (literature review / sim ≤1h / analysis ≤1h) | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| 6 | Single core question or core idea | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | ✅ |
| 7 | Not requiring external data collection or experimentation | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| 8 | Not trivial / non-impactful (clear "why does this matter") | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |

Legend: ✅ pass, ⚠️ borderline (passes but has caveats noted below), ❌ fail.

Detailed rationale per project:

- **PROJ-261** (CS, code-duplication × LLM): seed body is well-formed but **scope creep risk** (criterion 2): "evaluating … on a *large* corpus of open-source Python" + running CodeGen/StarCoder inference (StarCoder is ~3-15B params, may not fit 7GB RAM). Single-core-question framing is also weak (criterion 6: lists three sub-tasks "predict next token, generate code summaries, OR identify bugs"). Mild prior-work nod ("largely unexplored") but no specific citations — passes criterion 3.
- **PROJ-262** (chem, GNN dipole moments): cleanest seed. Single sharp question, named public dataset (Open Quantum Chemistry Database), clear analysis path. Tiny criterion-3 caveat ("traditional methods are often slow") is opinion, not a citation. **Strong carry-forward candidate.**
- **PROJ-263, 264, 265** (statistics methodology trio): all three are well-constructed individually but cluster around the same theme ("how do standard methods behave on small/perturbed inputs?"). All three fail criterion 8 (trivial/non-impactful): the answers are largely already known in the textbooks (small-sample t-intervals undercover; performance varies across subsets; bootstrap is sensitive to dependence). The pipeline would produce confirmatory results no one would cite. **Reject all three** for carry-forward.
- **PROJ-266** (chem, molecular flexibility × permeability): mentions "molecular dynamics simulations to calculate flexibility metrics" — that's a scope-violation flag (criterion 2 + 5: full-atom MD does NOT fit ≤1h on 2 CPU / 7 GB RAM). Also mixes correlation analysis with simulation — multi-thread (criterion 6 fail risk). Caco-2 permeability data is publicly available but the project as written reads more like "a study that needs HPC + the public data" than "a study scoped to public data alone." **Borderline; would need flesh_out to scope down.**
- **PROJ-267** (biology, plant proteomics × stress): single sharp question, named public datasets (NCBI GEO, ProteomeXchange), explicit ML methods (random forests, SVR), clear "why does this matter" (climate change → crop improvement). **Strong carry-forward candidate.**
- **PROJ-268** (neuroscience, network centrality × fMRI synchrony): single sharp question, named public dataset (Human Connectome Project), explicit hypothesis ("regions with higher centrality will exhibit greater functional synchrony"), clear "why does this matter" (cognitive function/dysfunction). Mild criterion-3 caveat ("Existing work demonstrates …") but it's general background, not a citation. **Strong carry-forward candidate.**

##### Cohort-1 defects identified

- **D2** (HIGH, scope_breadth): 3/8 seeds (PROJ-263, 264, 265) cluster on "stability/validity of standard statistical methods on small/perturbed inputs" — technically in-scope but trivial/confirmatory. The brainstorm prompt should *more strongly* emphasize the "non-impactful / mechanically-true claims" rejection criterion in FR-003a. Tightening target: `agents/prompts/brainstorm.md:120-125` (the new "non-impactful" subsection).
- **D3** (MEDIUM, scope_creep_within_idea): 2/8 seeds (PROJ-261 LLM-on-code, PROJ-266 chem flexibility) propose computations that exceed the GHA envelope (large-LLM inference, full-atom MD). The prompt should explicitly require the seed to name the specific compute primitive and stay inside concrete RAM/runtime bounds. Tightening target: `agents/prompts/brainstorm.md:50-79` (existing GHA scope section).
- **D4** (LOW, multi_thread_proposal): 2/8 seeds (PROJ-261 "predict tokens / summarize / find bugs", PROJ-264 multi-metric stability) blur the "single core question" rule in subtle ways (offering 2-3 alternative tasks). The prompt could push harder on this with an explicit "name exactly one outcome variable / one core hypothesis" constraint. Tightening target: `agents/prompts/brainstorm.md:118-119`.
- Cluster diversity is acceptable (6 fields across 8 seeds — but 3/8 in statistics suggests model bias toward the field). Not flagged as a defect because the prompt does not constrain field distribution.

##### Cohort-1 verdict

**3 of 8 seeds clearly meet both bars** (PROJ-262, PROJ-267, PROJ-268). **3 of 8 are reject** (PROJ-263, PROJ-264, PROJ-265 — trivial/non-impactful). **2 of 8 are borderline** (PROJ-261, PROJ-266 — scope-creep risk that flesh_out *might* tighten down).

Per the spec's decision gate (T017): the cohort already has 3 strong candidates that meet both bars. **Skip iteration to T024 (provisional carry-forward candidate list)** with PROJ-262, PROJ-267, PROJ-268 as the leads. The borderline cases can be revisited if any strong candidate fails downstream. The defect-driven prompt patches (D2/D3/D4) are recorded in Section 6 as **deferred** to follow-up issues, since cohort 1 yielded enough quality without iterating.

**Brainstorm iteration count for the strong candidates**: 1 (cohort 1, no re-runs needed).

#### Induced failure-mode run (FR-015)

_(Populated by T023.)_

### Flesh_out

_(One subsection per selected project. Same content shape as brainstorm.)_

### Idea_selector

_(One subsection per project that survived flesh_out. Includes per-project verdict-comparison table per T038 / U1.)_

---

## Section 4: Citation resolution audit

_(One subsection per project that ran flesh_out. Quotes:_
- _Stage 1 JSON output from `tests/phase1/citation_resolver.py` verbatim_
- _Stage 2 (agent verifier) output per ambiguous citation_
- _Final per-citation verdict table per FR-010)_

---

## Section 5: Iteration diffs

_(One block per fix-and-re-run cycle. Quotes `git diff <prev-hash> <curr-hash> -- <path>` blocks with short SHAs per FR-008.)_

---

## Section 6: Defects categorized by severity

_(Single consolidated table populated by T044. Columns: ID, Severity, Category, Description, File:line, Status. SC-007 verification gate: every CRITICAL/HIGH row must have a non-empty Status.)_

| ID | Severity | Category | Description | File:line | Status |
|-|-|-|-|-|-|
| D0 | HIGH | spec/runbook bug | T014 / quickstart Step 1 documented `python -m llmxive run --max-tasks 1 --stage brainstormed` for cohort generation, but that command advances *existing* projects rather than creating new ones. Correct command is `python -m llmxive brainstorm --count N`. | `specs/003-phase1-idea-lifecycle-testing/tasks.md:T014`; `specs/003-phase1-idea-lifecycle-testing/quickstart.md:Step1`; `specs/003-phase1-idea-lifecycle-testing/research.md:Decision1` | resolved (commit `<TBD this commit>`) |
| D1 | HIGH | run-log gap | `python -m llmxive brainstorm` (`_cmd_brainstorm` in `cli.py`) does NOT write run-log entries — confirmed by `grep -l "PROJ-26[1-8]" state/run-log/2026-05/*.jsonl` returning empty. Violates FR-007 + Constitution III. | `src/llmxive/cli.py:_cmd_brainstorm` | deferred (issue #TBD) — fix is in production code outside Phase 1 testing scope |
| D2 | HIGH | scope_breadth | 3/8 cohort-1 seeds (PROJ-263/264/265) cluster on "stability/validity of standard statistical methods on small/perturbed inputs" — technically in-scope but trivial/confirmatory; would produce results no one would cite. | `agents/prompts/brainstorm.md:120-125` (the new "non-impactful" subsection) | deferred (issue #TBD) — cohort 1 yielded 3 strong candidates without iterating, so we skip the iteration loop per T017's decision gate |
| D3 | MEDIUM | scope_creep_within_idea | 2/8 seeds (PROJ-261 LLM inference of StarCoder, PROJ-266 molecular dynamics) propose computations that exceed GHA envelope (large-LLM inference, full-atom MD). Prompt needs explicit RAM/runtime budget naming requirement. | `agents/prompts/brainstorm.md:50-79` (existing GHA scope section) | deferred (issue #TBD) |
| D4 | LOW | multi_thread_proposal | 2/8 seeds (PROJ-261, PROJ-264) blur "single core question" rule by offering 2-3 alternative tasks. Prompt could require exactly-one-outcome-variable framing. | `agents/prompts/brainstorm.md:118-119` | deferred (issue #TBD) |

---

## Section 7: After-fix re-runs

_(One subsection per defect with `Status: resolved (commit <sha>)` from Section 6 — quotes the corresponding sibling-iteration artifact + run-log + acceptance-criteria evaluation showing the defect is gone.)_

---

## Section 8: Carry-forward summary

_(Populated by T051 after `carry-forward.yaml` is written. Quotes the YAML verbatim, then a one-paragraph commentary per project explaining selection.)_
