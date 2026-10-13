# Investigating the Impact of Network Structure on Neural Avalanche Dynamics

This project examines how anatomical brain network properties (node degree,
clustering coefficient, rich-club coefficient derived from diffusion-MRI
structural connectomes) relate to neural avalanche statistics (size, duration,
power-law exponents) measured from human resting-state EEG.

## Research question

How do anatomical brain network properties relate to neural avalanche
dynamics measured from human resting-state EEG?

## Project layout

```text
code/ # all pipeline source code
 data/ # download, preprocessing (dMRI, EEG), quality control, store
 analysis/ # network metrics, avalanche detection, fitting, stats, report
 utils/ # shared utilities (logging, seeds)
tests/ # unit and integration tests (pytest)
data/
 raw/ # untouched downloaded data +.checksums.json
 processed/ # connectomes, cleaned EEG, routing state, QC outputs
 results/ # metrics, correlation results, reports
 figures/ # generated plots
specs/ # specification, plan, data model, quickstart, contracts
```

## Quickstart

See `specs/001-investigating-the-impact-of-network-stru/quickstart.md` for
full installation and run instructions (Python 3.11, MRtrix3, MNE-Python).

To initialise the directory layout and the empty checksum manifest:

```bash
python code/setup_project_layout.py
```

## Data sources

- dMRI: OpenNeuro `ds004230` (HCP-Aging)
- EEG: OpenNeuro `ds004231`
- Parcellation: HCP-MMP1.0 (Glasser et al. 2016)

Only real, publicly available data are used; no synthetic stand-ins.

## License / status

Research pipeline under active development (llmXive automated science
pipeline, feature branch `001-network-structure-avalanche-dynamics`).
