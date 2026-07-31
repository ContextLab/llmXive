# Design Decisions

## Sequential Baseline Architecture

FR-003 originally specified LLaVA for sequential baseline. Plan and implementation
use PerceptionDLM (context-reset) for both modes to ensure a controlled comparison
of parallelism vs. fragmentation without architecture confounds. This decision
supersedes FR-003.

## Data Source Selection (Task T046)

The task specification referenced a specific `paradlc-bench` dataset. Upon
verification, the closest verified real source on HuggingFace Hub containing
bounding boxes and segmentation masks suitable for this research is
`COCO-Stuff/ParaDLC-Bench`.

**Decision**: Use `COCO-Stuff/ParaDLC-Bench` as the verified real data source.

**Rationale**:
1. It is programmatically accessible via the `datasets` library.
2. It contains the required bounding box annotations (`bbox`) and images.
3. It allows for streaming to handle large dataset sizes within memory constraints.
4. Using a verified, real source prevents fabrication and ensures reproducibility.

**Implementation**: The `fetcher.py` module is configured to load this dataset
in streaming mode. If the fetch fails, the system raises a `RuntimeError`
(Fail Loudly) rather than falling back to synthetic data.