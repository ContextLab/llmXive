---
artifact_hash: 056c0815626cf07a81083eaa18cf8e32049f9408da58499094fbb2c8371aebce
artifact_path: projects/PROJ-570-leveraging-verifier-based-reinforcement/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T15:05:40.519817Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses strictly on data quality, provenance, licensing, and reproducibility. While the paper provides detailed schema documentation for the reasoning traces and principles in Appendix A (Listing 1-3, lines 1300-1500), significant gaps exist regarding dataset licensing and external dependencies that threaten reproducibility.

First, the provenance of the custom training datasets is insufficiently documented. Section 3.1.1 (lines 430-500) describes curating 200K samples from a "public image-editing benchmark" but does not explicitly name the source dataset or provide a citation link. Similarly, Section 3.1.2 (lines 580-600) details 10,000 human-annotated preference pairs without stating the licensing terms under which these annotations are released. Without explicit licenses (e.g., CC-BY, MIT) or clear usage restrictions for the 2M quadruples and 10K pairs, downstream researchers cannot legally or ethically reuse this data, hindering community validation.

Second, the data generation pipeline relies heavily on external APIs that introduce link rot and availability risks. Section 3.1.1 (lines 440-460) states that the Seed-1.5-VL API is used to decompose instructions into principles and verify CoT trajectories. Since this API is a closed service, the exact data generation process cannot be reproduced if the API changes or becomes unavailable. The paper should either open-source the generated data directly or provide a script using open-source alternatives to ensure long-term stability.

Third, while evaluation benchmarks like GEdit-Bench-EN (Section 4.1, line 1020) and EditRewardBench are cited, the training data split is not clearly versioned. There is no mention of data versioning control (e.g., DVC, specific commit hashes) for the 200K SFT dataset. To meet data quality standards for large-scale model training, the authors must release the dataset with a clear license and version identifier, or explicitly state why these cannot be shared.

Recommendations:
1. Specify the exact source and license for the "public image-editing benchmark" used in Section 3.1.1.
2. Declare the license for the 10K human preference pairs in Section 3.1.2.
3. Mitigate API dependency risks by releasing the generated quadruple data or documenting an open-source alternative for principle decomposition.
4. Provide data versioning details to ensure exact reproducibility of the training set.
