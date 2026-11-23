# Quickstart: llmXive follow-up: extending "ResearchStudio-Idea"

./run_pipeline.sh --stage all

*(In-place revision; steps preserved, expected outputs aligned to the redone tasks; fail-first acquisition semantics made explicit.)*

## Prerequisites

- Python 3.11+
- Git
- GitHub Actions access (or local environment with ≥7 GB RAM)
- Hugging Face API key (for generation)
- Expert recruitment channel (for real evaluation)

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-1011-llmxive-follow-up-extending-researchstud
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

## Running the Pipeline

### Step 1: Data Acquisition (T011)
```bash
python code/01_data_acquisition.py
```
Downloads (with pagination, balancing, and per-venue fallback/error logging). **Fail-first semantics**: if no configured source is reachable, the script logs a per-venue error and exits non-zero — it does NOT proceed with incomplete data. To exercise downstream logic without real sources, run the deterministic, clearly-labeled fixture explicitly:
```bash
python code/01_data_acquisition.py --dry-run
```
*Expected outputs*: `data/raw/corpus_raw.jsonl`, `data/processed/corpus_clean.jsonl`.

### Step 2: Pattern Mapping
```bash
python code/02_pattern_mapping.py
```
*Expected output*: `data/processed/embeddings.jsonl` (top-3 patterns per problem statement, cosine ≥ 0.6). If the configured embedding model fails to load, the script switches to a lighter fallback model and logs the switch.

### Step 3: Proposal Generation (T030)
```bash
python code/03_proposal_generation.py
```
Generates 50 pattern-guided + 50 baseline proposals (batched, ≤4 h). Falls back to Ollama if the API is rate-limited.
*Expected output*: `data/results/generated_proposals.jsonl`.

### Step 4: Evaluation Loader (T059a, T059b)
```bash
python code/04_evaluation_loader.py --blind    # writes blinded_batches.csv (incl. alignment rubric in instructions)
python code/04_evaluation_loader.py --mock     # deterministic dry-run ratings
```
For real evaluation: distribute blinded batches, collect ratings, place at `data/results/ratings_filled.csv` (replacing mock). Experts rate alignment against the problem statement/domain only; pattern cards are never shown.
*Expected outputs*: `data/results/blinded_batches.csv`, `data/results/ratings_filled.csv`.

### Step 5: Statistical Analysis (T024b, T055, T032, T033, T036, T037)
```bash
python code/05_statistical_analysis.py
```
Runs the IRR gate on raw ratings, power configuration (reported against the 0.8 convention), normality check + paired test, BH correction, outlier sensitivity, validity metrics, and report generation.
*Expected outputs*: `data/results/power_analysis_config.json`, `data/results/validity_metrics.json`, `data/results/analysis_report.md`.

## Verification

```bash
pytest tests/ -v
python code/05_statistical_analysis.py --dry-run
```

## Troubleshooting

- **OOM**: reduce batch size in `utils/config.py` or use API-based generation; the embedding step auto-falls-back to a lighter model with a logged switch.
- **Source inaccessible**: check logs for the per-venue error; the script exits non-zero by design — fix source configuration or add a verified source. Use `--dry-run` only for pipeline validation, never for real conclusions.
- **Low IRR**: alpha < 0.6 halts analysis before cleaning; recruit more experts and re-run Step 5.
- **Mock data present**: the report labels dry-run results; replace `ratings_filled.csv` with real ratings for final conclusions.