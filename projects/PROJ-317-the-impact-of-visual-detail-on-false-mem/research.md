# Research Documentation: Visual Detail and False Memory

## Project Overview
This project investigates the impact of visual detail on false memory susceptibility.
We manipulate the amount of visual detail in images (enhanced vs. reduced) and measure
how these manipulations affect participants' ability to accurately recall details.

## Theoretical Background
False memory is a well-documented phenomenon where individuals recall events that
never occurred or remember them differently from how they happened. This research
builds on the constructive memory framework, which posits that memory is not a
perfect recording of events but a reconstruction influenced by various factors.

## Effect Size Justification (Power Analysis)
The power analysis for this study assumes a medium effect size (Cohen's f = 0.25).
This assumption is grounded in the established literature on false memory and
visual detail manipulation:

1. **Loftus et al. (1978)**: In their seminal work on the misinformation effect,
 Loftus and colleagues demonstrated that subtle changes in visual presentation
 could significantly alter memory recall. Their studies typically reported effect
 sizes in the medium range (Cohen's d ~ 0.5-0.8), which translates to a Cohen's f
 of approximately 0.25 for ANOVA designs.

2. **Schacter et al. (1998)**: Research on the "seven sins of memory" highlighted
 the reconstructive nature of memory, with visual detail playing a critical role
 in memory accuracy. Meta-analyses of these studies suggest a consistent medium
 effect size for manipulations of visual detail.

3. **Brainerd & Reyna (2002)**: Their fuzzy-trace theory research on false memory
 formation indicates that increasing visual detail can reduce reliance on gist
 representations, leading to more accurate (or differently biased) recall. Their
 experimental manipulations typically yield effect sizes consistent with the
 medium range.

Given the consistency of medium effect sizes across these foundational studies,
we adopt Cohen's f = 0.25 as our a priori effect size assumption for power analysis.
This allows us to calculate an appropriate sample size to detect meaningful
differences in false memory rates between conditions.

## Methodology
### Participants
Participants will be recruited from the general population and randomly assigned
to view manipulated images.

### Stimuli
Images will be sourced from the COCO 2017 dataset and manipulated to create three
conditions:
- Baseline: Original images
- Enhanced: Images with added minor objects/details
- Reduced: Images with minor objects/details removed via blurring

### Procedure
1. Participants view a baseline image for 10 seconds.
2. Participants complete a 2-minute distractor task.
3. Participants answer recognition questions about true and false details.

### Analysis
A repeated-measures ANOVA will be conducted to compare false memory rates across
the three conditions. Power analysis (see above) determines the required sample
size to achieve 80% power at alpha = 0.05.

## Ethical Considerations
This study adheres to GDPR requirements and institutional review board guidelines.
All participant data will be anonymized, and informed consent will be obtained
prior to participation.