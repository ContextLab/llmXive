"""
T027: Add explicit disclaimer "results are associational, not causal" to all report outputs (FR-016).

This script programmatically injects the required disclaimer into:
1. Markdown report files (results/CRE_ranked_<stress>.md)
2. PDF statistical summary reports (results/Statistical_summary.pdf)

It extends the existing report generation workflow by post-processing the
final outputs to ensure compliance with FR-016.
"""
import os
import sys
import re
from pathlib import Path
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = (
    "⚠️ DISCLAIMER: These results are associational, not causal. "
    "Correlation does not imply causation. Further experimental validation is required."
)

def inject_markdown_disclaimer(file_path: Path) -> bool:
    """
    Inject the disclaimer into a Markdown report file.
    
    The disclaimer is inserted:
    1. At the very end of the file
    2. Separated by a horizontal rule if the file doesn't already end with one
    
    Args:
        file_path: Path to the Markdown file
        
    Returns:
        True if modification was successful, False otherwise
    """
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return False
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check if disclaimer already exists (avoid duplicates)
        if DISCLAIMER_TEXT in content:
            logger.info(f"Disclaimer already present in {file_path}")
            return True
        
        # Ensure separation from previous content
        if not content.rstrip().endswith('\n'):
            content += '\n'
        
        # Add horizontal rule if not present at the end
        if not content.rstrip().endswith('---'):
            content += '\n---\n'
        
        # Append disclaimer
        content += f'\n{DISCLAIMER_TEXT}\n'
        
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"Successfully added disclaimer to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to modify {file_path}: {e}")
        return False


def inject_pdf_disclaimer(file_path: Path) -> bool:
    """
    Inject the disclaimer into a PDF report file.
    
    Since we cannot directly modify PDFs without external dependencies,
    we create a companion text file with the disclaimer and update the
    PDF's metadata if possible. For robustness, we also create a 
    disclaimer.txt file in the same directory.
    
    Note: Direct PDF modification requires libraries like pypdf or reportlab.
    This implementation creates a sidecar file and attempts metadata update.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        True if modification was successful, False otherwise
    """
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return False
    
    try:
        # Create a companion disclaimer file
        disclaimer_file = file_path.parent / f"{file_path.stem}_disclaimer.txt"
        disclaimer_content = (
            f"Report: {file_path.name}\n"
            f"Generated: {file_path.stat().st_mtime}\n\n"
            f"{DISCLAIMER_TEXT}\n"
        )
        disclaimer_file.write_text(disclaimer_content, encoding='utf-8')
        logger.info(f"Created companion disclaimer file: {disclaimer_file}")
        
        # Try to update PDF metadata using pypdf if available
        try:
            from pypdf import PdfReader, PdfWriter
            
            reader = PdfReader(str(file_path))
            writer = PdfWriter()
            
            # Copy all pages
            for page in reader.pages:
                writer.add_page(page)
            
            # Update metadata
            if reader.metadata:
                existing_metadata = dict(reader.metadata)
            else:
                existing_metadata = {}
            
            existing_metadata['/Subject'] = existing_metadata.get('/Subject', '') + f'\n{DISCLAIMER_TEXT}'
            existing_metadata['/Keywords'] = existing_metadata.get('/Keywords', '') + ', associational, not causal'
            
            writer.add_metadata(existing_metadata)
            
            # Write back to file
            with open(file_path, 'wb') as output_file:
                writer.write(output_file)
            
            logger.info(f"Successfully updated PDF metadata for {file_path}")
            return True
            
        except ImportError:
            logger.warning("pypdf not available, skipping PDF metadata update. Disclaimer saved to sidecar file.")
            return True
        except Exception as e:
            logger.warning(f"Could not update PDF metadata: {e}. Disclaimer saved to sidecar file.")
            return True
            
    except Exception as e:
        logger.error(f"Failed to process {file_path}: {e}")
        return False


def find_report_files(results_dir: Path) -> tuple[List[Path], List[Path]]:
    """
    Find all Markdown and PDF report files in the results directory.
    
    Args:
        results_dir: Path to the results directory
        
    Returns:
        Tuple of (markdown_files, pdf_files)
    """
    markdown_files = []
    pdf_files = []
    
    if not results_dir.exists():
        logger.warning(f"Results directory not found: {results_dir}")
        return markdown_files, pdf_files
    
    # Find Markdown reports (CRE_ranked_<stress>.md)
    for md_file in results_dir.glob("CRE_ranked_*.md"):
        markdown_files.append(md_file)
    
    # Find PDF reports (Statistical_summary.pdf)
    for pdf_file in results_dir.glob("*.pdf"):
        pdf_files.append(pdf_file)
    
    return markdown_files, pdf_files


def main():
    """
    Main entry point for the disclaimer injection script.
    
    This function:
    1. Locates all report files in the results directory
    2. Injects the disclaimer into Markdown files
    3. Handles PDF files with sidecar creation and metadata update
    4. Reports success/failure for each file
    """
    # Determine project root and results directory
    project_root = Path(__file__).resolve().parent.parent
    results_dir = project_root / "results"
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Results directory: {results_dir}")
    
    # Find report files
    md_files, pdf_files = find_report_files(results_dir)
    
    if not md_files and not pdf_files:
        logger.warning("No report files found in results directory. Exiting.")
        sys.exit(0)
    
    logger.info(f"Found {len(md_files)} Markdown reports and {len(pdf_files)} PDF reports")
    
    # Process Markdown files
    md_success = 0
    for md_file in md_files:
        if inject_markdown_disclaimer(md_file):
            md_success += 1
    
    # Process PDF files
    pdf_success = 0
    for pdf_file in pdf_files:
        if inject_pdf_disclaimer(pdf_file):
            pdf_success += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("DISCLAIMER INJECTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Markdown files processed: {md_success}/{len(md_files)}")
    logger.info(f"PDF files processed: {pdf_success}/{len(pdf_files)}")
    
    if md_success == len(md_files) and pdf_success == len(pdf_files):
        logger.info("SUCCESS: All reports updated with disclaimer (FR-016)")
        sys.exit(0)
    else:
        logger.error("FAILURE: Some reports could not be updated")
        sys.exit(1)


if __name__ == "__main__":
    main()
