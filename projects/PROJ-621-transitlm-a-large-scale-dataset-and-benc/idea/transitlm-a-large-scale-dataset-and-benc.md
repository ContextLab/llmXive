---
field: linguistics
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/224
paper_authors:
  - Hanyu Guo
  - Jiedong Yang
  - Chao Chen
  - Longfei Xu
  - Kaikui Liu
  - Xiangxiang Chu
---

# TransitLM: A Large-Scale Dataset and Benchmark for Map-Free Transit Route Generation

**Field**: Computational Linguistics / Urban Computing

## Research question

Can large language models, trained exclusively on textual transit logs and station metadata without explicit geographic coordinates or map topology, learn to generate valid public transit routes that satisfy real-world connectivity constraints?

## Motivation

Current transit routing systems rely heavily on explicit graph databases and geographic information systems (GIS), creating a barrier for rapid deployment in data-scarce regions. This research addresses the gap in understanding whether the implicit spatial and topological knowledge required for route planning can be acquired purely through the statistical patterns of natural language descriptions and station sequences, potentially enabling "map-free" AI agents for urban mobility.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv for terms including "map-free route generation," "LLM transit planning," "large language models public transport routing," and "implicit spatial grounding in transportation." The search aimed to identify prior work attempting to solve transit connectivity problems using purely linguistic or sequence-based models without external map lookups.

### What is known

- [A Unified Approach to Evaluation and Routing in Public Transport Systems](https://arxiv.org/abs/2207.09969) — This work establishes that evaluating public transport service quality and understanding passenger route choice are critical, but it relies on traditional graph-based evaluation metrics and explicit network data rather than generative language models.

### What is NOT known

No published work has rigorously benchmarked the ability of large language models to generate valid transit routes using *only* textual station names and sequence history, specifically isolating the model's ability to infer connectivity without access to a map graph or coordinate system during inference. Existing literature focuses on optimizing routes on known graphs or using LLMs as wrappers for existing routing APIs, not as end-to-end generators of topological knowledge from text.

### Why this gap matters

Filling this gap is crucial for developing robust, low-infrastructure navigation agents that can operate in cities with poor digital map coverage or for rapidly adapting to temporary network disruptions (e.g., strikes, construction) where the static map graph is outdated. If models can learn this implicitly, it could revolutionize how transit data is collected and utilized in developing regions.

### How this project addresses the gap

This project addresses the gap by constructing a massive, map-free dataset of transit logs and training/evaluating LLMs on the task of generating route sequences that match ground-truth connectivity, explicitly excluding geographic coordinates from the input to test for implicit spatial learning.

## Expected results

We expect to find that while general-purpose LLMs struggle with long-haul connectivity and hallucinate non-existent transfers, models fine-tuned on the proposed dataset will achieve a statistically significant improvement in route validity (measured by exact match against ground-truth paths). The level of evidence required is a benchmark showing that performance degrades only when the model is forced to rely on external map lookups, confirming the learning of internal topological representations.

## Methodology sketch

- **Data Acquisition**: Download the public "TransitLM" dataset (or a verified subset from the original submission if available via a persistent DOI like Zenodo; otherwise, construct a synthetic benchmark using OpenStreetMap GTFS feeds converted to text sequences) ensuring all GPS coordinates are stripped to enforce the "map-free" constraint.
- **Preprocessing**: Convert GTFS route and stop data into natural language sequences (e.g., "Take Line X from Station A to Station B") and generate negative samples (invalid transfers) for contrastive learning.
- **Model Selection**: Select open-source LLMs (e.g., Llama-3-8B, Qwen2.5-7B) available via HuggingFace that fit within 7GB RAM constraints (using quantization if necessary) to serve as the base models.
- **Training**: Perform Supervised Fine-Tuning (SFT) on the positive route sequences using a lightweight adapter (LoRA) to minimize memory usage, ensuring no geographic coordinates are included in the prompt context.
- **Evaluation**: Generate routes for a held-out set of origin-destination pairs and validate them against the ground-truth GTFS graph using a deterministic graph-traversal script (independent of the model) to compute "Route Exact Match" and "Connectivity Validity" scores.
- **Statistical Analysis**: Apply a paired t-test or Wilcoxon signed-rank test to compare the validity scores of the fine-tuned model against zero-shot general-purpose LLM baselines to determine statistical significance.

## Duplicate-check

- Reviewed existing ideas: (None found in the provided context).
- Closest match: None.
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-29T22:51:19Z
**Outcome**: exhausted
**Original term**: TransitLM: A Large-Scale Dataset and Benchmark for Map-Free Transit Route Generation linguistics
**Verified citation count**: 1

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | TransitLM: A Large-Scale Dataset and Benchmark for Map-Free Transit Route Generation linguistics | 0 |
| 1 | map-free public transport route planning | 2 |
| 2 | large-scale transit dataset for natural language processing | 4 |
| 3 | natural language to transit route generation | 0 |
| 4 | text-based public transportation navigation | 0 |
| 5 | LLM-based multimodal transport planning | 0 |
| 6 | spoken language transit itinerary generation | 0 |
| 7 | map-independent route recommendation systems | 0 |
| 8 | large language models for urban mobility | 0 |
| 9 | semantic parsing for public transit queries | 0 |
| 10 | conversational agents for transit routing | 0 |
| 11 | benchmark datasets for navigation instruction generation | 0 |
| 12 | text-to-route generation for buses and trains | 0 |
| 13 | natural language understanding in smart city transit | 0 |
| 14 | AI-driven public transport itinerary synthesis | 0 |
| 15 | zero-shot transit route generation from text | 0 |
| 16 | corpus linguistics for transportation instruction | 0 |
| 17 | generative AI for map-free navigation | 0 |
| 18 | dialogue systems for public transport guidance | 0 |
| 19 | syntactic analysis of transit directions | 0 |
| 20 | spatial reasoning in language models for transport | 0 |

### Verified citations

1. **A Unified Approach to Evaluation and Routing in Public Transport Systems** (2022). Rolf Nelson van Lieshout, Kevin Dalmeijer. arXiv. [2207.09969](https://arxiv.org/abs/2207.09969). PDF-sampled: No.
