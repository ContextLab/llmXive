"""
API Collector for ClinicalTrials.gov and OSF.

Implements FR-001, FR-002 with rate-limiting and exponential backoff.
Enforces Constitution Principle VI by limiting sources to ClinicalTrials.gov and OSF.
Logs retrieval metadata to data/raw/retrieval_log.json for audit compliance.
"""
import json
import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, urljoin
import requests

from code.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
CLINICALTRIALS_BASE = "https://clinicaltrials.gov/api/v2"
OSF_BASE = "https://api.osf.io/v2"
RATE_LIMIT_DELAY = 1.0  # seconds between requests
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 60.0

# Audit log path relative to project root
AUDIT_LOG_PATH = "data/raw/retrieval_log.json"

class APICollector:
    """
    Collector for retrieving study data from ClinicalTrials.gov and OSF.

    Implements rate-limiting, exponential backoff, and audit logging.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "llmXive-Research-Collector/1.0"
        })
        self.last_request_time = 0
        self.audit_log: List[Dict[str, Any]] = []

    def _log_audit_event(self, query: str, source: str, success: bool,
                          record_count: int, error: Optional[str] = None):
        """
        Log retrieval event to memory and persist to JSON file.

        Satisfies Constitution Principle VI audit requirements.
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "query": query,
            "success": success,
            "record_count": record_count,
            "error": error
        }
        self.audit_log.append(event)

        # Persist immediately to ensure durability
        try:
            # Ensure directory exists
            log_path = AUDIT_LOG_PATH
            import os
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

            # Append to file (or create if new)
            with open(log_path, "r") as f:
                existing_log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_log = []

        existing_log.append(event)

        with open(log_path, "w") as f:
            json.dump(existing_log, f, indent=2)

        logger.info(f"Audit logged: {source} query '{query[:50]}...' -> {'SUCCESS' if success else 'FAILED'}")

    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            sleep_time = RATE_LIMIT_DELAY - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _fetch_with_backoff(self, url: str, params: Dict[str, Any],
                             source: str, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch data with exponential backoff and retry logic.

        Returns list of records or None on failure.
        """
        attempt = 0
        backoff = INITIAL_BACKOFF

        while attempt < MAX_RETRIES:
            self._wait_for_rate_limit()
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Successfully fetched from {source}: {len(data.get('data', data.get('results', [])))} records")
                return data.get('data', data.get('results', []))
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    logger.warning(f"Rate limit hit on {source}. Backing off for {backoff}s")
                    time.sleep(backoff)
                    backoff = min(backoff * 2, MAX_BACKOFF)
                    attempt += 1
                    continue
                else:
                    logger.error(f"HTTP Error {e.response.status_code} on {source}: {str(e)}")
                    self._log_audit_event(query, source, False, 0, str(e))
                    return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed on {source}: {str(e)}")
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF)
                attempt += 1
                continue

        logger.error(f"Max retries exceeded for {source} query: {query}")
        self._log_audit_event(query, source, False, 0, "Max retries exceeded")
        return None

    def fetch_clinicaltrials_studies(self, search_query: str,
                                     age_range: str = "6-12",
                                     max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch studies from ClinicalTrials.gov matching criteria.

        Args:
            search_query: Search string for the API (e.g., "mindfulness ASD social skills")
            age_range: Age range filter (default "6-12" per inclusion criteria)
            max_results: Maximum number of results to fetch

        Returns:
            List of study records
        """
        source = "ClinicalTrials.gov"
        logger.info(f"Fetching from {source} with query: {search_query}")

        # Construct ClinicalTrials.gov v2 API query
        # Note: API v2 uses a different structure than v1
        endpoint = urljoin(CLINICALTRIALS_BASE, "/studies")
        params = {
            "query": search_query,
            "limit": max_results,
            "fields": "nctId,briefTitle,briefSummary,conditions,interventions,eligibilityCriteria,studyType,phase,startDate,completionDate,hasResults,overallStatus,studyIds,protocolSection"
        }

        # Add age filter if supported by API (ClinicalTrials.gov v2 may require specific filters)
        # The API structure for age filters might vary; using general query for now
        # Specific age filtering might need to be done post-fetch or via advanced query syntax

        results = self._fetch_with_backoff(endpoint, params, source, search_query)

        if results:
            self._log_audit_event(search_query, source, True, len(results))
            return results
        return []

    def fetch_osf_studies(self, search_query: str,
                          max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch studies from OSF (Open Science Framework) matching criteria.

        Args:
            search_query: Search string for the API
            max_results: Maximum number of results to fetch

        Returns:
            List of study records
        """
        source = "OSF"
        logger.info(f"Fetching from {source} with query: {search_query}")

        # OSF API v2 endpoint for registrations
        endpoint = urljoin(OSF_BASE, "/registrations/")
        params = {
            "filter[title]": search_query,
            "page[size]": max_results,
            "fields[registration]": "title,description,registration_type,contributors,date_registered,date_modified,license,category,access",
            "sort": "-date_registered"
        }

        # OSF API requires pagination; fetch first page
        results = self._fetch_with_backoff(endpoint, params, source, search_query)

        if results:
            self._log_audit_event(search_query, source, True, len(results))
            return results
        return []

    def collect_all_studies(self, search_queries: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect studies from all allowed sources using provided search queries.

        Args:
            search_queries: List of search queries to execute

        Returns:
            Dictionary mapping source name to list of study records
        """
        all_studies = {
            "ClinicalTrials.gov": [],
            "OSF": []
        }

        for query in search_queries:
            # Fetch from ClinicalTrials.gov
            ct_results = self.fetch_clinicaltrials_studies(query)
            all_studies["ClinicalTrials.gov"].extend(ct_results)

            # Fetch from OSF
            osf_results = self.fetch_osf_studies(query)
            all_studies["OSF"].extend(osf_results)

        total_count = sum(len(v) for v in all_studies.values())
        logger.info(f"Collection complete. Total studies: {total_count}")

        return all_studies

def main():
    """
    Main entry point for the API collector.

    Executes a predefined search strategy for mindfulness and social skills
    in children with ASD, collects data from ClinicalTrials.gov and OSF,
    and logs all retrieval events.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    collector = APICollector()

    # Define search strategy per research plan
    # Queries target mindfulness interventions for social skills in ASD children
    search_queries = [
        "mindfulness social skills autism spectrum disorder children",
        "mindfulness intervention ASD social skills 6-12 years",
        "mindfulness based social skills training autism"
    ]

    logger.info("Starting data collection for mindfulness and social skills in ASD")

    try:
        results = collector.collect_all_studies(search_queries)

        # Log summary
        for source, studies in results.items():
            logger.info(f"{source}: {len(studies)} studies retrieved")

        logger.info("Data collection completed successfully")
        return results

    except Exception as e:
        logger.error(f"Data collection failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()