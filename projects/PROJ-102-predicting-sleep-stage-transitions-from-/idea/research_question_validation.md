## Research-question validation

### Phenomenon-vs-method check

**Verdict**: fail

The question is framed as whether a specific architecture (lightweight deep learning) can work under specific resource constraints (CPU-only), not as a scientific question about sleep or EEG. The answer ("yes, it can classify" or "no, it cannot") evaluates the method, not the neuroscience. The underlying phenomenon question would be about what EEG patterns characterize sleep stage transitions.

### Circularity check

**Verdict**: pass

The predictor (PSD features from single-channel EEG) and the predicted variable (sleep stage labels) are nominally independent. Sleep stage labels are assigned by expert scorers following AASM guidelines based on EEG interpretation, not computed from the same mathematical transformation as the predictor features. This is a standard supervised learning setup.

### Triviality check

**Verdict**: concern

While both positive and null results have deployment implications (can lightweight models work on CPU or not?), the scientific contribution is limited. Either outcome primarily answers "does this architecture work" rather than advancing understanding of sleep neurophysiology. The expected results section confirms this focus on F1-score targets rather than mechanistic insights.

### Question-narrowing check

**Verdict**: fail

The question explicitly names implementation constraints (lightweight architecture, CPU-only, resource constraints) rather than a domain relationship. "Can method M handle X under constraint Y?" is an implementation question masquerading as a neuroscience question. A domain question would ask about what EEG features or neural dynamics characterize sleep stage transitions.

### Overall verdict

**Verdict**: validator_revise

[REVISED]
What EEG features and temporal dynamics best characterize transitions between sleep stages (Wake, REM, N1, N2, N3), and how do these patterns differ across NREM and REM sleep in single-channel scalp recordings?
[/REVISED]
Reframing shifts the focus from method performance to the neuroscience question (what characterizes sleep transitions), allowing the lightweight architecture to remain the implementation choice without making it the research question. The CPU constraint can be preserved as a design requirement without being the scientific contribution.
