# Automated-review action items — Identifying stimulus-driven neural activity patterns in multi-patient intracranial recordings

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer — verdict: accept

# Free-form review body

## Strengths
- **Comprehensive Scope**: The chapter provides an exceptionally thorough overview of the challenges and methodologies involved in identifying stimulus-driven neural activity, specifically tailored to the complexities of multi-patient intracranial recordings (iEEG).
- **Methodological Clarity**: The distinction between within-participant (GLMs, MVPA, RSA) and across-participant (HTFA, Gaussian Processes, Hyperalignment, ISC/ISFC) approaches is clearly articulated. The mathematical formulations for key models (e.g., TFA, GLMs) are presented with appropriate rigor yet remain accessible.
- **Contextual Awareness**: The author effectively addresses the unique constraints of iEEG data, particularly the non-uniform electrode coverage across patients and the clinical origins of the data (epilepsy monitoring). The discussion on how to bridge these gaps using functional alignment and probabilistic modeling is a significant strength.
- **Visual Intuition**: The LaTeX source references figures that effectively illustrate complex concepts like the trade-off between spatial/temporal resolution, the geometry of joint stimulus-activity models, and the mechanics of Gaussian process reconstruction.
- **Literature Integration**: The bibliography is extensive and well-integrated, citing foundational work (Hubel & Wiesel) alongside cutting-edge methods (Transformers, Hyperalignment) and the author's own contributions to the field.

## Concerns
- **Minor Typographical Issues**: There are a few minor typos in the text (e.g., "absense" instead of "absence" in the description of Figure 2; "proceed" misspelled as "procede" in Section 2.1.2). These do not impact scientific validity but should be corrected for publication quality.
- **Figure Referencing**: The text references `Fig.~\ref{fig:spacetime}` and others, but since the reviewer cannot see the rendered PDF, it is assumed the figures are correctly placed. However, the caption for Figure 2 mentions "absense" which is a typo.
- **Data Availability Note**: As this is a review of a third-party preprint, the absence of bundled code/data in the submission is expected. The text mentions "Data & code availability" generally, but for a final publication, a specific link to the repository (if one exists) should be explicitly stated in the text or a footnote, though this is a minor formatting suggestion rather than a scientific flaw.

## Recommendation
The manuscript is scientifically robust, logically structured, and provides a valuable synthesis of current methods for analyzing multi-patient iEEG data. The arguments are well-supported by the literature, and the proposed frameworks (such as the use of hierarchical models to handle electrode variability) are sound. The minor typographical errors are easily fixable and do not detract from the overall quality. The paper is ready for publication with only minor copy-editing required.

**Verdict**: accept

## paper_reviewer_claim_accuracy — verdict: accept

The manuscript demonstrates high factual accuracy regarding the definitions, methodologies, and theoretical frameworks of stimulus-driven neural activity analysis. The claims made about specific techniques—such as Generalized Linear Models (GLMs), Multivariate Pattern Analysis (MVPA), Representational Similarity Analysis (RSA), and Hyperalignment—are consistent with the cited literature. For instance, the description of RSA as a method comparing correlation structures without requiring explicit mapping (Section 2.1.3, citing \citep{KrieEtal08b}) is accurate. Similarly, the explanation of Hierarchical Topographic Factor Analysis (HTFA) and its use of radial basis functions to handle variable electrode locations (Section 2.2.1, citing \citep{MannEtal14b, KumaEtal21}) correctly reflects the underlying mathematical approach.

The citations provided for foundational concepts (e.g., Hubel and Wiesel for receptive fields, Hodgkin and Huxley for action potentials) are appropriate and correctly attributed. The distinction between invasive and non-invasive modalities, and the specific challenges of multi-patient intracranial recordings (e.g., variable electrode coverage), are supported by the referenced works (e.g., \citep{EzzyEtal17, OwenEtal20}). The claim that broadband shifts in LFP power correlate with firing rates (Section 1.2.1, citing \citep{MannEtal09a}) is a well-established finding in the field and is accurately presented.

No instances were found where claims were overstated relative to the evidence provided in the cited sources, nor were there obvious misattributions of specific methodological capabilities. The text carefully qualifies statements regarding the limitations of current methods (e.g., the difficulty of linking neural and stimulus features at high levels of detail in the conclusion), maintaining a balanced and accurate scientific tone. The references to specific figures (e.g., Figure 1 for spatiotemporal resolution, Figure 4 for electrode coverage) align logically with the textual descriptions of the data and concepts they represent.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption states 'Green shading denotes in vitro methods,' but the only green region ('Patch clamp') is a solid box, not a shaded region, creating a minor inconsistency in terminology.
- **[science]** Figure 1: The caption notes 'axes are not drawn to scale,' yet the x-axis labels (nanoseconds to decades) and y-axis labels (angstroms to decimeters) imply a logarithmic scale that is not explicitly marked or labeled as such on the axes themselves.
- **[writing]** Figure 2: The caption text for Panel B is incomplete, ending abruptly with 'recording surface' and missing the description for Panels C and D.
- **[writing]** Figure 2: Panels C and D display oscillatory waveforms but lack any caption description or definition in the provided text.
- **[writing]** Figure 2: The axes in all panels lack tick marks, numerical scales, or unit labels, making the 'arbitrary units' mentioned in the caption impossible to verify visually.
- **[science]** Figure 5: Panel A's x-axis is labeled 'Time' with ticks 0 and 99, but the caption describes a continuous stimulus without specifying the time unit or scale; the axis lacks intermediate ticks or a clear time unit (e.g., seconds, frames).
- **[science]** Figure 5: Panels B and C show 3D trajectories and 2D heatmaps but lack axis labels for the 3D plots (no indication of which feature corresponds to x/y/z axes) and no colorbar for the heatmap intensity mapping.
- **[writing]** Figure 5: The caption states Panel C exhibits 'event boundaries,' but the visual representation in Panel C does not clearly distinguish these boundaries from Panel B's trajectory—no visual markers (e.g., vertical lines, color changes) indicate event boundaries.
- **[science]** Figure 6B: The caption states that colors denote different patients (m=53), but the rendered image lacks a legend or colorbar to map specific colors to patient IDs, making the data uninterpretable.
- **[writing]** Figure 6: The panels are not labeled with 'A' or 'B' in the rendered image, despite the caption explicitly distinguishing between 'A. Example patient' and 'B. Across-patient electrode locations'.
- **[writing]** Figure 7: The caption for Panel C is truncated ('Interpreting coord'), leaving the panel's purpose undefined.
- **[science]** Figure 7: Panel C displays a 'Reconstruction' image but lacks a corresponding legend entry or visual key to explain the reconstruction method or quality metrics.
- **[fatal]** Figure 8: The caption text is truncated mid-sentence at the end ('The per-image weig'), indicating missing content.
- **[science]** Figure 8: Panel A displays a 2D heatmap with overlaid white circles and 'x' markers, but the image lacks a colorbar or scale to interpret the heatmap values.
- **[science]** Figure 8: Panel B is completely missing from the rendered image; the caption describes it ('Brain images are described by weighted sums...'), but only Panel A is visible.
- **[fatal]** Figure 9: The rendered image displays panels labeled A through E (Electrode locations, RBF interpolation, Correlation matrices, etc.), but the provided caption describes a completely different figure (Building across-patient models using Gaussian process regression) with panels A and B only. The visual content and text are mismatched.
- **[science]** Figure 9: The image contains no axes, units, or legends for the heatmaps in panels C and D, making the data values and color scales illegible.
- **[science]** Figure 9: Panel E shows 'Observed activity' and 'Reconstructed activity' but lacks a legend or color key to define the specific waveforms or metrics being plotted.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'GLM' (Generalized Linear Models) and 'MVPA' (Multivariate Pattern Analysis) at their first occurrence in the Abstract and Section 41.2.1, rather than assuming reader familiarity.
- **[writing]** Replace the acronym 'RSA' (Representational Similarity Analysis) with the full term upon first use in Section 41.2.2, and ensure 'ISC' and 'ISFC' are fully spelled out before abbreviation in Section 41.3.2.
- **[writing]** Replace 'LFP' (Local Field Potentials) with the full term at first mention in Section 41.1.3, and define 'TFA' (Topographic Factor Analysis) and 'HTFA' (Hierarchical TFA) before using the acronyms in Section 41.3.1.
- **[writing]** Simplify 'procrustean transformation' to 'geometric alignment' or 'optimal rotation/scaling' in Section 41.2.3 and 41.3.2, as the mathematical term may exclude non-specialist readers.
- **[writing]** Replace 'microwires' with 'fine-wire electrodes' and 'patch clamp' with 'intracellular recording' in Section 41.1.2 to use more descriptive, less jargon-heavy terminology for a general audience.

## paper_reviewer_logical_consistency — verdict: accept

The manuscript demonstrates strong logical consistency throughout its exposition of methods for identifying stimulus-driven neural activity. The argument structure follows a clear deductive path: it first establishes the fundamental challenges of defining neural activity and modeling stimuli (Sections 1.1–1.2), then systematically evaluates specific methodological solutions (Section 2) that directly address the previously identified gaps.

The causal claims linking methodological choices to their utility are well-supported. For instance, the text logically derives the necessity of "across-participant" approaches (Section 2.2) from the premise that intracranial electrode locations vary significantly between patients (Section 1.3, Fig. 1.3). The explanation of how Hierarchical Topographic Factor Analysis (HTFA) and Gaussian Process models solve this specific alignment problem is internally consistent, with the mathematical descriptions (e.g., the radial basis function constraints in Eq. 4) aligning with the stated goal of creating a "global template" (Fig. 1.5).

Furthermore, the distinction between "within-participant" and "across-participant" analyses is maintained without contradiction. The text correctly identifies that methods like GLMs and MVPA are primarily within-subject (Section 2.1.1), while methods like Inter-Subject Correlation (ISC) are inherently across-subject (Section 2.2.2), and the logical implications of these distinctions for generalizability are consistently applied. The discussion of "joint stimulus-activity models" (Section 2.1.3) logically follows the critique of treating stimulus and neural features as independent ground truths, offering a coherent alternative that accounts for mutual uncertainty.

No internal contradictions were found regarding the definitions of terms (e.g., "stimulus model," "neural activity") or the capabilities of the described algorithms. The conclusion that no single method is universally superior, but rather that the choice depends on the specific spatiotemporal scale and research question, is a logical synthesis of the preceding evidence. The manuscript successfully avoids overclaiming; for example, it explicitly notes the limitations of generalizing findings from epilepsy patients to the broader population (Section 3), maintaining logical integrity regarding the scope of its claims.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The abstract and introduction imply the chapter presents new analysis or primary results by using phrases like 'we will consider' and 'examples serve to illustrate.' Since this is a tutorial/survey, the language should be adjusted to clearly frame these as methodological overviews rather than implying the chapter performs these identifications on new data.
- **[writing]** Section 41.3.2 claims intracranial recordings are 'ideally suited' for identifying stimulus-driven activity. This overstates the case by ignoring that sparse, non-random electrode placement makes direct identification in unimplanted regions impossible. The text should clarify that 'identification' in those areas is entirely model-dependent and speculative, not a direct observation.
- **[writing]** The conclusion claims neural insights elucidate cognition 'in ways that behavior alone cannot.' This is a broad generalization unsupported by a specific example in the text where iEEG identified a pattern that behavior failed to explain. A concrete citation or example is needed to avoid overreach regarding the unique explanatory power of these techniques.

## paper_reviewer_safety_ethics — verdict: accept

The manuscript appropriately addresses the critical safety and ethical considerations inherent in intracranial EEG (iEEG) research. The text explicitly acknowledges the clinical context of the data, noting that recordings are obtained from neurosurgical patients (typically with drug-resistant epilepsy) undergoing invasive monitoring for treatment purposes, rather than healthy volunteers (Section "Invasive approaches", lines 230-245). This distinction is vital for establishing the risk-benefit ratio and the necessity of the procedure.

The authors correctly identify that the primary goal of electrode implantation is clinical (localizing seizure foci), and that research participation is secondary and voluntary. The manuscript emphasizes that these procedures are not appropriate for non-patient populations due to the surgical risks involved (lines 246-250). Furthermore, the discussion on the limitations of generalizing findings from this specific patient population (who may have brain abnormalities) to the broader population (Section "Summary and concluding remarks", lines 530-535) demonstrates a responsible approach to interpreting results and avoiding overgeneralization that could mislead clinical understanding.

While the paper is a methodological review and does not present new primary data requiring a specific IRB statement for this specific chapter, the text consistently frames the methodology within the ethical constraints of human subjects research involving invasive procedures. There are no indications of dual-use risks, as the methods described (e.g., GLMs, RSA, hyperalignment) are standard analytical tools for understanding neural coding and do not facilitate the creation of harmful technologies or the manipulation of neural activity in a way that poses immediate safety threats. The discussion of "brain activity" and "stimulus-driven patterns" remains within the bounds of cognitive neuroscience inquiry. No further action items are required regarding safety or ethics.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Summarize sample sizes and key effect sizes from cited foundational studies (e.g., Haxby et al., 2011) to allow readers to assess the robustness of the evidence base without cross-referencing.
- **[science]** Quantify typical ISC effect sizes and subject counts in cited iEEG studies (e.g., MukaEtal05) to validate claims of robustness given the modality's high noise and sparse sampling.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The manuscript describes statistical methods (GLMs, RSA, ISC) but lacks a dedicated section on multiple-comparisons correction. Given the high dimensionality of iEEG data (many electrodes, timepoints, frequencies) and the use of searchlight analyses (Section 41.2.1), the authors must explicitly state how false discovery rates (FDR) or family-wise error rates (FWER) are controlled to prevent spurious findings.
- **[science]** In the description of Representational Similarity Analysis (RSA) and Inter-Subject Correlation (ISC), the text mentions computing correlations but omits details on significance testing. The authors should specify the null models used (e.g., permutation tests, phase randomization) and how p-values or confidence intervals are derived for these correlation matrices, particularly given the temporal autocorrelation inherent in neural time series.
- **[science]** The section on Gaussian Process regression (Section 41.3.2) describes the kernel and interpolation but does not address model selection or uncertainty quantification. The authors should clarify how kernel hyperparameters are optimized and whether the model provides credible intervals for the reconstructed activity, which is critical for interpreting the reliability of the 'superEEG' estimates.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Correct the typo 'absense' to 'absence' in Section 2.1 (Building explicit stimulus models), paragraph 3, where the text reads 'describe the absense, presence, or values'.
- **[writing]** Fix the redundant phrasing 'participant participant' in Section 1.4 (Static versus dynamic measures), paragraph 4, which currently reads 'across repeated presentations to a single participant participant'.
- **[writing]** Remove the extraneous space before the comma in Section 1.2 (How can we measure neural activity), paragraph 2, where the text reads '100 billion glial cells~\citep{AzevEtal09, MotaHerc14} , which also play'.
- **[writing]** Correct the typo 'to procede' to 'to proceed' in Section 2.1, paragraph 4, where the text states 'one must make informed decisions about how to procede based on the sorts of insights'.
- **[writing]** Fix the typo 'taken taken' in Section 3.2 (Hyperalignment and the shared response model), paragraph 3, where the text reads 'intracranial recordings, taken taken as patients watched a movie'.
