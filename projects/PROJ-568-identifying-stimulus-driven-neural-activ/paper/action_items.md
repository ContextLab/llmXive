# Automated-review action items — Identifying stimulus-driven neural activity patterns in multi-patient intracranial recordings

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 1.2.1: The claim that the cortex is 80% mass but 20% neurons cites Herc09. Verify if this specific ratio is explicitly in that paper or if it is a derived statistic requiring clarification.
- **[writing]** Section 1.2.1: The text cites AzevEtal09 for '100 billion glial cells,' but that paper argues for a ~1:1 ratio (~86B each). The '100B' figure contradicts the cited source's main finding. Clarify the numbers.
- **[writing]** Section 1.2.1: Claiming single-neuron responses 'can only be measured using... iEEG and ECoG' is inaccurate. Microelectrode arrays (e.g., Utah arrays) also measure single units invasively but are distinct from standard iEEG/ECoG.
- **[writing]** Section 2.1.2: The RSA description implies Pearson correlation is the standard method. However, KrieEtal08b emphasizes Spearman/Kendall as robust alternatives. Acknowledge this flexibility to align with the source.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption states 'Green shading denotes in vitro methods' and 'Blue shading denotes invasive in vivo methods,' but the figure itself contains no legend or key to map these colors to the specific methods (e.g., Patch clamp, iEEG, ECoG) shown. The reader must infer the color coding solely from the caption text.
- **[science]** Figure 1: The caption explicitly notes 'axes are not drawn to scale,' yet the figure uses a linear grid layout for both spatial and temporal axes. This is misleading because the data spans orders of magnitude (e.g., nanoseconds to decades, angstroms to decimeters); a linear representation distorts the relative resolution differences between methods like Patch clamp and fMRI.
- **[writing]** Figure 2: The caption text for Panel B is incomplete, ending abruptly with 'recording surface' and missing the description for Panels C and D.
- **[writing]** Figure 2: Panels C and D display oscillatory waveforms but lack any caption description or definition of what these signals represent.
- **[science]** Figure 2: The axes in all panels lack tick marks, numerical scales, or units, making it impossible to verify the 'arbitrary units' claim or the temporal resolution.
- **[science]** Figure 5: Panel A's x-axis is labeled 'Time' with ticks 0 and 99, but the caption describes a continuous stimulus without specifying the time unit or scale, making it impossible to assess autocorrelation claims.
- **[science]** Figure 5: Panels B and C show 3D trajectories and heatmaps but lack axis labels for the 3D plot axes and no colorbar/legend mapping grayscale intensity to feature values, despite the caption discussing 'values'.
- **[writing]** Figure 5: The grayscale colorbar in Panel C is present but unlabeled; the caption does not define what the grayscale range (0 to 1) represents, leaving the scale ambiguous.
- **[science]** Figure 6: Panel B displays a dense cloud of multi-colored dots representing 5023 electrodes from 53 patients, but the figure lacks a color legend or key to map specific colors to individual patients, rendering the 'Colors denote different patients' claim unverifiable.
- **[writing]** Figure 6: The caption states 'A. Example patient' and 'B. Across-patient...', but the rendered image lacks explicit 'A' and 'B' labels to distinguish the two rows of panels.
- **[writing]** Figure 7: The caption text is truncated at the end ('C. Interpreting coord'), cutting off the description for Panel C.
- **[science]** Figure 7: Panel C displays images labeled 'Original' and 'Reconstruction' but lacks a corresponding legend entry in the caption to explain what these images represent or how they relate to the geometric models in Panels A and B.
- **[fatal]** Figure 8: The caption text is truncated mid-sentence at the end ('The per-image weig'), preventing the reader from understanding the description of Panel B.
- **[science]** Figure 8: Panel A contains a raw LaTeX formatting artifact ('$$s') in the caption instead of the intended symbol (likely 'x' or 'x_s'), making the reference to factor centers illegible.
- **[science]** Figure 8: Panel A displays a color heatmap but lacks a colorbar or scale, making it impossible to interpret the magnitude of the 'spherical factors' or 'radial basis functions' shown.
- **[fatal]** Figure 9: The rendered image displays panels labeled A through E (Electrode locations, RBF interpolation, Correlation matrices, Merged model, Observed activity), but the provided caption describes a completely different figure (Building across-patient models using Gaussian process regression) with panels A and B only. The visual content and text are mismatched.
- **[science]** Figure 9: The rendered image lacks a colorbar or legend to interpret the 'Location' heatmaps in Panels B, C, and D, making the intensity values and correlation strengths illegible.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'GLM' (Generalized Linear Models) and 'MVPA' (Multivariate Pattern Analysis) at their first occurrence in Section 41.1.1. While the full terms are used initially, the acronyms appear frequently thereafter; ensure the first instance explicitly states 'Generalized Linear Models (GLMs)' and 'Multivariate Pattern Analysis (MVPA)' to aid non-specialist readers."
- **[writing]** Replace the term 'procrustean transformation' in Section 41.2.1 with 'Procrustes analysis' or provide a brief parenthetical explanation (e.g., 'a geometric alignment method') upon first use. The current phrasing assumes familiarity with a specific statistical term that may exclude readers from adjacent fields."
- **[writing]** In Section 41.1.2, define 'LFP' (Local Field Potentials) immediately after the first mention. The text introduces 'Local field potentials (LFPs)' but later uses 'LFPs' and 'LFP' interchangeably without re-establishing the acronym for readers who may have skipped the initial definition."
- **[writing]** In Section 41.2.1, clarify 'ISC' and 'ISFC' (Inter-subject correlation and Inter-subject functional correlation) at first use. The text introduces the full terms but relies heavily on the acronyms in subsequent sentences; ensure the expansion is clear and the acronym is explicitly defined for the first time."
- **[writing]** In Section 41.1.1, replace 'timeseries' with 'time series' (two words) for consistency with standard English usage, or define it as a specific technical term if the single-word form is intended as a distinct jargon. The current usage varies and may confuse non-specialists."

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 2.1 defines 'brain activity' to include glial metabolism but later reviews methods (GLMs, RSA) that only measure neuronal signals. Clarify if the methods are insufficient for the defined scope or if the definition should be narrowed to 'neural activity' to maintain logical consistency.
- **[science]** Section 3.1.3 claims joint models are 'most accurate' because truth lies 'between' stimulus and neural trajectories. This assumes a linear intermediate without proving why the true representation isn't a non-linear transform of one or the other. Provide a mechanism for this assumption.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The abstract and introduction list numerous specific modeling approaches (GLMs, MVPA, RSA, etc.) as if the chapter presents novel applications or comparative results. However, the text is a methodological review. The language should be adjusted to clearly frame these as 'reviewed approaches' rather than implying the chapter itself performs these analyses on new data.
- **[writing]** In Section 3.2.2, the text states that RSA 'can sometimes be a more sensitive way' than GLMs/MVPA. This is a strong comparative claim. The text should explicitly cite the specific literature demonstrating this sensitivity advantage in the context of noisy iEEG data, rather than presenting it as a general, unqualified fact.
- **[writing]** The conclusion states the field is 'decades away' from linking neural and stimulus features at high levels of detail. While a reasonable opinion, this specific temporal prediction ('decades') is an extrapolation not supported by the data or analysis presented in the chapter. This should be softened to reflect it as a current challenge rather than a fixed timeline.

## paper_reviewer_safety_ethics — verdict: accept

The manuscript is a methodological survey chapter rather than an empirical study reporting new human data collection. Consequently, it does not present primary IRB/IACUC concerns, as the authors are synthesizing existing literature and describing established analytical frameworks (e.g., GLMs, RSA, Hyperalignment) rather than detailing a specific new experimental protocol involving human subjects.

The text appropriately contextualizes the ethical and clinical constraints of intracranial EEG (iEEG) research. Specifically, the "Invasive approaches" section (lines 230–255) correctly identifies that such recordings are restricted to neurosurgical patients (typically with drug-resistant epilepsy) and emphasizes that electrode placement is driven by clinical necessity, not research goals. The manuscript explicitly notes the limitations this imposes on generalizability and the inherent risks of the procedure, satisfying the requirement to acknowledge the vulnerable nature of the study population.

Regarding data privacy and consent, the paper discusses the use of "multi-patient" data and "across-participant" models (Section 4.2) but does not present raw patient data or specific datasets that would require a new consent review. The references to external datasets (e.g., citing \cite{EzzyEtal17}, \cite{SedeEtal03}) imply that the original studies adhered to necessary ethical standards. The manuscript does not propose any dual-use applications (e.g., neural decoding for non-consensual surveillance or mind-reading) that would raise safety alarms; the described technologies (decoding speech, identifying stimulus categories) are standard in cognitive neuroscience and are framed within the context of understanding brain function and potential clinical applications like brain-computer interfaces.

No conflicts of interest are apparent in the text provided. The discussion of "Human-in-the-loop" techniques and automated modeling (Section 3.2) is methodological and does not suggest the deployment of these systems in high-stakes, unregulated environments. The review concludes that the manuscript adheres to standard ethical norms for a review chapter in this field.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The manuscript is a methodological survey and does not present primary empirical data, sample sizes, or statistical tests. Consequently, standard evidence metrics (power, effect sizes, p-values) are not applicable to the text itself. However, the review of external literature lacks a systematic search strategy or inclusion criteria, making the evidence base for the claimed "comprehensive" overview difficult to verify or replicate.
- **[science]** Several methodological claims regarding the superiority or specific utility of techniques like HTFA or Gaussian Process models (e.g., Section 4.2) rely on citations to external studies (e.g., Owen et al., 2020) without summarizing the sample sizes, patient heterogeneity, or statistical robustness of those foundational studies. The review should briefly contextualize the evidence strength of the cited works to support the recommendations.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The manuscript describes statistical methods (GLMs, RSA, ISC) but lacks a dedicated section on multiple-comparisons correction. Given the high dimensionality of intracranial data (thousands of electrodes/timepoints) and the use of searchlight analyses, the authors must explicitly state how false discovery rates (FDR) or family-wise error rates (FWER) are controlled to prevent spurious findings.
- **[science]** In the description of Representational Similarity Analysis (RSA) and Inter-Subject Correlation (ISC), the text mentions computing correlations between matrices or time series but omits details on significance testing. The authors should specify the permutation strategies or null models used to generate p-values and confidence intervals for these correlation coefficients.
- **[science]** The section on Gaussian Process regression (SuperEEG) describes the kernel and interpolation but does not address model validation. The authors should clarify how hyperparameters (e.g., length scales) are selected and whether cross-validation or out-of-sample testing was used to prevent overfitting when reconstructing full-brain activity from sparse electrodes.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Correct the typo 'absense' to 'absence' in Section 2.1 (Building explicit stimulus models), paragraph 3, where the text describes multivariate real-valued feature vectors.
- **[writing]** Fix the grammatical error 'a the M-dimensional' to 'the M-dimensional' in Section 3.1.1 (Generalized linear models), where the GLM equation variables are defined.
- **[writing]** Remove the redundant word 'participant' in Section 1.4 (Static versus dynamic measures), where the text reads 'across repeated presentations to a single participant participant'.
- **[writing]** Correct the typo 'drug-resistent' to 'drug-resistant' in the Summary section (Section 5), where the text discusses the limitations of the subject population.
- **[writing]** Fix the typo 'procede' to 'proceed' in Section 2.1, paragraph 4, where the text discusses making informed decisions based on prior work.
