"""
Data Extractor Module for Psychology Research Project (PROJ-008).

This module handles the extraction of study metadata and intervention details.
It includes a specific fallback mechanism for abstract reconstruction using
pdfplumber when API metadata is missing or incomplete.

Constraints:
- Abstract-only extraction (no full-text OCR) to comply with CPU/RAM limits.
- Uses pdfplumber for PDF text extraction.
"""
import logging
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

import pdfplumber

from utils.logging import get_logger
from utils.config import get_data_path

logger = get_logger(__name__)

def extract_abstract_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract text from a PDF file, specifically targeting the abstract section.

    This function attempts to locate the abstract by looking for common headers
    (e.g., "Abstract", "Background", "Objective") and extracts the subsequent
    text block.

    Constraints:
    - Does NOT perform OCR (full-text OCR is disabled per constraints).
    - Returns None if the file cannot be opened or no abstract is found.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        A string containing the extracted abstract text, or None if extraction fails.
    """
    if not os.path.exists(pdf_path):
        logger.warning(f"PDF file not found: {pdf_path}")
        return None

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            if not full_text.strip():
                logger.warning(f"No text extracted from {pdf_path}. May require OCR (disabled).")
                return None

            # Attempt to locate the abstract section
            abstract_keywords = ["abstract", "background", "objective", "summary"]
            abstract_text = None

            lines = full_text.split("\n")
            start_index = -1

            for i, line in enumerate(lines):
                lower_line = line.lower().strip()
                # Check if line starts with a keyword (case-insensitive)
                if any(lower_line.startswith(kw) for kw in abstract_keywords):
                    start_index = i
                    break

            if start_index != -1:
                # Extract from the keyword line until the next section header or end
                # Heuristic: Stop at the next line that looks like a section header (all caps or short)
                # or simply take the next 10-15 lines if it's an abstract.
                # For robustness in this specific task, we take a block of text.
                end_index = start_index + 30  # Assume abstract is within 30 lines
                abstract_lines = lines[start_index:end_index]
                
                # Clean up the extracted block
                clean_lines = []
                for line in abstract_lines:
                    # Stop if we hit a clear new section (e.g., "Methods", "Results")
                    if line.strip().lower() in ["methods", "results", "discussion", "conclusion", "references"]:
                        break
                    clean_lines.append(line)
                
                abstract_text = " ".join(clean_lines).strip()
            else:
                # Fallback: If no keyword found, return the first 500 characters as a potential abstract
                # This is a weak fallback but better than nothing for "missing metadata" scenarios.
                logger.info(f"No explicit 'Abstract' header found in {pdf_path}. Returning initial text block.")
                abstract_text = full_text[:500].strip()

            return abstract_text

    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        return None

def extract_study_metadata(study_record: Dict[str, Any], pdf_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract and enrich study metadata.

    If the primary API metadata (study_record) is missing the 'abstract' field,
    this function attempts to reconstruct it using the provided PDF path.

    Args:
        study_record: Dictionary containing study data from the API collector.
        pdf_path: Optional path to the PDF file if the record lacks an abstract.

    Returns:
        Updated study_record with abstract text if successfully extracted.
    """
    # Check if abstract is already present
    if study_record.get("abstract") and study_record["abstract"].strip():
        logger.debug(f"Abstract already present for study {study_record.get('id', 'unknown')}")
        return study_record

    # Fallback to PDF extraction
    if pdf_path:
        logger.info(f"Abstract missing for study {study_record.get('id', 'unknown')}. Attempting PDF extraction from {pdf_path}.")
        extracted_abstract = extract_abstract_from_pdf(pdf_path)
        
        if extracted_abstract:
            study_record["abstract"] = extracted_abstract
            logger.info(f"Successfully reconstructed abstract for study {study_record.get('id', 'unknown')}")
        else:
            logger.warning(f"Failed to extract abstract from PDF for study {study_record.get('id', 'unknown')}")
            # Ensure we don't leave a None or empty string that might break downstream
            study_record["abstract"] = "[Abstract extraction failed]"
    else:
        logger.warning(f"No PDF path provided and abstract missing for study {study_record.get('id', 'unknown')}.")
        study_record["abstract"] = "[Abstract missing and no PDF source]"

    return study_record

def process_studies_with_fallback(studies: List[Dict[str, Any]], pdf_base_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Process a list of studies, applying the abstract extraction fallback where necessary.

    Args:
        studies: List of study dictionaries.
        pdf_base_dir: Base directory where PDFs are stored (e.g., data/raw/pdfs).
                      If None, assumes PDFs are named by study ID in a default location.

    Returns:
        List of enriched study dictionaries.
    """
    processed_studies = []
    
    if not pdf_base_dir:
        pdf_base_dir = str(get_data_path() / "raw" / "pdfs")

    for study in studies:
        study_id = study.get("id") or study.get("nct_id") or "unknown"
        
        # Construct expected PDF path
        # Assuming naming convention: {study_id}.pdf or {study_id}_abstract.pdf
        possible_names = [
            f"{study_id}.pdf",
            f"{study_id}_abstract.pdf",
            f"{study_id}_full.pdf"
        ]
        
        pdf_path = None
        for name in possible_names:
            candidate = os.path.join(pdf_base_dir, name)
            if os.path.exists(candidate):
                pdf_path = candidate
                break

        # Apply extraction logic
        enriched_study = extract_study_metadata(study, pdf_path)
        processed_studies.append(enriched_study)

    return processed_studies