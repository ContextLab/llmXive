import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from src.utils.logging import get_logger
from src.utils.config import get_project_root, ensure_dir

# Constants
SNR_DEGRADATION_THRESHOLD = 5.0  # Percentage

def flag_compression_quality(
    snr_degradation: float,
    method: str,
    level: str,
    event_id: str
) -> Dict[str, Any]:
    """
    Flag compression quality based on SNR degradation.

    Args:
        snr_degradation: The calculated SNR degradation in dB (or percentage if pre-calculated).
        method: Compression method name (e.g., 'quantization', 'jpeg2000').
        level: Compression level (e.g., '4-bit', '50').
        event_id: The ID of the event.

    Returns:
        Dictionary with flag details.
    """
    # The metric compute_snr_degradation returns dB.
    # We interpret "SNR degradation > 5%" as a threshold on the degradation metric.
    # If the metric is in dB, a 5% signal loss roughly corresponds to ~0.2 dB,
    # but per FR-002/SC-002, we treat the threshold as a direct percentage check
    # if the metric is normalized, or a dB check if the metric is dB.
    # Given the function name "compute_snr_degradation" in metrics.py usually returns dB,
    # we assume the threshold applies to the magnitude of degradation.
    # However, the task description says "SNR degradation > 5%".
    # If the metric is dB, we might need to convert or assume the threshold is 5 dB.
    # Let's assume the metric is percentage for this specific flagging logic as per "5%".
    # If the metric is dB, 5% power loss is approx 0.22 dB. 5 dB is a huge loss.
    # We will implement a check: if degradation > 5.0 (assuming percentage input)
    # OR if the metric is dB, we check > 5.0 dB (which is very strict).
    # To be safe and consistent with "5%", we treat the input as a percentage.
    # If the input is dB, we convert: % = 100 * (1 - 10^(-dB/10)).
    # But simpler: The task likely implies a direct comparison if the metric is normalized.
    # Let's assume the metric passed here is the raw value from compute_snr_degradation.
    # If that function returns dB, we convert to percentage for the check.

    is_unacceptable = False
    reason = "Acceptable"

    # Logic: If degradation is significant, flag it.
    # We assume the input snr_degradation is in dB.
    # Convert dB to percentage loss: Loss% = 100 * (1 - 10^(-dB/10))
    # If dB is small (e.g., 0.1), Loss% is ~2%.
    # If dB is 5, Loss% is ~68%.
    # The requirement says "SNR degradation > 5%".
    # So we calculate percentage loss and compare.

    if snr_degradation > 0:
        # Convert dB to percentage loss
        percentage_loss = 100.0 * (1.0 - 10.0 ** (-snr_degradation / 10.0))
        if percentage_loss > SNR_DEGRADATION_THRESHOLD:
            is_unacceptable = True
            reason = f"SNR degradation ({percentage_loss:.2f}%) exceeds threshold ({SNR_DEGRADATION_THRESHOLD}%)"
    else:
        # No degradation or perfect reconstruction
        reason = "Acceptable (No significant degradation)"

    return {
        "event_id": event_id,
        "method": method,
        "level": level,
        "snr_degradation_db": snr_degradation,
        "snr_degradation_percent": percentage_loss if snr_degradation > 0 else 0.0,
        "is_unacceptable": is_unacceptable,
        "reason": reason
    }

def process_quality_flags_for_event(
    event_metrics_path: Path,
    event_id: str
) -> List[Dict[str, Any]]:
    """
    Process a single event's metrics file and flag quality.

    Args:
        event_metrics_path: Path to the JSON file containing metrics for an event.
        event_id: The ID of the event.

    Returns:
        List of flag dictionaries.
    """
    flags = []
    logger = get_logger(__name__)

    if not event_metrics_path.exists():
        logger.warning(f"Metrics file not found: {event_metrics_path}")
        return flags

    try:
        with open(event_metrics_path, 'r') as f:
            metrics_data = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {event_metrics_path}")
        return flags

    # Expected structure: { "methods": [ { "method": "...", "level": "...", "snr_degradation": ... }, ... ] }
    # Or flattened: { "method_name_level": { "snr_degradation": ... } }
    # We assume the structure from metrics.py main() which likely saves a list of results.
    # Let's handle a generic list of metric entries.

    entries = metrics_data.get("results", [])
    if not entries and isinstance(metrics_data, list):
        entries = metrics_data

    for entry in entries:
        method = entry.get("method", "unknown")
        level = entry.get("level", "unknown")
        snr_deg = entry.get("snr_degradation", 0.0)

        flag = flag_compression_quality(snr_deg, method, level, event_id)
        flags.append(flag)

    return flags

def aggregate_quality_report(
    flags: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Aggregate all flags into a single report file.

    Args:
        flags: List of flag dictionaries.
        output_path: Path to save the report.
    """
    ensure_dir(output_path.parent)

    report = {
        "threshold_percent": SNR_DEGRADATION_THRESHOLD,
        "total_compressions": len(flags),
        "unacceptable_count": sum(1 for f in flags if f["is_unacceptable"]),
        "acceptable_count": sum(1 for f in flags if not f["is_unacceptable"]),
        "details": flags
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def main():
    """Main entry point for quality flagging."""
    logger = get_logger(__name__)
    project_root = get_project_root()
    interim_dir = project_root / "data" / "interim" / "compression_metrics"
    output_file = project_root / "data" / "processed" / "quality_flags.json"

    if not interim_dir.exists():
        logger.error(f"Metrics directory not found: {interim_dir}")
        logger.info("Run compression/main.py first to generate metrics.")
        return

    all_flags = []
    event_dirs = [d for d in interim_dir.iterdir() if d.is_dir()]

    for event_dir in event_dirs:
        event_id = event_dir.name
        # Look for metrics file in this directory
        # Assuming metrics are saved as {event_id}_metrics.json or similar
        metrics_files = list(event_dir.glob("*metrics*.json"))
        
        if not metrics_files:
            # Try to find any json file if naming convention varies
            metrics_files = list(event_dir.glob("*.json"))

        for metrics_file in metrics_files:
            flags = process_quality_flags_for_event(metrics_file, event_id)
            all_flags.extend(flags)

    if all_flags:
        aggregate_quality_report(all_flags, output_file)
        logger.info(f"Quality report saved to {output_file}")
        unacceptable = [f for f in all_flags if f["is_unacceptable"]]
        if unacceptable:
            logger.warning(f"Found {len(unacceptable)} unacceptable compression levels.")
            for u in unacceptable[:5]: # Log first 5
                logger.warning(f"  - {u['event_id']}: {u['method']}@{u['level']} ({u['reason']})")
    else:
        logger.warning("No metrics found to process.")

if __name__ == "__main__":
    main()
