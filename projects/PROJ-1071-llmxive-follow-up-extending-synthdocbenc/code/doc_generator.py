"""
Synthetic Document Generator for SynthDocBench.
Generates exactly 200 synthetic long documents with precise 'middle-third' metadata.
Ensures every document has a valid 'middle-third' region with sufficient text density.
"""
import os
import json
import random
import hashlib
from typing import List, Dict, Any, Tuple
from dataclasses import asdict

# Import existing project utilities and models
from utils import pin_random_seed, compute_file_checksum, update_state_json, load_state_json
from logging_config import get_logger
from models.document import MiddleThirdMetadata, Page, Document

logger = get_logger(__name__)

# Constants
NUM_DOCUMENTS = 200
MIN_PAGES = 10
MAX_PAGES = 50
OUTPUT_DIR = "data/raw"
CHECKSUM_FILE = "data/checksums.json"
STATE_FILE = "data/state.json"
MIN_MIDDLE_THIRD_DENSITY = 0.4  # Minimum text density for middle third (40%)
TEXT_SOURCES = [
    "The quick brown fox jumps over the lazy dog. ",
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. ",
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ",
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris. ",
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum. ",
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia. ",
]

def generate_text_block(length: int) -> str:
    """Generate a block of text of approximate length."""
    result = []
    current_len = 0
    while current_len < length:
        segment = random.choice(TEXT_SOURCES)
        result.append(segment)
        current_len += len(segment)
    return "".join(result)[:length]

def calculate_text_density(text: str, page_width: int = 600, page_height: int = 800) -> float:
    """
    Calculate text density as the ratio of text area to page area.
    Approximation: text length / (page_width * page_height * density_factor)
    """
    if not text:
        return 0.0
    # Approximate characters per square inch (simplified)
    chars_per_area = 0.002  # Tuned for synthetic generation
    text_area = len(text) / chars_per_area
    page_area = page_width * page_height
    return min(1.0, text_area / page_area)

def generate_page(page_idx: int, total_pages: int, is_middle: bool = False) -> Tuple[Page, str]:
    """Generate a single page with text and metadata."""
    # Determine text density based on position
    if is_middle:
        # Ensure high density in middle third
        density = random.uniform(MIN_MIDDLE_THIRD_DENSITY, 0.8)
    else:
        # Variable density for other sections
        density = random.uniform(0.1, 0.6)

    # Calculate text length based on density
    page_area = 600 * 800
    chars_per_area = 0.002
    target_chars = int(density * page_area * chars_per_area)
    text = generate_text_block(target_chars)

    # Create page metadata
    page = Page(
        page_number=page_idx + 1,
        text=text,
        text_density=density,
        width=600,
        height=800,
        layout_type="standard"
    )
    return page, text

def generate_document(doc_id: int) -> Document:
    """Generate a single synthetic document."""
    num_pages = random.randint(MIN_PAGES, MAX_PAGES)
    middle_start = (num_pages // 3) + 1
    middle_end = (2 * num_pages // 3) + 1

    pages: List[Page] = []
    middle_text_parts: List[str] = []

    for i in range(num_pages):
        is_middle = middle_start <= i < middle_end
        page, text = generate_page(i, num_pages, is_middle)
        pages.append(page)
        if is_middle:
            middle_text_parts.append(text)

    # Calculate middle third metadata
    middle_text = "".join(middle_text_parts)
    middle_density = calculate_text_density(middle_text)

    # Ensure middle third meets density requirement
    if middle_density < MIN_MIDDLE_THIRD_DENSITY:
        # Boost density by adding more text to middle pages
        for page in pages[middle_start-1:middle_end]:
            extra_text = generate_text_block(500)
            page.text += extra_text
            page.text_density = calculate_text_density(page.text)

    middle_metadata = MiddleThirdMetadata(
        start_page=middle_start,
        end_page=middle_end,
        text_density=middle_density,
        total_chars=len(middle_text)
    )

    document = Document(
        doc_id=f"doc_{doc_id:04d}",
        pages=pages,
        middle_third=middle_metadata,
        total_pages=num_pages,
        total_chars=sum(len(p.text) for p in pages)
    )

    return document

def save_document(document: Document, output_dir: str) -> str:
    """Save document to PDF (simulated) and metadata JSON."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate PDF filename (simulated - in real implementation would use reportlab)
    pdf_path = os.path.join(output_dir, f"{document.doc_id}.pdf")
    
    # For this implementation, we create a placeholder PDF file
    # In a real scenario, this would use reportlab to generate actual PDFs
    with open(pdf_path, "wb") as f:
        # Write minimal valid PDF header and content
        f.write(b"%PDF-1.4\n")
        f.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        f.write(b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n")
        f.write(b"xref\n0 3\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n")
        f.write(b"trailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n116\n%%EOF\n")

    # Save metadata
    metadata_path = os.path.join(output_dir, f"{document.doc_id}.json")
    with open(metadata_path, "w") as f:
        json.dump(asdict(document), f, indent=2)

    return pdf_path

def generate_all_documents(num_docs: int = NUM_DOCUMENTS) -> List[str]:
    """Generate all documents and return list of PDF paths."""
    pin_random_seed(42)  # Reproducibility
    pdf_paths = []

    logger.info(f"Generating {num_docs} synthetic documents...")
    
    for i in range(num_docs):
        doc = generate_document(i)
        pdf_path = save_document(doc, OUTPUT_DIR)
        pdf_paths.append(pdf_path)
        
        # Validate middle third density
        if doc.middle_third.text_density < MIN_MIDDLE_THIRD_DENSITY:
            logger.warning(f"Document {doc.doc_id} has low middle-third density: {doc.middle_third.text_density}")
            # This should not happen due to our generation logic, but log if it does
        
        if (i + 1) % 50 == 0:
            logger.info(f"Generated {i + 1}/{num_docs} documents")

    return pdf_paths

def compute_checksums(pdf_paths: List[str]) -> Dict[str, str]:
    """Compute checksums for all generated files."""
    checksums = {}
    
    for pdf_path in pdf_paths:
        json_path = pdf_path.replace(".pdf", ".json")
        
        if os.path.exists(pdf_path):
          pdf_checksum = compute_file_checksum(pdf_path)
          checksums[pdf_path] = pdf_checksum
        
        if os.path.exists(json_path):
            json_checksum = compute_file_checksum(json_path)
            checksums[json_path] = json_checksum

    return checksums

def validate_documents(pdf_paths: List[str]) -> bool:
    """Validate that all documents meet requirements."""
    if len(pdf_paths) != NUM_DOCUMENTS:
        logger.error(f"Expected {NUM_DOCUMENTS} documents, got {len(pdf_paths)}")
        return False

    for pdf_path in pdf_paths:
        json_path = pdf_path.replace(".pdf", ".json")
        if not os.path.exists(json_path):
            logger.error(f"Missing metadata for {pdf_path}")
            return False

        with open(json_path, "r") as f:
            doc_data = json.load(f)
            middle_density = doc_data["middle_third"]["text_density"]
            if middle_density < MIN_MIDDLE_THIRD_DENSITY:
                logger.error(f"Document {doc_data['doc_id']} has insufficient middle-third density: {middle_density}")
                return False

    return True

def update_state(checksums: Dict[str, str]):
    """Update project state with generation results."""
    state = load_state_json(STATE_FILE)
    state["generation"] = {
        "status": "completed",
        "num_documents": NUM_DOCUMENTS,
        "output_dir": OUTPUT_DIR,
        "checksums": checksums,
        "timestamp": json.dumps({"status": "ok", "count": NUM_DOCUMENTS})
    }
    update_state_json(state)

def main():
    """Main entry point for document generation."""
    logger.info("Starting synthetic document generation...")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate documents
    pdf_paths = generate_all_documents(NUM_DOCUMENTS)
    
    # Validate generation
    if not validate_documents(pdf_paths):
        logger.error("Document validation failed!")
        return 1
    
    logger.info(f"Successfully generated {len(pdf_paths)} documents")
    
    # Compute and save checksums
    checksums = compute_checksums(pdf_paths)
    with open(CHECKSUM_FILE, "w") as f:
        json.dump(checksums, f, indent=2)
    
    # Update state
    update_state(checksums)
    
    logger.info(f"Checksums saved to {CHECKSUM_FILE}")
    logger.info("Document generation completed successfully!")
    return 0

if __name__ == "__main__":
    exit(main())