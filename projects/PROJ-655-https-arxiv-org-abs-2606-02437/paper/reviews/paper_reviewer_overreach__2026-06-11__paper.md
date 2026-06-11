---
action_items:
- id: 13c8b1597522
  severity: writing
  text: Title claims Million Personal Models but only 10^6 addressable catalog is
    described, not actual deployment. Clarify this is a theoretical target, not demonstrated
    capability. (Abstract, Section 6.4)
- id: c2d597be958a
  severity: science
  text: Kimi K2 trillion-scale LoRA RL presented as proof of existence with limited
    empirical data. Add full experimental details or reframe as unverified claim.
    (Section 3.3)
- id: 6524e5fd1f16
  severity: science
  text: Collective intelligence from majority voting may be simple ensemble effect.
    Distinguish diversity-based gains from repetition baselines more rigorously. (Section
    6.3, Figure 26)
- id: 48a5c076bf25
  severity: science
  text: LoRA memory capacity law (10^-3 to 10^-2 tokens/param) is benchmark-specific.
    Add generalization caveats and real-world validation. (Section 6.2, Figure 20)
- id: fbf39fa6ac98
  severity: writing
  text: OLoRA-tail claims as RL-native initialization overreach - it is one method
    that works, not proven optimal. Temper language. (Section 4.2.2, Figure 14)
artifact_hash: 98f7fcdee505c1b0d734c7251a396631b218366acf62d66b7a26c51efa8d758b
artifact_path: projects/PROJ-655-https-arxiv-org-abs-2606-02437/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T21:55:32.954179Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper makes several claims that extend beyond what the presented evidence justifies:

**Title Overreach (Critical)**: "Towards Million Personal Models of Trillion Parameters" suggests demonstrated capability at these scales. The paper describes a 10^6-entry adapter catalog (Section 6.4, Table 14) but this is addressability, not simultaneous deployment. The conclusion must clarify this is a theoretical target, not achieved scale.

**Kimi K2 Claims (Science)**: The trillion-scale LoRA RL on 1T-parameter MoE is presented as empirical evidence (Section 3.3), but only high-level curves are shown with many experimental details omitted. This should be reframed as a case study or require full experimental transparency.

**Memory Capacity Law (Science)**: The claimed 10^-3 to 10^-2 tokens per trainable parameter capacity bound (Section 6.2, Figure 20) derives from DishNameBenchmark, a controlled synthetic task. The paper treats this as a general PEFT memory law without acknowledging benchmark-specific limitations or testing on real conversational memory scenarios.

**OLoRA-tail Characterization (Writing)**: Calling OLoRA-tail RL-native initialization overstates the evidence. The paper shows it works better than standard LoRA at rank-1, but does not prove it is uniquely suited to RL or superior to all alternatives. This language should be tempered.

**Collective Intelligence Claim (Science)**: The majority voting accuracy improvement from 0.3644 to 0.4867 at k=198 (Section 6.3, Figure 26) is presented as diversity-based collective intelligence. However, the collaboration curve is compared to repetition baselines, and the distinction between true diversity effects and simple ensemble averaging needs more rigorous statistical separation.

**Personal Model Persistence (Science)**: The core thesis that adapters store persistent adaptive state (Section 1, 6.1) lacks long-term validation. No experiments demonstrate adapters maintaining identity or behavioral consistency over extended interaction histories.

The paper would benefit from more conservative language distinguishing demonstrated results from theoretical targets, and from acknowledging where benchmark results may not generalize to production scenarios.
