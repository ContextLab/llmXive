---
action_items:
- id: 82338545dd1e
  severity: science
  text: "Table 1 claims ResearchStudio-Reel beats author ground-truth on aesthetics\
    \ (3.52 vs 2.94) with no reported variance or seed count. A single run per paper\
    \ cannot distinguish a real effect from seed noise or VLM idiosyncrasy. Report\
    \ results across 3-5 seeds with mean \xB1 SD or bootstrap CIs to confirm stability.\
    \ (science)"
- id: 749bb764d237
  severity: science
  text: Section 5.1 attributes the ~0.76 aesthetic gain to the 'measured-fill loop'
    by comparing single-shot vs. pipeline. However, the pipeline also uses multi-turn
    tool use while the baseline is static. This confounds the loop with the agent
    harness. Add a control with tool use but no iterative loop to isolate the loop's
    specific contribution. (science)
- id: febb108c34b2
  severity: science
  text: The claim of 'surpassing authors' relies solely on VLM judges, which may bias
    towards the system's consistent layout over human bespoke designs. Include a small
    human evaluation (n=20-30) blind to source to verify VLM scores correlate with
    expert human preference before claiming superiority. (science)
artifact_hash: 3fa75923fecff6d59faa810352ca7bfd8c82759dca2686ca78438d4eab3732e9
artifact_path: projects/PROJ-1005-researchstudio-reel-automate-the-last-mi/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-08T04:18:14.812220Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling system for automating research dissemination, but the central quantitative claims regarding performance superiority over human authors and baselines rest on experimental designs that lack necessary controls for variance and confounding factors.

First, the headline result in Table 1—that ResearchStudio-Reel exceeds author ground-truth posters on aesthetics (3.52 vs 2.94) and wins 84-93% of papers—is derived from a single run per paper evaluated by two VLM judges. The paper reports no standard deviation, confidence intervals, or seed variation for the generation process. In generative AI tasks, performance can fluctuate significantly based on random seeds, especially when using iterative loops. A 0.58 point margin on a 5-point scale with n=100 is plausible but not definitive without variance estimates. The reader cannot distinguish a robust effect from a lucky seed or a specific alignment between the VLM judges' preferences and the system's output style. Reporting results across multiple seeds (e.g., 3-5) with mean ± SD is essential to establish the stability of this gain.

Second, the ablation study in Section 5.1 attempts to isolate the contribution of the "skill machinery" (the measured-fill loop) by comparing a single-shot prompt against the full pipeline. However, the comparison is confounded: the single-shot baseline uses a fixed, static prompt (Appendix C), while the pipeline employs a multi-turn agent with tool use (e.g., reading the DOM, executing code). The observed gain (~0.76 points) could be driven by the agent's ability to use tools and iterate, rather than the specific "measured-fill" logic itself. To rigorously attribute the gain to the loop, the authors should control for the agent harness, perhaps by comparing a single-shot agent with tool access but no iterative fill loop, or by running the loop with a simpler agent.

Finally, the claim of surpassing human authors relies entirely on VLM judges. While the paper notes that VLMs are used to avoid human bias, VLMs themselves have known biases towards certain visual styles (e.g., clean layouts, specific color palettes) that may not align with human expert preferences for scientific posters. The "author ground-truth" posters are often bespoke and may contain idiosyncratic design choices that VLMs penalize. Without a human evaluation study (even a small one) to validate that the VLM scores correlate with human expert judgment, the claim of "surpassing" human authors remains an artifact of the evaluation metric rather than a proven improvement in quality.
