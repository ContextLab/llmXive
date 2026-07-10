---
action_items:
- id: 69ad92023028
  severity: writing
  text: The paper presents a comprehensive benchmark, but the evidentiary strength
    of the comparative claims in the leaderboards is weakened by insufficient reporting
    of variance and experimental replication. First, the Simulation Leaderboard (Table
    1) presents aggregate success rates and scores as single point estimates (e.g.,
    8.80% for Hy-Embodied-0.5-VLA). While the text mentions evaluation over 3 seeds,
    the table does not report the standard deviation or confidence intervals for these
    means. In robo
artifact_hash: ea08a1f2032c23dcddfe48c893242879f7f30600dd1ba71197caa7f1b2ba7f13
artifact_path: projects/PROJ-1024-robodojo-a-unified-sim-and-real-benchmar/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-10T03:33:15.541416Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a comprehensive benchmark, but the evidentiary strength of the comparative claims in the leaderboards is weakened by insufficient reporting of variance and experimental replication.

First, the Simulation Leaderboard (Table 1) presents aggregate success rates and scores as single point estimates (e.g., 8.80% for Hy-Embodied-0.5-VLA). While the text mentions evaluation over 3 seeds, the table does not report the standard deviation or confidence intervals for these means. In robotics benchmarks, performance can vary significantly across seeds due to stochastic initialization and environment dynamics. The Appendix (Table 4) reveals high per-task variance (e.g., a 23.1% standard deviation in success rate for the 'store_in_safe' task for $\pi_{0.5}$). Without reporting this variance in the main leaderboard, it is impossible to determine if the observed differences between policies (e.g., 8.80% vs 8.04%) are statistically significant or merely within the noise of the evaluation process. The authors should report mean ± standard deviation for all leaderboard entries.

Second, the claim that "scene-level randomization causes broad performance collapse" (Finding 2, Section 5.1) relies on a comparison between "Standard" and "Random" settings. However, the experimental design appears to compare a single "Standard" run against a single "Random" run (or a small set) without explicitly controlling for the random seed used in the Standard condition. If the "Standard" set happened to be easier or the "Random" set harder due to a specific seed, the magnitude of the "collapse" could be exaggerated. To robustly support this claim, the authors should report performance across multiple seeds for both conditions or demonstrate that the drop is consistent regardless of the specific random seed used for the "Standard" baseline.

Third, the Real-World Benchmark results (Section 5.2) are based on a single seed per embodiment (Section 4.2). While real-world evaluation is expensive, relying on a single seed with only 10 trials per task makes the comparative ranking of policies highly susceptible to luck or specific initial conditions. The paper claims to reveal "execution instability," but the current design cannot distinguish between a policy that is generally unstable and one that simply encountered a rare failure mode in a single run. To support the comparative claims in the real-world leaderboard, the authors should ideally report results across at least 3 seeds, or at minimum, explicitly acknowledge that the rankings are preliminary and sensitive to the specific seed chosen.

These issues do not invalidate the benchmark itself, but they prevent the specific performance claims and rankings from being fully trusted as generalizable scientific evidence.
