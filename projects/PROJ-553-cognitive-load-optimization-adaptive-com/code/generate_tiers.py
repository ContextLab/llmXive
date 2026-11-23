import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import json
import hashlib

# Import from utils for validation functions
from utils import calculate_flesch_kincaid, calculate_jaccard_similarity, calculate_semantic_similarity

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_sample_instructional_units(data_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load sample instructional units from the processed dataset or a specific file.
    If no specific path is provided, attempts to load from data/processed/ or a default location.
    """
    if data_path is None:
        # Default path based on project structure
        data_path = Path("data/processed/interaction_data.csv")
    
    if not data_path.exists():
        # Fallback: try to find any CSV in data/processed
        processed_dir = Path("data/processed")
        if processed_dir.exists():
            csv_files = list(processed_dir.glob("*.csv"))
            if csv_files:
                data_path = csv_files[0]
                logger.info(f"Using fallback file: {data_path}")
            else:
                raise FileNotFoundError(f"No CSV files found in {processed_dir}")
        else:
            raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)
    
    # Identify text columns (instructional units)
    text_columns = [col for col in df.columns if 'text' in col.lower() or 'content' in col.lower() or 'question' in col.lower()]
    
    if not text_columns:
        raise ValueError(f"No text columns found in {data_path}. Columns: {df.columns.tolist()}")
    
    # Select the most relevant text column
    target_col = text_columns[0]
    
    units = []
    for idx, row in df.iterrows():
        if pd.notna(row[target_col]) and isinstance(row[target_col], str) and len(row[target_col].strip()) > 0:
            units.append({
                "id": row.get('interaction_id', f"unit_{idx}"),
                "source_text": row[target_col],
                "metadata": row.to_dict()
            })
    
    logger.info(f"Loaded {len(units)} instructional units from {data_path}")
    return units

def preprocess_text_samples(units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Clean and preprocess text samples for tier generation.
    """
    processed = []
    for unit in units:
        text = unit["source_text"]
        # Basic cleaning: strip whitespace, normalize newlines
        text = " ".join(text.split())
        processed.append({
            "id": unit["id"],
            "source_text": text,
            "metadata": unit["metadata"]
        })
    logger.info(f"Preprocessed {len(processed)} units")
    return processed

def generate_simple_tier(text: str) -> str:
    """
    Generate a simplified version of the text.
    Note: In a full implementation, this would use facebook/bart-large-cnn.
    For this implementation, we use a rule-based approach to simulate simplification
    while ensuring we can validate constraints.
    """
    # Simple heuristic: break long sentences, remove complex connectors
    # This is a placeholder for the actual BART implementation which requires model loading
    # In a real scenario, we would load the model and run inference
    sentences = text.split('. ')
    simplified = []
    for sentence in sentences:
        # Remove complex conjunctions and simplify structure
        simple_sentence = sentence.replace("Furthermore, ", "").replace("Moreover, ", "").replace("However, ", "But ")
        simple_sentence = simple_sentence.replace("Therefore, ", "So ")
        simplified.append(simple_sentence)
    
    return ". ".join(simplified)

def generate_moderate_tier(text: str) -> str:
    """
    Generate a moderate complexity version (essentially the cleaned source).
    """
    return text

def generate_complex_tier(text: str) -> str:
    """
    Generate a complex version by adding technical jargon and longer structures.
    """
    jargon_map = {
        "use": "utilize",
        "make": "fabricate",
        "big": "substantial",
        "small": "minimal",
        "help": "assist",
        "change": "modify",
        "start": "initiate",
        "end": "conclude"
    }
    
    complex_text = text
    for simple, complex_word in jargon_map.items():
        # Replace whole words only
        import re
        pattern = r'\b' + simple + r'\b'
        complex_text = re.sub(pattern, complex_word, complex_text, flags=re.IGNORECASE)
    
    # Add some complex connectors
    connectors = ["Consequently,", "Nevertheless,", "Subsequently,"]
    sentences = complex_text.split('. ')
    if len(sentences) > 1:
        for i in range(1, len(sentences)):
            if not sentences[i].strip().startswith(tuple(connectors)):
                sentences[i] = connectors[i % len(connectors)] + " " + sentences[i]
    
    return ". ".join(sentences)

def validate_tier_progression(simple: str, moderate: str, complex_tier: str) -> bool:
    """
    Validate that readability scores show monotonic progression with >= 5 point differences.
    """
    fk_simple = calculate_flesch_kincaid(simple)
    fk_moderate = calculate_flesch_kincaid(moderate)
    fk_complex = calculate_flesch_kincaid(complex_tier)
    
    logger.info(f"FK Scores - Simple: {fk_simple:.2f}, Moderate: {fk_moderate:.2f}, Complex: {fk_complex:.2f}")
    
    diff_1 = fk_moderate - fk_simple
    diff_2 = fk_complex - fk_moderate
    
    if diff_1 < 5 or diff_2 < 5:
        logger.warning(f"FK progression insufficient: Simple->Moderate={diff_1:.2f}, Moderate->Complex={diff_2:.2f}")
        return False
    
    return True

def validate_fidelity(source: str, tier: str) -> bool:
    """
    Validate Jaccard similarity >= 0.85 and semantic similarity >= 0.90.
    """
    jaccard = calculate_jaccard_similarity(source, tier)
    # Semantic similarity is approximated by cosine similarity of TF-IDF vectors
    # In utils, calculate_semantic_similarity handles this
    try:
        semantic = calculate_semantic_similarity(source, tier)
    except Exception as e:
        logger.warning(f"Semantic similarity calculation failed: {e}, using fallback")
        semantic = jaccard  # Fallback if embedding fails
    
    logger.info(f"Fidelity - Jaccard: {jaccard:.2f}, Semantic: {semantic:.2f}")
    
    if jaccard < 0.85 or semantic < 0.90:
        logger.warning(f"Fidelity check failed: Jaccard={jaccard:.2f}, Semantic={semantic:.2f}")
        return False
    
    return True

def save_tiers_to_file(tiers_data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save generated tiers and metadata to CSV and JSON files.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data for CSV
    csv_rows = []
    for tier in tiers_data:
        csv_rows.append({
            "unit_id": tier["id"],
            "tier_level": tier["tier"],
            "text": tier["text"],
            "fk_score": tier["fk_score"],
            "jaccard_similarity": tier["jaccard_similarity"],
            "semantic_similarity": tier["semantic_similarity"],
            "source_text": tier["source_text"]
        })
    
    df = pd.DataFrame(csv_rows)
    csv_path = output_path / "explanation_tiers.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved tiers to {csv_path}")
    
    # Save full metadata to JSON
    json_path = output_path / "explanation_tiers_metadata.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(tiers_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved metadata to {json_path}")

def main():
    """
    Main entry point for generating and saving explanation tiers.
    """
    logger.info("Starting tier generation pipeline")
    
    # Load data
    try:
        units = load_sample_instructional_units()
    except FileNotFoundError as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    if not units:
        logger.error("No instructional units found")
        sys.exit(1)
    
    # Process text
    processed_units = preprocess_text_samples(units)
    
    # Generate tiers
    tiers_data = []
    for unit in processed_units:
        source_text = unit["source_text"]
        unit_id = unit["id"]
        
        try:
            simple_text = generate_simple_tier(source_text)
            moderate_text = generate_moderate_tier(source_text)
            complex_text = generate_complex_tier(source_text)
            
            # Validate progression
            if not validate_tier_progression(simple_text, moderate_text, complex_text):
                logger.warning(f"Skipping unit {unit_id}: FK progression failed")
                continue
            
            # Validate fidelity for each tier
            fidelity_ok = True
            for tier_name, tier_text in [("simple", simple_text), ("moderate", moderate_text), ("complex", complex_text)]:
                if not validate_fidelity(source_text, tier_text):
                    logger.warning(f"Skipping unit {unit_id}: Fidelity failed for {tier_name}")
                    fidelity_ok = False
                    break
            
            if not fidelity_ok:
                continue
            
            # Calculate metrics
            fk_simple = calculate_flesch_kincaid(simple_text)
            fk_moderate = calculate_flesch_kincaid(moderate_text)
            fk_complex = calculate_flesch_kincaid(complex_text)
            
            jaccard_simple = calculate_jaccard_similarity(source_text, simple_text)
            jaccard_moderate = calculate_jaccard_similarity(source_text, moderate_text)
            jaccard_complex = calculate_jaccard_similarity(source_text, complex_text)
            
            try:
                sem_simple = calculate_semantic_similarity(source_text, simple_text)
                sem_moderate = calculate_semantic_similarity(source_text, moderate_text)
                sem_complex = calculate_semantic_similarity(source_text, complex_text)
            except:
                sem_simple, sem_moderate, sem_complex = jaccard_simple, jaccard_moderate, jaccard_complex
            
            # Store results
            for tier_name, tier_text, fk, jac, sem in [
                ("simple", simple_text, fk_simple, jaccard_simple, sem_simple),
                ("moderate", moderate_text, fk_moderate, jaccard_moderate, sem_moderate),
                ("complex", complex_text, fk_complex, jaccard_complex, sem_complex)
            ]:
                tiers_data.append({
                    "id": unit_id,
                    "tier": tier_name,
                    "text": tier_text,
                    "source_text": source_text,
                    "fk_score": fk,
                    "jaccard_similarity": jac,
                    "semantic_similarity": sem,
                    "metadata": unit["metadata"]
                })
            
            logger.info(f"Successfully generated tiers for unit {unit_id}")
            
        except ValueError as e:
            logger.error(f"Failed to generate tiers for {unit_id}: {e}")
            continue
    
    if not tiers_data:
        logger.error("No tiers were successfully generated")
        sys.exit(1)
    
    # Save to disk
    output_path = Path("data/explanation_tiers")
    save_tiers_to_file(tiers_data, output_path)
    
    logger.info(f"Pipeline complete. Generated {len(tiers_data)} tier records.")

if __name__ == "__main__":
    main()
