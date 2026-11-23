# Data Model: llmXive follow-up: extending "On the Geometry of On-Policy Distillation"

## Core Entities
| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **GSM8KRecord** | One question‑answer pair from the GSM8K dataset. | `question: str`, `answer: str`, `difficulty: int (optional)` |
| **ModelCheckpoint** | Serialized TinyLlama weights after a training epoch. | `epoch: int`, `seed: int`, `path: str` |
| **ParameterDelta** | Per‑layer weight change Δθ collected during OPD epochs. | `layer_name: str`, `delta_matrix: np.ndarray (stored as .npz)` |
| **SVDResult** | Output of randomized SVD per layer. | `layer_name: str`, `U: np.ndarray`, `S: np.ndarray`, `Vt: np.ndarray`, `cum_variance: list[float]` |
| **SubspaceMask** | Binary mask derived from top‑k singular vectors. | `layer_name: str`, `mask: np.ndarray (bool)`, `k: int`, `variance_explained: float` |
| **ExperimentRun** | One training/evaluation run (specific condition, seed). | `run_id: str`, `condition: enum[full_opd, frozen_opd, frozen_sft, random_sft, full_sft]`, `seed: int`, `accuracy: float`, `peak_ram_gb: float`, `wall_time_sec: float`, `loss_log_path: str` |
| **AggregatedMetrics** | Consolidated statistics for a condition. | `condition: str`, `mean_accuracy: float`, `std_accuracy: float`, `power_estimate: float`, `equivalence_result: enum[equivalent,inconclusive,not_equivalent]`, `t_test_result: enum[significant,non‑significant,inconclusive]` |

## File Layout
- `data/raw/` – Original GSM8K parquet files (unchanged).  
- `data/processed/` –  
  - `parameter_deltas/` (per‑layer `.npz`)  
  - `svd_results/` (per‑layer `.npz`)  
  - `subspace_masks/` (`mask_{seed}.json`)  
  - `random_masks/` (`randmask_{seed}.json`)  
- `results/` –  
  - `run_logs/` (`run_{run_id}.jsonl`)  
  - `loss_logs/` (`loss_{run_id}.jsonl`)  
  - `state.yaml` (single source of truth).  

## Validation & Independence Guarantees
- **Mask‑derivation split**: The Δθ used for SVD are computed on a **held‑out validation split** of GSM8K that is disjoint from the training split used for OPD/SFT and from the held‑out generalization subset used for final evaluation. This ensures the subspace mask is independent of the evaluation data, addressing potential data‑leakage concerns.
- **Seed separation**: Mask derivation uses several dedicated seeds distinct from the evaluation seeds (FR‑020).  

## Schema Overview
Two JSON‑Schema contracts are provided (see `contracts/`):
1. `experiment.schema.yaml` – validates the overall `state.yaml` top‑level structure.  
2. `experiment_results.schema.yaml` – validates each `ExperimentRun` entry.

Both schemas enforce:
- Presence of required fields.  
- Correct data types (e.g., `accuracy` ∈ [0,1]).  
- Numeric ranges for RAM (`<=7`) and wall‑time (`<=21600`).  

All downstream scripts read only from these validated structures.

---


