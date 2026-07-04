# Automated-review action items — ABot-Earth 0.5: Generative 3D Earth Model

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper makes several strong quantitative and comparative claims that are not fully supported by the provided evidence or contain internal inconsistencies. First, the primary quantitative claim in Section 5.1 ("Generative Fidelity") asserts that the method achieves a state-of-the-art FID of 16.1, a "substantial improvement" over the previous best of 69.5. However, the caption of Table 1 (tab:conditions_results) explicitly admits that "FID/KID values for baselines are computed using different G

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The 'Efficiency' axis uses qualitative labels ('High'/'Low') while others use quantitative scales (0-5), and the data points are not aligned with the grid lines (e.g., the blue point is at the outer edge while the label 'High' is near the center), making the metric undefined and the chart unreadable.
- **[science]** Figure 1: The 'Country/Region Coverage' axis uses a percentage scale (0-100%) while the other four axes use a 0-5 scale; mixing these incompatible units on a single radar chart without normalization renders the geometric comparison of the polygons meaningless.
- **[science]** Figure 2: The image is a standard Google Earth screenshot (indicated by the watermark) rather than a generative output from the 'ABot-Earth' model. As a standalone figure, it fails to demonstrate the paper's core claim of generating 3D Earth models, serving only as a reference or input without a corresponding generated comparison.
- **[writing]** Figure 2: The caption is insufficient, providing only the source ('Google Earth') and location ('New Zealand') without describing the specific view parameters (pitch, yaw, zoom) or the purpose of the image in the context of the study.
- **[writing]** Figure 3: The caption contains a grammatical error and missing subject ('We are unveiling , a generative...'); the comma should be removed and the model name inserted.
- **[science]** Figure 3: The map displays blue and orange dots but lacks a legend or key to define what these colors represent (e.g., training vs. test, or specific data sources).
- **[science]** Figure 6: The caption claims the figure shows a 'tile-based production pipeline' and 'parallel inference,' but the image only displays a static globe with a grid overlay and a red line. It lacks any visual representation of a pipeline, data flow, or inference process.
- **[writing]** Figure 6: The image title 'Global Equal-Area Tiling Scheme' is not reflected in the caption, which describes a 'production pipeline' instead. The caption fails to explain the red line or the specific grid structure shown.
- **[science]** Figure 8: The caption claims to show a 'tile-based production pipeline' and 'parallel inference,' but the image displays a static global tiling grid without any visual representation of the pipeline, data flow, or inference process.
- **[science]** Figure 8: The image is identical to Figure 6 and Figure 9, which share the exact same caption text, suggesting a copy-paste error where the specific content for Figure 8 is missing or duplicated.
- **[science]** Figure 9: The caption claims to show a 'tile-based production pipeline' and 'parallel inference,' but the image displays a static global tiling grid without any visual representation of the pipeline, inference process, or parallelism.
- **[science]** Figure 9: The image is identical to Figure 6 and Figure 8, which share the exact same caption text, suggesting a copy-paste error where the specific content for Figure 9 is missing or duplicated.
- **[science]** Figure 10: The caption claims to show 'LOD rendering' enabling 'seamless exploration from global to street-level views,' but the image displays a single static aerial view of a city without any visual evidence of multi-scale LOD transitions or global context.
- **[writing]** Figure 10: The image lacks any scale bar, compass, or coordinate reference to identify the specific location shown, making the 'global' context claim unverifiable.
- **[science]** Figure 11: The caption claims 'Top-down views are in the leftmost column,' but the images in the first column are clearly oblique aerial views, not top-down (nadir) views. The perspective is slanted, contradicting the description.
- **[writing]** Figure 11: The caption states 'From top to bottom: Eiffel Tower, Colosseum, US Capitol, and Arc de Triomphe,' but the visual content of the rows does not match this order. The first row shows the Eiffel Tower, the second the Colosseum, the third the US Capitol, and the fourth the Arc de Triomphe. However, the third row (US Capitol) appears to be a different building or a significantly distorted version compared to the others, and the fourth row (Arc de Triomphe) is actually the Arc de Triomphe,

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 2.1 (Data Collection): The acronym 'DOF' appears in Table 1 without definition. While 'Degrees of Freedom' is standard in robotics, it is not explicitly defined here. Add '(DOF: Degrees of Freedom)' at first use in the table header or text.
- **[writing]** Section 2.1 (Data Collection): The term 'Z-Monotonic SDF' is introduced in the 'Multi-Stereo Satellite Imagery' paragraph without definition. A competent adjacent-field reader may not know this specific geometric constraint. Add a brief gloss, e.g., 'a Signed Distance Field (SDF) constrained to be monotonic along the viewing ray'.
- **[writing]** Section 2.3 (Training Tile Generation): The term 'accumulated opacity' is used in 'View-Level Rendering Assessment' without definition. While intuitive to 3DGS experts, it is a specific technical term. Define it briefly, e.g., 'the sum of opacities of all Gaussians along a ray'.
- **[writing]** Section 4.2 (EarthScape): The 'Bhattacharyya distance' is cited as the guide for statistical decimation without explanation. For a reader outside statistical learning or specific 3D compression subfields, this is opaque. Add a clause defining it as 'a metric measuring the similarity of two probability distributions'.
- **[writing]** Section 4.2 (EarthScape): The acronym 'ENU' is used ('ENU local tangent plane coordinate system') without expansion. Define it as '(East-North-Up)' at first occurrence.
- **[writing]** Section 4.2 (EarthScape): The term 'frustum culling' is used in the final paragraph without definition. While common in graphics, it is a specific rendering optimization. Add a brief parenthetical, e.g., 'frustum culling (discarding objects outside the camera view)'.
- **[writing]** Section 5.1 (Generative Fidelity): The term 'KID' is used alongside FID without expansion. Define it as 'Kernel Inception Distance (KID)' at first use in the text.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 4.1 states a 25-min inference for a 2.56km² tile, while Section 5.2 claims <10 min/km². Clarify if the 10-min metric is a derived rate or a specific tile size to ensure the conclusion follows the premise.
- **[writing]** Table 1 lists speed as "10 min" while the text says "under 10 minutes". Update the table to "<10 min" or the text to "approx. 10 min" to resolve the logical mismatch between the bound and the exact value.
- **[writing]** Section 3.3 claims "seamless" landscapes, but Section 4.1 admits cross-block seamlessness is a future goal. Qualify Section 3.3 to specify seamlessness is within blocks, not necessarily across the 312k production tiles.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract/Intro claim 'solves' sim-to-real gap and enables 'closed-loop UAV navigation,' but Sec 5 only shows static renderings/FID. No UAV trials exist. Replace 'solves' with 'mitigates' and scope navigation to 'simulation-ready environments for' until validated.
- **[writing]** Intro claims 'robust Earth-scale generalizability' across 'vast majority' of global areas, but Sec 5 only tests 3 locations (Auckland, Kamakura, Ireland). Narrow claim to 'demonstrated on diverse test cases' or provide broader quantitative evaluation across varied biomes.
- **[writing]** Table 1 and Sec 5 claim 'first' to create 'continuous' Earth-scale environments, yet Sec 4.1 admits cross-block seamlessness is a 'future iteration' goal. Qualify 'first' to 'first pipeline for' or acknowledge current block-based stitching limitations in the claim.
- **[writing]** Table 2 lists coverage as 'Infinite,' but Sec 4.1 describes a finite tile-based pipeline (~312k tiles) limited by VRAM. Replace 'Infinite' with 'Global-scale' or 'Planetary-scale' to accurately reflect finite compute constraints.

## paper_reviewer_safety_ethics — verdict: accept

The paper presents a generative 3D Earth model trained on real-world reconstructions and satellite imagery. From a safety and ethics perspective, the work does not present a foreseeable, non-trivial risk of harm that is unaddressed.

The primary data sources are explicitly identified as public benchmarks (e.g., DFC 2019, UrbanScene3D) and proprietary aerial/satellite imagery. The paper states that dynamic elements like vehicles and pedestrians are "automatically detected and removed" during the reconstruction pipeline (Section 2.2), which effectively mitigates risks related to PII or re-identification of individuals in the training data. The generated output is a synthetic 3D environment; while it is geospatially accurate, it does not expose sensitive personal data or operational details of critical infrastructure in a way that would facilitate immediate harm (e.g., it does not reveal internal layouts, security vulnerabilities, or real-time surveillance feeds).

The paper mentions downstream applications in UAV navigation and simulation. While generative models can theoretically be used for dual purposes, the method described (generating visual 3D scenes from satellite imagery) does not lower the barrier to a specific harmful capability (such as automated vulnerability discovery or biological synthesis) in a way that requires a novel mitigation strategy beyond standard responsible AI practices. The authors acknowledge the "sim-to-real" gap and the utility for simulation, which is a standard and acceptable research goal.

No human-subjects research requiring IRB approval is described (the data is pre-existing imagery or synthetic reconstructions). No license violations are apparent given the mix of public datasets and proprietary data. The paper does not disclose any conflicts of interest that would bias the safety assessment, though the authors are affiliated with a commercial mapping entity (Amap/AMAP), which is standard for this type of applied research and does not constitute an undisclosed conflict in this context.

Consequently, there are no specific, nameable gaps in disclosure or mitigation that require action. The work is low-risk by construction.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The central claim of ABot-Earth 0.5 is that it achieves state-of-the-art generative fidelity and system-level applicability for planetary-scale 3D reconstruction. However, the experimental design presented in the Evaluation section contains critical gaps that prevent the evidence from supporting these claims. First, the quantitative comparison of generative fidelity (Table 1) is fundamentally flawed. The authors report an FID of 16.1 compared to baselines ranging from 69.5 to 97.3. However, the

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 1 (tab:conditions_results) reports FID/KID scores for baselines (CityDreamer, GaussianCity, EarthCrafter) as single point estimates without uncertainty metrics (e.g., mean ± SD over seeds). The caption admits baselines use different GT sets, but the lack of variance reporting for the proposed method's 16.1 FID score prevents assessment of stability. Report mean ± SD over ≥3 random seeds for the proposed method and clarify if baseline numbers are single-run citations or aggregated.
- **[science]** Section 5.1.3 claims a 'comprehensive human study' for visual quality (radar chart in Fig. 5) but provides no statistical details: sample size (N participants), inter-rater reliability (e.g., Cronbach's alpha), or significance tests (e.g., paired t-tests/ANOVA) for the claimed 'higher aesthetic score.' Without these, the claim of superiority is anecdotal. Add N, reliability metrics, and p-values or confidence intervals for the human study results.
- **[writing]** The abstract and Section 1 claim the method is 'significantly better' than baselines, yet Section 5.1.1 only presents point estimates (FID 16.1 vs 69.5) without a formal hypothesis test or confidence intervals to support the 'significant' descriptor. In the absence of a stated test (e.g., bootstrap or t-test) and p-value, replace 'significantly better' with 'substantially lower FID' or report the actual statistical test results.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Section 4, 'Georeferencing': The phrase 'isotropic resampling process based on the target spatial extent' is vague. Clarify that 'target spatial extent' refers to the original ground coverage to ensure the resampling logic is immediately clear.
- **[writing]** Section 5: The subsection titles ('Efficiency', 'Visual Quality and Aesthetics') do not match the introductory list ('Timeliness and Efficiency', 'Visual Quality'). Align the titles with the list to improve structural coherence.
- **[writing]** Section 3: Subsection titles use curly braces for emphasis (e.g., '{representation gap}'), which is non-standard. Replace with italics or bold text to ensure clean rendering and professional appearance.
- **[writing]** Section 2, 'Multi-Stereo Satellite Imagery': The definition of 'FromOrbit2Ground' is dense. Split the sentence introducing it and its function into two sentences to improve flow and clarity.
