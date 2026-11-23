import os
import sys
import json
import re
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_literature_search_results(input_path: Path) -> dict:
    """
    Parses the literature search results text file to extract numeric
    variance and effect size estimates.

    Args:
        input_path: Path to the literature_search_results.txt file.

    Returns:
        A dictionary containing extracted estimates.
    """
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    results = {
        "source_file": str(input_path),
        "variance_estimates": [],
        "effect_size_estimates": [],
        "citations": []
    }

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        raise

    # Regex to capture variance values (e.g., "variance: [0.45, 0.12]")
    variance_pattern = r"variance:\s*\[([^\]]+)\]"
    variance_matches = re.findall(variance_pattern, content)

    for match in variance_matches:
        try:
            # Split by comma, strip whitespace, convert to float
            values = [float(v.strip()) for v in match.split(',')]
            results["variance_estimates"].extend(values)
        except ValueError:
            logger.warning(f"Could not parse variance values from: {match}")

    # Regex to capture effect size d values (e.g., "effect_size_d: [0.78]")
    effect_size_pattern = r"effect_size_d:\s*\[([^\]]+)\]"
    effect_matches = re.findall(effect_size_pattern, content)

    for match in effect_matches:
        try:
            values = [float(v.strip()) for v in match.split(',')]
            results["effect_size_estimates"].extend(values)
        except ValueError:
            logger.warning(f"Could not parse effect size values from: {match}")

    # Extract citations for context
    citation_pattern = r"\[(\d+)\]\s*(.+?)(?=\n\s*\[|\Z)"
    citations = re.findall(citation_pattern, content, re.DOTALL)
    for num, title in citations:
        results["citations"].append({
            "id": num,
            "title": title.strip()
        })

    # Compute aggregated statistics if data exists
    if results["variance_estimates"]:
        import statistics
        results["variance_stats"] = {
            "mean": statistics.mean(results["variance_estimates"]),
            "count": len(results["variance_estimates"])
        }
    else:
        results["variance_stats"] = None

    if results["effect_size_estimates"]:
        import statistics
        results["effect_size_stats"] = {
            "mean": statistics.mean(results["effect_size_estimates"]),
            "count": len(results["effect_size_estimates"])
        }
    else:
        results["effect_size_stats"] = None

    return results

def write_estimates_json(data: dict, output_path: Path) -> None:
    """
    Writes the parsed estimates to a JSON file.

    Args:
        data: The parsed data dictionary.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Successfully wrote estimates to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description="Parse literature search results to extract numeric estimates."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/metrics/literature_search_results.txt",
        help="Path to the literature search results text file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/metrics/literature_estimates.json",
        help="Path to the output JSON file."
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    logger.info(f"Starting parsing of {input_path}")

    try:
        estimates = parse_literature_search_results(input_path)
        write_estimates_json(estimates, output_path)
        logger.info("Parsing completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
