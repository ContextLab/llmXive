# Architecture Overview

## Design Principles
1. **CPU-First**: All algorithms must be tractable on CPU within 7GB RAM.
2. **Data Hygiene**: All external data is checksummed and validated (Constitution Principle III).
3. **Modularity**: Each user story is independently testable and deployable.
4. **Fail Loudly**: Resource limits and data validity checks raise errors immediately.

## Component Diagram

```
+----------------+ +------------------+ +-------------------+
| Data Loader | ----> | Pre-Clustering | ----> | Active Ranker |
| (BEIR + Synth) | | (MinHash-LSH) | | (Pairwise) |
+----------------+ +------------------+ +-------------------+
 | | |
 v v v
+----------------+ +------------------+ +-------------------+
| Redundancy | | Filtered | | NDCG / |
| Metrics | | Candidates | | Efficiency Stats |
+----------------+ +------------------+ +-------------------+
```

## Data Flow
1. **Ingestion**: BEIR datasets downloaded and optionally augmented with synthetic redundancy.
2. **Clustering**: MinHash-LSH groups near-duplicates; representatives selected.
3. **Ranking**: Active ranker processes filtered candidates.
4. **Evaluation**: NDCG@10 and wasted call ratios calculated and statistically validated.

## Configuration
- `code/config.py`: Centralized configuration for runtime limits, dataset paths, and hyperparameters.
- `state/projects/`: Persistent state for artifact hashes and experiment metadata.

## Error Handling
- **Resource Watchdog**: Terminates execution if limits exceeded.
- **Data Validation**: Raises errors if checksums mismatch or datasets missing.
- **Statistical Checks**: Fails if significance criteria (p < 0.05) not met.
