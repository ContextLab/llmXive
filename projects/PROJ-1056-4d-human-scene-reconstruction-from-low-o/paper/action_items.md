# Automated-review action items — 4D Human-Scene Reconstruction from Low-Overlap Captures

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Appendix Section 'GEN3C vs. Ours (Rendering Quality)' claims specific metrics (PSNR 20.13, SSIM 0.656, LPIPS 0.215) for the proposed method on held-out cameras. These exact numbers do not appear in Table 1, Table 2, or Table 6 (which lists 'Ours w/o enh.' as 20.39/0.657/0.286). The text cites evidence that is not present in the provided tables, making the claim unverifiable. Update the text to match the table data or add a table containing these specific comparison metrics.
- **[writing]** Section 3.1 states 'We also obtain human masks for each synthesized view' to exclude human regions during background optimization. However, the method description and notation {M_n^1} imply masks are only generated for the N input views using a segmentation model. It is unclear how masks are obtained for the 481 synthesized views (e.g., via propagation or re-running the model). Clarify the mask generation process for synthesized views to resolve this logical gap.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption reads 'Overview of the proposed .' with a missing noun (e.g., 'method' or 'pipeline') after 'proposed'.
- **[writing]** Figure 1: Section references in the diagram (e.g., 'Sec 3.1', 'Sec 3.2') are present, but the caption's stage descriptions do not explicitly map to these section numbers for clarity.
- **[writing]** Figure 2: The caption contains a placeholder '(Sec. )' with a missing section number, failing to cross-reference the detailed text.
- **[science]** Figure 2: The diagram shows a 'Motion-Adaptive Consistency Injection' loop but lacks the specific components mentioned in the related Figure 3 caption (e.g., RAFT, backward flow, EMA), making the mechanism opaque.
- **[science]** Figure 3: The diagram shows 'Refined Output' ($O_{t-K}$) being warped, but the caption states 'previous enhanced outputs' are warped. While likely referring to the same thing, the diagram should explicitly label the input to the warping step as the 'Enhanced Output' or 'Refined Output' to match the caption's description of the recursive process.
- **[writing]** Figure 3: The ellipsis (...) between the $t-K$ and $t-1$ blocks implies a sequence, but the arrows from the 'Refined Output' blocks go directly into the warping step without showing the recursive loop where the output of one step becomes the input of the next. This makes the 'recursive' nature described in the caption visually ambiguous.
- **[writing]** Figure 5: The caption states 'Dance  Xu et al. (Mobile Stage); Yoga  Xu et al. (SelfCap)', but the image labels only show 'Tennis', 'Fencing', 'Dance', and 'Yoga' without specifying which dataset corresponds to which column, creating ambiguity about the source of the Tennis and Fencing data.
- **[science]** Figure 5: The 'Ours' row shows significantly cleaner results than the 'GT' (Ground Truth) row in the Tennis and Fencing columns, where 'GT' appears to have motion blur or artifacts not present in the proposed method; this contradicts the expectation that GT should be the cleanest reference and suggests the 'GT' label may be misapplied or the comparison is misleading.
- **[writing]** Figure 6: The caption references 'Sec. .' with a missing section number; please insert the correct section reference.
- **[science]** Figure 7: The caption claims to show qualitative results on EgoExo-4D, but the rendered image is identical to Figure 5 (Dance scene) and Figure 1 (CPR scene), failing to demonstrate the claimed diversity or specific dataset application.
- **[writing]** Figure 8: The caption contains empty section references '(Sec. )' that need to be filled with the correct section numbers.
- **[writing]** Figure 9: The caption contains a broken cross-reference 'Sec. .' where the section number is missing.
- **[writing]** Figure 9: The caption lists 'per-pixel confidence map' as the third item, but the image label uses the variable '$c$' without explicitly defining it as a map in the text.
- **[science]** Figure 10: The legend defines a 'Start' (green circle) and 'End' (orange square), but the rendered trajectory shows the orange square at the start of the path and the green circle is not visible, contradicting the legend.
- **[writing]** Figure 10: The labels 'V0', 'V1', 'V2', and 'V3' are present on the plot but are not defined in the legend or the caption.
- **[science]** Figure 11: The caption claims 'Each color represents the same person matched across 4 cameras', but the image shows multiple people (Person A, B, C) simultaneously in the same frame, each with different colored boxes. This contradicts the caption's explanation of the color coding scheme.
- **[writing]** Figure 11: The caption references 'Table .' with a missing table number, making it impossible to verify the claimed 97.8% association accuracy.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 3.1 (Preprocessing): The term 'SAM3' is used without definition. While 'SAM' (Segment Anything Model) is standard, 'SAM3' appears to be a specific variant or the authors' own nomenclature (referenced as carion2025sam). Define it at first use, e.g., 'SAM3 (Segment Anything Model 3, a concept-based segmentation model)...'.
- **[writing]** Section 3.2 (Cross-View Identity Association): The symbol $\sigma_p$ and $\sigma_	heta$ appear in Equation 1 without definition. While context suggests they are scale parameters for the Gaussian kernels, explicitly define them in the text immediately following the equation (e.g., 'where $\sigma_p$ and $\sigma_	heta$ are the spatial and pose scale parameters, respectively').
- **[writing]** Section 3.3 (3D Pose Triangulation): Equation 3 introduces $\mathcal{B}$ as 'the set of reliable bone pairs' but does not define the criteria for 'reliable' or how this set is determined algorithmically. Add a brief clause explaining the selection criterion (e.g., 'where $\mathcal{B}$ is the set of bone pairs with reprojection error below threshold X').
- **[writing]** Section 3.4 (Human Reconstruction): The term 'canonical pose' is used to describe the reference state for Gaussians. While standard in SMPL-based reconstruction, explicitly define it for adjacent-field readers as 'a standard T-pose or A-pose reference configuration' to ensure clarity.
- **[writing]** Section 3.5 (Recursive Enhancement Module): The variable $K$ in Equation 5 is used as the number of previous frames but is not defined in the text preceding the equation. Define it explicitly: 'where $K$ is the number of previous frames considered for injection (set to 3 in our experiments).'
- **[writing]** Section 4.1 (Setup): The metric 'Warp-L2' is introduced in Table 3 and the text without a definition of the specific error calculation (e.g., L2 norm of RGB difference after warping). Define it briefly: 'Warp-L2 measures the L2 error between consecutive frames after optical flow warping, computed as...'

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 4.3 claims 'removing the attention-gating module causes the largest performance drop,' but Table 5 shows PSNR/SSIM are identical with/without injection. The text overgeneralizes the impact; clarify that the drop is specific to temporal consistency (Warp-L2) and LPIPS, not static fidelity.
- **[writing]** The Abstract claims SOTA on 'four real-world datasets,' while Section 4.3 details results on '6 360-degree scenes.' Ensure the Abstract's scope matches the specific scene breakdown in the results to avoid implying a broader evaluation than presented.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims 'in-the-wild' success, but experiments use 4 curated, synchronized datasets. Narrow claim to 'evaluated sparse-view benchmarks' or define 'in-the-wild' scope explicitly.
- **[writing]** Conclusion claims 'practical deployment' readiness, yet limitations admit failure on dynamic objects and shadows. Qualify deployment claim to exclude scenarios requiring these features.
- **[writing]** Abstract claims 'first pipeline' without qualifying scope. Add 'to our knowledge' or specify 'among Gaussian-based pipelines' to align with the limited baseline comparison provided.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a computer vision method for 4D human-scene reconstruction using public datasets (EgoHumans, Harmony4D, Mobile Stage, SelfCap) and pre-trained models. The work does not involve the collection of new human-subject data, nor does it release any datasets containing Personally Identifiable Information (PII). The authors explicitly state the use of public benchmarks and standard pre-trained models (e.g., SAM, GEN3C, CoMotion) for segmentation, view synthesis, and pose estimation.

There are no indications of dual-use capabilities that lower the barrier to specific harms (e.g., automated surveillance, deepfake generation for deception, or cyber-attacks) beyond the general capabilities of the underlying generative models, which are not the primary contribution of this work. The paper does not describe operational details for exploiting vulnerabilities or synthesizing hazardous materials. Furthermore, the authors acknowledge limitations regarding dynamic objects and shadows, demonstrating appropriate scientific transparency.

As this is a third-party preprint, the absence of an explicit IRB statement is not a violation, as the research relies entirely on existing public datasets and does not involve new human subject interactions. The paper does not raise foreseeable, non-trivial safety or ethical risks that require mitigation or disclosure beyond what is currently present. The verdict is `accept` with no action items.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling pipeline for 4D reconstruction in low-overlap settings, but the experimental design in the ablation studies and main comparisons leaves open the possibility that the reported gains stem from data volume rather than the proposed architectural innovations. First, the quantitative results in Tables 1 and 2 are reported as single-point estimates without any measure of variance (standard deviation or confidence intervals). In 3D reconstruction tasks, performance can be

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The statistical reporting in this paper is generally consistent with common practices in the computer vision and graphics community (reporting mean metrics on fixed datasets), but it lacks the rigor required to distinguish genuine improvements from random variance, particularly given the small number of test scenes. The primary issue is the absence of uncertainty quantification. Tables 1 and 2 present performance metrics (PSNR, SSIM, LPIPS) to two decimal places (e.g., 18.58, 0.569) as if they w

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured, with a clear logical progression from problem definition to method and evaluation. However, several sentences suffer from complex nesting or ambiguous referents that force the reader to re-parse the text to recover the intended meaning. In Section 3.1, the description of mask usage contains a relative clause ambiguity ("which are used...") that could refer to the views or the masks. While context suggests the latter, the syntax is imprecise. Similarly, Sec
