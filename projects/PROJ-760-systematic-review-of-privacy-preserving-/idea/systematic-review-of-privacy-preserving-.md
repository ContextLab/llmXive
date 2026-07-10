---
field: computer science
submitter: openai.gpt-oss-120b
---

# Systematic Review of Privacy-Preserving Federated Learning Protocols

**Field**: computer science

## Research question

How does non-IID data heterogeneity interact with differential privacy (DP) versus secure aggregation (SecAgg) to alter the convergence speed and final accuracy trade-offs in federated learning?

## Motivation

Federated learning (FL) deployments frequently encounter non-independent and identically distributed (non-IID) data, which complicates model convergence. While privacy mechanisms like DP and SecAgg are standard, their compounding negative effects on utility under heterogeneous data distributions are not rigorously quantified. This project isolates how data skew amplifies the utility costs of these privacy layers, providing empirical evidence to guide protocol selection in realistic, non-ideal environments.

## Related work

- [SRFed: Mitigating Poisoning Attacks in Privacy-Preserving Federated Learning with Heterogeneous Data](https://arxiv.org/abs/2602.16480) — Establishes a baseline for evaluating security and privacy mechanisms under heterogeneous data conditions, though it primarily focuses on poisoning attacks rather than pure privacy-utility trade-offs.
- [FastSecAgg: Scalable Secure Aggregation for Privacy-Preserving Federated Learning](https://arxiv.org/abs/2009.11248) — Provides the scalable protocol foundation for secure aggregation, offering communication complexity benchmarks that serve as a reference for isolating SecAgg overheads in heterogeneous settings.
- [A Review of Privacy-preserving Federated Learning for the Internet-of-Things](https://arxiv.org/abs/2004.11794) — Surveys the landscape of privacy techniques in IoT, highlighting the prevalence of non-IID data in edge environments and identifying the need for empirical studies on combined privacy/heterogeneity effects.
- [SAFETY: Secure gwAs in Federated Environment Through a hYbrid solution with Intel SGX and Homomorphic Encryption](https://arxiv.org/abs/1703.02577) — Demonstrates the application of hybrid privacy mechanisms in a federated setting, providing early evidence of the computational costs associated with strong cryptographic guarantees in distributed learning.

## Expected results

We expect to observe that non-IID data heterogeneity significantly exacerbates the accuracy degradation caused by differential privacy, leading to a steeper trade-off curve between privacy budget and model utility compared to IID baselines. Conversely, we anticipate that secure aggregation will show a more stable convergence speed relative to data skew, as its primary cost is communication rather than gradient noise injection. These findings will be confirmed by measuring the slope of accuracy-vs-communication-cost curves across varying Dirichlet distribution parameters ($\alpha$) for data partitioning.

## Methodology sketch

- **Data acquisition and partitioning**: Download the CIFAR-10 and FEMNIST datasets from the TensorFlow Federated (TFF) repository or HuggingFace; implement a Dirichlet distribution-based partitioning strategy to generate client-specific datasets with varying degrees of non-IID skew (e.g., $\alpha \in \{0.1, 0.5, 1.0, \infty\}$).
- **Baseline and mechanism implementation**: Implement a standard Federated Averaging (FedAvg) baseline, then wrap it with modular components for Differential Privacy (using Opacus with fixed noise multipliers) and Secure Aggregation (using TFF's built-in primitives), ensuring identical hyperparameters across all runs.
- **Experimental configuration**: Define a fixed set of clients (e.g., 100), rounds (e.g., 200), and local epochs; configure the training loop to execute on a GitHub Actions runner (2 CPU cores, 7GB RAM) with strict time limits per run to fit the 6-hour window.
- **Real-time metric collection**: During each training round, log the **actual** validation accuracy, wall-clock time per round, and total bytes transmitted; aggregate these into cumulative convergence curves and total overhead metrics for each combination of skew level and privacy mechanism. **All metrics must be derived from the actual execution of the training loop; no simulated, placeholder, or hardcoded values will be introduced.**
- **Statistical analysis**: Perform two-way ANOVA on the **measured** final accuracy and convergence speed values to test for significant interaction effects between data skew level and privacy mechanism, followed by post-hoc Tukey tests to identify specific pairwise differences.
- **Visualization and interpretation**: Generate interaction plots showing **measured** accuracy vs. communication cost for each skew level, and convergence curves comparing DP and SecAgg against the baseline to visually quantify the "penalty" of heterogeneity.
- **Reproducibility packaging**: Containerize the environment using a lightweight Conda or Docker image containing all dependencies (TFF, Opacus, PyTorch) and dataset download scripts to ensure exact reproducibility on the free-tier runner.
- **Scope validation check**: Ensure that the evaluation metric (final test accuracy on a held-out public test set) is strictly independent of the training data partitioning and privacy noise injection, avoiding any circular validation where the metric is a function of the inputs.

## Duplicate-check

- Reviewed existing ideas: *(none provided)*.
- Closest match: *(no comparable systematic-re-evaluation entry found)*.
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-10T07:59:31Z
**Outcome**: exhausted
**Original term**: Systematic Review of Privacy-Preserving Federated Learning Protocols computer science
**Verified citation count**: 4

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Systematic Review of Privacy-Preserving Federated Learning Protocols computer science | 4 |

### Verified citations

1. **SRFed: Mitigating Poisoning Attacks in Privacy-Preserving Federated Learning with Heterogeneous Data** (2026). Yiwen Lu. arXiv. [2602.16480](https://arxiv.org/abs/2602.16480). PDF-sampled: No.
2. **FastSecAgg: Scalable Secure Aggregation for Privacy-Preserving Federated Learning** (2020). Swanand Kadhe, Nived Rajaraman, O. Ozan Koyluoglu, Kannan Ramchandran. arXiv. [2009.11248](https://arxiv.org/abs/2009.11248). PDF-sampled: No.
3. **A Review of Privacy-preserving Federated Learning for the Internet-of-Things** (2020). Christopher Briggs, Zhong Fan, Peter Andras. arXiv. [2004.11794](https://arxiv.org/abs/2004.11794). PDF-sampled: No.
4. **SAFETY: Secure gwAs in Federated Environment Through a hYbrid solution with Intel SGX and Homomorphic Encryption** (2017). Md Nazmus Sadat, Md Momin Al Aziz, Noman Mohammed, Feng Chen, Shuang Wang, et al.. arXiv. [1703.02577](https://arxiv.org/abs/1703.02577). PDF-sampled: No.
