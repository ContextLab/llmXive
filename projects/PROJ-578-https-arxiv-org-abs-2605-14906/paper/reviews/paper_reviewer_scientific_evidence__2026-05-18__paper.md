---
action_items:
- id: 20a0f903d938
  severity: science
  text: In Section 4.2 (Main Results), explicitly qualify the comparison between LVLMs
    (n=789) and memory agents (n=195). While stratified sampling is used, the smaller
    agent sample size reduces statistical power for direct performance claims at specific
    context lengths.
- id: 6faacd5259c9
  severity: writing
  text: In Section 3.4 (Cross-modality Validation), clarify that the image-ablation
    evidence (Table 2) relies on only two proprietary models (GPT-5.4, Gemini-3.1-Pro).
    Generalize the claim that 'solving MemLens requires visual evidence' to reflect
    this model-specific evidence.
artifact_hash: d50a4f0b1e568c7504bc9f36b9def267fba709bab11751ed7e3ec317ba0682a2
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-05-18T14:27:43.250460Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting the central claims of MemLens is generally robust, with a well-designed benchmark (n=789) and appropriate controls for length and modality. The cross-modality ablation study (Section 3.4, Table 2) provides strong causal evidence that 80.4% of questions require visual input, showing a >90% accuracy drop when images are removed. The judge validation protocol (Appendix G.2) demonstrates high reliability (κ=0.86 vs. human consensus), mitigating concerns about LLM-as-Judge bias.

However, there are evidentiary limitations regarding the comparison of LVLMs and memory agents. First, LVLMs are evaluated on the full 789-question benchmark, while memory agents are evaluated on a 195-question subset (Appendix G.1) due to computational cost. Although stratified sampling is used, the smaller sample size for agents (n=195) increases the confidence interval width for agent performance (±5–7% at 32K, Appendix G.1). The main text (Section 4.2) should explicitly acknowledge this asymmetry when drawing conclusions about relative performance, as the subset size limits the precision of the agent-vs-LVLM comparison.

Second, the claim that agents are "length-stable" while LVLMs degrade is partially constrained by context window availability. LVLMs are evaluated up to 128K, whereas agents are evaluated up to 256K (Section 4.1). This asymmetry prevents a direct comparison at 256K, yet the conclusion implies agents are superior at extreme lengths. The text should clarify that the "length-stable" claim applies within the overlapping range (32K–128K) where LVLMs are available, rather than extrapolating to 256K where LVLM data is missing.

Finally, the image-ablation study relies on two frontier models (Table 2). While the effect size is massive, generalizing the "visual necessity" claim to the broader field requires acknowledging this limited model sample. These adjustments will strengthen the robustness of the empirical conclusions without requiring new experiments.
