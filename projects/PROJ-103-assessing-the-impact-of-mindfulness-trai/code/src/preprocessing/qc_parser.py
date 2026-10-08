"""
fMRIPrep HTML Report Parser for Quality Control.

Extracts QC metrics (motion summary, SNR, temporal SNR) from fMRIPrep HTML reports
and outputs a JSON summary along with the report path.
"""
import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from bs4 import BeautifulSoup

from src.config.env import get_data_dir

logger = logging.getLogger(__name__)

class QCParserError(Exception):
    """Custom exception for QC parsing errors."""
    pass

def find_fmriprep_reports(
    data_dir: Optional[str] = None,
    dataset_id: Optional[str] = None
) -> List[Path]:
    """
    Find all fMRIPrep HTML reports in the data directory.

    Args:
        data_dir: Root data directory (defaults to DATA_DIR env var).
        dataset_id: Optional specific dataset ID to filter by.

    Returns:
        List of paths to fMRIPrep HTML reports.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    processed_path = Path(data_dir) / "processed"
    reports = []

    if not processed_path.exists():
        logger.warning(f"Processed directory not found: {processed_path}")
        return reports

    # fMRIPrep typically places reports in:
    # <data_dir>/processed/<dataset>/sub-<label>/figures/sub-<label>_report.html
    # or <data_dir>/processed/<dataset>/sub-<label>/sub-<label>_report.html
    for html_file in processed_path.rglob("*.html"):
        # Filter for fMRIPrep report naming patterns
        if "report" in html_file.name.lower():
            # Additional filter if dataset_id is provided
            if dataset_id:
                if dataset_id in str(html_file):
                    reports.append(html_file)
            else:
                reports.append(html_file)

    return reports

def parse_fmriprep_html(
    report_path: Path
) -> Dict[str, Any]:
    """
    Parse a single fMRIPrep HTML report to extract QC metrics.

    Extracts:
    - Motion summary (mean FD, max FD, number of high-motion volumes)
    - SNR (Signal-to-Noise Ratio)
    - tSNR (temporal Signal-to-Noise Ratio)

    Args:
        report_path: Path to the fMRIPrep HTML report.

    Returns:
        Dictionary containing extracted QC metrics.

    Raises:
        QCParserError: If the report cannot be parsed or metrics are missing.
    """
    if not report_path.exists():
        raise QCParserError(f"Report file not found: {report_path}")

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
    except Exception as e:
        raise QCParserError(f"Failed to read report {report_path}: {e}")

    qc_data: Dict[str, Any] = {
        "report_path": str(report_path),
        "subject_id": None,
        "motion": {
            "mean_fd": None,
            "max_fd": None,
            "high_motion_volumes": None,
            "mean_translation": None,
            "mean_rotation": None
        },
        "snr": {
            "snr": None,
            "tSNR": None
        },
        "parsing_status": "success",
        "warnings": []
    }

    # Extract Subject ID from filename or page content
    subject_match = re.search(r"sub-([a-zA-Z0-9]+)", str(report_path))
    if subject_match:
        qc_data["subject_id"] = subject_match.group(0)

    # Helper to find numeric value in text
    def extract_number(text: str) -> Optional[float]:
        if not text:
            return None
        # Look for patterns like "0.5 mm", "12.3", "1.2%"
        match = re.search(r"([\d.]+)\s*(?:mm|deg|%)?", text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    # Parse Motion Metrics
    # fMRIPrep reports often contain tables or specific divs for motion
    # Look for "framewise displacement" or "FD"
    motion_text = soup.find(string=re.compile(r"framewise\s*displacement", re.I))
    if motion_text:
        parent = motion_text.parent
        if parent:
            # Try to find the value nearby
            next_sibling = parent.next_sibling
            if next_sibling:
                val = extract_number(str(next_sibling))
                if val is not None:
                    qc_data["motion"]["mean_fd"] = val

    # Look for max FD
    max_fd_text = soup.find(string=re.compile(r"max.*fd|maximum.*displacement", re.I))
    if max_fd_text:
        parent = max_fd_text.parent
        if parent:
            next_sibling = parent.next_sibling
            if next_sibling:
                val = extract_number(str(next_sibling))
                if val is not None:
                    qc_data["motion"]["max_fd"] = val

    # Look for Translation/Rotation means
    trans_text = soup.find(string=re.compile(r"mean.*translation|translation.*mean", re.I))
    if trans_text:
        parent = trans_text.parent
        if parent:
            next_sibling = parent.next_sibling
            if next_sibling:
                val = extract_number(str(next_sibling))
                if val is not None:
                    qc_data["motion"]["mean_translation"] = val

    rot_text = soup.find(string=re.compile(r"mean.*rotation|rotation.*mean", re.I))
    if rot_text:
        parent = rot_text.parent
        if parent:
            next_sibling = parent.next_sibling
            if next_sibling:
                val = extract_number(str(next_sibling))
                if val is not None:
                    qc_data["motion"]["mean_rotation"] = val

    # Parse SNR / tSNR
    # Often found in "Quality Control" section or tables
    snr_text = soup.find(string=re.compile(r"snr|signal.*noise", re.I))
    if snr_text:
        parent = snr_text.parent
        if parent:
            next_sibling = parent.next_sibling
            if next_sibling:
                val = extract_number(str(next_sibling))
                if val is not None:
                    # Heuristic: if value is large (>20), likely tSNR, else SNR
                    if val > 20:
                        qc_data["snr"]["tSNR"] = val
                    else:
                        qc_data["snr"]["snr"] = val

    tsnr_text = soup.find(string=re.compile(r"tsnr|temporal.*snr", re.I))
    if tsnr_text:
        parent = tsnr_text.parent
        if parent:
            next_sibling = parent.next_sibling
            if next_sibling:
                val = extract_number(str(next_sibling))
                if val is not None:
                    qc_data["snr"]["tSNR"] = val

    # If specific metrics weren't found in text, look for tables
    # fMRIPrep often renders QC metrics in tables
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                value = cells[1].get_text(strip=True)
                num_val = extract_number(value)
                if num_val is not None:
                    if "fd" in label or "displacement" in label:
                        if "max" in label:
                            qc_data["motion"]["max_fd"] = num_val
                        else:
                            qc_data["motion"]["mean_fd"] = num_val
                    elif "snr" in label:
                        qc_data["snr"]["snr"] = num_val
                    elif "tsnr" in label:
                        qc_data["snr"]["tSNR"] = num_val
                    elif "translation" in label:
                        qc_data["motion"]["mean_translation"] = num_val
                    elif "rotation" in label:
                        qc_data["motion"]["mean_rotation"] = num_val

    # Validate that we found something
    if not any([
        qc_data["motion"]["mean_fd"],
        qc_data["motion"]["max_fd"],
        qc_data["snr"]["snr"],
        qc_data["snr"]["tSNR"]
    ]):
        qc_data["parsing_status"] = "partial"
        qc_data["warnings"].append(
            "Could not extract standard QC metrics (Motion, SNR) from report. "
            "Report structure might differ from expected fMRIPrep template."
        )

    return qc_data

def run_qc_parsing(
    data_dir: Optional[str] = None,
    dataset_id: Optional[str] = None,
    output_json_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run QC parsing on all fMRIPrep reports found in the data directory.

    Args:
        data_dir: Root data directory.
        dataset_id: Optional specific dataset ID.
        output_json_path: Path to write the aggregated JSON summary.
            If None, writes to data/processed/qc_summary.json.

    Returns:
        List of parsed QC dictionaries.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    reports = find_fmriprep_reports(data_dir, dataset_id)

    if not reports:
        logger.warning("No fMRIPrep reports found to parse.")
        return []

    results = []
    for report in reports:
        try:
            logger.info(f"Parsing report: {report}")
            qc_data = parse_fmriprep_html(report)
            results.append(qc_data)
        except QCParserError as e:
            logger.error(f"Error parsing {report}: {e}")
            results.append({
                "report_path": str(report),
                "parsing_status": "error",
                "error_message": str(e)
            })
        except Exception as e:
            logger.error(f"Unexpected error parsing {report}: {e}")
            results.append({
                "report_path": str(report),
                "parsing_status": "error",
                "error_message": str(e)
            })

    # Write aggregated JSON summary
    if output_json_path is None:
        processed_dir = Path(data_dir) / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        output_json_path = str(processed_dir / "qc_summary.json")
    else:
        output_json_path = str(Path(output_json_path).resolve())
        Path(output_json_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"QC summary written to: {output_json_path}")
    return results

def main():
    """Main entry point for the QC parser script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse fMRIPrep HTML reports for QC metrics."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Root data directory (defaults to DATA_DIR env var)."
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default=None,
        help="Specific dataset ID to filter reports."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path for output JSON summary."
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    run_qc_parsing(
        data_dir=args.data_dir,
        dataset_id=args.dataset_id,
        output_json_path=args.output
    )

if __name__ == "__main__":
    main()
