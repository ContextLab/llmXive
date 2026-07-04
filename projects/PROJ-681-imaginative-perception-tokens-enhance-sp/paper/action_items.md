# Automated-review action items — Imaginative Perception Tokens Enhance Spatial Reasoning in Multimodal Language Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: reject

- **[fatal]** The paper's central claims regarding state-of-the-art performance and the efficacy of Imaginative Perception Tokens (IPT) are fundamentally undermined by the citation of non-existent or future-dated models as baselines and training sources. Specifically, the results tables (Table 1 in the main text, Table tab:pt_breakdown in the supplement) list "GPT-5", "GPT-5.1", "Gemini 2.5 Flash", "Gemini 3 Flash", "Qwen3-VL-8B", and "InternVL3.5-8B" as comparison points. As of the current date, none of thes

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 3: The 'Generated Thought' column displays a top-down view in the third row, contradicting the caption's description of generating a 'visual thought (imagined sideview at M1)'.
- **[writing]** Figure 3: The third row's 'Generated Thought' image depicts a living room with a sofa and rug, which is spatially inconsistent with the input top-down map and views showing a kitchen/dining area.
- **[science]** Figure 6: The caption claims to show examples from 'four sub-categories', but the figure only displays two categories (Distance and Position). The other two sub-categories mentioned in the caption are missing.
- **[writing]** Figure 6: The text labels for the sub-categories (e.g., 'closer', 'further', 'left', 'right') are extremely small and illegible in the rendered image, making it difficult to distinguish the specific task type for each row.
- **[fatal]** Figure 9: The rendered image is a 3D scene (room with table, chair, door) that does not match the caption's description of a 'VQGAN reconstruction quality' analysis; the figure appears to be a rendering artifact or the wrong file.
- **[science]** Figure 10: The rendered image displays a single, unlabelled 3D scene (a room with a window and shadow) that does not visually correspond to the caption's description of a 'Ground-truth vs. decoded IPTs' comparison. There are no side-by-side panels, no ground-truth reference, and no decoded output visible to support the claim of 'visually degraded images' or 'limitations of discrete token generation'.
- **[writing]** Figure 10: The image lacks all necessary scientific annotation, including axis labels, a legend distinguishing 'Ground-truth' from 'Decoded IPTs', and any visual indicators (such as arrows or grid lines) to facilitate the comparison described in the caption.
- **[fatal]** Figure 11: The rendered image is a 3D bathroom scene (sink, wall, painting) that does not match the caption's description of 'grayscale representations' or 'decoded IPTs' from a VLM; the figure content appears to be a rendering artifact or incorrect file.
- **[writing]** Figure 12: The column headers 'Latent 64', 'Latent 32', 'Latent 16', and 'Latent 4' contradict the caption's description which states resolution increases from left to right (Latent-4 to Latent-64). The visual evidence shows the rightmost column is the blurriest (lowest quality), implying it corresponds to the lowest resolution (Latent-4), meaning the headers are either reversed or mislabeled relative to the visual data.
- **[writing]** Figure 12: The column headers do not match the caption's terminology. The caption uses 'Latent-4' and 'Latent-64' (with hyphens), while the figure uses 'Latent 4' and 'Latent 64' (with spaces). While minor, consistency is preferred.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 'Imaginative Token Exploration with Different VLMs' (Supp. e002) uses 'CB' and 'f' in table headers and text (e.g., 'CB 1K, f=16') without defining them. Define 'CB' as 'codebook size' and 'f' as 'downsampling factor' at first use.
- **[writing]** Section 'Data Curation Details' (Supp. e001) references 'TIFA filtering' multiple times without defining the acronym. Expand to 'Text-Image Faithfulness Assessment (TIFA)' at first occurrence and briefly state its purpose (verifying object visibility/position).
- **[writing]** Section 'Perspective Taking' (Supp. e001) uses 'HM3D' as a shorthand for the dataset source without expansion. Define as 'Habitat-Matterport3D (HM3D)' at first use to clarify the relationship to the previously mentioned Matterport3D dataset.
- **[writing]** Section 'Multiview Counting' (Supp. e001) uses 'BEV' (Bird's-eye view) without expansion. While common in robotics, it is not universal in general VLM literature; define at first use (e.g., 'Bird's-eye view (BEV) map').

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 'Imaginative Token Exploration with Different VLMs' claims 'IPT consistently outperformed answer-only and Text CoT on Path Tracing' based on Table 'tab:qwen_discrete'. However, the table shows IPT (55.0/55.9) underperforming 'Answer-only' (48.6/37.6) for the 3B model in PT, and the 7B model has no 'Answer-only' PT baseline listed for comparison. The text's claim of 'consistent' superiority is not entailed by the provided data table.
- **[writing]** In 'Data Curation Details' (Path Tracing, AI2-THOR), the text states 'Training set includes ProcTHOR-10k' but the 'Statistics' subsection immediately below reports '11,204 synthetic examples'. The relationship between the 10k ProcTHOR scenes and the 11,204 examples is ambiguous; it is unclear if the 11k count includes the 10k or if they are distinct subsets, creating a potential inconsistency in dataset composition reporting.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Title/Abstract claim general 'spatial reasoning' enhancement, but results (Table 1) are limited to AI2-THOR, Habitat, VST, and Matterport3D. Narrow scope to tested environments or add cross-domain evaluation.
- **[writing]** Conclusion claims 'internalized spatial reasoning,' yet Fig 3 admits generated thoughts are 'spatially imprecise' and 'lack structure.' Hedge claim to 'improves performance' rather than asserting a verified cognitive mechanism.
- **[writing]** Abstract claims superiority over 'all baselines,' but Table 1 shows Gemini 3 Flash (96.2%) beats Bagel+Mixed (66.5%) on 'Real+Arr.' Correct to 'outperforms most baselines on synthetic splits' or acknowledge the gap.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a method for enhancing spatial reasoning in multimodal models using "Imaginative Perception Tokens" (IPT) to generate intermediate visual representations (e.g., imagined side-views or top-down maps) during inference. The research relies on synthetic data generated from established simulation environments (AI2-THOR, Habitat, ProcTHOR) and public, pre-existing real-world datasets (Matterport3D, Visual Spatial Tuning, ScanNet++, MessyTable).

From a safety and ethics perspective, the work is low-risk. The methodology does not involve:
1.  **Human Subjects:** No new human-subjects data collection, surveys, or behavioral experiments are described. The "human review" mentioned in Section `supp_data_pt` refers to quality control of synthetic annotations, not interaction with human participants requiring IRB oversight.
2.  **PII or Sensitive Data:** The datasets used are standard benchmarks in computer vision and robotics, which are publicly available and do not contain personally identifiable information (PII) or sensitive medical/financial records.
3.  **Dual-Use Harm:** The capability to "imagine" spatial layouts is a reasoning enhancement for navigation and scene understanding. It does not lower the barrier to generating disinformation, biological/chemical hazards, or cyber-attacks. The generated images are abstract spatial representations (often low-fidelity or grayscale in early experiments) intended for internal model reasoning, not for creating deceptive deepfakes or surveillance tools.
4.  **Data Licensing:** The paper cites standard licenses for the public datasets used (e.g., Matterport3D, ScanNet++) and does not appear to scrape data in violation of Terms of Service.

There are no missing disclosures regarding consent, conflicts of interest, or responsible release of harmful capabilities. The paper does not present operational details for exploits or vulnerabilities. Consequently, no action items are required.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The paper presents a compelling method for spatial reasoning, but the experimental design currently fails to rule out several alternative explanations for the reported gains. First, the primary evidence for the efficacy of Imaginative Perception Tokens (IPTs) relies on single-run results reported in Table 1 and the supplementary Table pt_breakdown. The authors report specific accuracy improvements (e.g., Bagel + IPT achieving 61.1% vs. Bagel base at 36.3% on EgoDir) without providing standard de

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Table 1 (main) and Table~ef{tab:pt_breakdown} report single-point accuracy percentages (e.g., 73.5%, 61.1%) for the proposed BAGEL models without any measure of variance (SD, SE, or CI) or number of seeds. In deep learning, single-run reporting is insufficient to distinguish signal from stochastic noise. Report mean ± SD over at least 3 independent training seeds for all primary results, or explicitly state that results are from a single run and treat them as preliminary.
- **[science]** The paper claims 'significant' improvements (e.g., Bagel label-only vs. base in Table~ef{tab:pt_breakdown}) based on point estimates alone. No hypothesis tests (e.g., paired t-tests or bootstrap tests) are reported to validate these differences. Given the multiple comparisons across 5 splits and 3 model variants, apply a statistical test with appropriate multiple-comparison correction (e.g., Holm-Bonferroni) or rephrase claims to 'observed improvement' without invoking statistical significance.
- **[writing]** Table~ef{tab:qwen_discrete} and Table~ef{tab:qwen_modality} report accuracy differences (e.g., 55.0% vs 59.6%) for Qwen2.5-VL experiments without reporting the number of seeds or variance. Since these are ablation studies on model architecture (codebook size, grayscale), the lack of uncertainty reporting makes it impossible to determine if the observed gains are robust or due to random initialization variance. Report variance across seeds for these specific ablation results.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript generally presents a clear narrative flow, with well-structured sections that guide the reader through the methodology, data curation, and results. The use of specific subsections for different data sources (AI2-THOR, Habitat, etc.) aids in digesting the complex data generation pipeline. However, several areas require attention to ensure the prose is frictionless and the structural elements are complete. First, the section "Imaginative Token Exploration with Different VLMs" (Secti
