# Quickstart: Automated Detection of Algorithmic Bias in Public Code Repositories

## Prerequisites

*   Python 3.11
*   `pip` package manager

## Installation

1.  Clone the repository:

    ```bash
    git clone [repository URL]
    cd [repository directory]
    ```

2.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Run the main script:

    ```bash
    python src/cli/main.py --repo-list [list of repository URLs] --output-dir [output directory]
    ```

    Replace `[list of repository URLs]` with a text file containing a list of repository URLs, one per line. Replace `[output directory]` with the desired output directory.

2.  Analyze the results:

    The output directory will contain the following files:

    *   `repositories.csv`: A CSV file containing information about the analyzed repositories.
    *   `textual_artifacts.csv`: A CSV file containing the extracted textual artifacts and their bias scores.
    *   `correlation_results.csv`: A CSV file containing the correlation results.

## Configuration

The script can be configured using command-line arguments:

*   `--repo-list`: Path to a text file containing a list of repository URLs.
*   `--output-dir`: Path to the output directory.
*   `--num-repositories`: Number of repositories to analyze.
*   `--injected-skew-magnitude`: Magnitude of bias to inject in the synthetic data.

## Example

```bash
python src/cli/main.py --repo-list repo_list.txt --output-dir results --num-repositories 10 --injected-skew-magnitude 0.1
```
