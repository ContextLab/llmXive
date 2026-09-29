"""
API Collector for ClinicalTrials.gov and OSF.

Implements FR-001 (Data Ingestion) and FR-002 (Rate Limiting/Backoff).
Strictly enforces Constitution Principle VI (Registry Integrity).
"""
import json
import logging
import time
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests
from code.utils.logging import get_logger
from code.utils.config import get_config

# Configure logging
logger = get_logger(__name__)

# Constants for Constitution Principle VI
ALLOWED_REGISTRIES = ["ClinicalTrials.gov", "OSF"]
MOCK_DATA_PATH = "data/raw/mock_registry_response.json"
VERIFIED_SNAPSHOT_PATH = "data/raw/verified_snapshot_2026.json"

class APICollector:
    """
    Collects study data from ClinicalTrials.gov and OSF APIs.
    Implements exponential backoff and rate limiting.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.session = requests.Session()
        self.rate_limits = {
            "ClinicalTrials.gov": 3,  # requests per second
            "OSF": 5
        }
        self.last_request_time = {"ClinicalTrials.gov": 0, "OSF": 0}
        self.base_delay = 1.0
        self.max_delay = 60.0
        self.max_retries = 5

    def _rate_limit(self, registry: str):
        """Enforce rate limiting for a specific registry."""
        current_time = time.time()
        min_interval = 1.0 / self.rate_limits.get(registry, 1)
        time_since_last = current_time - self.last_request_time[registry]
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time[registry] = time.time()

    def _fetch_with_backoff(self, url: str, registry: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch data with exponential backoff."""
        attempt = 0
        while attempt < self.max_retries:
            try:
                self._rate_limit(registry)
                logger.info(f"Fetching {registry} URL: {url} with params: {params}")
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                attempt += 1
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"Request failed for {registry}: {e}. Retrying in {delay}s (attempt {attempt}/{self.max_retries})")
                time.sleep(delay)
        
        logger.error(f"Max retries exceeded for {registry}. Aborting.")
        raise RuntimeError(f"Failed to fetch data from {registry} after {self.max_retries} attempts.")

    def fetch_clinical_trials(self, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        Fetch studies from ClinicalTrials.gov.
        
        Args:
            start_year: Start year for search (inclusive)
            end_year: End year for search (inclusive)
        
        Returns:
            List of study records.
        """
        url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "format": "json",
            "query.cond": "mindfulness",  # Broad search term
            "query.cond": "autism",
            "limit": 100
        }
        
        # Note: ClinicalTrials.gov API v2 doesn't support direct year filtering in simple params
        # We fetch and filter client-side or use more complex query construction
        # For this implementation, we'll use a representative query structure
        
        data = self._fetch_with_backoff(url, "ClinicalTrials.gov", params)
        
        studies = []
        if "studies" in data:
            for study in data["studies"]:
                # Extract relevant fields and filter by year
                protocol_section = study.get("protocolSection", {})
                enrollment_info = protocol_section.get("enrollmentInfo", {})
                start_date = protocol_section.get("statusModule", {}).get("startDate", {}).get("date", "")
                
                # Simple year extraction (format: "Month Year" or "Year")
                year = None
                if start_date:
                    try:
                        year = int(start_date.split()[-1])
                    except (ValueError, IndexError):
                        pass
                
                if year and start_year <= year <= end_year:
                    studies.append({
                        "id": study.get("nctId"),
                        "title": protocol_section.get("designationModule", {}).get("title", ""),
                        "registry": "ClinicalTrials.gov",
                        "age_range": self._extract_age_range(protocol_section),
                        "diagnosis": "ASD",  # Filtered by query
                        "outcomes": self._extract_outcomes(protocol_section),
                        "abstract": protocol_section.get("descriptionModule", {}).get("briefSummary", ""),
                        "intervention_components": [],  # Extracted later by T017a
                        "delivery_format": "not-reported",  # Extracted later by T017b
                        "social_skill_domain": "not-reported",  # Extracted later by T017b
                        "follow_up": self._extract_follow_up(protocol_section),
                        "rater_type": "unknown",  # Extracted later by T022
                        "blinded_assessment_flag": False  # Extracted later by T022
                    })
        
        return studies

    def fetch_osf(self, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        Fetch studies from OSF.
        
        Args:
            start_year: Start year for search (inclusive)
            end_year: End year for search (inclusive)
        
        Returns:
            List of study records.
        """
        url = "https://api.osf.io/v2/registrations/"
        params = {
            "filter[tags]": "mindfulness,autism",
            "page[size]": 50
        }
        
        data = self._fetch_with_backoff(url, "OSF", params)
        
        studies = []
        if "data" in data:
            for study in data["data"]:
                attributes = study.get("attributes", {})
                created_date = attributes.get("date_created", "")
                
                # Extract year from ISO format date
                year = None
                if created_date:
                    try:
                        year = int(created_date.split("-")[0])
                    except (ValueError, IndexError):
                        pass
                
                if year and start_year <= year <= end_year:
                    studies.append({
                        "id": study.get("id"),
                        "title": attributes.get("title", ""),
                        "registry": "OSF",
                        "age_range": self._extract_age_range_osf(attributes),
                        "diagnosis": "ASD",
                        "outcomes": self._extract_outcomes_osf(attributes),
                        "abstract": attributes.get("description", ""),
                        "intervention_components": [],
                        "delivery_format": "not-reported",
                        "social_skill_domain": "not-reported",
                        "follow_up": None,
                        "rater_type": "unknown",
                        "blinded_assessment_flag": False
                    })
        
        return studies

    def _extract_age_range(self, protocol_section: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """Extract age range from ClinicalTrials.gov protocol section."""
        eligibility = protocol_section.get("eligibilityModule", {})
        criteria = eligibility.get("criteria", {})
        text = criteria.get("eligibilityCriteria", "")
        
        # Simple regex for age extraction
        import re
        match = re.search(r'(\d+)\s*[-to]+\s*(\d+)\s*years?', text, re.IGNORECASE)
        if match:
            return {"min": int(match.group(1)), "max": int(match.group(2))}
        
        # Try single age
        match = re.search(r'(\d+)\s*years?', text, re.IGNORECASE)
        if match:
            age = int(match.group(1))
            return {"min": age, "max": age}
        
        return None

    def _extract_age_range_osf(self, attributes: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """Extract age range from OSF attributes."""
        description = attributes.get("description", "")
        import re
        match = re.search(r'(\d+)\s*[-to]+\s*(\d+)\s*years?', description, re.IGNORECASE)
        if match:
            return {"min": int(match.group(1)), "max": int(match.group(2))}
        return None

    def _extract_outcomes(self, protocol_section: Dict[str, Any]) -> List[str]:
        """Extract outcome measures from ClinicalTrials.gov."""
        outcomes_module = protocol_section.get("outcomesModule", {})
        primary_outcomes = outcomes_module.get("primaryOutcomes", [])
        secondary_outcomes = outcomes_module.get("secondaryOutcomes", [])
        
        outcomes = []
        for outcome in primary_outcomes + secondary_outcomes:
            outcomes.append(outcome.get("measure", ""))
        
        return outcomes

    def _extract_outcomes_osf(self, attributes: Dict[str, Any]) -> List[str]:
        """Extract outcome measures from OSF."""
        # OSF doesn't have a structured outcomes field, extract from description
        description = attributes.get("description", "")
        # Placeholder: In real implementation, NLP would extract outcomes
        return []

    def _extract_follow_up(self, protocol_section: Dict[str, Any]) -> Optional[str]:
        """Extract follow-up duration from ClinicalTrials.gov."""
        outcomes_module = protocol_section.get("outcomesModule", {})
        primary_outcomes = outcomes_module.get("primaryOutcomes", [])
        
        for outcome in primary_outcomes:
            time_frame = outcome.get("timeFrame", "")
            if time_frame:
                return time_frame
        return None

    def collect(self, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        Collect data from all allowed registries.
        
        Args:
            start_year: Start year for search
            end_year: End year for search
        
        Returns:
            Combined list of studies from all registries.
        """
        all_studies = []
        
        # Fetch from ClinicalTrials.gov
        try:
            ct_studies = self.fetch_clinical_trials(start_year, end_year)
            all_studies.extend(ct_studies)
            logger.info(f"Collected {len(ct_studies)} studies from ClinicalTrials.gov")
        except Exception as e:
            logger.error(f"Failed to collect from ClinicalTrials.gov: {e}")
        
        # Fetch from OSF
        try:
            osf_studies = self.fetch_osf(start_year, end_year)
            all_studies.extend(osf_studies)
            logger.info(f"Collected {len(osf_studies)} studies from OSF")
        except Exception as e:
            logger.error(f"Failed to collect from OSF: {e}")
        
        return all_studies

def main():
    """
    Main entry point for the collector script.
    
    Usage:
        python code/data/collector.py --start-year 2015 --end-year 2024
    
    Logic:
        1. Check for CI_MODE environment variable.
        2. If CI_MODE=true, load verified snapshot (data/raw/verified_snapshot_2026.json).
        3. If CI_MODE=false or not set, fetch from real APIs.
        4. NEVER load mock data (data/raw/mock_registry_response.json) in production/CI.
        5. Log retrieval details to data/raw/retrieval_log.json.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect study data from registries")
    parser.add_argument("--start-year", type=int, required=True, help="Start year for search")
    parser.add_argument("--end-year", type=int, required=True, help="End year for search")
    args = parser.parse_args()
    
    # Ensure output directories exist
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    ci_mode = os.environ.get("CI_MODE", "").lower() == "true"
    logger.info(f"Running in {'CI' if ci_mode else 'Production'} mode")
    
    # Check for mock data in production/CI (strict enforcement)
    if os.path.exists(MOCK_DATA_PATH):
        raise RuntimeError("Mock data detected in production/CI run; aborting.")
    
    collector = APICollector()
    
    if ci_mode:
        # CI Mode: Load verified snapshot
        snapshot_path = Path(VERIFIED_SNAPSHOT_PATH)
        if not snapshot_path.exists():
            raise FileNotFoundError(
                f"Verified snapshot missing at {VERIFIED_SNAPSHOT_PATH}. "
                "CI requires real data snapshot to be present."
            )
        
        logger.info(f"Loading verified snapshot from {snapshot_path}")
        with open(snapshot_path, "r") as f:
            studies = json.load(f)
        
        logger.info(f"Loaded {len(studies)} studies from verified snapshot")
    else:
        # Production Mode: Fetch from APIs
        logger.info(f"Fetching data from registries for years {args.start_year}-{args.end_year}")
        studies = collector.collect(args.start_year, args.end_year)
        logger.info(f"Collected {len(studies)} total studies")
    
    # Save raw data
    output_file = Path("data/raw/studies_raw.json")
    with open(output_file, "w") as f:
        json.dump(studies, f, indent=2)
    
    # Log retrieval details
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "start_year": args.start_year,
        "end_year": args.end_year,
        "mode": "CI" if ci_mode else "Production",
        "count": len(studies),
        "output_file": str(output_file)
    }
    
    log_file = Path("data/raw/retrieval_log.json")
    if log_file.exists():
        with open(log_file, "r") as f:
            log_history = json.load(f)
    else:
        log_history = []
    
    log_history.append(log_entry)
    
    with open(log_file, "w") as f:
        json.dump(log_history, f, indent=2)
    
    logger.info(f"Saved {len(studies)} studies to {output_file}")
    logger.info(f"Updated retrieval log at {log_file}")

if __name__ == "__main__":
    main()