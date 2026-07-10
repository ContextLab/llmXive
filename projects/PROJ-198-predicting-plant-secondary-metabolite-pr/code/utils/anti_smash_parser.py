"""
antiSMASH JSON Parser for Plant Secondary Metabolite Prediction Pipeline.

This module handles the parsing of antiSMASH output (JSON format) to extract
Biosynthetic Gene Cluster (BGC) information. It supports both real antiSMASH
output files and mock data for CI environments.

Key functionalities:
- Parse antiSMASH JSON structure (v7+ format)
- Extract BGC counts per species
- Extract BGC type classifications
- Handle missing or malformed data gracefully
- Support mock data loading for CI testing
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for antiSMASH JSON structure
ANTIMASH_RESULTS_KEY = "results"
ANTIMASH_BGC_KEY = "biosynthetic_clusters"
ANTIMASH_GENOME_KEY = "genome"
ANTIMASH_ORIGINAL_FILENAME_KEY = "original_filename"
ANTIMASH_CLUSTER_TYPE_KEY = "cluster_type"
ANTIMASH_PREDICTED_TYPE_KEY = "predicted_cluster_types"
ANTIMASH_COMPOUND_CLASSES_KEY = "compound_classes"

# Mock data keys for CI mode
MOCK_DATA_KEY = "mock_bgc_data"


def parse_anti_smash_json(json_path: str) -> Dict[str, Any]:
    """
    Parse an antiSMASH JSON output file.

    Args:
        json_path: Path to the antiSMASH JSON file.

    Returns:
        Dictionary containing parsed BGC data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"antiSMASH JSON file not found: {json_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_path}: {e}")
        raise

    return data


def extract_bgc_summary(data: Dict[str, Any]) -> Dict[str, Dict[str, Union[int, List[str]]]]:
    """
    Extract BGC summary from parsed antiSMASH data.

    Handles both real antiSMASH output and mock data structures.

    Args:
        data: Parsed JSON data from antiSMASH output.

    Returns:
        Dictionary mapping species/genome names to BGC statistics:
        {
            "species_name": {
                "total_count": int,
                "types": List[str],
                "clusters": List[Dict]
            }
        }
    """
    summary = {}

    # Handle mock data format for CI
    if MOCK_DATA_KEY in data:
        logger.info("Detected mock data format, processing accordingly.")
        mock_entries = data[MOCK_DATA_KEY]
        for entry in mock_entries:
            genome_name = entry.get("genome_name", "unknown_genome")
            clusters = entry.get("clusters", [])

            if genome_name not in summary:
                summary[genome_name] = {
                    "total_count": 0,
                    "types": [],
                    "clusters": []
                }

            summary[genome_name]["total_count"] = len(clusters)
            types = set()
            for cluster in clusters:
                cluster_type = cluster.get("type", "unknown")
                types.add(cluster_type)
                summary[genome_name]["clusters"].append(cluster)

            summary[genome_name]["types"] = sorted(list(types))
        return summary

    # Handle real antiSMASH output format
    if ANTIMASH_RESULTS_KEY not in data:
        logger.warning(f"No '{ANTIMASH_RESULTS_KEY}' key found in JSON. Assuming empty BGC data.")
        return {}

    results = data[ANTIMASH_RESULTS_KEY]

    for genome_id, genome_data in results.items():
        # Extract genome name from original filename if available
        genome_name = genome_data.get(ANTIMASH_ORIGINAL_FILENAME_KEY, genome_id)
        # Clean the name (remove extensions)
        if genome_name.endswith('.fa') or genome_name.endswith('.fna'):
            genome_name = Path(genome_name).stem

        if ANTIMASH_BGC_KEY not in genome_data:
            logger.debug(f"No BGCs found for genome: {genome_name}")
            summary[genome_name] = {
                "total_count": 0,
                "types": [],
                "clusters": []
            }
            continue

        clusters = genome_data[ANTIMASH_BGC_KEY]
        if not clusters:
            summary[genome_name] = {
                "total_count": 0,
                "types": [],
                "clusters": []
            }
            continue

        types = set()
        cluster_list = []

        for cluster in clusters:
            # Extract primary type
            cluster_type = cluster.get(ANTIMASH_CLUSTER_TYPE_KEY, "unknown")
            types.add(cluster_type)

            # Also capture predicted types if available
            predicted_types = cluster.get(ANTIMASH_PREDICTED_TYPE_KEY, [])
            if isinstance(predicted_types, list):
                types.update(predicted_types)

            cluster_list.append({
                "id": cluster.get("id", "unknown_id"),
                "type": cluster_type,
                "compound_classes": cluster.get(ANTIMASH_COMPOUND_CLASSES_KEY, [])
            })

        summary[genome_name] = {
            "total_count": len(clusters),
            "types": sorted(list(types)),
            "clusters": cluster_list
        }

    return summary


def bgc_summary_to_dataframe(summary: Dict[str, Dict]) -> pd.DataFrame:
    """
    Convert BGC summary dictionary to a pandas DataFrame.

    Args:
        summary: BGC summary dictionary from extract_bgc_summary().

    Returns:
        DataFrame with columns: ['species', 'bgc_count', 'bgc_types']
        where bgc_types is a comma-separated string of types.
    """
    if not summary:
        return pd.DataFrame(columns=['species', 'bgc_count', 'bgc_types'])

    records = []
    for species, data in summary.items():
        records.append({
            'species': species,
            'bgc_count': data['total_count'],
            'bgc_types': ','.join(data['types']) if data['types'] else 'none'
        })

    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values('species').reset_index(drop=True)
    return df


def get_bgc_counts_by_type(summary: Dict[str, Dict]) -> pd.DataFrame:
    """
    Get BGC counts aggregated by type across all species.

    Args:
        summary: BGC summary dictionary.

    Returns:
        DataFrame with columns: ['bgc_type', 'count', 'species_present']
    """
    type_counts = {}
    type_species = {}

    for species, data in summary.items():
        for bgc_type in data['types']:
            if bgc_type not in type_counts:
                type_counts[bgc_type] = 0
                type_species[bgc_type] = set()
            type_counts[bgc_type] += 1
            type_species[bgc_type].add(species)

    if not type_counts:
        return pd.DataFrame(columns=['bgc_type', 'count', 'species_present'])

    records = [
        {
            'bgc_type': bgc_type,
            'count': count,
            'species_present': ','.join(sorted(list(sps)))
        }
        for bgc_type, count in type_counts.items()
    ]

    df = pd.DataFrame(records)
    return df.sort_values('count', ascending=False).reset_index(drop=True)


def parse_anti_smash_directory(directory_path: str) -> Dict[str, Any]:
    """
    Parse all antiSMASH JSON files in a directory.

    Args:
        directory_path: Path to directory containing antiSMASH JSON files.

    Returns:
        Combined BGC summary dictionary for all files.
    """
    dir_path = Path(directory_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory_path}")

    combined_summary = {}
    json_files = list(dir_path.glob("*.json"))

    if not json_files:
        logger.warning(f"No JSON files found in {directory_path}")
        return combined_summary

    logger.info(f"Found {len(json_files)} JSON files in {directory_path}")

    for json_file in json_files:
        try:
            logger.info(f"Processing: {json_file.name}")
            data = parse_anti_smash_json(str(json_file))
            file_summary = extract_bgc_summary(data)
            # Merge into combined summary (species names must be unique)
            for species, stats in file_summary.items():
                if species in combined_summary:
                    logger.warning(f"Duplicate species found: {species}. Merging counts.")
                    combined_summary[species]["total_count"] += stats["total_count"]
                    combined_summary[species]["types"] = sorted(list(set(
                        combined_summary[species]["types"] + stats["types"]
                    )))
                    combined_summary[species]["clusters"].extend(stats["clusters"])
                else:
                    combined_summary[species] = stats
        except Exception as e:
            logger.error(f"Error processing {json_file.name}: {e}")
            continue

    return combined_summary


def main():
    """
    Main entry point for standalone execution.
    Parses a provided JSON file or directory and prints summary statistics.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse antiSMASH JSON output and extract BGC statistics."
    )
    parser.add_argument(
        "input_path",
        help="Path to antiSMASH JSON file or directory containing JSON files."
    )
    parser.add_argument(
        "--output", "-o",
        help="Path to save output CSV (default: stdout)",
        default=None
    )
    parser.add_argument(
        "--mode",
        choices=["file", "directory", "auto"],
        default="auto",
        help="Input mode: file, directory, or auto-detect"
    )

    args = parser.parse_args()
    input_path = Path(args.input_path)

    if args.mode == "file" or (args.mode == "auto" and input_path.is_file()):
        logger.info(f"Parsing single file: {input_path}")
        try:
            data = parse_anti_smash_json(str(input_path))
            summary = extract_bgc_summary(data)
        except Exception as e:
            logger.error(f"Failed to parse file: {e}")
            return 1
    elif args.mode == "directory" or (args.mode == "auto" and input_path.is_dir()):
        logger.info(f"Parsing directory: {input_path}")
        try:
            summary = parse_anti_smash_directory(str(input_path))
        except Exception as e:
            logger.error(f"Failed to parse directory: {e}")
            return 1
    else:
        logger.error(f"Invalid input path: {input_path}")
        return 1

    if not summary:
        logger.warning("No BGC data found in input.")
        if args.output:
            pd.DataFrame(columns=['species', 'bgc_count', 'bgc_types']).to_csv(
                args.output, index=False
            )
            logger.info(f"Empty CSV saved to {args.output}")
        return 0

    # Convert to DataFrame
    df_summary = bgc_summary_to_dataframe(summary)
    df_types = get_bgc_counts_by_type(summary)

    # Print summary
    print("\n=== BGC Summary ===")
    print(df_summary.to_string(index=False))
    print("\n=== BGC Counts by Type ===")
    print(df_types.to_string(index=False))

    # Save to CSV if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_summary.to_csv(output_path, index=False)
        logger.info(f"Summary saved to {args.output}")

    return 0


if __name__ == "__main__":
    exit(main())
