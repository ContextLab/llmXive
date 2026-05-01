---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Performance of Different Data Structures in Implementing Bloom Filters

**Field**: computer science

## Research question

How do underlying data structures (native arrays, dynamic vectors, and specialized bitsets) affect the memory overhead and operation latency of Bloom filters across varying dataset sizes?

## Motivation

Bloom filters are critical for memory-constrained applications like networking and databases, yet implementation choices often lack empirical comparison. This project addresses the gap in understanding the practical trade-offs between standard library containers and optimized bitset implementations.

## Related work

- [Network Applications of Bloom Filters: A Survey (2004)](https://doi.org/10.1080/15427951.2004.10129096) — Provides the foundational theoretical bounds and application contexts for Bloom filters in network systems.

## Expected results

Specialized bitsets will demonstrate lower memory usage compared to dynamic vectors, while native arrays will offer consistent latency for fixed-size sets. Statistical analysis will confirm significant performance differences (p < 0.05) between implementations at scale.

## Methodology sketch

- Download public datasets: Google 10000 English words (https://raw.githubusercontent.com/first20hours/google-10000-english/master/20k.txt) and a subset of the Enron Email Corpus (https://www.cs.cmu.edu/~enron/).
- Implement three Bloom filter variants in Python/C++: native `array`, `std::vector`/`ArrayList`, and `std::bitset`/`bitarray`.
- Configure false positive rates (1%, 5%, 10%) to ensure fair comparison across memory constraints.
- Run insertion benchmarks for set sizes ranging from 10,000 to 1,000,000 elements to fit within 7GB RAM limits.
- Measure wall-clock time for 10,000 membership queries per set size using `time` module or `perf` counters.
- Record peak memory usage via `memory_profiler` or OS-level tools during execution.
- Repeat each experiment 5 times to account for system noise and ensure reproducibility on GHA runners.
- Apply Kruskal-Wallis H-test to determine if performance differences between data structures are statistically significant.
- Visualize results using Matplotlib to generate memory vs. size and latency vs. size plots.
- Document all dependencies and script configurations in `requirements.txt` for GHA environment setup.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None detected.
- Verdict: NOT a duplicate
