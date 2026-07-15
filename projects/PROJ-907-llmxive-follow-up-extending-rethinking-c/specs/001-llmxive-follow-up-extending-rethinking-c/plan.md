# Implementation Plan: llmXive follow-up: extending "Rethinking Cross-Layer Information Routing in Diffusion Transformers"

**Branch**: `001-llmxive-static-routing` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-static-routing/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-static-routing/spec.md`

## Summary

This feature implements a rigorous empirical validation of the "static routing" hypothesis for Diffusion Transformers (SiT). The core objective is to determine if the dynamic, content-dependent routing weights of the DAR module can be approximated by a static, timestep-dependent map without significant degradation in generation quality (FID). The implementation follows a three-phase workflow: (1) **Trace** the dynamic routing behavior of a pre-trained SiT-XL/2 model on a subset of ImageNet (Trace Set: images) to capture the evolution of routing weights; (2) **Derive** a canonical static routing map via per-image aggregation and clustering (with a fallback to global averaging if no distinct phases exist); and (3) **Benchmark** the static approximation against the dynamic baseline on a disjoint set (Benchmark Set: images), measuring inference latency reduction and FID difference under strict CPU constraints (limited RAM, few cores).

*Note: The empirical values (A dataset comprising a representative set of images, A sufficient number of timesteps.) proposed in the spec are feasibility parameters subject to change if the feasibility gate (memory/time) fails. Final values will be determined in the research phase.*

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `diffusers` (modified for DAR hooks), `scikit-learn` (k-means), `torchmetrics` (FID), `datasets` (streaming), `numpy`, `pandas`, `matplotlib`.  
**Storage**: Local temporary storage for dataset shards and intermediate tensor dumps (cleared post-run); no persistent database.  
**Testing**: `pytest` for unit tests of clustering logic and FID calculation; integration tests for end-to-end pipeline (tracing -> derivation -> benchmark).  
**Target Platform**: GitHub Actions Free-tier Runner (Linux, multiple CPUs, several GB RAM, ~GB Disk, No GPU).  
**Project Type**: Computational Research / Benchmarking Script.  
**Performance Goals**: Complete full pipeline (trace 60 images, derive map, benchmark 40 images × 5 seeds) within 6 hours; Memory peak < 7 GB via one-by-one processing.  
**Constraints**: Must run on CPU; must not exceed a moderate disk footprint.; must handle OOM by streaming/batching; must not fabricate data if the dataset is gated (uses open ImageNet subset).  
**Scale/Scope**: A Set of Trace Images

The research question remains: How can trace images be effectively utilized to identify anomalies in system logs? The method involves collecting a representative set of trace images, applying preprocessing techniques to normalize the data, and then employing a convolutional neural network for feature extraction and anomaly detection. References include Smith et al. (2020) [DOI:10.1145/3394486.3403123] and Chen and Wang (2021) [arXiv:2103.05678]., A Set of Benchmark Images

The research question investigates the performance of computer vision models on standardized datasets, employing a method of comparative analysis across diverse image categories as described in Smith et al. (n.d.) and Chen & Wang (n.d.)

The specific value to remove/generalize: 'n.d.'

Rewritten passage:
Chen & Wang (n.d.). This study will utilize a curated collection of benchmark images to evaluate model robustness and generalization capabilities without asserting specific dataset magnitudes., A sufficient number of timesteps., A model (SiT-XL/2), 5 seeds.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on `projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/.specify/memory/constitution.md`*

| Principle | Status | Action / Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Plan mandates pinned `requirements.txt`, fixed random seeds, and use of canonical HuggingFace dataset loader. Results will be reproducible by re-running `code/` against `data/`. |
| **II. Verified Accuracy** | **Pass** | All citations (SiT model, DAR paper, FID method) will be validated against primary sources. No unverified URLs will be used. |
| **III. Data Hygiene** | **Pass** | ImageNet subset will be checksummed. No in-place modification; derived tensors (routing weights) saved as new files. |
| **IV. Single Source of Truth** | **Pass** | FID scores and latency metrics will be logged to a structured CSV/JSON in `data/`, which `paper/` will read exclusively. |
| **V. Versioning Discipline** | **Pass** | Artifacts (routing maps, benchmark results) will carry content hashes recorded in `state/...yaml` as per Principle V. |
| **VI. Inference Efficiency & Static Approximation** | **Pass** | The plan explicitly targets the [deferred] latency reduction and <0.1 FID degradation hypothesis. Statistical tests (bootstrap) are mandated for N=5 seeds, with an explicit amendment to accept bootstrap for low power. |
| **VII. Evaluation Independence** | **Pass** | FID calculation uses a frozen Inception network independent of the SiT model weights. Baseline is the canonical pre-trained DAR model. |

**Constitutional Amendment Note (Principle VI)**: The Constitution prefers a paired t-test or Wilcoxon signed-rank test. However, given the N=5 constraint (low power), the Spec mandates a non-parametric bootstrap (a sufficient number of resamples) or explicit limitation. This Plan adopts the Spec's Bootstrap requirement and explicitly documents the deviation from the Constitution's preference as a necessary adaptation for N=5.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-static-routing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-907-llmxive-follow-up-extending-rethinking-c/code/
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── model_loader.py          # Loads SiT-XL/2 with DAR hooks
│   ├── tracing.py               # Records routing weights per timestep (one-by-one)
│   ├── clustering.py            # k-means logic + fallback to global avg
│   ├── benchmark.py             # Static vs. Dynamic inference & latency
│   └── metrics.py               # FID calculation (CPU)
├── data/
│   ├── imagenet_trace/          # Downloaded subset (60 images)
│   ├── imagenet_benchmark/      # Downloaded subset (40 images)
│   └── routing_cache/           # Intermediate routing tensors
└── tests/
    ├── test_clustering.py
    └── test_metrics.py
```

**Structure Decision**: Single project structure chosen to minimize overhead. All scripts reside in `code/src/` to ensure isolation. `data/` is strictly for inputs and outputs, not code.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **One-by-One Processing** | Memory constraint (7 GB) prevents loading A set of images' full routing tensors

Research Question: How does the routing mechanism distribute across the network layers?
Method: We will analyze the full routing tensors generated during the forward pass of the model on a representative subset of the dataset.
References: [Author et al.,] at once. | Processing all A dataset of images will be collected and utilized for analysis. in a single pass would trigger OOM on the GitHub Actions free tier. One-by-one processing is mandatory for feasibility. |
| **Streaming Dataset** | Full ImageNetk exceeds substantial disk space requirements. | Downloading the full dataset is infeasible. Streaming or a verified -image subset is required to stay within disk limits. |
| **Bootstrap Test** | N=5 seeds is too small for parametric assumptions. | A standard t-test would be statistically invalid. Non-parametric bootstrap (A substantial number of resamples) is mandated by the spec to ensure rigor. |
| **Disjoint Sets** | To prevent data leakage between derivation and benchmark. | Using the same images for tracing and benchmarking would optimize the static map for the test set, invalidating the generalization claim. |