"""
Utility to verify ASCII vs Visual ground truth consistency.
Implements SC-005 (Constitution Principle).
"""
import os
import sys
import json
import argparse
import logging
import difflib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from logger import setup_logger, configure_global_logging, get_logger

# Placeholder for image processing if needed, but SC-005 focuses on text consistency
# If visual frames are images, we assume a pre-processing step converts them to ASCII
# or we compare the generated ASCII against the expected ASCII from the visual source.
# For this implementation, we assume the visual input is also represented as ASCII 
# or we have a mapping function. Since the task mentions "ASCII vs Visual", 
# we will assume the visual frames are converted to ASCII by the renderer itself 
# or we are comparing the generated ASCII against a reference ASCII derived from visual.

# However, the task T022 says: "Execute utils/renderer_validator.py on generated 
# data/processed/seeds_*.ascii and data/processed/seeds_*.png files".
# This implies we need to compare the .ascii file against the .png file.
# To do this, we need a way to convert .png to ASCII or compare them structurally.
# Since the renderer generates ASCII from a state, and the visual is a rendering of that state,
# the validator should check if the ASCII representation matches the visual representation.
# Without an image-to-ASCII library dependency in requirements, we will assume a simple 
# structural check or that the visual input is also available as ASCII for comparison.

# Given the constraints, we will implement a check that assumes the visual frames 
# have been converted to ASCII (perhaps by the renderer in a different mode) 
# or we compare the generated ASCII against a known good reference if available.
# For the purpose of this task, we will simulate the comparison by checking 
# if the ASCII file exists and is non-empty, and if the visual file exists.
# A real implementation would use PIL/Pillow to render the image to ASCII and compare.

# Let's assume we have a helper to convert image to ASCII for comparison.
# We will add a basic implementation using PIL if available, otherwise skip.

def convert_image_to_ascii(image_path: str, width: int = 80) -> str:
    """Convert an image to ASCII string."""
    try:
        from PIL import Image
        img = Image.open(image_path)
        img = img.convert('L') # Grayscale
        img = img.resize((width, int(img.height * width / img.width)))
        
        ascii_str = ""
        for y in range(img.height):
            for x in range(img.width):
                pixel = img.getpixel((x, y))
                # Map 0-255 to characters
                chars = "@%#*+=-:. "
                idx = int(pixel / 255 * (len(chars) - 1))
                ascii_str += chars[idx]
            ascii_str += "\n"
        return ascii_str
    except ImportError:
        logging.getLogger("renderer_validator").warning("PIL not available, skipping image conversion.")
        return ""
    except Exception as e:
        logging.getLogger("renderer_validator").error(f"Failed to convert image {image_path}: {e}")
        return ""

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def validate_pair(ascii_path: str, visual_path: str) -> Dict[str, Any]:
    """Validate a single pair of ASCII and Visual files."""
    result = {
        "ascii_file": ascii_path,
        "visual_file": visual_path,
        "status": "FAIL",
        "levenshtein_distance": -1,
        "error": None
    }

    try:
        # Read ASCII file
        with open(ascii_path, 'r', encoding='utf-8') as f:
            ascii_content = f.read().strip()

        # Convert visual to ASCII
        visual_ascii = convert_image_to_ascii(visual_path)
        if not visual_ascii:
            result["error"] = "Could not convert visual to ASCII (PIL missing or error)"
            return result

        visual_ascii = visual_ascii.strip()

        # Compare
        distance = levenshtein_distance(ascii_content, visual_ascii)
        result["levenshtein_distance"] = distance

        if distance == 0:
            result["status"] = "PASS"
        else:
            result["status"] = "FAIL"
            result["error"] = f"Levenshtein distance is {distance}, expected 0"

    except Exception as e:
        result["error"] = str(e)

    return result

def run_validation(ascii_pattern: str, visual_pattern: str, output_path: str):
    """Run validation on matching pairs of files."""
    logger = get_logger("renderer_validator")
    results = []
    passed_count = 0

    # Find files
    ascii_files = list(Path(".").glob(ascii_pattern))
    visual_files = list(Path(".").glob(visual_pattern))

    if not ascii_files:
        logger.error(f"No ASCII files found matching {ascii_pattern}")
        return

    if not visual_files:
        logger.error(f"No visual files found matching {visual_pattern}")
        return

    # Match files (assuming same naming convention)
    # This is a simple heuristic; in production, use a more robust matching
    for ascii_file in ascii_files:
        # Extract seed/name from filename
        name = ascii_file.stem
        # Find corresponding visual file
        matching_visual = None
        for vf in visual_files:
            if vf.stem.startswith(name):
                matching_visual = vf
                break

        if not matching_visual:
            logger.warning(f"No matching visual file for {ascii_file}")
            continue

        logger.info(f"Validating pair: {ascii_file} vs {matching_visual}")
        res = validate_pair(str(ascii_file), str(matching_visual))
        results.append(res)
        if res["status"] == "PASS":
            passed_count += 1

    # Summary
    total = len(results)
    summary = {
        "total_pairs": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "status": "PASS" if passed_count == total and total > 0 else "FAIL",
        "details": results
    }

    # Save report
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Validation complete. Results saved to {output_path}")
    return summary

def main():
    parser = argparse.ArgumentParser(description="Validate ASCII vs Visual consistency.")
    parser.add_argument("--input", type=str, required=True, help="Glob pattern for ASCII files.")
    parser.add_argument("--visual-input", type=str, required=True, help="Glob pattern for visual files.")
    parser.add_argument("--output", type=str, required=True, help="Output JSON report path.")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level.")

    args = parser.parse_args()

    configure_global_logging(level=args.log_level)
    logger = get_logger("renderer_validator")

    try:
        summary = run_validation(args.input, args.visual_input, args.output)
        if summary["status"] == "PASS":
            logger.info("VALIDATION PASSED")
            sys.exit(0)
        else:
            logger.error("VALIDATION FAILED")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
