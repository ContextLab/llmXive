# The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

This project implements a pipeline to investigate how visual salience biases moral decision-making using the Moral Machine dataset and an augmented drift-diffusion model (aDDM).

## Project Structure

- `code/`: Source code for data processing, modeling, and analysis
- `data/`: Raw and processed data artifacts
- `tests/`: Unit and contract tests
- `paper/`: Generated reports and analysis artifacts
- `specs/`: Feature specifications and design documents

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Run the pipeline:
 ```bash
 python code/main.py --stage download
 python code/main.py --stage salience
 python code/main.py --stage fit
 python code/main.py --stage compare
 ```

## License

This project is for research purposes only.
