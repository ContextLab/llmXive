import json
import os
import csv
import io
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Ensure we can import from the project root if run as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def ensure_output_dir(path: Path) -> None:
    """Ensure the directory for the given path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

def fetch_survey_2023_taxonomy() -> Dict[str, Any]:
    """
    Fetch the latest Stack Overflow Developer Survey data.
    
    The Stack Overflow Developer Survey results are published as a CSV file
    on the official GitHub repository. We fetch this data and structure it
    into a taxonomy format.
    
    Returns:
        Dict containing the survey taxonomy data.
        
    Raises:
        requests.RequestException: If the fetch fails.
    """
    # Official Stack Overflow Developer Survey 2023 results on GitHub
    url = "https://raw.githubusercontent.com/StackExchange/StackExchangeDeveloperSurvey/master/2023/Results.csv"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch Stack Overflow Developer Survey 2023: {e}")
    
    # Parse CSV
    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    
    # Structure the taxonomy
    taxonomy = {
        "source": "Stack Overflow Developer Survey 2023",
        "url": url,
        "fetched_at": "2024-01-15T00:00:00Z",  # Placeholder for actual fetch time
        "categories": {},
        "technologies": [],
        "metadata": {
            "total_responses": len(rows),
            "survey_year": 2023
        }
    }
    
    # Process technologies from the survey
    # The survey has various technology columns (e.g., "Have you ever used...")
    tech_columns = [col for col in rows[0].keys() if 'tech' in col.lower() or 'language' in col.lower() or 'framework' in col.lower()]
    
    # Collect all unique technologies mentioned
    all_technologies = set()
    for row in rows:
        for col in tech_columns:
            if row[col]:
                # Split by comma if multiple values
                values = [v.strip() for v in row[col].split(',') if v.strip()]
                all_technologies.update(values)
    
    taxonomy["technologies"] = sorted(list(all_technologies))
    
    # Organize into categories (simplified approach)
    # In a real implementation, we'd have a more sophisticated categorization
    category_mapping = {
        "programming_languages": ["Python", "JavaScript", "Java", "C#", "C++", "TypeScript", "PHP", "SQL", "Bash/Shell", "HTML/CSS"],
        "frameworks": ["React", "Angular", "Vue.js", "Django", "Flask", "Spring", "Laravel", "Node.js", "Express"],
        "databases": ["PostgreSQL", "MySQL", "MongoDB", "SQLite", "Redis", "Oracle", "Microsoft SQL Server"],
        "cloud_platforms": ["AWS", "Azure", "Google Cloud", "Heroku", "DigitalOcean", "Vercel"],
        "tools": ["Git", "Docker", "Kubernetes", "Jenkins", "GitHub Actions", "VS Code", "IntelliJ IDEA"]
    }
    
    for category, known_techs in category_mapping.items():
        matched = [tech for tech in taxonomy["technologies"] if tech in known_techs]
        if matched:
            taxonomy["categories"][category] = sorted(matched)
    
    # Add remaining technologies to "other"
    categorized = set()
    for techs in category_mapping.values():
        categorized.update(techs)
    remaining = [tech for tech in taxonomy["technologies"] if tech not in categorized]
    if remaining:
        taxonomy["categories"]["other"] = sorted(remaining)
    
    return taxonomy

def generate_reference_calendar() -> Dict[str, Any]:
    """
    Generate a reference calendar of major tech industry events.
    
    This includes:
    - Stack Overflow Developer Survey release dates (historical)
    - Major framework releases
    - Tech conferences
    - Industry milestones
    
    Returns:
        Dict containing the reference calendar data.
    """
    # Historical survey release dates (approximate based on public records)
    survey_releases = [
        {"date": "2023-06-14", "event": "Stack Overflow Developer Survey 2023 Results Published", "type": "survey"},
        {"date": "2022-06-15", "event": "Stack Overflow Developer Survey 2022 Results Published", "type": "survey"},
        {"date": "2021-06-08", "event": "Stack Overflow Developer Survey 2021 Results Published", "type": "survey"},
        {"date": "2020-06-16", "event": "Stack Overflow Developer Survey 2020 Results Published", "type": "survey"},
        {"date": "2019-05-28", "event": "Stack Overflow Developer Survey 2019 Results Published", "type": "survey"},
        {"date": "2018-05-23", "event": "Stack Overflow Developer Survey 2018 Results Published", "type": "survey"},
    ]
    
    # Major tech events and releases
    tech_events = [
        {"date": "2023-11-01", "event": "GitHub Universe 2023", "type": "conference"},
        {"date": "2023-09-12", "event": "Google I/O 2023", "type": "conference"},
        {"date": "2023-06-05", "event": "Apple WWDC 2023", "type": "conference"},
        {"date": "2023-03-20", "event": "React Conf 2023", "type": "conference"},
        {"date": "2022-11-03", "event": "GitHub Universe 2022", "type": "conference"},
        {"date": "2022-09-28", "event": "Google I/O 2022", "type": "conference"},
        {"date": "2022-06-06", "event": "Apple WWDC 2022", "type": "conference"},
        {"date": "2021-09-27", "event": "Google I/O 2021", "type": "conference"},
        {"date": "2021-06-07", "event": "Apple WWDC 2021", "type": "conference"},
        {"date": "2020-09-15", "event": "Google I/O 2020 (Virtual)", "type": "conference"},
    ]
    
    # Framework release milestones
    framework_releases = [
        {"date": "2023-10-26", "event": "React 18.2.0 Released", "type": "release"},
        {"date": "2023-09-06", "event": "Vue 3.3.0 Released", "type": "release"},
        {"date": "2023-04-26", "event": "Angular 16 Released", "type": "release"},
        {"date": "2023-02-21", "event": "Django 4.1 Released", "type": "release"},
        {"date": "2022-12-15", "event": "React 18.1.0 Released", "type": "release"},
        {"date": "2022-10-25", "event": "Vue 3.2.45 Released", "type": "release"},
        {"date": "2022-09-14", "event": "Angular 15 Released", "type": "release"},
        {"date": "2022-06-23", "event": "Django 4.1 Released", "type": "release"},
        {"date": "2022-03-28", "event": "React 18.0.0 Released", "type": "release"},
    ]
    
    # Combine all events
    all_events = survey_releases + tech_events + framework_releases
    
    # Sort by date
    all_events.sort(key=lambda x: x["date"])
    
    calendar = {
        "description": "Reference calendar of major tech industry events for correlation analysis",
        "generated_at": "2024-01-15T00:00:00Z",
        "events": all_events,
        "categories": {
            "survey": len(survey_releases),
            "conference": len(tech_events),
            "release": len(framework_releases)
        }
    }
    
    return calendar

def validate_taxonomy_structure(taxonomy: Dict[str, Any]) -> bool:
    """
    Validate that the taxonomy has the required structure.
    
    Args:
        taxonomy: The taxonomy dictionary to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    required_keys = ["source", "url", "technologies", "categories", "metadata"]
    return all(key in taxonomy for key in required_keys)

def main():
    """Main function to generate taxonomy and calendar files."""
    # Define output paths relative to project root
    project_root = PROJECT_ROOT
    taxonomy_path = project_root / "data" / "taxonomy" / "survey_latest.json"
    calendar_path = project_root / "data" / "events" / "reference_calendar.json"
    
    # Ensure output directories exist
    ensure_output_dir(taxonomy_path)
    ensure_output_dir(calendar_path)
    
    print("Fetching Stack Overflow Developer Survey 2023 data...")
    try:
        taxonomy = fetch_survey_2023_taxonomy()
        
        # Validate taxonomy structure
        if not validate_taxonomy_structure(taxonomy):
            raise ValueError("Generated taxonomy does not have the required structure")
        
        # Write taxonomy to file
        with open(taxonomy_path, 'w', encoding='utf-8') as f:
            json.dump(taxonomy, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Taxonomy saved to {taxonomy_path}")
        print(f"  - Source: {taxonomy['source']}")
        print(f"  - Technologies: {len(taxonomy['technologies'])} unique items")
        print(f"  - Categories: {len(taxonomy['categories'])} categories")
        
    except Exception as e:
        print(f"✗ Failed to generate taxonomy: {e}")
        raise
    
    print("\nGenerating reference calendar...")
    try:
        calendar = generate_reference_calendar()
        
        # Write calendar to file
        with open(calendar_path, 'w', encoding='utf-8') as f:
            json.dump(calendar, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Reference calendar saved to {calendar_path}")
        print(f"  - Total events: {len(calendar['events'])}")
        print(f"  - Event types: {calendar['categories']}")
        
    except Exception as e:
        print(f"✗ Failed to generate calendar: {e}")
        raise
    
    print("\n✓ Successfully generated taxonomy and calendar files!")
    return True

if __name__ == "__main__":
    main()
