# Automated-review action items — TriSplat: Simulation-Ready Feed-Forward 3D Scene Reconstruction

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 4.2 claims Gaussian baselines suffer 'substantial' degradation while TriSplat is stable. Table 2 shows MeshSplat (a Gaussian method) has -3.18dB degradation, nearly identical to TriSplat's -3.21dB. The claim overgeneralizes; clarify that standard TSDF fusion degrades, but optimized variants like MeshSplat do not.
- **[writing]** Section 3.2 states the point map 'may be optionally detached' from the graph. It is unclear if this was used in final results. If used, clarify the impact on gradient flow; if not, remove 'optionally' to avoid confusion about the reported method's architecture.
- **[writing]** Section 4.2 attributes Gaussian degradation to 'discarding primitives'. However, MeshSplat uses TSDF fusion yet matches TriSplat's stability. The text should specify that the degradation applies to standard TSDF pipelines, not all Gaussian methods, or explain MeshSplat's distinct pipeline.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains multiple placeholders and broken references, including 'Overview of .' (missing method name), 'Sec. ' (missing section number), and 'The resulting oriented triangles are  [pipeline2.pdf]' (incomplete sentence with a filename artifact).
- **[writing]** Figure 1: The 'Geometry Anchored Triangle Orientation' block in the main diagram is labeled 'Triangle Orientation', while the detailed inset below is labeled 'Geometry-Anchored Triangle Orientation', creating inconsistent terminology.
- **[science]** Figure 2: The caption states 'Gaussian baselines show missing surfaces... whereas keeps more complete structure,' but the text 'TriSplat' is missing from the sentence (likely 'whereas TriSplat keeps...'). Additionally, the method name 'TriSplat' is not explicitly labeled in the figure grid (columns are labeled 'Input', 'MVSplat', 'DepthSplat', 'AnySplat', 'YoNoSplat', 'TriSplat', 'Ground Truth'), so the reader must infer which column corresponds to the claim; the caption should explicitly state
- **[writing]** Figure 2: The caption contains a placeholder '[main_dl3dv_mesh_render.pdf]' which appears to be a file reference rather than part of the caption text; this should be removed or replaced with proper citation formatting.
- **[writing]** Figure 3: The caption contains a placeholder '[main_dl3dv_textured_mesh.pdf]' instead of the method name 'TriSplat', and the sentence 'directly exports' lacks a subject, making the claim ambiguous.
- **[writing]** Figure 3: The column labels 'MVSplat', 'DepthSplat', 'AnySplat', 'YoNoSplat', and 'TriSplat' are not visible in the rendered image, making it impossible to identify which method corresponds to which column.
- **[science]** Figure 4: The caption claims to compare 'TSDF-fused Gaussian baselines' against the proposed method, but the image labels show 'MVSplat', 'DepthSplat', 'AnySplat', 'YoNoSplat', 'MeshSplat', and 'SurfelSplat'. These are feed-forward baselines, not TSDF-fused ones, creating a contradiction between the visual evidence and the textual claim.
- **[writing]** Figure 4: The caption contains a missing subject in the phrase 'while preserves sharper triangle-rendered detail'; the name of the proposed method (TriSplat) is omitted.
- **[science]** Figure 5: The caption claims to visualize 'exported textured meshes' and 'geometry-only views', but the image displays 2D image-space renders of the scenes. The 'geometry-only' column (second from left) shows a shaded 3D view, not a raw mesh file or wireframe, which contradicts the claim of visualizing the exported asset directly.
- **[writing]** Figure 5: The figure lacks column headers or row labels to distinguish between the different input view counts (e.g., 6, 12, 24 views) or the specific scene identities, making it impossible to correlate specific rows with the dataset statistics mentioned in the caption.
- **[science]** Figure 6: The caption claims to show 'depth and surface normals' for each method, but the figure displays two distinct rows of images (likely depth and normals) without any row labels or headers to distinguish them.
- **[science]** Figure 6: The caption states 'All models are trained on RE10K and evaluated zero-shot on ScanNet', but the figure lacks a legend or column headers identifying which method corresponds to which column (e.g., which is TriSplat vs. baselines).
- **[writing]** Figure 6: The caption contains a missing subject in the final sentence ('produces smoother...'), likely due to a placeholder error where the method name 'TriSplat' should be.
- **[writing]** Figure 7: The legend at the top uses the method name 'TriSplat (Ours)' but the caption text contains a missing subject (e.g., 'produces a usable mesh...') instead of the method name, likely due to a LaTeX compilation error where the macro was not expanded.
- **[writing]** Figure 7: The x-axis labels ('6 views', '12 views', '24 views') are positioned between bar groups rather than centered under them, which creates ambiguity about which bars belong to which input view count.
- **[writing]** Figure 8: The caption claims the figure demonstrates 'interaction' and 'locomotion,' but the image consists of four static snapshots with no visual indicators of motion, collision events, or temporal progression to substantiate these dynamic claims.
- **[writing]** Figure 8: The sub-captions ('Unity character', 'Unity interaction', 'Isaac HI', 'Isaac quadruped') are generic and do not describe the specific scene content or the action occurring in each panel, making it difficult to verify the 'simulation-ready' claim without external context.
- **[writing]** Figure 9: The caption contains a placeholder '[supp_prim_re10k_01.pdf]' instead of the method name (likely 'TriSplat'), and the text 'closer to under primitive rendering' is grammatically incomplete.
- **[writing]** Figure 9: The caption references 'Fig. ' with a missing figure number for the mesh-rendering comparison.
- **[writing]** Figure 10: The caption contains a broken cross-reference ('counterpart to Fig. ') where the figure number is missing.
- **[writing]** Figure 10: The image lacks column labels to identify the specific methods being compared, relying on the reader to infer them from Figure 2 or 3.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'SE(3)' and 'SO(3)' at first use in Section 3.1. While standard in robotics, these acronyms exclude non-specialist readers in computer vision or graphics who may not recall the specific Lie group notation immediately.
- **[writing]** Replace the acronym 'TSDF' with 'truncated signed distance function' upon its first appearance in the Introduction and Related Work sections. The term is used frequently without definition, assuming reader familiarity with volumetric reconstruction pipelines.
- **[writing]** Define 'LPIPS' (Learned Perceptual Image Patch Similarity) at first use in Section 4.1. The acronym is used as a primary metric without spelling out the full name, which hinders accessibility for readers outside the specific subfield of perceptual metrics.
- **[writing]** Clarify the term 'feed-forward' in the context of the network architecture. While used repeatedly, the distinction between 'feed-forward' (single-pass inference) and 'optimization-based' methods could be briefly explicit for readers less familiar with the specific jargon of 'feed-forward 3D reconstruction'.
- **[writing]** Define 'SH' (Spherical Harmonics) when first mentioned in Section 3.1 regarding triangle attributes. The abbreviation is used without expansion, which is a barrier for readers from adjacent fields like robotics or general computer vision.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 4.2 attributes Recall gains solely to TSDF fusion, but the comparison conflates primitive type (Gaussian vs. Triangle) with extraction method. Clarify if the gap is due to the primitive or the TSDF step to support the causal claim.
- **[science]** Section 3.2 derives tangent vectors from image-space derivatives without explicitly stating the coordinate transformation (intrinsics/pose) required to align them with world-space surface gradients. This gap makes the 'dominant gradient' claim logically incomplete.
- **[science]** Section 3.3 claims opacity binarization ensures stability, yet vanishing gradients at 0/1 opacity risk premature pruning before geometry converges. Explicitly link the 'alpha floor' mechanism to this stability claim to close the logical gap.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The 'simulation-ready' claim (Abstract, Intro) overreaches. Qualitative robot videos (Appx 6.2) do not prove mesh validity for physics solvers. Authors must quantify mesh topology (manifoldness, holes) or simulation stability metrics, or temper claims to 'visually ready'.
- **[writing]** The assertion that Gaussian baselines inherently suffer 'substantial quality drop' (Intro, Sec 4.2) is overstated. The degradation depends on specific TSDF parameters used. Authors should clarify if optimized baselines could close the gap or if the drop is an implementation artifact.
- **[writing]** Claiming meshes are 'directly exported' for simulation (Sec 3.4) implies watertightness. The described extraction (pruning, merging) does not guarantee manifold geometry. Authors must qualify claims or prove output meshes meet physics engine topology requirements.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript presents TriSplat, a feed-forward method for generating simulation-ready 3D meshes. From a safety and ethics perspective, the primary concern lies in the gap between the claimed "simulation-ready" output and the rigorous safety validation required for deployment in robotics and physics engines. Safety Validation of Simulation Outputs: The paper repeatedly asserts that the output meshes are directly usable in physics engines like NVIDIA Isaac Sim and Unity for tasks such as locomot

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of 'simulation-ready' output relies on visual demonstrations in Appendix Sec. 6.4 (Figs. 14-17) and qualitative descriptions of physics engine behavior. To support this central claim scientifically, the authors must provide quantitative metrics on mesh manifoldness (e.g., non-manifold edge count), watertightness, and collision detection success rates in the physics engines, rather than relying solely on visual sequences.
- **[science]** The ablation studies in Appendix Sec. 6.3 (Tables 10-12) report performance on RE10K but do not explicitly isolate the contribution of the 'mono-normal bootstrap' (Eq. 5) to the final surface accuracy (F1/CD). A specific ablation removing the bootstrap while keeping the refinement head is needed to prove the necessity of the teacher-student schedule for convergence stability.
- **[science]** Table 4 (Appendix) reports a primitive-to-mesh PSNR degradation of -3.21 dB for TriSplat, which is non-negligible. The authors claim 'minimal degradation' in the text. The evidence requires a more rigorous statistical analysis (e.g., paired t-tests or confidence intervals) across the test set to determine if this degradation is statistically significant compared to the baselines' larger drops, or if it falls within the noise floor of the metric.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The ablation studies in Appendix~ef{sec:app_ablation} (Tables~ef{tab:ablation_scale}, ef{tab:ablation_blur}, ef{tab:ablation_temperature}) report single-point performance metrics without any measure of variance (e.g., standard deviation) or statistical significance testing. Given the stochastic nature of deep learning training, claims of superiority based on small metric differences (e.g., CD 0.190 vs 0.189) are statistically unsupported without reporting results over multiple random seeds.
- **[science]** In Section~ef{sec:setup} and Table~ef{tab:main_re10k}, the evaluation protocol does not specify the number of random seeds used for training or the variance across runs. To ensure the reported improvements (e.g., +2.75 dB PSNR) are robust and not artifacts of specific initialization, the authors must report mean and standard deviation over at least 3 independent training runs for the main baselines and their method.
- **[science]** The large-loss filter mentioned in Section~ef{sec:supervision} ('suppress outlier samples after warm-up') lacks a statistical definition. The threshold for 'large loss' should be explicitly defined (e.g., based on a specific percentile of the loss distribution or a multiple of the standard deviation) to ensure reproducibility and prevent arbitrary data curation that could bias the results.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 4.1, the phrase 'primary rende ring metric' contains a typographical error with an unintended space. Please correct to 'primary rendering metric'.
- **[writing]** In Section 4.2, the sentence '...with a mean angular error of 27.9$^\circ$ and a $$~0.06 or pose loss~$>$~1.0) have their loss contribution...' appears to be a severe formatting or copy-paste error where a sentence fragment or equation was inserted mid-stream, breaking the grammatical flow. This section requires a complete rewrite to restore coherence.
- **[writing]** In Section 4.2, the phrase 'a clear margin, with a mean angular error of 27.9$^\circ$ and a $$~0.06' contains a broken mathematical expression or placeholder that disrupts readability. The intended metric value and context are missing or malformed.
