# Quickstart: llmXive Verifier Graph Augmentation Study

This guide walks a researcher through a single CI-compatible run that reproduces all results.

## 1. Prerequisites
- GitHub Actions runner (or local Linux environment) with Python 3.11.
- Internet access to download the InstructPix2Pix data.
- Optional: GPU access (Kaggle free GPU) — the pipeline will automatically offload if necessary.

## 2. Setup
```bash
# Clone the repository (assumed already present)
git checkout 001-llmxive-verifier-graph

# Create a fresh virtual environment
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```
Note: if `python -m spacy download en_core_web_sm` fails with a
`numpy.dtype size changed` binary-incompatibility error, the venv's
`spacy`/`thinc` wheels were built against a different numpy ABI; fix by
reinstalling a matching pair (e.g. `pip install -U "spacy>=3.7,<3.8"
"numpy<2"`) before continuing. This affects only the parser stage (T003).

## 3. Data download & curation
```bash
python -m code.src.data.download           # streams the real InstructPix2Pix train split; writes data/raw/prompts_sample.parquet (an initial subset of real prompts with row SHA-256 checksums)
python -m code.src.data.curate             # creates data/results/curated_prompts.csv (adds synthetic_score)
python -m code.src.data.conflict_generator # injects contradictions into neutral prompts → conflicting set
```

### Input provenance (T001)
- **Dataset ID**: `timbrooks/instructpix2pix` (Hugging Face)
- **Split**: `train`
- **Streaming rule**: `datasets.load_dataset("timbrooks/instructpix2pix", split="train", streaming=True)` — the full stream is scanned in fixed-size chunks without loading it into RAM.
- **Real fallbacks** (same dataset, no synthetic data, used only if the primary loader fails on the runner): (1) the dataset's canonical auto-converted parquet shards listed by the official HF datasets-server API and the Hub parquet API, streamed shard-by-shard with `load_dataset("parquet", data_files=<url>, streaming=True)`. The source actually used is recorded in `data/raw/prompts_sample_provenance.json`.
- **Checksums**: each output row carries a SHA-256 checksum over its `(edit_prompt, original_prompt, edit_type)` values; the output file's own SHA-256 is recorded in `data/raw/prompts_sample_provenance.json`.
- **Output**: `data/raw/prompts_sample.parquet` — a sample of real `(image, edit_prompt)` prompt texts with non-null prompts and checksums, sized for exploratory analysis. The loader raises on any fetch error; there is no synthetic fallback.
- **Runnable command**: `python -m code.src.data.download`

## 4. Human feasibility validation (required for primary evaluation)
```bash
python -m code.src.data.human_annotation   # launches a lightweight web form or MTurk batch for the full set of prompts
# Results are saved to data/results/human_validation.csv and merged into data/results/curated_prompts.csv as the `human_score` column.
```

## 5. Symbolic graph construction
```bash
python -m code.src.parser.graph_builder     # reads data/results/curated_prompts.csv, writes JSON graphs to data/results/graphs/
# Logs runtime; should finish < 30 minutes (SC-002).
```

## 6. Baseline verifier evaluation
```bash
python -m code.src.verifier.baseline        # produces data/results/baseline_scores.csv
# This script will request a CUDA device; if unavailable it will trigger the GPU escape hatch.
# Baseline runtime must be ≤ 2 h (SC-009) and will be logged automatically.
```

## 7. Graph-augmented verifier evaluation
```bash
python -m code.src.verifier.augmented       # produces data/results/augmented_scores.csv and control condition files
```

## 8. Statistical analysis & report generation
```bash
python -m code.src.analysis.stats           # runs paired tests (conflicting & neutral), control comparison, robustness check, correlation, correction
python -m code.src.analysis.report          # writes data/results/report.json and report.csv
# The report includes SC-001 (mean diff), SC-004 (p < 0.05), SC-005 (robustness p ≥ 0.05), SC-006 (baseline mean ± SD), SC-007 (Pearson r ≥ 0.5), SC-008 (effect size ≥ 0.5).
```

## 9. Expected outputs
| File | Description |
|------|-------------|
| `data/raw/prompts_sample.parquet` | An initial subset of real InstructPix2Pix prompt texts with row SHA-256 checksums. |
| `data/raw/prompts_sample_provenance.json` | Dataset ID, split, streaming rule, source used, output SHA-256. |
| `data/results/curated_prompts.csv` | Prompt text + synthetic & **human** feasibility scores. |
| `data/results/graphs/*.json` | One graph per prompt (structural abstraction only). |
| `data/results/baseline_scores.csv` | Verifier scores without graph context (aligned to human scores). |
| `data/results/augmented_scores.csv` | Verifier scores with graph context and control runs. |
| `data/results/report.json` | Full statistical results, runtime, memory usage, baseline runtime, correlation. |
| `data/results/report.csv` | Human-readable table for inclusion in the paper. |

## 10. Verification
Run the contract tests to ensure schema compliance:
```bash
pytest code/tests/test_evaluation_report.py
```
All tests must pass before the CI job is considered successful.

## 11. GPU Escape Hatch Note
If the runner reports `torch.cuda.is_available() == False`, the verifier scripts automatically switch to the Kaggle GPU escape hatch (the platform will re-run the same command on a free GPU). No code changes are required; just ensure that the `torch` and `transformers` versions support `device="cuda"`.