---
action_items:
- id: 382589224c9c
  severity: science
  text: The manuscript cites specific quantitative performance metrics (e.g., '98%+
    precision' for QualityFlow, '16.9% bronze' for AIDE, '41 of 58' compounds for
    A-Lab) without providing the underlying sample sizes, confidence intervals, or
    statistical significance tests. For a survey paper, these claims require explicit
    citation to the primary source's statistical analysis or a summary of the experimental
    design (N, controls) to verify robustness.
- id: acdb73859ac7
  severity: science
  text: Several claims regarding 'state-of-the-art' performance or 'best accuracy'
    (e.g., failure attribution accuracy of 14-53%) lack a clear definition of the
    evaluation protocol or the specific benchmark versions used. Without specifying
    the test sets and baseline comparisons, these ranges are difficult to interpret
    as robust scientific evidence rather than anecdotal observations.
- id: 6f0ca90c8237
  severity: science
  text: The paper discusses 'simulated execution' achieving high precision but does
    not quantify the divergence between simulated and real-world execution in terms
    of error rates or specific failure modes. A brief quantitative comparison or a
    citation to a study that explicitly measures this gap is needed to support the
    claim that simulation is a sufficient proxy for verification.
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:40:48.389319Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript "Code as Agent Harness" presents a comprehensive taxonomy of code-centric agentic systems. From a scientific evidence perspective, the primary concern is the reliance on point estimates and qualitative assertions without sufficient statistical grounding or experimental context.

While the paper synthesizes a vast amount of literature, it frequently cites specific performance metrics (e.g., "98%+ precision" for QualityFlow in Section 4.2, "16.9% bronze medal rate" for AIDE in Section 5.1, "41 of 58" compounds synthesized by A-Lab in Section 5.1) without detailing the sample sizes (N), the specific benchmark versions, or the statistical significance of these results. In a survey context, this is acceptable only if the cited numbers are directly linked to the primary source's rigorous statistical analysis. However, the text often presents these figures as definitive facts without clarifying the experimental conditions (e.g., number of runs, variance, or control baselines). For instance, the claim that "best step-level attribution accuracies" range from 14–53% (Section 5.1) lacks a clear definition of the evaluation protocol or the specific datasets used, making it difficult to assess the robustness of this range against potential selection bias or p-hacking in the cited works.

Furthermore, the paper makes strong claims about the efficacy of "simulated execution" (Section 4.2) and "imagined execution" achieving high precision, but does not provide quantitative evidence of the divergence between these simulations and real-world execution. Without a comparative analysis of failure modes or error rates between simulated and actual environments, the claim that simulation is a sufficient proxy for verification remains an unverified hypothesis rather than a supported conclusion. The discussion on "oracle adequacy" (Section 6.1) correctly identifies this as a bottleneck, yet the paper itself relies on the very metrics it critiques without providing the necessary statistical context to validate them.

To strengthen the scientific evidence, the authors should:
1. Explicitly cite the sample sizes and experimental designs (e.g., number of tasks, runs, or agents) for every quantitative claim.
2. Clarify the statistical significance or confidence intervals for performance metrics where available in the primary sources.
3. Provide a brief summary of the evaluation protocols for the benchmarks mentioned to ensure reproducibility and context.
4. Include a quantitative comparison or a specific citation regarding the gap between simulated and real-world execution to support claims about simulation fidelity.

The paper is otherwise well-structured, but the lack of statistical rigor in presenting evidence undermines the reliability of its central claims regarding system performance and efficacy.
