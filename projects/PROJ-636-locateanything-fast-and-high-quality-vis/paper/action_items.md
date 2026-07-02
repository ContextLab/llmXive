# Automated-review action items — LocateAnything: Fast and High-Quality Vision-Language Grounding with Parallel Box Decoding

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 2.4 claims '138M queries' and '14.2% rejection rate' on 'All 138M samples'. This implies 138M is the pre-rejection count, yet the final dataset is stated as 138M. Clarify if 138M is pre- or post-verification to resolve the mathematical contradiction.
- **[writing]** Table 1 sums to ~139.3M queries, contradicting the text's '138M' claim. Additionally, Section 3.2 cites '76.8' and '70.1' F1 for DocLayNet/M6Doc, while Table 2 reports '77.7' and '70.5'. Align text values with table data.
- **[writing]** Section 3.2 claims '10x faster than Qwen3-VL (1.1 BPS)', but no table or citation supports the 1.1 BPS figure for Qwen3-VL. Table 3 only lists Qwen2.5-VL. Provide the source for the 1.1 BPS baseline or update the comparison table.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a grammatical error and likely typo: 'predicts points representing geometric units (, bounding box corners)' includes a dangling comma and missing word before the parenthesis.
- **[writing]** Figure 1: The caption states 'coordinate tokens in the bottom panel are rendered at high resolution to ensure legibility at print scale,' but the bottom panel is a schematic diagram, not a print-scale rendering of the actual model output.
- **[science]** Figure 2: The 'Generic Multi-Token Prediction' row shows a sequence of tokens (e.g., <911>, <832>) that are not explicitly defined as coordinate values in the caption, creating ambiguity about whether they represent coordinates or other data. The caption mentions 'irregular distributions' but the visual representation does not clearly illustrate this concept.
- **[writing]** Figure 2: The scissors icons and warning symbols lack explicit definitions in the caption or legend, making their meaning unclear to readers unfamiliar with the context.
- **[science]** Figure 4: The 'Spatial Ambiguity' panel shows the model discarding the erroneous block '<121>' and reverting to NTP to predict '<647>', yet the diagram visually depicts the model *accepting* the erroneous block '<121>' (highlighted with a cursor icon) before the correction arrow appears. This contradicts the caption's claim that the model 'discards the erroneous block' and misrepresents the re-decoding mechanism.
- **[writing]** Figure 4: The legend in the top-right corner ('Correct'/'Wrong') is not explicitly referenced in the caption or figure labels, making it ambiguous whether the red boxes represent 'Wrong' predictions or simply 'Format Irregularity'/'Spatial Ambiguity' states.
- **[science]** Figure 5: The bottom panel's 'Detection' category lists 'NuImages (382.1K)' and 'MOT17DET (5.3K)', but the pie chart for 'LocateAnything-Data-Queries' (138M) shows Detection at 66.9% (93M). The sum of the listed datasets (93M) matches the total, but the breakdown includes datasets like 'NuImages' which are typically video-based, raising questions about the 'unique images' count in the rightmost pie chart (12M) versus the query count.
- **[writing]** Figure 5: The legend for 'Pointing' (3M, 2.2%) is cut off at the bottom of the image, making it impossible to see the full list of contributing datasets (only 'Object365', 'OpenImages', 'PixmoPoints', 'RoboAfford' are visible, but the row is truncated).
- **[writing]** Figure 5: The legend row for 'Pointing' is partially cut off at the bottom edge of the image, truncating the list of source datasets.
- **[science]** Figure 5: The 'LocateAnything-Data-Images' pie chart indicates 12M unique images, yet the 'Detection' query breakdown lists datasets like NuImages (382.1K) and MOT17DET (5.3K) which are video-centric; the caption does not clarify how video frames are aggregated into 'unique images' or if the 12M count excludes these sources.
- **[science]** Figure 6: The right panel's legend defines 'Textual (BPS)', 'Quantized (BPS)', and 'Parallel (BPS)' as line plots, but the chart only displays lines for 'Textual' and 'Quantized'. The 'Parallel' throughput line is missing, despite the caption claiming a comparison of all three methods.
- **[writing]** Figure 6: The right panel's right y-axis label reads 'Throughput+, BPS (Box per Second)'. The '+' symbol appears to be a typo or rendering artifact and should be removed for clarity.
- **[writing]** Figure 7: The caption lists four query categories (MyRedattribute, MyBluepart, MyOrangereasoning, MyGreenspatial) corresponding to the box colors, but the figure lacks a visual legend or key to map these specific names to the colors, forcing the reader to guess the mapping.
- **[writing]** Figure 7: The text labels below each image (e.g., 'yellow leaves scattered among the purple leaves') are not explicitly defined as the 'free-form textual queries' mentioned in the caption, creating ambiguity about whether these are the inputs or just descriptions.
- **[writing]** Figure 8: The caption text is truncated at the end ('produce bo'), cutting off the description of the final output (likely 'bounding boxes').
- **[writing]** Figure 8: The top-left label contains a typo, spelling 'Category' as 'Categroy'.
- **[writing]** Figure 8: The bottom-middle query box contains a typo, spelling 'center' as 'centerx'.
- **[science]** Figure 9: The legend defines six task categories (Detection, GUI, Referring, OCR, Layout, Pointing), but the x-axis groups (e.g., 10-20, 20-30) show missing bars for several categories (e.g., GUI, Layout, Pointing) without explanation in the caption or visual indication (e.g., zero-height bars) of their absence.
- **[writing]** Figure 9: The x-axis label 'Bbox/Point Count' contradicts the caption's description ('number of targets per query'); clarify whether the axis represents targets, boxes, or points to ensure consistency.
- **[science]** Figure 10: The 'LocateAnything' column (right) shows a failure in the third row (trees) where the model produces fragmented, overlapping boxes for 'bare trees' instead of a single coherent region, contradicting the caption's claim of 'superior compositional grounding capabilities'.
- **[writing]** Figure 10: The text labels inside the bounding boxes (e.g., 'black helmet with TCU logo', 'man wearing glasses') are rendered at a resolution that makes them illegible in the provided image, hindering verification of the specific queries being tested.
- **[writing]** Figure 11: The rendered image displays a 'Dense Object Detection' title and a 'Ground Truth' column, but the caption describes it as a 'Qualitative comparison on Dense Object Detection (DOD)' without explicitly mentioning the inclusion of ground truth labels or the specific column layout.
- **[science]** Figure 11: The 'Ground Truth' column shows red bounding boxes, but the caption does not define this color coding, potentially causing confusion with the 'LocateAnything' column which uses blue boxes.
- **[writing]** Figure 12: The column headers 'Qwen3-VL', 'Rex-Omni', and 'LocateAnything' are not defined in the caption; the caption only mentions 'baseline models' without specifying which are which.
- **[science]** Figure 12: The 'Ground Truth' column displays bounding boxes that are not perfectly tight around text elements (e.g., the 'GURGEL' logo boxes include significant whitespace), which contradicts the caption's claim that LocateAnything yields 'tightly bounded boxes' compared to baselines.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized acronyms and coined terms that hinder accessibility for a broader audience. In the Introduction, the terms MTP and NTP are used immediately without definition. While "Multi-Token Prediction" and "Next-Token Prediction" are standard in the field, they must be spelled out at first use (e.g., "Multi-Token Prediction (MTP)") to comply with general readability standards. Similarly, IoU appears in the Abstract and Section 4 without expansion; "Intersection

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim of '138M unique images' in the Abstract contradicts Section 2.4 (LocateAnything-Data) which states '12M unique images'. This internal inconsistency regarding the dataset scale must be resolved.
- **[writing]** The fallback mechanism in Section 3.3 specifies a threshold of 'max-min difference > 80' in [0, 1000] space, but the text does not explain the causal link between this specific value and 'unreliability' or 'format violations'. The logic for this heuristic is missing.
- **[writing]** Table 1 (e000) reports LocateAnything-3B throughput as 12.7 BPS, while Table 2 (e001) and the text in Section 4.2 report Hybrid Mode throughput as 12.7 BPS but Fast Mode as 16.9 BPS (Table 3). The main text claims '12.7 BPS (Hybrid)' is 'over 10x faster than Qwen3-VL (1.1 BPS)', but the ablation table shows PBD (Fast) at 16.9 BPS. The paper conflates the 'Hybrid' throughput with the 'Fast' potential in the narrative, obscuring the actual speed gain of the proposed method.

## paper_reviewer_overreach — verdict: full_revision

- **[science]** The paper makes several claims that extend beyond the immediate evidence provided in the text and tables, particularly regarding the magnitude of speed improvements, the statistical validity of dataset quality assertions, and the definition of "State-of-the-Art" performance. First, the Introduction claims the method achieves "up to 2.5x higher decoding throughput." While Table 1 shows a 2.54x improvement over Rex-Omni (12.7 vs 5.0 BPS), the same table shows an 11.5x improvement over Qwen3-VL (12

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript presents a significant technical contribution to vision-language grounding but requires clarification on data safety and ethical sourcing before acceptance. Data Provenance and Synthetic Bias: The core of the training data, "LocateAnything-Data," is largely synthetic, generated by Qwen3-VL and SAM 3 (Appendix: "LocateAnything-Data Construction"). While the authors report a 99.4% agreement rate on a 500-sample spot-check, this sample size is statistically insufficient to guarantee

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The claim of 138M training samples with a 14.2% rejection rate and 99.4% spot-check agreement (Abstract) lacks statistical rigor. The paper must report the confidence interval for the 99.4% agreement metric (n=500) and clarify the rejection criteria. Without this, the data quality claim is unsubstantiated.
- **[science]** The throughput comparison (12.7 BPS vs 1.1 BPS) is potentially confounded by hardware and implementation differences. The paper must explicitly state the hardware (GPU model, count, memory) and software stack (framework version, precision) used for all baselines to ensure a fair speed comparison.
- **[science]** The ablation study (Table 3) shows PBD (Fast) has lower F1 (49.6) than PBD (Slow) (52.1) but claims a 2.5x speedup. The paper must provide a detailed breakdown of the fallback frequency in Hybrid mode and the specific cost of the fallback mechanism to validate the "optimal" trade-off claim.
- **[science]** The dataset statistics table (Table 2) lists 138M queries but the validation set is also listed as 138M queries, which is logically inconsistent for a standard train/val split. The authors must clarify the data split strategy and correct the reported numbers to avoid confusion about the actual training volume.

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The manuscript presents a novel Parallel Box Decoding (PBD) approach but lacks rigorous statistical validation for its core empirical claims. First, the data quality assertions in the Abstract are statistically unsupported. The claim of a "14.2% rejection rate" across 138M samples and "99.4% agreement" on a 500-sample spot-check lacks necessary statistical context. The authors must report the confidence interval for the 99.4% agreement rate (which, for n=500, is approximately ±1.3% at 95% confid

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Correct the typo 'categroy' to 'category' in the caption of Figure 2 (e001) and the corresponding label reference.
- **[writing]** Resolve the inconsistency in dataset statistics: The abstract and Section 2.4 state 138M queries, while Table 1 (e001) lists 138M queries but Table 2 (e001) lists 138M for both training and validation, implying a total of 276M or a duplication error. Clarify the exact split.
- **[writing]** Fix the grammatical error in Table 3 (e001) caption: 'The results of the *Hybrid Mode* are reported here' should be 'The results of the *Hybrid Mode* are reported herein' or rephrased for better flow.
- **[writing]** Standardize the capitalization of 'Boxes Per Second' in the text (e.g., Section 3.2) versus 'BPS' in table headers to ensure consistent terminology throughout the manuscript.
