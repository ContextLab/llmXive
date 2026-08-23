# Data Model: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

All pipeline artifacts are stored under `data/derived/` and conform to the JSON‑Schema contracts in `specs/001-llmxive-crosslingual/contracts/`.

## Artifact Overview
| Artifact | Description | Schema |
|----------|-------------|--------|
| `edge_spectrum.json` | Edge‑spectrum bases for each model (top leading singular vectors) **and** model‑pair similarity matrix (see FR‑014). | `contracts/edge_spectrum.schema.yaml` |
| `frequency_list_{lang}.json` | Normalized token frequency distribution for language `{lang}` (size = shared vocabulary of several thousand tokens). | `contracts/frequency_list.schema.yaml` |
| `token_attribution_{model}.json` | Ranked list of token IDs with highest logit weights in the edge spectrum for `{model}`. | `contracts/token_attribution.schema.yaml` |
| `language_projection_{model}_{lang}.json` | Language‑specific projection coordinates of mean embedding onto the model’s edge spectrum. | `contracts/language_projection.schema.yaml` |
| `similarity_metric.json` | Cosine similarity scores between model‑pair edge spectra with confidence intervals (model‑pair view). | `contracts/similarity_metric.schema.yaml` |
| `bootstrap_test.json` | Parametric bootstrap test results for edge‑spectrum similarity (see `bootstrap_test.schema.yaml`). | `contracts/bootstrap_test.schema.yaml` |
| `similarity_matrix.json` | Cosine similarity matrix (model‑pair × language‑pair) for language‑projection vectors with bootstrap CIs. | `contracts/similarity_matrix.schema.yaml` |
| `validation.json` | Correlation results between projection residuals and (a) WALS typological feature differences, (b) SentEval STS drops. Includes Pearson $r$, two‑tailed $p$, and 95 % CI. | `contracts/validation.schema.yaml` |
| `permutation_test.json` | Permutation test output: p‑value, significance flag, null‑distribution summary statistics. | `contracts/permutation_test.schema.yaml` |
| `similarity_report.json` | Consolidated report combining similarity metrics, adjusted metrics, and narrative findings. | `contracts/similarity_report.schema.yaml` |
| `feasibility_report.json` | Runtime, CPU usage, RAM peak, any abort warnings, and verification timestamps for all external URLs. | `contracts/feasibility_report.schema.yaml` |
| `token_count_guard.json` | Guard file produced by the data‑loader confirming that each language’s token count ≥ 1 M and recording SHA‑256 checksums. | *No separate schema* (simple JSON with counts and checksums). |
| `reproducibility_audit.json` | Records random seeds, checksum logs, and any deviations from the deterministic pipeline (supports Constitution Principle I). | *No separate schema* (internal audit). |
| `state/projects/PROJ-880-llmxive-follow-up-extending-your-unembed.yaml` | Project state file updated with artifact hashes and timestamps (supports Principle V). | *No separate schema* (managed by the workflow). |

## Relationships
- `edge_spectrum.json` → feeds into `similarity_metric.json` and `token_attribution_{model}.json`.  
- `frequency_list_{lang}.json` + `edge_spectrum.json` → feed `language_projection_{model}_{lang}.json`.  
- `language_projection_{model}_{lang}.json` → feeds `similarity_matrix.json` and `validation.json`.  
- `edge_spectrum.json` + control analyses (paired‑architecture) → produce `similarity_report.json`.  
- All artifacts are version‑hashed; the hash is recorded in `feasibility_report.json` for Principle V compliance.

---



