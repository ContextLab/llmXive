"""
Training Data Estimation Logic (Task T021)

Parses model cards (MD and PDF) to extract speech/music/env training hours.
Derives proxy estimates when explicit data is missing.
Outputs: data/training_data_estimates.yaml
"""
import os
import re
import logging
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Optional imports for PDF parsing
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("pdfplumber not installed. PDF parsing disabled.")

try:
    import PyPDF2
    PYPDF2_SUPPORT = True
except ImportError:
    PYPDF2_SUPPORT = False
    if not PDF_SUPPORT:
        logging.warning("Neither pdfplumber nor PyPDF2 installed. PDF parsing disabled.")

from config import load_config, get_model_list_path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TrainingEstimate:
    model_name: str
    speech_hours: Optional[float]
    music_hours: Optional[float]
    env_hours: Optional[float]
    uncertainty_notes: str

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text content from a PDF file."""
    text = ""
    if pdf_path.endswith('.pdf'):
        if PDF_SUPPORT:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                logger.error(f"Failed to parse {pdf_path} with pdfplumber: {e}")
        elif PYPDF2_SUPPORT:
            try:
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                logger.error(f"Failed to parse {pdf_path} with PyPDF2: {e}")
        else:
            logger.warning(f"PDF parsing requested for {pdf_path} but no library available.")
    return text

def parse_markdown_card(md_path: str) -> str:
    """Read raw text from a markdown file."""
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read {md_path}: {e}")
        return ""

def find_hours_in_text(text: str, domain: str) -> Optional[float]:
    """
    Search for explicit hour counts in text for a specific domain.
    Patterns: '100 hours', '100h', '100.5 hours of speech', '10k hours'.
    Returns None if not found.
    """
    if not text:
        return None

    # Normalize domain for search (e.g., 'speech' -> 'speech|audio|spoken')
    domain_patterns = {
        'speech': r'speech|audio|spoken|transcription|asr',
        'music': r'music|audio|musical|melody',
        'env': r'environment|ambient|noise|sound|esc|urban|nature'
    }
    
    # If domain is specific, try to match context, otherwise general audio
    keywords = domain_patterns.get(domain, domain)
    
    # Regex to find numbers followed by hours (e.g., 100 hours, 1.5k hours, 100h)
    # We look for numbers near the domain keywords
    # Pattern: number (with optional k/m suffix) followed by 'hours' or 'h'
    # Context: within 50 chars of domain keyword
    
    # Simple approach: Find all occurrences of hours first
    hour_pattern = r'(\d+(?:\.\d+)?(?:\s*[kmKMBB]?)?)\s*(?:hours?|hrs?|h)\b'
    matches = re.finditer(hour_pattern, text, re.IGNORECASE)
    
    found_hours = []
    for match in matches:
        number_str = match.group(1)
        suffix = number_str[-1].lower() if number_str[-1].lower() in ['k', 'm', 'b'] else ''
        try:
            num = float(number_str[:-1]) if suffix else float(number_str)
            if suffix == 'k': num *= 1000
            elif suffix == 'm': num *= 1_000_000
            elif suffix == 'b': num *= 1_000_000_000
            
            # Check context around the match
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].lower()
            
            if re.search(keywords, context):
                found_hours.append(num)
        except ValueError:
            continue
    
    # Return the largest match found for this domain (heuristic)
    return max(found_hours) if found_hours else None

def derive_proxy_estimate(text: str, domain: str, existing_hours: Optional[float]) -> Tuple[Optional[float], str]:
    """
    Derive a proxy estimate if explicit hours are missing.
    Strategies:
    1. Check for token counts and convert (assuming ~1 token = 4 bytes, ~4 bytes = 0.5s audio? -> rough heuristic)
       Actually, audio tokens vary wildly. Better to look for dataset names.
    2. Check for dataset names and use known sizes.
    3. Default fallback: 'unknown'
    """
    if existing_hours is not None:
        return existing_hours, "Explicit value found."

    # Heuristic: Look for dataset names
    dataset_map = {
        'librispeech': 1000, # 1000 hours
        'common_voice': 1000, # Approx 1000+ hours
        'fma': 1500, # ~1500 hours (80k tracks)
        'esc50': 20, # 20 hours
        'audiocaps': 50, # ~50 hours
        'soundscapes': 500, # Approx
        'musdb': 150, # ~150 hours
    }
    
    total_hours = 0.0
    found_datasets = []
    
    for ds_name, hours in dataset_map.items():
        if ds_name in text.lower():
            total_hours += hours
            found_datasets.append(ds_name)
    
    if found_datasets:
        # If we found datasets but they don't match the specific domain, 
        # we might need to filter, but for now we assume general audio coverage.
        # If domain is 'music' and we found 'fma', that's good.
        # If domain is 'speech' and we found 'librispeech', that's good.
        # If mixed, we return the sum with a note.
        return total_hours, f"Derived from datasets: {', '.join(found_datasets)}. Uncertainty: High."
    
    return None, "No explicit hours or known dataset sizes found. Proxy derivation failed."

def process_model_card(file_path: str) -> TrainingEstimate:
    """Process a single model card file."""
    name = Path(file_path).stem
    text = ""
    
    if file_path.endswith('.md'):
        text = parse_markdown_card(file_path)
    elif file_path.endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    
    if not text:
        return TrainingEstimate(
            model_name=name,
            speech_hours=None,
            music_hours=None,
            env_hours=None,
            uncertainty_notes="Could not extract text from file."
        )

    # Extract explicit hours
    speech_hours = find_hours_in_text(text, 'speech')
    music_hours = find_hours_in_text(text, 'music')
    env_hours = find_hours_in_text(text, 'env')

    notes = []
    
    # Derive proxies if missing
    if speech_hours is None:
        val, note = derive_proxy_estimate(text, 'speech', None)
        if val: speech_hours = val
        if note: notes.append(f"Speech: {note}")
    
    if music_hours is None:
        val, note = derive_proxy_estimate(text, 'music', None)
        if val: music_hours = val
        if note: notes.append(f"Music: {note}")
        
    if env_hours is None:
        val, note = derive_proxy_estimate(text, 'env', None)
        if val: env_hours = val
        if note: notes.append(f"Env: {note}")

    uncertainty_str = "; ".join(notes) if notes else "All values explicit."
    
    return TrainingEstimate(
        model_name=name,
        speech_hours=speech_hours,
        music_hours=music_hours,
        env_hours=env_hours,
        uncertainty_notes=uncertainty_str
    )

def main():
    config = load_config()
    model_cards_dir = config.get('model_cards_dir', 'data/model_cards')
    output_path = Path('data/training_data_estimates.yaml')
    
    if not os.path.exists(model_cards_dir):
        logger.error(f"Model cards directory not found: {model_cards_dir}")
        # Create empty output to prevent pipeline crash
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump([], f)
        return

    results = []
    for filename in os.listdir(model_cards_dir):
        if filename.endswith('.md') or filename.endswith('.pdf'):
            file_path = os.path.join(model_cards_dir, filename)
            logger.info(f"Processing {filename}...")
            estimate = process_model_card(file_path)
            results.append(asdict(estimate))
    
    # Sort by model name
    results.sort(key=lambda x: x['model_name'])
    
    # Write YAML
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(results, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Saved estimates to {output_path}")

if __name__ == '__main__':
    main()
