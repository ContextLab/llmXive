"""
Verify Data Dictionary Alignment for the Cyberbullying Survey 2021.

This module checks that the Data Dictionary in spec.md lists the
Cyberbullying Survey 2021 as the SOLE source for all variables.
"""

import sys
import logging
import re
from pathlib import Path

# Import logger from project utils
try:
    from utils.logger import get_logger
except ImportError:
    # Fallback for direct execution if utils is not in path yet
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
else:
    logger = get_logger(__name__)

def find_data_dictionary_table(spec_path: Path) -> str | None:
    """
    Locate the Data Dictionary table section in the spec.md file.
    Returns the text content of the table or None if not found.
    """
    if not spec_path.exists():
        logger.error(f"Spec file not found: {spec_path}")
        return None

    content = spec_path.read_text(encoding='utf-8')
    
    # Look for a markdown table header that suggests a Data Dictionary
    # Common patterns: "| Variable | Description | Source |"
    # We look for the table structure
    lines = content.split('\n')
    table_lines = []
    in_table = False
    
    for i, line in enumerate(lines):
        # Detect table start (header row with pipes)
        if line.strip().startswith('|') and '|' in line:
            # Check if it looks like a header (contains 'Variable' or 'Source')
            if 'Variable' in line or 'Source' in line or 'Description' in line:
                in_table = True
                table_lines.append(line)
                continue
        
        if in_table:
            table_lines.append(line)
            # Detect table end (empty line or line without pipes)
            if not line.strip().startswith('|'):
                break
            # Also break if we hit a new header section
            if line.strip().startswith('###') or line.strip().startswith('##'):
                break
    
    if not table_lines:
        return None
    
    return '\n'.join(table_lines)

def parse_table_rows(table_text: str) -> list[dict]:
    """
    Parse markdown table rows into a list of dictionaries.
    Assumes standard markdown table format.
    """
    rows = []
    lines = table_text.strip().split('\n')
    
    # Skip header and separator lines
    if len(lines) < 2:
        return rows
    
    # Find column indices from header
    header_line = lines[0]
    separator_line = lines[1] if len(lines) > 1 else None
    
    # Simple parser: split by | and clean up
    # This assumes consistent pipe usage
    for line in lines[2:]:
        if not line.strip().startswith('|'):
            continue
        if '---' in line: # Skip separator row
            continue
        
        cells = line.split('|')
        # Clean up cells
        cells = [cell.strip() for cell in cells if cell.strip()]
        
        if len(cells) >= 3:
            # Assuming structure: Variable | Description | Source
            rows.append({
                'variable': cells[0],
                'description': cells[1] if len(cells) > 1 else '',
                'source': cells[2] if len(cells) > 2 else ''
            })
    
    return rows

def verify_alignment(rows: list[dict]) -> tuple[bool, list[str]]:
    """
    Verify that every row in the Data Dictionary has 'Cyberbullying Survey 2021'
    (or equivalent sole source marker) in the Source column.
    
    Returns (is_aligned, list_of_errors)
    """
    errors = []
    is_aligned = True
    
    # Expected sole source identifiers
    sole_sources = [
        'Cyberbullying Survey 2021',
        'Cyberbullying Survey',
        'Sole Source',
        '(Sole Source)',
        'Cyberbullying 2021'
    ]
    
    for row in rows:
        source = row.get('source', '').strip()
        variable = row.get('variable', 'Unknown')
        
        if not source:
            errors.append(f"Variable '{variable}' has no source listed.")
            is_aligned = False
            continue
        
        # Check if the source matches any of the expected sole source identifiers
        # Case-insensitive check
        source_lower = source.lower()
        matched = False
        for ss in sole_sources:
            if ss.lower() in source_lower:
                matched = True
                break
        
        if not matched:
            errors.append(
                f"Variable '{variable}' has source '{source}', "
                f"expected 'Cyberbullying Survey 2021' (Sole Source)."
            )
            is_aligned = False
    
    return is_aligned, errors

def main():
    """Main entry point for verification."""
    project_root = Path(__file__).parent.parent.parent
    spec_path = project_root / 'specs' / '001-social-support-resilience' / 'spec.md'
    log_path = project_root / 'data' / 'results' / 'data_dict_verification.log'

    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Setup file logging
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add to existing logger or create new
    if not logger.handlers:
        logger.addHandler(file_handler)
    else:
        # Replace handlers to ensure clean log
        logger.handlers = [file_handler]
    
    logger.info("=" * 60)
    logger.info("Starting Data Dictionary Alignment Verification (T073a)")
    logger.info("=" * 60)

    # Find the table
    table_text = find_data_dictionary_table(spec_path)
    if not table_text:
        logger.error("Could not find Data Dictionary table in spec.md")
        logger.error("Pipeline halted due to missing Data Dictionary.")
        print("ERROR: Data Dictionary table not found in spec.md")
        sys.exit(1)
    
    logger.info(f"Found Data Dictionary table at: {spec_path}")
    
    # Parse rows
    rows = parse_table_rows(table_text)
    if not rows:
        logger.error("Could not parse any rows from the Data Dictionary table.")
        sys.exit(1)
    
    logger.info(f"Parsed {len(rows)} variables from the Data Dictionary.")
    
    # Verify alignment
    is_aligned, errors = verify_alignment(rows)
    
    if is_aligned:
        logger.info("SUCCESS: Data Dictionary verified.")
        logger.info("All variables list 'Cyberbullying Survey 2021' as the sole source.")
        print("INFO: Data Dictionary verified.")
    else:
        logger.error("ERROR: Data Dictionary mismatch.")
        for err in errors:
            logger.error(f"  - {err}")
        print("ERROR: Data Dictionary mismatch. See logs for details.")
        sys.exit(1)

    logger.info("Verification complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
