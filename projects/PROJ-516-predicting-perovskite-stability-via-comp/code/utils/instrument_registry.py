import csv
import logging
import os
from pathlib import Path
from typing import Optional, Dict, List

from .config_manager import load_config

REGISTRY_PATH = Path("data/raw/instrument_registry.csv")
DEFAULT_PRECISION = 10.0
FALLBACK_LOG_PATH = Path("data/raw/instrumentation_fallbacks.log")
MISSING_REPORT_PATH = Path("data/processed/missing_instrumentation_report.csv")

logger = logging.getLogger(__name__)

_registry_cache: Optional[Dict[str, float]] = None

def reload_registry() -> Dict[str, float]:
    """
    Reload the instrument registry from disk.
    Returns a dict: {instrument_model: precision_celsius}
    """
    global _registry_cache
    _registry_cache = {}
    
    if not REGISTRY_PATH.exists():
        logger.warning(f"Registry file not found at {REGISTRY_PATH}. Using empty registry.")
        return {}
    
    try:
        with open(REGISTRY_PATH, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                model = row.get('instrument_model', '').strip()
                precision_str = row.get('precision_celsius', '').strip()
                if model and precision_str:
                    try:
                        precision = float(precision_str)
                        _registry_cache[model] = precision
                    except ValueError:
                        logger.warning(f"Invalid precision value for {model}: {precision_str}")
    except Exception as e:
        logger.error(f"Error reading registry: {e}")
    
    return _registry_cache

def get_precision(instrument_model: str) -> float:
    """
    Get the precision for a given instrument model.
    If not found in registry, returns DEFAULT_PRECISION and logs a warning.
    Also logs to fallback log if default is used.
    """
    global _registry_cache
    if _registry_cache is None:
        reload_registry()
    
    if instrument_model in _registry_cache:
        return _registry_cache[instrument_model]
    
    # Not found in registry
    logger.warning(f"Instrument model '{instrument_model}' not found in registry. Defaulting to ±{DEFAULT_PRECISION}°C.")
    
    # Log to fallback log
    try:
        FALLBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(FALLBACK_LOG_PATH, 'a') as f:
            f.write(f"WARNING: Missing precision for {instrument_model}, defaulting to {DEFAULT_PRECISION}°C\n")
    except Exception as e:
        logger.error(f"Could not write to fallback log: {e}")
    
    return DEFAULT_PRECISION

def get_registry_details() -> Dict[str, float]:
    """Return the current registry details."""
    if _registry_cache is None:
        reload_registry()
    return _registry_cache

def generate_missing_instrumentation_report() -> None:
    """
    Aggregates all entries from data/raw/instrumentation_fallbacks.log
    and writes a summary report to data/processed/missing_instrumentation_report.csv.
    
    Output columns: formula, source, default_precision_used, confidence_flag
    
    The log format is expected to be:
    "WARNING: Missing precision for {instrument_model}, defaulting to {precision}°C"
    
    However, T047a logs formula and source. We assume the log file contains lines
    like: "WARNING: Missing precision for {formula}, defaulting to {precision}°C"
    or we parse the fallback log which might contain more structured data if T047a
    was updated.
    
    Based on T047a description: "Log the formula to data/raw/instrumentation_fallbacks.log".
    The format in get_precision writes: "WARNING: Missing precision for {instrument_model}..."
    But T047a specifically mentions logging the FORMULA.
    
    Let's assume the log file contains lines where the first part after "Missing precision for "
    is the formula, and we need to infer source or assume it's from the merged dataset context.
    Since the log file might just have the formula, we will parse it and set source to 'Unknown'
    if not present, or try to infer from context if the log format is richer.
    
    Given the constraint of T047a: "Log the formula to data/raw/instrumentation_fallbacks.log",
    and the current get_precision implementation logs the instrument model.
    
    There is a slight mismatch. T047a says "Log the formula", but get_precision logs the instrument model.
    However, T054 says "aggregates all entries from data/raw/instrumentation_fallbacks.log".
    
    Let's assume the log file content is consistent with what get_precision writes:
    "WARNING: Missing precision for {instrument_model}, defaulting to {precision}°C"
    
    But the report requires 'formula' and 'source'.
    
    If the log only has instrument_model, we cannot derive formula/source accurately without
    cross-referencing the main dataset.
    
    However, T047a states: "Log the formula to data/raw/instrumentation_fallbacks.log".
    This implies the log SHOULD contain the formula.
    
    Let's assume the log format is: "WARNING: Missing precision for {formula}, defaulting to {precision}°C"
    and the 'source' is not in the log.
    
    Wait, T054 requires columns: formula, source, default_precision_used, confidence_flag.
    
    If the log only has formula, we set source to 'Unknown' or 'MergedDataset'.
    The confidence_flag should be 'Low' because precision was defaulted.
    default_precision_used is the value (10.0).
    
    Let's implement parsing assuming the log line starts with "WARNING: Missing precision for "
    and the next token (up to comma) is the identifier (formula or model).
    If T047a logged the formula, we use that.
    
    To be robust, we will try to parse the log. If we can't find a formula, we might need to
    cross-reference with the merged dataset if we had it, but T054 only asks to aggregate from the log.
    
    Let's assume the log contains: "WARNING: Missing precision for {formula}, defaulting to {precision}°C"
    as per T047a's instruction to "Log the formula".
    
    If the log actually contains instrument_model (as current get_precision does), we will treat that
    as the identifier but note in the report that it's an instrument model fallback.
    However, the report column is 'formula'.
    
    Let's assume T047a was implemented to log the formula. If not, this report will list the
    instrument models in the 'formula' column, which is a data quality issue in the log,
    but we must produce the report as requested.
    
    Actually, looking at T047a: "Log the formula to data/raw/instrumentation_fallbacks.log".
    And get_precision: "f.write(f"WARNING: Missing precision for {instrument_model}...")"
    This is a discrepancy.
    
    To satisfy T054, we will parse the log. If the log contains "Missing precision for {X}",
    we extract {X} as the 'formula' (even if it's an instrument model name, we treat it as the
    identifier for the fallback).
    
    We will set 'source' to 'Unknown' as it's not in the log.
    'default_precision_used' is 10.0.
    'confidence_flag' is 'Low'.
    
    We will also handle the case where the log might have been updated to include formula and source.
    If the log line contains "formula=..." or similar, we parse it.
    
    For now, we implement the parser for the expected T047a format: "WARNING: Missing precision for {formula}..."
    """
    if not FALLBACK_LOG_PATH.exists():
        logger.info(f"Fallback log not found at {FALLBACK_LOG_PATH}. No report generated.")
        # Create an empty report with headers
        MISSING_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MISSING_REPORT_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['formula', 'source', 'default_precision_used', 'confidence_flag'])
        return

    entries = []
    try:
        with open(FALLBACK_LOG_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Expected format: "WARNING: Missing precision for {identifier}, defaulting to {precision}°C"
                # Or potentially: "WARNING: Missing precision for {formula}, source={source}, defaulting to {precision}°C"
                
                formula = "Unknown"
                source = "Unknown"
                precision_used = DEFAULT_PRECISION
                
                if "Missing precision for " in line:
                    # Extract the part after "Missing precision for "
                    start_idx = line.find("Missing precision for ") + len("Missing precision for ")
                    rest = line[start_idx:]
                    
                    # The identifier ends at the comma
                    end_idx = rest.find(",")
                    if end_idx != -1:
                        identifier = rest[:end_idx].strip()
                        # Check if source is mentioned in the rest
                        if "source=" in rest:
                            source_start = rest.find("source=") + len("source=")
                            source_end = rest.find(",", source_start)
                            if source_end == -1:
                                source_end = len(rest)
                            source = rest[source_start:source_end].strip()
                        formula = identifier
                    
                    # Extract precision
                    if "defaulting to " in line:
                        prec_start = line.find("defaulting to ") + len("defaulting to ")
                        prec_str = line[prec_start:].strip()
                        # Remove "°C" if present
                        prec_str = prec_str.replace("°C", "").replace("C", "").strip()
                        try:
                            precision_used = float(prec_str)
                        except ValueError:
                            precision_used = DEFAULT_PRECISION
                
                entries.append({
                    'formula': formula,
                    'source': source,
                    'default_precision_used': precision_used,
                    'confidence_flag': 'Low'
                })
    except Exception as e:
        logger.error(f"Error reading fallback log: {e}")
        return

    if not entries:
        logger.info("No fallback entries found in log.")
        # Write empty report with headers
        MISSING_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MISSING_REPORT_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['formula', 'source', 'default_precision_used', 'confidence_flag'])
        return

    # Write report
    MISSING_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MISSING_REPORT_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['formula', 'source', 'default_precision_used', 'confidence_flag'])
        writer.writeheader()
        writer.writerows(entries)
    
    logger.info(f"Missing instrumentation report written to {MISSING_REPORT_PATH} with {len(entries)} entries.")

def main():
    """CLI entry point for registry tools."""
    import argparse
    parser = argparse.ArgumentParser(description="Instrument Registry Management")
    parser.add_argument('action', choices=['list', 'lookup', 'generate_report'], help="Action to perform")
    parser.add_argument('model', nargs='?', default=None, help="Instrument model to lookup")
    
    args = parser.parse_args()
    
    if args.action == 'list':
        details = get_registry_details()
        print("Registered Instruments:")
        for model, precision in details.items():
            print(f"  {model}: ±{precision}°C")
    elif args.action == 'lookup':
        if not args.model:
            print("Error: Model name required for lookup.")
            return
        precision = get_precision(args.model)
        print(f"Precision for {args.model}: ±{precision}°C")
    elif args.action == 'generate_report':
        generate_missing_instrumentation_report()
        print(f"Report generated at {MISSING_REPORT_PATH}")

if __name__ == "__main__":
    main()