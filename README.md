# Experimental Dataset for Lagrangian Particle Tracking Validation in Open-Channel Flow

This repository contains raw videos, processed particle trajectories, velocity data, and Python post-processing scripts for laboratory experiments of floating particle transport in an open-channel flow.

The dataset is intended for validation of Lagrangian Particle Tracking (LPT) and Particle Tracking Velocimetry (PTV) workflows.

## Contents

- `Experiment1/`: videos and processed data for the first experimental geometry.
- `Experiment2/`: videos and processed data for the second experimental geometry.
- `Geometry_Experiment1.pdf`: schematic of Experiment 1.
- `Geometry_Experiment2.pdf`: schematic of Experiment 2.
- `Example_trajectories.gif`: example visualization of tracked particles.

Each experiment folder contains:

- `raw_videos/`: original recorded videos.
- `processed_trajectories/`: particle detections and linked trajectories.
- `processed_results/`: velocities, initial particle positions, and visualizations.
- `ptv_pipeline/`: Python modules used for post-processing.
- `main.py`: main processing script.
- `visualize.py`: visualization script.
- `select_obstacles.py`: interactive obstacle-mask selection script.
- `config.py`: experiment-specific processing parameters.
- `requirements.txt`: Python dependencies.
- `README_PTV.md`: detailed processing instructions.

## Experimental Conditions

The videos were recorded at 60 Hz. The spatial calibration used for the processed data is 5.5 px/mm. Thus, 1 px = 0.181818 mm.

Floating particles were segmented using HSV color thresholds. Fixed obstacles and reflective regions were removed using polygon masks when required. Particle centroids were detected from cleaned binary masks and linked between frames to obtain trajectories and velocities.

## Data Products

The main processed CSV files are:

- *_detections.csv: particle centroids detected in each frame.
- *_trajectories.csv: linked particle trajectories with particle IDs.
- *_velocities.csv: instantaneous and smoothed particle velocities.
- *_initial_positions.csv: first tracked position of each particle.

Coordinates are provided in pixels and, where applicable, in millimetres.

## Reproducing the Post-Processing

Create a Python environment and install dependencies:

```bash
pip install -r requirements.txt
```

The pipeline requires ffmpeg and ffprobe to be available on the system path.

Example:

```bash
cd Experiment1
python3 main.py --cases case1 --frame-start 200 --frame-end 300 --stages segment detect track velocities --overwrite
```

See each experiment's README_PTV.md for the exact commands used to generate the included processed results.

## License

This dataset is released under the Creative Commons Attribution 4.0 International License (CC-BY-4.0). See LICENSE.

## Citation

If you use this dataset, please cite the Zenodo record associated with this repository.

## Contact

For questions about the dataset or processing workflow, contact:

Pablo Vallés
University of Zaragoza
pvalles@unizar.es

Jose Segovia-Burillo
University of Zaragoza
jsegovia@unizar.es

Sergio Martínez-Aranda
University of Zaragoza
sermar@unizar.es

Mario Morales-Hernández
University of Zaragoza
mmorales@unizar.es

Pilar García-Navarro
University of Zaragoza
pigar@unizar.es
