---
action_items:
- id: 715d4f95b609
  severity: writing
  text: Abstract and Introduction claim ViQ ranks 'first among mainstream discrete
    visual autoencoders' for reconstruction quality. However, Table 2 shows UniTok
    achieves superior PSNR (25.32 vs 22.73) and rFID (0.37 vs 0.62). The Results section
    correctly states 'second only to UniTok'. Update Abstract/Intro to align with
    the data.
- id: 385f7efe3a23
  severity: writing
  text: Figure 1 caption and Introduction claim 'state-of-the-art performance compared
    with continuous visual encoders'. While average scores are competitive, ViQ trails
    significantly on OCRBench (636 vs 690 for 6B continuous). Qualify this claim to
    acknowledge specific task gaps where continuous encoders remain superior.
artifact_hash: b0d13f79598805d86a50b3ae742d6ff735642238ad128fe0a6c96ca6ef0ec5e0
artifact_path: projects/PROJ-793-viq-text-aligned-visual-quantized-repres/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-27T16:35:22.037819Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method for discrete visual representations, but there are notable instances of over-claiming in the summary sections that contradict the empirical data presented later in the manuscript.

First, the Abstract and Introduction assert that ViQ achieves "high precision in low-level reconstruction" and ranks "first among mainstream discrete visual autoencoders" (Introduction, Paragraph 4). This claim is directly contradicted by Table 2 (Comparison of reconstruction quality), where UniTok outperforms ViQ on both PSNR (25.32 vs. 22.73) and rFID (0.37 vs. 0.62). The Results section (Image Reconstruction Experiments, Paragraph 2) correctly acknowledges this, stating ViQ is "second only to UniTok." This inconsistency between the high-level summary and the detailed results constitutes over-claiming. The Abstract and Introduction must be revised to accurately reflect ViQ's standing relative to UniTok to maintain scientific integrity.

Second, the Figure 1 caption and Introduction claim ViQ delivers "state-of-the-art performance compared with continuous visual encoders." While the aggregated average scores in Table 1 are competitive (e.g., 57.2 vs. 57.0 on Qwen2.5-1.5B), the data reveals significant gaps on detail-intensive benchmarks. Specifically, on OCRBench, ViQ (636.0) trails the 6B parameter InternViT-2.5-6B (690.0) by a substantial margin. While the Results section admits this ("ViQ still trails some continuous encoders... on certain detail-intensive benchmarks"), the initial claims in the Abstract and Figure 1 are too broad and imply parity across all tasks. These claims should be qualified to specify that performance is competitive on average but may lag on high-frequency detail tasks.

The Limitations section is appropriately honest regarding model scale (70B+) and data biases, but the over-optimistic framing in the Abstract undermines the paper's credibility. Correcting these specific claims to align with the reported metrics is necessary before acceptance.
