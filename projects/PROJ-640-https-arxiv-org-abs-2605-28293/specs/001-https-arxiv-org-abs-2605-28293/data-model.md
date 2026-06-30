# Data Model: Reproduce & Validate ProRL

## 1. Input Data Schema

### Dataset: `Books` (Local Submodule)
The input data is expected to be in the format defined by the ProRL repository.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `inter` | `.inter` (CSV/TSV) | User-Item interaction sequences (UserID, ItemID, Timestamp). | Submodule `datasets/Books/inter` |
| `datamaps` | `.datamaps` (JSON/CSV) | Mappings for User/Item IDs to integer indices. | Submodule `datasets/Books/datamaps` |
| `sem_ids` | `.sem_ids` (NPY/PK) | Pre-computed semantic embeddings (e.g., `qwen3-embedding-8b-pca`). | Submodule `datasets/Books/sem_ids` |

**Validation Rules**:
- `inter` must contain at least 1000 interactions.
- `sem_ids` must exist; if missing, pipeline aborts (FR-006).
- If total file size > 6GB, a random sample of [deferred] of interactions is used.

## 2. Intermediate Data Structures

### Checkpoint (`.pth`)
Serialized PyTorch state dictionary.
- **Keys**: `model_state`, `optimizer_state`, `epoch`, `metrics`.
- **Constraint**: Must be loadable on CPU (`map_location='cpu'`).

### Metrics Log (`.json`)
Structured output of evaluation.
- **Fields**: `hit_rate@10`, `ndcg@10`, `epochs_completed`, `runtime_seconds`.

## 3. Output Schema

### Reproduction Report (`reproduction_report.md`)
A Markdown document containing:
- **Environment**: `CPU: 2 vCPU`, `RAM: 7GB`, `No GPU`.
- **Dataset**: `Books` (with sample size if applicable).
- **Results**: Final metrics.
- **Status**: `SUCCESS` or `FAILED` (with reason).
