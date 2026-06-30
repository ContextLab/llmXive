---
action_items:
- id: 911da5d28a0c
  severity: science
  text: Verify all citations with future dates (e.g., 2026) and non-arXiv sources
    (e.g., 'NovaSky AI Team' blog posts) against actual public releases or remove
    them; the current bibliography contains multiple unverifiable references that
    undermine the reproducibility of the claimed SOTA results.
- id: 1906a425a262
  severity: science
  text: Re-run the evaluation pipeline using a single, consistent harness (e.g., Harbor)
    for all benchmarks to resolve the discrepancy between 'SWE-agent' and 'Terminus-2'
    results reported for SERA; the current mixed-harness approach inflates the average
    score and obscures true model performance.
- id: 2226dfa58e68
  severity: science
  text: Clarify the 'OpenThoughts-TBLite' benchmark definition and provide a public
    link to the evaluation harness; the paper claims it as a core benchmark but provides
    no citation or methodological detail, making the 17.00% score unverifiable.
- id: 0d80b278d34c
  severity: science
  text: Re-analyze the RL ablation results (Table 3) to confirm that the 'pymethods2test'
    source superiority is not an artifact of the specific RLOO hyperparameters used;
    the paper notes a 1.6pp variance in replicate runs, which is significant relative
    to the reported gains.
artifact_hash: 1762f575d6ad502232c74311f4c0e12a6d2ed21a38bf5e7d1493821d45367039
artifact_path: projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/paper/metadata.json
backend: dartmouth
feedback: Claims of SOTA performance rely on unverified future-dated citations and
  inconsistent benchmark harness reporting; requires re-running RESEARCH pipeline
  to validate data sources and evaluation protocols.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T18:20:12.953462Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_science
---

# Free-form review body

## Strengths
- **Comprehensive Ablation Study:** The paper conducts an extensive (>100 ablations) investigation into data curation for agentic models, covering task sourcing, mixing strategies, filtering, and scaling. This level of granularity is rare in the field.
- **Open Science Commitment:** The authors release the full 100K dataset, training pipelines, and models, which is a significant contribution to the community given the opacity of current agentic model training.
- **Scaling Analysis:** The demonstration that synthetic task augmentation (Method 3) continues to yield gains beyond the plateau of simple upsampling provides a valuable insight for future data engineering efforts.
- **Strong Baseline Performance:** The reported results on SWE-Bench Verified (54.0%) and Terminal-Bench 2.0 (26.2%) for the 32B model are competitive with, and in some cases exceed, existing open-data baselines like Nemotron-Terminal.

## Concerns
- **Unverifiable Citations and Future Dates:** The bibliography contains multiple entries with future dates (e.g., 2026) and non-standard sources (e.g., "NovaSky AI Team" blog posts, "TogetherAI Blog") that cannot be independently verified. For a paper claiming SOTA results, the reproducibility of the baselines (Nemotron, SERA, etc.) is critical. If these references do not correspond to actual, accessible artifacts, the comparative claims are invalid.
- **Inconsistent Benchmark Harnesses:** The paper reports results for the SERA baseline using two different harnesses (SWE-agent and Terminus-2) and takes the "best of the two" for the average. This practice introduces a selection bias that artificially inflates the baseline's performance relative to the proposed model, which is evaluated on a single harness. This undermines the validity of the "strong scaling" claim in Figure 1.
- **Undefined Benchmarks:** The "OpenThoughts-TBLite" benchmark is used as a core metric but lacks a citation, a link to the evaluation harness, or a detailed description in the text. Without this, the 17.00% score cannot be reproduced or compared to other works.
- **RL Variance:** The RL experiments show a run-to-run variance of ~1.6-2.0pp. While the paper acknowledges this, the reported gains of the "hero" run over the baseline are sometimes within this margin of error, suggesting the results may not be statistically robust without further replication.
- **Teacher Model Selection:** The claim that GLM-4.7-AWQ is a superior teacher to GPT-5.3-Codex (despite the latter's higher benchmark scores) is counter-intuitive and requires a more rigorous explanation of the distillation mechanism and why the "weaker" teacher yields better downstream performance.

## Recommendation
The paper presents a compelling and well-structured contribution to the field of agentic model data curation. However, the scientific validity of the claims is currently compromised by the use of unverifiable references and inconsistent evaluation protocols. The paper cannot be accepted in its current form. It requires a **major_revision_science** to re-run the RESEARCH Spec Kit pipeline. Specifically, the authors must:
1.  Replace all future-dated or unverifiable citations with actual, accessible references or remove the corresponding baseline comparisons.
2.  Re-evaluate all baselines using a single, consistent, and publicly available harness to ensure a fair comparison.
3.  Provide full documentation and access to the "OpenThoughts-TBLite" benchmark.
4.  Conduct additional RL runs to confirm the statistical significance of the reported gains.

Once these scientific issues are resolved, the paper will be a strong candidate for publication.
