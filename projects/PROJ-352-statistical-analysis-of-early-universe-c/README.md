# Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

## Overview

This project implements a pipeline for analyzing Cosmic Microwave Background (CMB)
temperature maps from the Planck satellite to search for signatures of topological defects.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Download Planck CMB map:
 ```bash
 python code/download.py
 ```

2. Apply Galactic mask:
 ```bash
 python code/mask.py
 ```

3. Compute Minkowski Functionals:
 ```bash
 python code/minkowski.py
 ```

4. Run statistical analysis:
 ```bash
 python code/statistics.py
 ```

## Project Structure

```
.
├── code/ # Source code
├── data/ # Data directories
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed data
├── tests/ # Unit tests
├── output/ # Final results
└── docs/ # Documentation
```

## License

MIT License
