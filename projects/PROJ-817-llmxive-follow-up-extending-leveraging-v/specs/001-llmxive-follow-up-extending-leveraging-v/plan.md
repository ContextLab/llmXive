# Implementation Plan: llmXive follow‑up – Graph‑augmented Verifier Evaluation

**Branch**: `001-llmxive-verifier-graph` | **Date**: 2026‑10‑24 | **Spec**: [spec.md]  
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-leveraging-v/spec.md`

## Summary
The project evaluates whether a **CPU‑only symbolic constraint‑graph** preprocessing layer mitigates the degradation of the distilled Edit‑R1 1B verifier on *conflicting* image‑editing instructions. The pipeline:

1. **Download & verify** three open InstructPix2Pix parquet shards (balanced large‑scale prompt set).  
2. **Curate** a balanced CSV of 1 000 prompts (500 conflicting, 500 neutral) **with manual verification of conflict status** (see Phase 0‑b).  
3. **Collect human feasibility scores for all 1 000 prompts** (crowdsourced, 0‑1 scale) and store them in `data/results/human_validation.csv`.  
4. **Parse** each instruction into a directed constraint graph using spaCy + networkx, detecting temporal and contradiction edges.  
5. **Run baseline verifier** on raw prompts (CPU‑only 8‑bit Edit‑R1 1B).  
6. **Run graph‑augmented verifier** with JSON graph context (plus two control contexts).  
7. **Statistical comparison** (paired test, multiple‑comparison correction, robustness hold‑out, power analysis).  
8. **Generate a machine‑readable report** conforming to `contracts/evaluation_report.schema.yaml`.  

All phases respect the established wall‑clock time constraint. and ≤ 7 GB RAM on a GitHub Actions free‑tier runner (Principle I, SC‑002, SC‑003, SC‑009).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `torch==2.3.0` (CPU‑only, 8‑bit quantized)  
  - `transformers==4.44.0`  
  - `datasets==2.21.0`  
  - `spacy==3.7.4` + `en_core_web_sm`  
  - `networkx==3.3`  
  - `pandas==2.2.2`  
  - `numpy==2.0.0`  
  - `scipy==1.13.1`  
  - `statsmodels==0.14.2`  
  - `tqdm==4.66.5`  
  - `psutil==5.9.8`  
- **Storage**: Files under `data/` (parquet, CSV, JSON).  
- **Testing**: `pytest` + contract validation.  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk).  
- **Constraints**: Symbolic parser CPU‑only; verifier runs **CPU‑only 8‑bit** inference (no GPU fallback).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | Fixed seeds (`numpy`, `torch`, `random`); deterministic data loaders (`datasets.load_dataset` with explicit URLs); all scripts are CI‑runnable. |
| II. Verified Accuracy | All external URLs are taken from the verified list in the spec; titles meet the required overlap. |
| III. Data Hygiene | Raw parquet files are streamed, SHA‑256 checksummed, and recorded in `data/raw/provenance.json`. |
| IV. Single Source of Truth | Every figure/table is derived from a single CSV/JSON artifact; no hand‑typed numbers. |
| V. Versioning Discipline | Content hashes of all artifacts are recorded in `state/projects/PROJ-817-...yaml`; any change updates the timestamp. |
| VI. Symbolic Preprocessing Fidelity | Parser uses only spaCy, networkx, and rule‑based logic; no GPU or differentiable components. |
| VII. Conflict‑Agnostic Robustness Validation | Separate analysis for conflicting vs. neutral prompts; paired tests; hold‑out re‑phrased conflict set; multiple‑comparison correction. |

## Project Structure
```
specs/001-llmxive-verifier-graph/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── evaluation_report.schema.yaml
└── tasks.md   # generated later

src/
├── data/
│   ├── download.py            # streams verified parquet files, verifies checksums
│   ├── curate.py              # balances, assigns UUIDs, writes curated_prompts.csv
│   ├── conflict_verify.py     # manual/heuristic verification of conflict status
│   ├── human_annotation.py    # crowdsourcing wrapper, writes human_validation.csv
│   └── filter_conflicts.py    # heuristic filter for naturally occurring conflicts
├── parser/
│   ├── graph_builder.py       # spaCy + networkx pipeline with contradiction & temporal detection
│   └── utils.py
├── verifier/
│   ├── baseline.py            # runs Edit‑R1 on raw prompts (CPU‑only 8‑bit)
│   └── augmented.py           # runs verifier with graph JSON context + two controls
├── analysis/
│   ├── stats.py               # paired tests, corrections, power checks
│   └── report.py              # writes report.json / report.csv
└── cli/
    └── run_all.py             # orchestrates the full pipeline

tests/
├── unit/
│   ├── test_graph_builder.py
│   └── test_stats.py
└── contract/
    └── test_evaluation_report.py
```

## Phase Mapping (covers every FR & SC)

| Phase | Tasks | FR(s) addressed | SC(s) addressed |
|-------|-------|-----------------|-----------------|
| **0 – Data Acquisition** | `src/data/download.py` (stream three verified parquet URLs, verify SHA‑256) → `src/data/curate.py` (balance, assign UUIDs, write `data/results/curated_prompts.csv`) → `src/data/conflict_verify.py` (manual/heuristic verification of conflict status, ensure exactly 500 conflicting and 500 neutral prompts) | FR‑001, FR‑009 (human scores later) | SC‑002, SC‑003 |
| **0‑b – Conflict Verification** | Human annotators (or a small expert review) label each prompt as truly *conflicting* or *neutral*; results stored in `conflict_verified` column of `curated_prompts.csv`. | FR‑001 (ensures valid conflict set) | SC‑002 |
| **1 – Human Annotation** | `src/data/human_annotation.py` (crowd‑source **all 1 000** prompts) → writes `data/results/human_validation.csv` and merges into `curated_prompts.csv` | FR‑001, FR‑009, FR‑010 (synthetic never used for evaluation) | SC‑001, SC‑006, SC‑007 |
| **2 – Symbolic Graph Construction** | `src/parser/graph_builder.py` (spaCy + networkx, ≤ 30 min) | FR‑002 | SC‑002 |
| **3 – Baseline Verifier Evaluation** | `src/verifier/baseline.py` (CPU‑only 8‑bit Edit‑R1 1B) | FR‑003 | SC‑009 (target ≤ 2 h) |
| **4 – Randomization & Counterbalancing** | Fixed‑seed permutation of condition order per prompt (`numpy.random.seed(12345)`) | FR‑008 | SC‑002 |
| **5 – Graph‑Augmented Evaluation** | `src/verifier/augmented.py` (inject graph JSON, plus control‑filler & control‑empty) | FR‑004 | – |
| **6 – Statistical Analysis** | `src/analysis/stats.py` (paired test, normality check, Wilcoxon fallback, Benjamini‑Hochberg correction, robustness hold‑out, power analysis) | FR‑005, FR‑006, FR‑007, FR‑008 | SC‑001‑SC‑008 |
| **7 – Reporting** | `src/analysis/report.py` (generate `report.json` & `report.csv` conforming to contract) | FR‑010 (no synthetic scores) | SC‑001‑SC‑010 |
| **8 – Verification** | `pytest` contract suite | – | – |

All phases are ordered so that data is available before any consumer step, models are fitted before evaluation, and figures/reports are generated last.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None – all requirements fit within a single‑module design respecting CPU‑only constraint (except verifier inference, which now uses 8‑bit CPU quantization) | – | – |

---


## projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/specs/001-llmxive-follow-up-extending-leveraging-v/research.md
# Research: llmXive follow‑up – Graph‑augmented Verifier Evaluation

## 1. Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Raw prompts & images | InstructPix2Pix (three verified parquet shards) | `datasets.load_dataset("parquet", data_files=[URL1, URL2, URL3], streaming=False)` | URLs are listed in the contract block; each file’s SHA‑256 is recorded in `data/raw/provenance.json`. |
| Human feasibility scores | Crowdsourced annotation of **all 1 000** prompts | `src/data/human_annotation.py` writes `data/results/human_validation.csv` | Provides the primary ground‑truth for alignment (FR‑001, FR‑009). |
| Conflict verification | Manual/heuristic verification of conflict status (via `src/data/conflict_verify.py`) | Outputs `conflict_verified` column in `curated_prompts.csv`; ensures exactly 500 conflicting and 500 neutral prompts. | Guarantees that the “conflicting” subset truly contains contradictory instructions. |
| Synthetic feasibility scores | Deterministic heuristic (Section 2) | Generated locally in `src/data/curate.py` (column `synthetic_score`) | **Never** used for evaluation (FR‑010). |

All downloads and processing are performed programmatically on the CI runner; no manual steps are required.

## 2. Synthetic Feasibility Scoring (generation only)
1. **Neutral prompts** → synthetic score `1.0`.  
2. **Conflicting prompts** → parse into atomic clauses; compute the proportion of mutually compatible clauses using a WordNet‑based antonym dictionary. Result ∈ [0, 1] reflects “partial compliance”.  
3. Store in the `synthetic_score` column of `curated_prompts.csv`.  

**Human Validation**: a separate annotation step (Section 1) collects `human_score`. If Pearson r between synthetic and human scores < 0.6, we flag the heuristic and **exclude synthetic scores from any downstream evaluation** (fulfilling FR‑010).

## 3. Baseline Verifier Evaluation (FR‑003)
- Load the distilled Edit‑R1 1B model from Hugging Face (`"llmxive/edit-r1-1b-distilled"`).  
- **CPU‑only 8‑bit quantized inference** is used to keep RAM < 7 GB and avoid any GPU dependence.  
- Run inference on each `prompt_text` **without** graph context, recording verifier alignment probability as `verifier_score`.  
- Output `data/results/baseline_scores.csv` with columns: `prompt_id`, `verifier_score`, `human_score`, `alignment_delta = verifier_score - human_score`.  

*Alignment delta is always computed against the independent **human_score** (synthetic scores are ignored).*

**Runtime target**: **≤ 2 hours** for the full 1 000‑prompt set (≈ 0.3 s per prompt with 8‑bit quantization). If runtime unexpectedly exceeds 2 h, the pipeline aborts and reports the limitation (SC‑009).

## 4. Symbolic Constraint‑Graph Parser (FR‑002, Principle VI)
- **Tokenization & POS** via spaCy (`en_core_web_sm`).  
- **Node extraction**: noun‑phrase chunks representing actionable principles.  
- **Temporal edges**: detect cue words (“first”, “then”, “after”) → `temporal-precedes`.  
- **Contradiction edges**: two complementary heuristics  
  1. WordNet antonym dictionary.  
  2. Cue‑word patterns (“but”, “however”, “contradict”, “while”).  
- Serialize each graph to JSON (`graph_<prompt_id>.json`).  
- **Runtime budget**: ≤ 30 min on 2‑core CPU (validated by profiling).  
- **GPU usage**: None; the parser runs strictly on CPU.  

**Failure policy**: Prompts for which graph construction fails are logged, a warning is emitted, and a `null` graph (`{}`) is used for that sample; the pipeline continues without halting.

## 5. Randomization & Counterbalancing (supports FR‑008)
For each prompt we randomly permute the order in which the four evaluation conditions are executed:

1. Baseline (raw prompt)  
2. Graph‑augmented  
3. Control‑filler (random JSON of similar size)  
4. Control‑empty (`{}`)

The permutation is generated with a fixed seed (`numpy.random.seed(12345)`) to ensure reproducibility while eliminating systematic order effects that could bias runtime or memory measurements (addresses FR‑008 and SC‑002).

## 6. Graph‑Augmented Verifier Evaluation (FR‑004)
- Embed each graph JSON into the verifier’s prompt template under a `Context:` section.  
- **Control Conditions**:  
  1. **Random filler** – a JSON object of similar size containing unrelated key‑value pairs.  
  2. **Empty graph** – `{}`.  
- Run inference (**CPU‑only 8‑bit quantized**) and store results in `data/results/augmented_scores.csv` (same schema as baseline, plus a `condition` column indicating `graph_augmented`, `control_filler`, or `control_empty`).  

## 7. Statistical Comparison (FR‑005, FR‑006, FR‑007, FR‑008)
1. **Primary paired test** – Conflicting subset (`baseline_scores` vs. `augmented_scores`).  
   - Normality check (Shapiro‑Wilk).  
   - If normal → paired **t‑test**; else → **Wilcoxon signed‑rank**.  
   - Report: mean alignment‑score difference, Cohen’s d (or rank‑biserial), 95 % CI, p‑value.  
2. **Neutral‑subset paired test** – Verify that graph augmentation does not degrade performance on neutral prompts (addresses SC‑006).  
3. **Control comparison** – Baseline vs. random filler (same test) to confirm improvements are not due to added context length.  
4. **Robustness check** – Apply the full pipeline to a hold‑out set of re‑phrased conflicting prompts generated via deterministic back‑translation; repeat the paired test.  
   - Verify that the effect‑size drop is **non‑significant (p ≥ 0.05)** (SC‑005).  
5. **Multiple‑comparison correction** – Apply **Benjamini‑Hochberg FDR** (α = 0.05) across the three hypothesis tests (primary, neutral, robustness). Adjusted p‑values are reported (SC‑004).  
6. **Correlation analysis** – Compute Pearson r between verifier scores (baseline & augmented) and human scores; require **r ≥ 0.5** (SC‑007).  

All calculations use `scipy.stats` and `statsmodels.stats.multitest`.

## 8. Power Analysis (Methodology)
Using G*Power (paired t‑test, α = 0.05, effect size d = 0.5), **N = 500** conflicting prompts yields power ≈ 0.85. Because we collect human scores for **all 1 000 prompts**, the paired analysis on the 500 conflicting items satisfies the planned power.  

**Justification**: Prior work on verifier‑graph interventions reported medium‑sized effects (see *Leveraging Verifier‑Based RL in Image Editing*, 2025).  

**Contingency**: If the observed effect size is **< 0.3**, the report will flag the study as under‑powered and recommend additional data collection rather than overstating significance.

## 9. Runtime & Memory Auditing (FR‑008, SC‑002, SC‑003, SC‑009)
- `psutil` logs peak RAM for each stage; assert ≤ 7 GB.  
- Wall‑clock timers log duration of parser, baseline inference, augmented inference, and analysis; total ≤ 6 h.  
- **Baseline verifier runtime** is recorded separately and must be **≤ 2 h** (target ≤ 2 h); if exceeded, the pipeline aborts and the limitation is reported (SC‑009).  

## 10. Decision / Rationale (CPU vs GPU)
The 1B Edit‑R1 model in float32 exceeds the 7 GB RAM limit on pure CPU, so inference scripts request **CPU‑only 8‑bit quantization**, which reduces RAM usage to ≈ 5 GB and fits within the free‑tier constraints without any GPU fallback.

## 11. Deliverables
- `data/raw/*.parquet` (original InstructPix2Pix shards)  
- `data/raw/provenance.json` (checksums and source metadata)  
- `data/results/curated_prompts.csv` (prompt text + synthetic & **human** feasibility scores)  
- `data/results/human_validation.csv` (raw crowd ratings)  
- `data/results/graphs/*.json` (constraint graphs)  
- `data/results/baseline_scores.csv`  
- `data/results/augmented_scores.csv` (graph + controls)  
- `analysis/report.json` (full statistical summary, runtime, memory, correlation, correction method)  
- `analysis/report.csv` (human‑readable summary for the paper)  

All files conform to the schemas defined in `contracts/evaluation_report.schema.yaml`.

## 12. Ethical & Reproducibility Notes
- Human annotation data are stored under `data/results/human_validation.csv` with SHA‑256 checksums recorded in the project state file.  
- All randomness seeded (`numpy.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)`).  
- Synthetic conflict generation is **not** used for evaluation; only the real conflict set is evaluated (fulfilling FR‑010).  

## 13. Verification
```bash
pytest tests/contract/test_evaluation_report.py
```
All contract tests must pass before CI marks the job successful.

---


## projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/specs/001-llmxive-follow-up-extending-leveraging-v/data-model.md
# Data Model: llmXive follow‑up – Graph‑augmented Verifier Study

## 1. Raw Dataset (`raw_parquet`)
- **Location**: `data/raw/` (three parquet files downloaded from the verified URLs).  
- **Schema (informal)**: columns include `image_id`, `prompt`, `source_image_path`, etc., exactly as provided by InstructPix2Pix. No modification is performed.

## 2. Curated Prompt CSV (`curated_prompts.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `prompt_id` | string | Deterministic UUID for the prompt. |
| `instruction_type` | enum(`conflicting`, `neutral`) | Ground‑truth label (balanced groups of equal size). |
| `prompt_text` | string | Full natural‑language instruction. |
| `synthetic_score` | number (0.0‑1.0) | Rule‑based feasibility heuristic (used only for internal diagnostics; **not** for evaluation). |
| `human_score` | number (0.0‑1.0) | Independent human‑annotated feasibility score (primary ground‑truth). |
| `conflict_verified` | boolean | `true` if manual/heuristic verification confirmed the prompt is truly conflicting; `false` otherwise. |
| `checksum` | string | SHA‑256 of the original parquet row (data hygiene). |

File path: `data/results/curated_prompts.csv`.

## 3. Human Validation CSV (`human_validation.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `prompt_id` | string | Links to `curated_prompts.csv`. |
| `human_rating` | number (0.0‑1.0) | Average rating from crowd workers. |
| `annotation_source` | string | e.g., `"MTurk"` or `"internal_form"`. |

File path: `data/results/human_validation.csv`.

## 4. Constraint Graph JSON (`graph_<prompt_id>.json`)
```yaml
graph_id: string          # same as prompt_id
nodes:
  - id: string            # e.g., "node_1"
    label: string         # principle phrase
    type: enum("principle")
edges:
  - source: string        # node id
    target: string        # node id
    label: enum("temporal-precedes", "contradiction")
    weight: number
metadata:
  parser_version: string
  parse_timestamp: string   # ISO‑8601
```
Stored under `data/results/graphs/`.

## 5. Baseline Scores CSV (`baseline_scores.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `prompt_id` | string | Links to `curated_prompts.csv`. |
| `verifier_score` | number (0.0‑1.0) | Alignment score from baseline verifier. |
| `human_score` | number (0.0‑1.0) | Copied from `curated_prompts.csv`. |
| `alignment_delta` | number | `verifier_score - human_score`. |

File path: `data/results/baseline_scores.csv`.

## 6. Augmented Scores CSV (`augmented_scores.csv`)
Same columns as `baseline_scores.csv` plus:
| Column | Type | Description |
|--------|------|-------------|
| `condition` | enum(`graph_augmented`, `control_filler`, `control_empty`) | Indicates which context was used. |

File path: `data/results/augmented_scores.csv`.

## 7. Final Evaluation Report (`report.json`)
```yaml
report_version: "1.0.0"
generated_at: "2026-10-22T12:00:00Z"
runtime_seconds: integer
memory_peak_gb: number
tests:
  primary:
    $ref: "#/definitions/test_result"
  robustness:
    $ref: "#/definitions/test_result"
multiple_comparison_correction:
  type: object
  required:
    - method
    - alpha
    - adjusted_p_values
  properties:
    method:
      type: string
      enum: ["benjamini_hochberg", "bonferroni"]
    alpha:
      type: number
      minimum: 0
      maximum: 1
    adjusted_p_values:
      type: object
      required:
        - primary
        - robustness
      properties:
        primary:
          type: number
          minimum: 0
          maximum: 1
        robustness:
          type: number
          minimum: 0
          maximum: 1
definitions:
  test_result:
    type: object
    required:
      - test_name
      - method
      - p_value
      - effect_size
      - ci_95
      - corrected
    properties:
      test_name:
        type: string
      method:
        type: string
        enum: ["paired_t_test", "wilcoxon"]
      p_value:
        type: number
        minimum: 0
        maximum: 1
      effect_size:
        type: number
        description: "Cohen's d for t‑test or rank‑biserial for Wilcoxon."
      ci_95:
        type: array
        minItems: 2
        maxItems: 2
        items:
          type: number
      corrected:
        type: boolean
        description: "True if p‑value has been corrected for multiple comparisons."
```
File path: `analysis/report.json`.

All CSV files are UTF‑8 encoded, line‑terminated with `\n`. JSON files are pretty‑printed with 2‑space indentation.

---


## projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/specs/001-llmxive-follow-up-extending-leveraging-v/quickstart.md
# Quickstart: Graph‑augmented Verifier Evaluation (llmXive)

A researcher can reproduce the entire study on a GitHub Actions free‑tier runner (or a local Linux environment) with the commands below.

## 1. Prerequisites
- Python 3.11
- Internet access (to download the InstructPix2Pix parquet files)
- Optional: GPU access (Kaggle free GPU). **The pipeline runs fully on CPU**, so a GPU is not required.

## 2. Setup
```bash
# Clone the repository (assumed already present)
git checkout 001-llmxive-verifier-graph

# Create a fresh virtual environment
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r requirements.txt

# Download the spaCy English model
python -m spacy download en_core_web_sm
```

## 3. Data download & curation
```bash
# Stream the verified parquet shards and write them to data/raw/
python -m src.data.download

# Build the balanced CSV, add synthetic scores, assign UUIDs, and write to data/results/
python -m src.data.curate
```

- **Provenance**: `data/raw/provenance.json` records the three URLs, their SHA‑256 checksums, and the generated file checksum.

## 4. Conflict set selection (no synthetic generation)
```bash
# Filter natural language prompts for realistic contradictions using heuristic cues
python -m src.data.filter_conflicts
# This creates `data/results/curated_prompts.csv` with an equal number of conflicting and neutral prompts.
```

## 5. Human feasibility annotation (required for evaluation)
```bash
python -m src.data.human_annotation
# Writes `data/results/human_validation.csv` and merges scores into `curated_prompts.csv`.
```

## 6. Symbolic graph construction (CPU‑only)
```bash
python -m src.parser.graph_builder
# Output: data/results/graphs/graph_<prompt_id>.json
# Expected runtime < 30 min on the 2‑core runner (SC‑002).
```

## 7. Baseline verifier evaluation
```bash
python -m src.verifier.baseline
# Produces data/results/baseline_scores.csv
# Uses CPU‑only 8‑bit quantized inference, staying within ≤ 7 GB RAM and **≤ 2 h** runtime (target ≤ 2 h; aborts and reports limitation if exceeded) (SC‑009).
```

## 8. Graph‑augmented verifier evaluation (with controls)
```bash
python -m src.verifier.augmented
# Produces data/results/augmented_scores.csv (conditions: graph_augmented, control_filler, control_empty)
```

## 9. Statistical analysis & report generation
```bash
python -m src.analysis.stats
python -m src.analysis.report
```

- Generates:
  - `analysis/report.json`  (machine‑readable, conforms to contract)
  - `analysis/report.csv`   (human‑readable table for the paper)

## 10. Verification
```bash
pytest tests/contract/test_evaluation_report.py
```

All contract tests must pass; otherwise the CI job fails.

## 11. Expected outputs
| File | Description |
|------|-------------|
| `data/raw/*.parquet` | Original InstructPix2Pix shards (verified URLs). |
| `data/raw/provenance.json` | Checksums and source metadata. |
| `data/results/curated_prompts.csv` | Prompt text + synthetic & **human** feasibility scores (human scores for all prompts). |
| `data/results/human_validation.csv` | Raw crowd ratings. |
| `data/results/graphs/*.json` | One constraint graph per prompt (CPU‑only). |
| `data/results/baseline_scores.csv` | Verifier scores without graph context. |
| `data/results/augmented_scores.csv` | Verifier scores with graph context and two control conditions. |
| `analysis/report.json` | Full statistical results, runtime, memory usage, correlation, correction method. |
| `analysis/report.csv` | Human‑readable summary for inclusion in the manuscript. |

The quickstart now points to the correct module paths (`src.data...`) and includes the new conflict‑filter step and the corrected output path for `curated_prompts.csv`.

---


## projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/specs/001-llmxive-follow-up-extending-leveraging-v/contracts/evaluation_report.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Evaluation Report Schema"
type: object
required:
  - report_version
  - generated_at
  - runtime_seconds
  - memory_peak_gb
  - tests
  - multiple_comparison_correction
properties:
  report_version:
    type: string
    description: "Semantic version of the report format."
  generated_at:
    type: string
    format: date-time
    description: "ISO‑8601 timestamp of report generation."
  runtime_seconds:
    type: integer
    minimum: 0
    description: "Total wall‑clock time of the entire pipeline."
  memory_peak_gb:
    type: number
    minimum: 0
    description: "Peak RAM usage in gigabytes."
  tests:
    type: object
    required:
      - primary
      - robustness
    properties:
      primary:
        $ref: "#/definitions/test_result"
      robustness:
        $ref: "#/definitions/test_result"
  multiple_comparison_correction:
    type: object
    required:
      - method
      - alpha
      - adjusted_p_values
    properties:
      method:
        type: string
        enum: ["benjamini_hochberg", "bonferroni"]
      alpha:
        type: number
        minimum: 0
        maximum: 1
      adjusted_p_values:
        type: object
        required:
          - primary
          - robustness
        properties:
          primary:
            type: number
            minimum: 0
            maximum: 1
          robustness:
            type: number
            minimum: 0
            maximum: 1
definitions:
  test_result:
    type: object
    required:
      - test_name
      - method
      - p_value
      - effect_size
      - ci_95
      - corrected
    properties:
      test_name:
        type: string
      method:
        type: string
        enum: ["paired_t_test", "wilcoxon"]
      p_value:
        type: number
        minimum: 0
        maximum: 1
      effect_size:
        type: number
        description: "Cohen's d for t‑test or rank‑biserial for Wilcoxon."
      ci_95:
        type: array
        minItems: 2
        maxItems: 2
        items:
          type: number
      corrected:
        type: boolean
        description: "True if p‑value has been corrected for multiple comparisons."