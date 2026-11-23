# Quickstart: llmXive follow-up: extending "ArcANE"

## Prerequisites

- Python 3.11+
- Sufficient RAM (for CPU quantized models)
- Git

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-919-llmxive-follow-up-extending-arcane-do-ro
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` includes `transformers`, `llama-cpp-python`, `scipy`, `pandas`, `hypothesis`, `sentence-transformers`, `textblob`.*

## Configuration

1. **Define Character Axes**:
 Input Coarse and Fine axis definitions via CLI flags (see T011a).
 Example JSON for `--coarse-file`:
 ```json
 {
 "character": "Elizabeth Bennet",
 "axis_name": "Pride to Humility",
 "description": "A journey from initial arrogance and prejudice to self-reflection and humility."
 }
 ```
 Example JSON for `--fine-file`:
 ```json
 {
 "character": "Elizabeth Bennet",
 "axis_name": "Initial Arrogance to Self-Reflection",
 "description": "Specific behavioral shift from dismissing Darcy to recognizing her own misjudgments.",
 "source_observation": "Elizabeth's reaction to Darcy's first proposal vs. her reaction to his letter."
 }
 ```

2. **Set Random Seeds**:
 Configuration is handled via `src/lib/config.py`. Default seed is 42.

## Data Pipeline Execution

The following steps must be executed in order. The CLI entry point `src/cli/run_experiment.py` (T036) enforces data integrity checks before proceeding.

### Step 1: Data Preparation (Prerequisites)
Ensure the source corpus and gold standard exist.
```bash
# Download source text (T013)
python -m src.cli.download_text --character "Elizabeth Bennet"

# Generate Gold Standard if missing (T009a)
python -m src.scripts.generate_gold_standard
```

### Step 2: Axis Validation (US1)
Validate Coarse and Fine axis definitions for semantic independence.
```bash
python -m src.cli.axis_input --coarse-file path/to/coarse.json --fine-file path/to/fine.json
```
*Expected Output: Validation pass/fail message. Validated axes are written to `data/derived/axes.jsonl` (T015).*

### Step 3: Probe Generation (US2)
Generate "Out-of-World" scenarios semantically distant from the source text.
```bash
python -m src.cli.generate_probes --character "Elizabeth Bennet" --output data/derived/probes.jsonl
```
*Expected Output: `data/derived/probes.jsonl` containing >= 50 unique probes per character.*

### Step 4: Experiment Execution (US3)
Run the target model under Coarse, Fine, and Hybrid conditions with Judge evaluation.
```bash
python -m src.cli.run_experiment
```
*Note: This command performs pre-flight checks (T053). It executes the full pipeline: Calibration (T029), Execution (T030), and Statistical Analysis (T033-T035).*
*Expected Output: `data/derived/results_raw.jsonl`, `data/derived/stats_results.json`, `data/derived/results_final.jsonl`.*

### Step 5: Statistical Analysis
The analysis is automatically performed during Step 4.
*Output: `data/derived/stats_results.json` containing ANOVA/Friedman results, p-values, and effect sizes.*

## Data Formats

### Axis Definition (`data/derived/axes.jsonl`)
Follows the schema in `specs/001-llmxive-follow-up-extending-arcane-do-ro/contracts/axis.schema.yaml` (T010).
```json
{
 "character": "Elizabeth Bennet",
 "coarse": {
 "character": "Elizabeth Bennet",
 "axis_name": "Pride to Humility",
 "description": "..."
 },
 "fine": {
 "character": "Elizabeth Bennet",
 "axis_name": "Initial Arrogance to Self-Reflection",
 "description": "...",
 "source_observation": "..."
 }
}
```

### Probe (`data/derived/probes.jsonl`)
```json
{
 "character": "Elizabeth Bennet",
 "probe_text": "You are in a cyberpunk city...",
 "condition": "coarse",
 "validity_score": 0.95
}
```

### Results (`data/derived/results_final.jsonl`)
```json
{
 "probe_id": "...",
 "condition": "hybrid",
 "judge_score": 0.82,
 "rule_score": 0.75,
 "consistency_score": 0.78,
 "adherence_flag": true
}
```

## Verification

1. **Check Data Integrity**:
 ```bash
 python -m src.cli.check_data_integrity
 ```
 *Verifies checksums of `data/raw/arcane_corpus.jsonl`, `data/derived/probes.jsonl`, and `data/gold_standard/human_annotations.json`.*

2. **Reproduce Results**:
 Ensure `CI_TIME_LIMIT_SECONDS` is set if running in a constrained environment.
 ```bash
 python -m src.cli.run_experiment
 ```