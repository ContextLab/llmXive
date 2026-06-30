---
action_items:
- id: dae5e4bf88dd
  severity: writing
  text: The paper makes several claims that extend beyond the immediate evidence provided
    in the text, specifically regarding the scope of its "strongest" performance claims
    and the definition of "annotation-free." First, the Conclusion states that \llmname{ForgeOwl-8B}
    is the "strongest open-data mobile GUI agent evaluated." This is factually contradicted
    by Table 2 (MobileWorld GUI-only results), where \llmname{GUI-Owl-1.5-32B} achieves
    a 43.9% success rate compared to \llmname{ForgeOwl-8B}'s 41.0%. W
artifact_hash: eb6909e8c26be542682832f5d7b13c92b92b728f8b94fb6c9612acad1621be79
artifact_path: projects/PROJ-782-mobileforge-annotation-free-adaptation-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T20:13:55.290352Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend beyond the immediate evidence provided in the text, specifically regarding the scope of its "strongest" performance claims and the definition of "annotation-free."

First, the Conclusion states that \llmname{ForgeOwl-8B} is the "strongest open-data mobile GUI agent evaluated." This is factually contradicted by Table 2 (MobileWorld GUI-only results), where \llmname{GUI-Owl-1.5-32B} achieves a 43.9% success rate compared to \llmname{ForgeOwl-8B}'s 41.0%. While the 32B model is larger, the claim of being the "strongest" without a qualifier (e.g., "strongest 8B model" or "strongest model trained without human annotations") is an overreach that misrepresents the current state-of-the-art. The authors must refine this claim to accurately reflect the model size constraints or the specific "open-data" definition used.

Second, the title and abstract emphasize "Annotation-Free Adaptation." However, Section 2.1 describes a \textbf{Critic} module that generates hierarchical feedback ($\mathcal{F}_k$) and corrective hints ($h_k$). If this Critic is a pre-trained model (e.g., Gemini 2.5 Pro as mentioned in the ablation study), the system is not truly "annotation-free" in the sense of unsupervised learning; it is "human-annotation-free" but "model-supervised." The paper risks over-claiming by implying a level of autonomy that relies on the implicit "annotations" of a stronger teacher model. The methodology section must explicitly distinguish between "human-free" and "model-free" to avoid misleading readers about the source of the training signal.

Finally, the claim of successful Out-of-Domain (OOD) adaptation to MobileWorld (Table 2) based on tasks generated from AndroidWorld (Section 3) lacks sufficient justification regarding domain shift. The paper notes that 3,249 tasks were mined from 20 specific apps (Table 3, Appendix), but does not analyze the functional overlap or UI distribution differences between these source apps and the MobileWorld benchmark. Claiming robust generalization without addressing the potential domain gap or providing evidence that the learned policy transfers across distinct app ecosystems is an over-extrapolation of the experimental results. The authors should either temper the OOD claims or provide a more rigorous analysis of the cross-app transferability.
