"""
Visualization templates for injecting mandatory limitation headers and footers.

This module implements FR-011: All visualizations and reports MUST include
mandatory limitation disclosures in headers and footers.

The limitation text is derived from the project's research constraints and
must be injected into all generated plots and notebooks.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import textwrap

# Standard limitation disclosure text as per FR-011
# This text must appear in all visualizations and reports
DEFAULT_LIMITATION_HEADER = """
================================================================================
LIMITATION DISCLOSURE
================================================================================
This analysis is subject to the following limitations:
1. Data Source: Stack Overflow public dump (posts and tags only)
2. Time Period: Limited to the available data range in the dump
3. Tag Normalization: Tags are lowercased and trimmed; some semantic variations may persist
4. External Correlation: GitHub/NPM mapping is approximate and may miss relevant projects
5. Statistical Power: Some trends classified as "Insufficient Data" may have low statistical power (MDES > observed effect)
6. Seasonality Detection: STL decomposition requires sufficient seasonal cycles; short series may yield unreliable components
7. Clustering: Jaccard similarity captures co-occurrence but not semantic relatedness
8. Causality: Correlation does not imply causation; observed relationships require domain validation
================================================================================
"""

DEFAULT_LIMITATION_FOOTER = """
================================================================================
END OF LIMITATION DISCLOSURE
================================================================================
For methodology details, see: docs/methodology.md
For data provenance, see: data/processed/*.json (with SHA-256 hashes)
Last updated: {timestamp}
================================================================================
"""

# Notebook-specific template with markdown formatting
NOTEBOOK_HEADER_TEMPLATE = """
### ⚠️ Limitation Disclosure

This analysis is subject to the following limitations:

1. **Data Source**: Stack Overflow public dump (posts and tags only)
2. **Time Period**: Limited to the available data range in the dump
3. **Tag Normalization**: Tags are lowercased and trimmed; some semantic variations may persist
4. **External Correlation**: GitHub/NPM mapping is approximate and may miss relevant projects
5. **Statistical Power**: Some trends classified as "Insufficient Data" may have low statistical power (MDES > observed effect)
6. **Seasonality Detection**: STL decomposition requires sufficient seasonal cycles; short series may yield unreliable components
7. **Clustering**: Jaccard similarity captures co-occurrence but not semantic relatedness
8. **Causality**: Correlation does not imply causation; observed relationships require domain validation

---
"""

NOTEBOOK_FOOTER_TEMPLATE = """
---
**End of Limitation Disclosure**

For methodology details, see: [docs/methodology.md](docs/methodology.md)  
For data provenance, see: `data/processed/*.json` (with SHA-256 hashes)  
Last updated: {timestamp}
"""

# Plot annotation template for matplotlib/seaborn
PLOT_ANNOTATION_TEMPLATE = """
LIMITATION: See FR-011 for full disclosure.
Key constraints: Data source (SO dump), Time range, Tag normalization, 
Statistical power (MDES), Seasonality detection limits, Causality disclaimer.
"""

def get_limitation_header(fmt: str = "text", timestamp: Optional[str] = None) -> str:
    """
    Generate a limitation header in the specified format.
    
    Args:
        fmt: Format type - 'text' for plain text, 'markdown' for notebook use
        timestamp: Optional timestamp string. If None, current time is not used 
                   (caller should provide or omit)
    
    Returns:
        Formatted limitation header string
    
    Raises:
        ValueError: If fmt is not 'text' or 'markdown'
    """
    if fmt == "text":
        return DEFAULT_LIMITATION_HEADER
    elif fmt == "markdown":
        ts = timestamp or "N/A"
        return NOTEBOOK_HEADER_TEMPLATE
    else:
        raise ValueError(f"Unsupported format: {fmt}. Use 'text' or 'markdown'.")

def get_limitation_footer(fmt: str = "text", timestamp: Optional[str] = None) -> str:
    """
    Generate a limitation footer in the specified format.
    
    Args:
        fmt: Format type - 'text' for plain text, 'markdown' for notebook use
        timestamp: Optional timestamp string. If None, current time is not used
    
    Returns:
        Formatted limitation footer string
    
    Raises:
        ValueError: If fmt is not 'text' or 'markdown'
    """
    if fmt == "text":
        ts = timestamp or "N/A"
        return DEFAULT_LIMITATION_FOOTER.format(timestamp=ts)
    elif fmt == "markdown":
        ts = timestamp or "N/A"
        return NOTEBOOK_FOOTER_TEMPLATE.format(timestamp=ts)
    else:
        raise ValueError(f"Unsupported format: {fmt}. Use 'text' or 'markdown'.")

def inject_limitation_to_notebook(
    notebook_path: Path,
    section: str = "header",
    timestamp: Optional[str] = None
) -> None:
    """
    Inject limitation disclosure into a Jupyter notebook.
    
    This function reads a notebook, inserts a markdown cell with the
    limitation disclosure at the specified location, and saves the result.
    
    Args:
        notebook_path: Path to the notebook file (.ipynb)
        section: Where to inject - 'header' (after first cell) or 'footer' (at end)
        timestamp: Optional timestamp for the footer
    
    Raises:
        FileNotFoundError: If notebook_path does not exist
        ValueError: If section is not 'header' or 'footer'
        ImportError: If nbformat is not available
    """
    try:
        import nbformat
        from nbformat import v4 as nbf
    except ImportError:
        raise ImportError(
            "nbformat is required for notebook injection. "
            "Install with: pip install nbformat"
        )
    
    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook not found: {notebook_path}")
    
    if section not in ("header", "footer"):
        raise ValueError(f"Invalid section: {section}. Use 'header' or 'footer'.")
    
    # Read the notebook
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)
    
    # Create the limitation cell
    if section == "header":
        content = NOTEBOOK_HEADER_TEMPLATE
    else:
        content = NOTEBOOK_FOOTER_TEMPLATE.format(timestamp=timestamp or "N/A")
    
    limitation_cell = nbf.new_markdown_cell(content)
    
    # Insert at appropriate location
    if section == "header":
        # Insert after the first cell (typically title/intro)
        if len(nb.cells) > 0:
            nb.cells.insert(1, limitation_cell)
        else:
            nb.cells.append(limitation_cell)
    else:
        # Append at the end
        nb.cells.append(limitation_cell)
    
    # Write back
    with open(notebook_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

def create_plot_with_limitation(
    ax,
    title: str,
    limitation_text: Optional[str] = None
) -> None:
    """
    Add a limitation text box to a matplotlib axes.
    
    This function adds a small text box in the corner of the plot
    indicating that limitation disclosures apply.
    
    Args:
        ax: Matplotlib axes object
        title: Plot title (used for context)
        limitation_text: Optional custom limitation text. If None, uses default.
    """
    import matplotlib.pyplot as plt
    
    if limitation_text is None:
        limitation_text = PLOT_ANNOTATION_TEMPLATE
    
    # Add text box in the lower right corner
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(
        0.98, 0.02, limitation_text,
        transform=ax.transAxes,
        fontsize=8,
        verticalalignment='bottom',
        horizontalalignment='right',
        bbox=props
    )

def validate_limitation_injection(
    file_path: Path,
    expected_formats: List[str] = None
) -> Dict[str, Any]:
    """
    Validate that a file contains proper limitation disclosures.
    
    Args:
        file_path: Path to the file to validate
        expected_formats: List of expected formats to check (e.g., ['text', 'markdown'])
    
    Returns:
        Dictionary with validation results:
        {
            "found": bool,
            "format": str or None,
            "message": str
        }
    """
    if not file_path.exists():
        return {
            "found": False,
            "format": None,
            "message": f"File not found: {file_path}"
        }
    
    if expected_formats is None:
        expected_formats = ["text", "markdown"]
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # Check for limitation keywords
    limitation_keywords = [
        "LIMITATION DISCLOSURE",
        "⚠️ Limitation Disclosure",
        "Data Source: Stack Overflow",
        "Statistical Power",
        "Causality"
    ]
    
    found_keyword = any(keyword in content for keyword in limitation_keywords)
    
    if not found_keyword:
        return {
            "found": False,
            "format": None,
            "message": "No limitation disclosure found in file"
        }
    
    # Determine format
    fmt = None
    if "### ⚠️ Limitation Disclosure" in content:
        fmt = "markdown"
    elif "LIMITATION DISCLOSURE" in content:
        fmt = "text"
    
    return {
        "found": True,
        "format": fmt,
        "message": f"Limitation disclosure found ({fmt} format)"
    }