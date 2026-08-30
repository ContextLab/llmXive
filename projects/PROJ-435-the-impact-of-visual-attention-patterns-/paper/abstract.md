# Abstract

## Title
The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

## Background
In the digital age, individuals are increasingly exposed to misleading news headlines. Understanding the cognitive mechanisms underlying susceptibility to such misinformation is critical for developing effective interventions. While previous research has examined the role of cognitive reflection and headline characteristics, the interplay between visual attention patterns and belief formation remains underexplored.

## Objective
This study investigates how visual attention patterns (specifically fixation duration on source attribution vs. headline body) interact with headline valence and cognitive reflection scores to predict belief ratings of potentially misleading headlines. We hypothesize a three-way interaction effect, wherein the relationship between attention and belief is moderated by both valence and cognitive reflection.

## Methods
We analyzed eye-tracking data from a verified dataset (Dundee Eye-Tracking Corpus) using a mixed-effects regression approach. The model included fixation duration, headline valence (calculated using NRC and VADER lexicons), and cognitive reflection scores as predictors, with random intercepts for participants and headlines. We applied Holm-Bonferroni correction to control for family-wise error rate across all fixed effects. Robustness analyses were conducted across multiple fixation thresholds (50ms, 100ms, 150ms) to ensure methodological stability.

## Results
Analysis of the regression model reveals the three-way interaction between source fixation duration, headline valence, and cognitive reflection scores. The causal framing statement, generated from the regression results in `output/causal_framing_statement.txt`, confirms the stability of these effects across methodological variations. Key findings include the moderating role of cognitive reflection in attenuating the influence of visual attention on belief formation, particularly for high-valence misleading content.

## Conclusion
This study provides empirical evidence for the complex interplay between visual attention, emotional content, and cognitive style in belief formation. The findings demonstrate that visual attention patterns alone do not determine susceptibility; rather, the interaction with individual cognitive traits and content valence shapes belief outcomes. These insights have implications for understanding how individuals process potentially misleading information and may inform the design of interventions to reduce susceptibility to misinformation.

## Keywords
visual attention, eye-tracking, misinformation, belief formation, cognitive reflection, mixed-effects regression, fixation duration, headline valence