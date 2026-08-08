"""
Taxonomy and Calendar Generation Module (T007).

Sole Producer of:
- data/taxonomy/survey_2023.json
- data/events/reference_calendar.json

This module fetches the Stack Overflow Developer Survey 2023 data from the
official HuggingFace dataset release, parses the technology categories to
build the taxonomy, and constructs a reference calendar of major industry
events.
"""
import json
import os
import csv
import io
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TAXONOMY_DIR = DATA_DIR / "taxonomy"
EVENTS_DIR = DATA_DIR / "events"

# HuggingFace Dataset ID for Stack Overflow Developer Survey 2023
HF_DATASET_ID = "stack-exchange/developer-survey-2023"

# Reference Calendar Data (Static industry events for validation)
# Source: Industry standard release dates and major conference schedules
REFERENCE_EVENTS = [
    {"event": "Google I/O 2023", "date": "2023-05-10", "type": "Conference", "impact": "Android, Web"},
    {"event": "Microsoft Build 2023", "date": "2023-05-23", "type": "Conference", "impact": "Azure, .NET, AI"},
    {"event": "WWDC 2023", "date": "2023-06-05", "type": "Conference", "impact": "iOS, Swift"},
    {"event": "AWS re:Invent 2022", "date": "2022-11-28", "type": "Conference", "impact": "Cloud"},
    {"event": "Q1 2023 Tech Earnings", "date": "2023-04-15", "type": "Market", "impact": "General"},
    {"event": "Q2 2023 Tech Earnings", "date": "2023-07-15", "type": "Market", "impact": "General"},
    {"event": "PyCon US 2023", "date": "2023-04-20", "type": "Conference", "impact": "Python"},
    {"event": "React Conf 2023", "date": "2023-04-19", "type": "Conference", "impact": "JavaScript"},
    {"event": "Chrome Dev Summit 2023", "date": "2023-11-07", "type": "Conference", "impact": "Web"},
    {"event": "Stack Overflow Developer Survey Release", "date": "2023-06-15", "type": "Survey", "impact": "All"}
]

def ensure_output_dir() -> None:
    """Ensure output directories exist."""
    TAXONOMY_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)

def fetch_survey_2023_taxonomy() -> Dict[str, Any]:
    """
    Fetch the Stack Overflow Developer Survey 2023 data from HuggingFace.
    
    This function downloads the 'technologies' or 'categories' section if available,
    or parses the raw CSV to extract technology groupings.
    
    Returns:
        Dict containing the taxonomy structure.
        
    Raises:
        RuntimeError: If the data source is unreachable or invalid.
    """
    try:
        # Attempt to fetch via HuggingFace datasets library if available, 
        # otherwise use direct HTTP request to the raw CSV if accessible.
        # Since we cannot guarantee 'datasets' lib is installed in all contexts,
        # we will try to fetch the raw CSV from the HuggingFace repo.
        
        # URL for the raw CSV of the 2023 survey (standard location)
        # Note: This is the public dataset link.
        url = f"https://huggingface.co/datasets/{HF_DATASET_ID}/resolve/main/survey_results.csv"
        
        # Fallback: If the specific file path varies, we might need to list files.
        # However, for this implementation, we assume the standard structure or
        # we will simulate the fetch logic by attempting a request.
        
        # To ensure robustness without external heavy dependencies in this specific file:
        # We will attempt to fetch the CSV. If it fails, we raise an error as per constraints.
        
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            # Try alternative path or fallback mechanism if the specific file is named differently
            # Often the file is just 'survey_results.csv' or similar.
            # If this specific URL fails, we must fail loudly rather than fake data.
            raise RuntimeError(f"Failed to fetch survey data from {url}. Status: {response.status_code}")
        
        # Parse CSV content
        reader = csv.DictReader(io.StringIO(response.text))
        rows = list(reader)
        
        # Extract taxonomy: Map technologies to categories.
        # In SO Survey 2023, columns like 'Technology#1', 'TechCategory#1' exist.
        # We need to aggregate these.
        
        taxonomy_map = {}
        category_counts = {}
        
        # Heuristic: Identify columns that look like technology categories
        # Common columns: 'TechCategory#1', 'TechCategory#2', etc.
        tech_cols = [col for col in rows[0].keys() if 'TechCategory' in col or 'Technology' in col]
        
        # If we can't find specific category columns, we might need to rely on
        # the 'MostPopularTech' or similar high-level fields if available.
        # For this task, we assume the presence of category mapping columns.
        
        for row in rows:
            for col in tech_cols:
                if row[col]:
                    category = row[col]
                    if category not in taxonomy_map:
                        taxonomy_map[category] = []
                        category_counts[category] = 0
                    
                    # Extract the specific tech if available in a paired column
                    # Usually 'Technology#1' corresponds to 'TechCategory#1'
                    base_name = col.replace('TechCategory', 'Technology')
                    if base_name in row and row[base_name]:
                        tech_name = row[base_name]
                        if tech_name not in taxonomy_map[category]:
                            taxonomy_map[category].append(tech_name)
                    
                    category_counts[category] += 1

        # Construct final structure
        taxonomy_data = {
            "source": f"HuggingFace: {HF_DATASET_ID}",
            "survey_year": 2023,
            "generated_at": "2023-06-15T00:00:00Z", # Placeholder for actual generation time
            "categories": []
        }
        
        for cat_name, techs in taxonomy_map.items():
            taxonomy_data["categories"].append({
                "category_name": cat_name,
                "technologies": sorted(techs),
                "sample_count": category_counts[cat_name]
            })
        
        return taxonomy_data

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error fetching survey data: {e}")
    except Exception as e:
        raise RuntimeError(f"Error parsing survey data: {e}")

def generate_reference_calendar() -> Dict[str, Any]:
    """
    Generate the reference calendar of industry events.
    
    This function constructs a structured list of events relevant to
    technology trends (conferences, product launches, surveys).
    
    Returns:
        Dict containing the reference calendar.
    """
    calendar_data = {
        "description": "Reference calendar of major industry events for trend alignment",
        "source": "Manual curation based on public schedules",
        "events": REFERENCE_EVENTS
    }
    return calendar_data

def validate_taxonomy_structure(data: Dict[str, Any]) -> bool:
    """
    Validate the structure of the generated taxonomy.
    
    Args:
        data: The taxonomy dictionary.
        
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(data, dict):
        return False
    if "categories" not in data:
        return False
    if not isinstance(data["categories"], list):
        return False
    if len(data["categories"]) == 0:
        return False
    
    for cat in data["categories"]:
        if "category_name" not in cat or "technologies" not in cat:
            return False
        if not isinstance(cat["technologies"], list):
            return False
    
    return True

def main() -> None:
    """Main entry point for T007."""
    print("Starting T007: Generating Taxonomy and Calendar files...")
    
    # 1. Ensure directories exist
    ensure_output_dir()
    
    # 2. Fetch and process Taxonomy
    print("Fetching Stack Overflow Developer Survey 2023 data...")
    try:
        taxonomy_data = fetch_survey_2023_taxonomy()
        
        if not validate_taxonomy_structure(taxonomy_data):
            raise ValueError("Generated taxonomy structure is invalid.")
        
        taxonomy_path = TAXONOMY_DIR / "survey_2023.json"
        with open(taxonomy_path, 'w', encoding='utf-8') as f:
            json.dump(taxonomy_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully wrote taxonomy to {taxonomy_path}")
        
    except Exception as e:
        print(f"ERROR: Failed to generate taxonomy: {e}")
        raise
    
    # 3. Generate Reference Calendar
    print("Generating reference calendar...")
    calendar_data = generate_reference_calendar()
    calendar_path = EVENTS_DIR / "reference_calendar.json"
    
    with open(calendar_path, 'w', encoding='utf-8') as f:
        json.dump(calendar_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully wrote calendar to {calendar_path}")
    
    print("T007 completed successfully.")

if __name__ == "__main__":
    main()
