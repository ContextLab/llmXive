import sys
import logging
import re
from pathlib import Path

# Ensure the project root is in the path for imports if run directly
# but we rely on the pipeline environment for standard imports.

def find_data_dictionary_table(content: str) -> list:
    """
    Locate the Data Dictionary table in the spec markdown.
    Returns a list of lines belonging to the table.
    """
    lines = content.split('\n')
    table_start = -1
    table_end = -1

    # Look for a header containing "Data Dictionary" or similar
    for i, line in enumerate(lines):
        if 'Data Dictionary' in line and ('|' in line or line.strip().startswith('#')):
            # If it's a markdown table header
            if '|' in line:
                table_start = i
            # If it's a section header followed by a table
            elif i + 1 < len(lines) and '|' in lines[i+1]:
                table_start = i + 1
            break

    if table_start == -1:
        return []

    # Find the end of the table (first line that doesn't contain '|' after the header)
    for i in range(table_start, len(lines)):
        if '|' not in lines[i] and not lines[i].strip().startswith('|'):
            # Check if it's a separator line (---)
            if i > table_start + 1 and lines[i].strip().replace('-', '').replace(' ', '') == '':
                continue
            table_end = i
            break

    if table_end == -1:
        # If no end found, take until end of file or next major header
        for i in range(table_start, len(lines)):
            if lines[i].startswith('#') and i > table_start + 5:
                table_end = i
                break
        if table_end == -1:
            table_end = len(lines)

    return lines[table_start:table_end]

def parse_table_rows(table_lines: list) -> list:
    """
    Parse markdown table rows into a list of dictionaries.
    Expects the first row to be headers, second to be separator, rest to be data.
    """
    if len(table_lines) < 3:
        return []

    # Find the actual header row (skip section titles if any)
    header_idx = -1
    for i, line in enumerate(table_lines):
        if '|' in line and not line.strip().startswith('#'):
            header_idx = i
            break

    if header_idx == -1:
        return []

    headers = [h.strip() for h in table_lines[header_idx].split('|') if h.strip()]
    # Skip separator row
    data_start = header_idx + 2
    rows = []

    for line in table_lines[data_start:]:
        if '|' not in line:
            continue
        cells = [c.strip() for c in line.split('|') if c.strip()]
        if len(cells) == len(headers):
            row_dict = dict(zip(headers, cells))
            rows.append(row_dict)

    return rows

def verify_alignment(rows: list) -> tuple:
    """
    Verify that every row in the Data Dictionary has "(Sole Source)" in the Source column.
    Returns (is_aligned, mismatched_rows).
    """
    mismatched = []
    # Try to find the 'Source' column index
    source_idx = -1
    if not rows:
        return True, []

    # Infer column name from the first row keys if possible
    # The task description implies a 'Source' column exists.
    # We check for keys like 'Source', 'Source(s)', 'Data Source'.
    possible_keys = ['Source', 'Source(s)', 'Data Source', 'Source Column']
    found_key = None

    first_row_keys = list(rows[0].keys())
    for key in possible_keys:
        if key in first_row_keys:
            found_key = key
            break
    
    # If exact match not found, try case-insensitive or partial
    if not found_key:
        for key in first_row_keys:
            if 'source' in key.lower():
                found_key = key
                break

    if not found_key:
        # If we can't find a source column, we assume alignment failure or invalid format
        # But for this task, we assume the column exists.
        return False, [{"error": "Source column not found"}]

    for row in rows:
        source_val = row.get(found_key, "")
        if "(Sole Source)" not in source_val:
            mismatched.append({
                "variable": row.get(list(row.keys())[0], "Unknown"),
                "current_source": source_val
            })

    return len(mismatched) == 0, mismatched

def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        logger.addHandler(handler)

    spec_path = Path("specs/001-social-support-resilience/spec.md")
    
    if not spec_path.exists():
        logger.error(f"Spec file not found: {spec_path}")
        sys.exit(1)

    content = spec_path.read_text(encoding='utf-8')
    table_lines = find_data_dictionary_table(content)

    if not table_lines:
        logger.error("Could not find Data Dictionary table in spec.")
        sys.exit(1)

    rows = parse_table_rows(table_lines)
    if not rows:
        logger.error("Could not parse any rows from the Data Dictionary table.")
        sys.exit(1)

    is_aligned, mismatches = verify_alignment(rows)

    if is_aligned:
        logger.info("INFO: Data Dictionary verified.")
        logger.info("All variables are marked with '(Sole Source)'.")
    else:
        logger.error("ERROR: Data Dictionary mismatch.")
        logger.error(f"Found {len(mismatches)} variables without '(Sole Source)'.")
        for m in mismatches:
            logger.error(f"  - {m.get('variable')}: '{m.get('current_source')}'")
        # Trigger T073b logic: The task description says "If not aligned, log ERROR... and trigger T073b".
        # Since we are T073b, we assume the caller (or the pipeline) knows to run the repair logic.
        # However, the task T073b is "Repair Data Dictionary Alignment".
        # This script is T073a (Verify). The prompt asks for T073b implementation.
        # Wait, the prompt says "Implement task T073b".
        # The task description for T073b says: "Update every row in the Data Dictionary table to have '(Sole Source)' in the 'Source' column."
        # So this script should perform the REPAIR, not just verify.
        # Let's re-read the prompt's "Task" section.
        # "Implement task T073b now."
        # T073b description: "Repair Data Dictionary Alignment: Update every row..."
        # So I must write the code to FIX the file.

    # REPAIR LOGIC (T073b)
    if not is_aligned:
        logger.info("Initiating repair of Data Dictionary alignment...")
        new_lines = []
        in_table = False
        table_start_idx = -1
        
        # Re-scan to find the table boundaries and fix in place
        lines = content.split('\n')
        header_idx = -1
        for i, line in enumerate(lines):
            if 'Data Dictionary' in line and '|' in line:
                header_idx = i
                break
            elif 'Data Dictionary' in line and i+1 < len(lines) and '|' in lines[i+1]:
                header_idx = i+1
                break

        if header_idx == -1:
            logger.error("Could not locate table header for repair.")
            sys.exit(1)

        # Find column index for 'Source'
        headers = [h.strip() for h in lines[header_idx].split('|') if h.strip()]
        source_col_idx = -1
        for i, h in enumerate(headers):
            if 'source' in h.lower():
                source_col_idx = i
                break

        if source_col_idx == -1:
            logger.error("Could not find 'Source' column index for repair.")
            sys.exit(1)

        # Iterate and fix
        fixed_content = []
        for i, line in enumerate(lines):
            if i == header_idx:
                fixed_content.append(line)
                continue
            
            # Check if we are in the table (starts with |)
            if line.strip().startswith('|') and not line.strip().startswith('###') and not line.strip().startswith('##'):
                # It's a table row
                cells = [c.strip() for c in line.split('|')]
                # Handle potential empty first/last cells due to markdown formatting
                if cells and cells[0] == '': cells = cells[1:]
                if cells and cells[-1] == '': cells = cells[:-1]
                
                if len(cells) > source_col_idx:
                    current_source = cells[source_col_idx]
                    if "(Sole Source)" not in current_source:
                        # Replace the source cell
                        cells[source_col_idx] = "(Sole Source)"
                        # Reconstruct line
                        new_line = "|" + "|".join(f" {c} " for c in cells) + "|"
                        fixed_content.append(new_line)
                        logger.info(f"Fixed row: {cells[0] if cells else 'Unknown'} -> Source: (Sole Source)")
                    else:
                        fixed_content.append(line)
                else:
                    fixed_content.append(line)
            else:
                fixed_content.append(line)

        # Write back
        new_spec_content = '\n'.join(fixed_content)
        spec_path.write_text(new_spec_content, encoding='utf-8')
        logger.info("Spec file updated successfully.")

if __name__ == "__main__":
    main()
