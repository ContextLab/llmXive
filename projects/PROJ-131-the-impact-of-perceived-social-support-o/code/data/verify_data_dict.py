"""
Task T073a: Verify Data Dictionary Alignment.

Verifies that the Data Dictionary in spec.md lists the Cyberbullying Survey 2021
as the SOLE source for all variables.

Action:
- Reads specs/001-social-support-resilience/spec.md.
- Parses the Data Dictionary table.
- Asserts that every row has "(Sole Source)" in the "Source" column.

Success: Logs "INFO: Data Dictionary verified." and exits 0.
Failure: Logs "ERROR: Data Dictionary mismatch." and exits 1.
"""
import sys
import logging
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_data_dictionary_table(content: str) -> str | None:
    """
    Locates the Data Dictionary table in the markdown content.
    Returns the raw text of the table if found, else None.
    """
    # Pattern to find the table starting with the header row
    # We look for the specific header pattern typically used in the spec
    header_pattern = r'\|\s*Variable\s*\|\s*Source\s*\|'
    
    match = re.search(header_pattern, content, re.IGNORECASE)
    if not match:
        logger.warning("Could not locate Data Dictionary table header.")
        return None

    start_idx = match.start()
    
    # Find the end of the table (next line starting with | or empty line)
    # We'll just capture lines until we hit a non-table line or end of file
    lines = content[start_idx:].split('\n')
    table_lines = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_table:
                break
            continue
        
        if line.startswith('|'):
            in_table = True
            table_lines.append(line)
        else:
            if in_table:
                break
    
    return '\n'.join(table_lines)

def parse_table_rows(table_text: str) -> list[dict]:
    """
    Parses a markdown table text into a list of dictionaries.
    """
    lines = table_text.strip().split('\n')
    if len(lines) < 3:
        return []
    
    # Skip header and separator lines
    # Header: | Variable | Source | ...
    # Sep: | --- | --- | ...
    data_lines = lines[2:]
    
    rows = []
    for line in data_lines:
        if not line.startswith('|'):
            continue
        
        # Split by | and clean up
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if len(cells) >= 2:
            rows.append({
                'variable': cells[0],
                'source': cells[1]
            })
    
    return rows

def verify_alignment(rows: list[dict]) -> bool:
    """
    Checks if every row has "(Sole Source)" in the source column.
    """
    if not rows:
        logger.error("No data rows found in the Data Dictionary.")
        return False
    
    all_aligned = True
    mismatched_rows = []
    
    for row in rows:
        source = row.get('source', '')
        # Check for the specific marker required by the Plan
        if '(Sole Source)' not in source:
            all_aligned = False
            mismatched_rows.append(row)
    
    if mismatched_rows:
        logger.error(f"Found {len(mismatched_rows)} rows without '(Sole Source)' marker.")
        for r in mismatched_rows[:5]: # Log first 5
            logger.error(f"  - Variable: {r['variable']}, Source: {r['source']}")
        if len(mismatched_rows) > 5:
            logger.error(f"  ... and {len(mismatched_rows) - 5} more.")
    
    return all_aligned

def main():
    spec_path = Path("specs/001-social-support-resilience/spec.md")
    
    if not spec_path.exists():
        logger.error(f"Spec file not found: {spec_path}")
        sys.exit(1)
    
    try:
        content = spec_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to read spec file: {e}")
        sys.exit(1)
    
    table_text = find_data_dictionary_table(content)
    
    if not table_text:
        logger.error("Could not parse the Data Dictionary table from spec.md.")
        sys.exit(1)
    
    rows = parse_table_rows(table_text)
    
    if verify_alignment(rows):
        logger.info("INFO: Data Dictionary verified.")
        sys.exit(0)
    else:
        logger.error("ERROR: Data Dictionary mismatch.")
        sys.exit(1)

if __name__ == "__main__":
    main()