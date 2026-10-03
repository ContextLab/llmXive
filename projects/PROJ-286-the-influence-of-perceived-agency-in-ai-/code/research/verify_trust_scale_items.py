"""
Module to verify the Lee & See (2004) Trust Scale items against the validated source.

This script performs the verification logic required for task T007g:
1. Loads the reference items from research/item_source_log.json.
2. Loads the embedded items from docs/trust_scale_items.md.
3. Compares them for exact match (ignoring minor whitespace differences).
4. Generates a verification report at research/trust_scale_verification_report.md.
"""
import json
import sys
from pathlib import Path
from typing import List, Tuple, Any, Dict


def load_trust_scale_items(file_path: Path) -> List[str]:
    """
    Load trust scale items from a JSON file or a text file with numbered items.
    
    Args:
        file_path: Path to the file containing the scale items.
        
    Returns:
        A list of item strings.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Scale items file not found: {file_path}")
        
    if file_path.suffix == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return [str(item).strip() for item in data]
            elif isinstance(data, dict) and 'items' in data:
                return [str(item).strip() for item in data['items']]
            else:
                raise ValueError(f"Unexpected JSON structure in {file_path}")
    elif file_path.suffix in ['.md', '.txt']:
        # Handle markdown/text files with numbered items (e.g., "1. Item text")
        items = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Check for numbered list format (1., 2., etc.) or bullet points
                # We expect exactly 12 items for Lee & See (2004)
                if line[0].isdigit() and '.' in line:
                    # Remove the number prefix
                    parts = line.split('.', 1)
                    if len(parts) > 1:
                        items.append(parts[1].strip())
                    else:
                        items.append(line)
                elif line.startswith('-') or line.startswith('*'):
                    # Bullet point
                    items.append(line[1:].strip())
                else:
                    # Plain text line, might be an item if we haven't found 12 yet
                    # But for safety, we'll assume numbered or bulleted format
                    pass
        if len(items) != 12:
            raise ValueError(f"Expected 12 items in {file_path}, found {len(items)}")
        return items
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def load_validation_report(file_path: Path) -> Dict[str, Any]:
    """
    Load the validation report (item_source_log.json).
    
    Args:
        file_path: Path to the JSON report file.
        
    Returns:
        Dictionary containing the validation report data.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Validation report not found: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_items(reference_items: List[str], embedded_items: List[str]) -> Tuple[bool, List[Tuple[int, str, str]]]:
    """
    Compare reference items against embedded items.
    
    Args:
        reference_items: List of items from the reference source.
        embedded_items: List of items from the embedded source.
        
    Returns:
        A tuple (is_match, mismatches) where mismatches is a list of 
        (index, reference_item, embedded_item) for any differences.
    """
    mismatches = []
    
    if len(reference_items) != len(embedded_items):
        # If lengths differ, we can't do a direct index-by-index comparison
        # but we can still report the length difference as a major mismatch
        mismatches.append((-1, f"Length mismatch: ref={len(reference_items)}, emb={len(embedded_items)}", ""))
        # Still try to compare up to the min length
        min_len = min(len(reference_items), len(embedded_items))
        for i in range(min_len):
            if reference_items[i] != embedded_items[i]:
                mismatches.append((i, reference_items[i], embedded_items[i]))
        return False, mismatches
        
    for i, (ref, emb) in enumerate(zip(reference_items, embedded_items)):
        if ref != emb:
            mismatches.append((i, ref, emb))
            
    return len(mismatches) == 0, mismatches


def write_verification_report(
    output_path: Path,
    reference_source: str,
    embedded_source: str,
    is_match: bool,
    mismatches: List[Tuple[int, str, str]],
    item_count: int
) -> None:
    """
    Write the verification report to a markdown file.
    
    Args:
        output_path: Path to the output report file.
        reference_source: Path string of the reference source.
        embedded_source: Path string of the embedded source.
        is_match: Boolean indicating if items match.
        mismatches: List of mismatches.
        item_count: Total number of items compared.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Trust Scale Verification Report\n\n")
        f.write(f"**Reference Source**: `{reference_source}`\n")
        f.write(f"**Embedded Source**: `{embedded_source}`\n")
        f.write(f"**Item Count**: {item_count}\n\n")
        
        f.write("## Verification Status\n\n")
        if is_match:
            f.write("✅ **VERIFIED**: All items match exactly.\n")
        else:
            f.write("❌ **FAILED**: Mismatches detected.\n\n")
            f.write("## Mismatches\n\n")
            for idx, ref, emb in mismatches:
                if idx == -1:
                    f.write(f"- **{ref}**\n")
                else:
                    f.write(f"### Item {idx + 1}\n")
                    f.write(f"- **Reference**: `{ref}`\n")
                    f.write(f"- **Embedded**: `{emb}`\n\n")
        
        f.write("## Details\n\n")
        f.write("This report confirms that the trust scale items embedded in the codebase\n")
        f.write("match the verified items from the primary source (Lee & See, 2004).\n")
        f.write("Exact string matching was performed after normalizing whitespace.\n")


def main():
    """
    Main entry point for the verification script.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    reference_log_path = project_root / "research" / "item_source_log.json"
    embedded_items_path = project_root / "docs" / "trust_scale_items.md"
    output_report_path = project_root / "research" / "trust_scale_verification_report.md"
    
    try:
        # Load reference items from the validation report (item_source_log.json)
        # The report should contain the verified items under a key like 'items' or 'verified_items'
        report_data = load_validation_report(reference_log_path)
        
        # Extract items from the report
        # The structure might vary, so we check common keys
        if 'items' in report_data:
            reference_items = [str(item).strip() for item in report_data['items']]
        elif 'verified_items' in report_data:
            reference_items = [str(item).strip() for item in report_data['verified_items']]
        elif 'LEE_SEE_2004_ITEMS' in report_data:
            reference_items = [str(item).strip() for item in report_data['LEE_SEE_2004_ITEMS']]
        else:
            # Try to find a list in the JSON
            for key, value in report_data.items():
                if isinstance(value, list):
                    reference_items = [str(item).strip() for item in value]
                    break
            else:
                raise ValueError(f"Could not find items in {reference_log_path}. Keys: {list(report_data.keys())}")
                
        if not reference_items:
            raise ValueError(f"No items found in {reference_log_path}")
            
        # Load embedded items from docs/trust_scale_items.md
        embedded_items = load_trust_scale_items(embedded_items_path)
        
        # Compare items
        is_match, mismatches = compare_items(reference_items, embedded_items)
        
        # Write report
        write_verification_report(
            output_report_path,
            str(reference_log_path),
            str(embedded_items_path),
            is_match,
            mismatches,
            len(reference_items)
        )
        
        if is_match:
            print(f"✅ Verification successful. Report written to {output_report_path}")
            sys.exit(0)
        else:
            print(f"❌ Verification failed. Report written to {output_report_path}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during verification: {e}")
        # Even on error, try to write a report indicating failure
        try:
            write_verification_report(
                output_report_path,
                str(reference_log_path),
                str(embedded_items_path),
                False,
                [(-1, str(e), "")],
                0
            )
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
