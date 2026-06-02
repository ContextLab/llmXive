---
action_items:
- id: 61d8c436797a
  severity: science
  text: Add a table categorizing evidence sources (peer-reviewed, preprint, tech report,
    blog) to clarify reliability of performance claims.
- id: ae9fde6b0846
  severity: science
  text: Include explicit caveats on the reproducibility and verification of proprietary
    system evaluations (e.g., Claude Code, Codex).
- id: 4d8fe91e438f
  severity: science
  text: Expand discussion on benchmark metric comparability when aggregating results
    across SWE-bench, AgentBench, and proprietary evals.
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T05:27:52.368428Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

This survey presents a comprehensive taxonomy of code-centric agent harnesses, but the strength of its scientific evidence varies significantly across sections. While the theoretical framework is well-structured, several key performance claims rely on non-peer-reviewed sources without sufficient qualification. For example, in Section 5.1 (Emerging Fields), the claim that LingmaAgent resolves 16.9% of issues autonomously cites internal reports (`ma2025alibaba`, `li2026advances`) rather than independent benchmarks. Similarly, Section 5.1 relies heavily on industry blog posts and technical reports (e.g., OpenAI, Anthropic, Cursor) to establish state-of-the-art capabilities for proprietary systems like Codex and Claude Code. These sources lack the transparency and reproducibility required for rigorous scientific evidence.

The survey aggregates results from diverse benchmarks (SWE-bench, AgentBench, OSWorld) in Section 5, but does not adequately address the heterogeneity of evaluation metrics or task distributions. This aggregation risks conflating performance across non-comparable environments. The "Open Problems" section (Section 6) acknowledges oracle adequacy issues, which is positive, but should explicitly extend this critique to the reliability of cited industry reports. Additionally, the bibliography includes numerous 2026-dated entries (e.g., `openai2026codexmax`), which are likely pre-prints or unreleased systems; the survey should distinguish between validated results and projected capabilities.

To improve the scientific rigor, the authors should add a dedicated evidence quality assessment, distinguishing between peer-reviewed studies, pre-prints, and engineering reports. This will help readers assess the robustness of the claims regarding agent efficacy. Finally, the discussion on benchmark comparability should be expanded to clarify the limitations of cross-benchmark comparisons in the current landscape.
