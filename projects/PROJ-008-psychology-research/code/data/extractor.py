"""
Data extractor module for the Psychology Research pipeline.

Implements FR-003: Extract standardized variables including intervention components
and delivery formats from study metadata using regex patterns.
"""

import logging
import os
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

import pdfplumber

from code.utils.logging import get_logger
from code.data.models import MindfulnessComponent, DeliveryFormat, BlindingStatus

# Initialize logger
logger = get_logger(__name__)

# Regex patterns for intervention components (FR-003)
# These patterns match common mindfulness components mentioned in ASD literature
COMPONENT_PATTERNS = {
    MindfulnessComponent.BREATHING: r'\b(breath|breathing|respirat|inhale|exhale)\b',
    MindfulnessComponent.BODY_SCAN: r'\b(body\s*scan|body\s*awareness|somat|propriocept)\b',
    MindfulnessComponent.MEDITATION: r'\b(meditat|mindful\s*meditat|silent\s*practice)\b',
    MindfulnessComponent.MINDFUL_MOVEMENT: r'\b(mindful\s*mov|yoga|tai\s*chi|qigong|stretch)\b',
    MindfulnessComponent.OBSERVING: r'\b(observ|notic|aware\s*of|attend\s*to)\b',
    MindfulnessComponent.DESCRIBING: r'\b(describ|label|name\s*emotion|verbaliz)\b',
    MindfulnessComponent.NON_JUDGMENTAL: r'\b(non[-\s]?judgment|non[-\s]?evalu|accept\s*without\s*judgment|acceptance)\b',
    MindfulnessComponent.ONE_MINDFULNESS: r'\b(one\s*mindful|single\s*task|focus\s*on\s*one)\b',
}

# Regex patterns for delivery formats
DELIVERY_FORMAT_PATTERNS = {
    DeliveryFormat.INDIVIDUAL: r'\b(individual|one[-\s]?on[-\s]?one|1[-\s]?on[-\s]?1|personalized\s*session)\b',
    DeliveryFormat.GROUP: r'\b(group|class|session\s*with\s*peers|multi[-\s]?participant)\b',
    DeliveryFormat.PARENT_DELIVERED: r'\b(parent[-\s]?delivered|caregiver[-\s]?led|parent[-\s]?training|family[-\s]?based)\b',
    DeliveryFormat.SCHOOL_BASED: r'\b(school[-\s]?based|classroom|teacher[-\s]?delivered|educational\s*setting)\b',
    DeliveryFormat.TELEHEALTH: r'\b(teles|telehealth|virtual|online|remote|video\s*call|zoom|webinar)\b',
    DeliveryFormat.HYBRID: r'\b(hybrid|mixed\s*mode|combination|both\s*in[-\s]?person\s*and\s*remote)\b',
}

# Regex for blinding status
BLINDING_PATTERNS = {
    BlindingStatus.SINGLE_BLIND: r'\b(single[-\s]?blind|assessor[-\s]?blind|outcome\s*assessor\s*blinded)\b',
    BlindingStatus.DOUBLE_BLIND: r'\b(double[-\s]?blind|both\s*participant\s*and\s*assessor\s*blinded)\b',
    BlindingStatus.UNBLINDED: r'\b(unblinded|open[-\s]?label|no\s*blinding|assessor\s*aware)\b',
}

def extract_intervention_components(text: str) -> List[str]:
    """
    Extract mindfulness intervention components from text using regex patterns.
    
    Args:
        text: The text to analyze (abstract, methods, or intervention description)
    
    Returns:
        List of detected MindfulnessComponent values as strings
    """
    if not text:
        return []
    
    text_lower = text.lower()
    detected_components = []
    
    for component, pattern in COMPONENT_PATTERNS.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            detected_components.append(component.value)
            logger.debug(f"Detected component '{component.value}' in text")
    
    # If no components detected, return empty list (study may not be mindfulness-based)
    return detected_components

def extract_delivery_format(text: str) -> Optional[str]:
    """
    Extract delivery format from text using regex patterns.
    
    Args:
        text: The text to analyze
    
    Returns:
        Detected DeliveryFormat value as string, or None if not found
    """
    if not text:
        return None
    
    text_lower = text.lower()
    detected_formats = []
    
    for format_type, pattern in DELIVERY_FORMAT_PATTERNS.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            detected_formats.append(format_type.value)
            logger.debug(f"Detected delivery format '{format_type.value}' in text")
    
    # Prioritize: if hybrid mentioned, return hybrid; otherwise first match
    if DeliveryFormat.HYBRID.value in detected_formats:
        return DeliveryFormat.HYBRID.value
    
    return detected_formats[0] if detected_formats else None

def extract_blinding_status(text: str) -> str:
    """
    Extract blinding status from text using regex patterns.
    
    Args:
        text: The text to analyze (typically methods section)
    
    Returns:
        BlindingStatus value as string, defaulting to 'not-reported'
    """
    if not text:
        return BlindingStatus.NOT_REPORTED.value
    
    text_lower = text.lower()
    
    # Check patterns in order of specificity
    for status, pattern in BLINDING_PATTERNS.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.debug(f"Detected blinding status '{status.value}' in text")
            return status.value
    
    return BlindingStatus.NOT_REPORTED.value

def extract_study_metadata(study_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract standardized metadata from a study record.
    
    Args:
        study_data: Raw study data from collector (dict with keys like 'title', 
                   'abstract', 'methods', 'intervention', etc.)
    
    Returns:
        Dictionary with extracted standardized fields
    """
    if not study_data:
        return {}
    
    # Combine relevant text fields for extraction
    text_for_extraction = " ".join([
        str(study_data.get('title', '')),
        str(study_data.get('abstract', '')),
        str(study_data.get('methods', '')),
        str(study_data.get('intervention', '')),
        str(study_data.get('description', '')),
    ]).strip()
    
    # Extract components
    components = extract_intervention_components(text_for_extraction)
    
    # Extract delivery format
    delivery_format = extract_delivery_format(text_for_extraction)
    
    # Extract blinding status (prefer methods section)
    methods_text = str(study_data.get('methods', ''))
    blinding_status = extract_blinding_status(methods_text)
    
    extracted = {
        'intervention_components': components,
        'delivery_format': delivery_format,
        'assessor_blinding': blinding_status,
    }
    
    # Log extraction results
    logger.info(f"Extracted metadata: {len(components)} components, "
               f"format={delivery_format}, blinding={blinding_status}")
    
    return extracted

def extract_abstract_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract abstract text from a PDF file using pdfplumber.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Extracted abstract text, or None if extraction fails
    """
    if not pdf_path or not os.path.exists(pdf_path):
        logger.warning(f"PDF file not found: {pdf_path}")
        return None
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Try first few pages for abstract
            for i, page in enumerate(pdf.pages[:3]):
                text = page.extract_text()
                if text:
                    # Look for abstract section
                    abstract_match = re.search(
                        r'(?:abstract|summary)[\s:]*([\s\S]*?)(?:\n\n|\n[A-Z]{3,}|$)',
                        text.lower(),
                        re.IGNORECASE
                    )
                    if abstract_match:
                        logger.debug(f"Extracted abstract from page {i+1}")
                        return abstract_match.group(1).strip()
                    
                    # If no explicit "Abstract" label, return first paragraph
                    paragraphs = text.split('\n\n')
                    if paragraphs:
                        logger.debug(f"Extracted first paragraph from page {i+1}")
                        return paragraphs[0].strip()
        
        logger.warning(f"No abstract found in PDF: {pdf_path}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to extract from PDF {pdf_path}: {e}")
        return None

def process_studies_with_fallback(studies: List[Dict[str, Any]], 
                                 pdf_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Process a list of studies, extracting metadata and attempting PDF extraction
    if registry data is insufficient.
    
    Args:
        studies: List of study records from collector
        pdf_dir: Optional directory containing PDF files for abstract extraction
    
    Returns:
        List of processed studies with extracted metadata
    """
    processed_studies = []
    
    for study in studies:
        study_id = study.get('id', 'unknown')
        logger.info(f"Processing study {study_id}")
        
        # Extract metadata from registry data
        extracted = extract_study_metadata(study)
        
        # Check if registry data is sufficient
        has_components = len(extracted.get('intervention_components', [])) > 0
        has_format = extracted.get('delivery_format') is not None
        
        # If insufficient, attempt PDF extraction (abstract only)
        if pdf_dir and (not has_components or not has_format):
            pdf_path = os.path.join(pdf_dir, f"{study_id}.pdf")
            if os.path.exists(pdf_path):
                logger.info(f"Attempting PDF extraction for {study_id}")
                abstract_text = extract_abstract_from_pdf(pdf_path)
                
                if abstract_text:
                    # Re-extract using abstract text
                    additional_extracted = extract_study_metadata({
                        'abstract': abstract_text
                    })
                    
                    # Merge results
                    if not has_components:
                        extracted['intervention_components'] = additional_extracted.get('intervention_components', [])
                    if not has_format:
                        extracted['delivery_format'] = additional_extracted.get('delivery_format')
                    
                    # Add abstract text to study
                    study['abstract_text'] = abstract_text
                    
                    logger.info(f"PDF extraction successful for {study_id}")
            else:
                logger.warning(f"PDF not found for {study_id}: {pdf_path}")
        
        # Combine extracted data with original study
        processed_study = {**study, **extracted}
        processed_studies.append(processed_study)
        
        # Log if study is still insufficient
        if not has_components and not has_format:
            logger.warning(f"Study {study_id} has insufficient data for inclusion")
    
    logger.info(f"Processed {len(processed_studies)} studies")
    return processed_studies