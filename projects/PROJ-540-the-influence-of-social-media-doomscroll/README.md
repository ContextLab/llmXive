# The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Overview
This project investigates the relationship between social media news exposure frequency and anticipatory anxiety using public survey data.

## Project Structure
- `data/`: Raw and processed data
- `code/`: Source code for analysis
- `outputs/`: Generated reports and plots
- `specs/`: Project specifications

## Installation
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`

## Usage
Run the pipeline in order:
1. `python code/ingest.py`
2. `python code/clean.py`
3. `python code/model.py`
4. `python code/robustness.py`
5. `python code/viz.py`
6. `python code/report_generator.py`

## Validation
Run `python code/run_quickstart_validation.py` to verify all outputs.

## License
MIT
