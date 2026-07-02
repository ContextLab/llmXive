---
action_items:
- id: 97e02369cab0
  severity: science
  text: The claim of being '55x faster' (Introduction, Sec 4.2) relies on a specific
    deployment configuration (CUDA Graphs) for GAM that is not applied to baselines.
    The text states baselines use 'official PyTorch' paths without CUDA Graphs, while
    GAM uses them. This comparison is unfair and overstates the speed advantage. The
    authors must either apply CUDA Graphs to all baselines or rephrase the claim to
    reflect the specific optimization used.
- id: e938b83b5841
  severity: writing
  text: The claim that GAM is 'more accurate' (Abstract, Introduction) is an overgeneralization.
    Table 1 shows GAM is not the most accurate on the standard LIBERO benchmark (Orig.
    SR 97.6% vs Cosmos-Policy 98.5% and pi0.5 96.9% is close, but Cosmos is higher).
    GAM is only 'more accurate' on specific perturbation settings (e.g., Camera).
    The text should qualify 'more accurate' to 'more robust under perturbations' or
    'more accurate in OOD settings'.
- id: 427f5a1faca6
  severity: writing
  text: The statement that GAM is 'lighter' (Abstract, Introduction) is ambiguous.
    While the total parameter count (1.4B) is lower than some baselines (e.g., 7B
    OpenVLA), it is comparable to or higher than others (e.g., 2B Cosmos, 3.3B pi0.5).
    The claim should be qualified to 'fewer trainable parameters' (which is true,
    ~983M vs 3.3B+) rather than 'lighter' in a general sense, as the frozen backbone
    still contributes to the model size.
artifact_hash: 2b47a226fbf60e77bf3630e010af6d066f9a3ac0ebb39463048a80ab1f66b524
artifact_path: projects/PROJ-718-geometric-action-model-for-robot-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:58:00.077649Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the superiority of the Geometric Action Model (GAM) over existing baselines, specifically that it is "more accurate, more robust, faster, and lighter." While the experimental results support the claim of improved robustness (particularly in camera-perturbation settings), the other claims exhibit overreach when scrutinized against the provided data.

First, the claim of being "55x faster" (Introduction, Section 4.2) is derived from a comparison where GAM utilizes CUDA Graphs for inference optimization, while the baselines are evaluated using their "official PyTorch" paths without this specific optimization (Appendix, Section A.4). This is a methodological inconsistency that inflates the reported speedup. The 55x figure represents the gap between an optimized GAM and unoptimized baselines, not an inherent architectural advantage. The authors must either benchmark all methods with identical optimization stacks (including CUDA Graphs) or temper the claim to reflect the specific conditions under which this speedup was achieved.

Second, the assertion that GAM is "more accurate" (Abstract, Introduction) is not universally supported by the data. In Table 1 (LIBERO Original), GAM achieves a 97.6% success rate, which is lower than Cosmos-Policy (98.5%) and comparable to pi0.5 (96.9%). GAM's accuracy advantage is primarily evident in the LIBERO-Plus (OOD) settings, particularly the camera perturbation. Claiming general "higher accuracy" without qualifying it as "higher accuracy in out-of-distribution scenarios" is an overstatement of the results.

Finally, the claim that GAM is "lighter" is imprecise. While GAM has fewer *trainable* parameters (~983M) compared to the full baselines, its total parameter count (1.4B) is not significantly "lighter" than all competitors (e.g., Cosmos-Policy is 2B, but pi0.5 is 3.3B). The term "lighter" often implies total model size or memory footprint. A more accurate claim would be "more parameter-efficient" or "requires fewer trainable parameters," which is supported by the ablation showing the backbone is largely frozen.

These issues do not invalidate the core contribution but require precise rephrasing to ensure the claims align strictly with the evidence presented.
