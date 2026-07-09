"""
API Collector for ClinicalTrials.gov and OSF.

Implements FR-001 (Data Collection) and FR-002 (Rate Limiting/Backoff)
strictly for ClinicalTriols.gov and OSF as mandated by Constitution Principle VI.
"""
import json
import logging
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.logging import get_logger, log_event
from utils.config import get_output_path

logger = get_logger(__name__)

# Constants
MAX_RETRIES = 5
BACKOFF_FACTOR = 1.0
CT_API_BASE = "https://clinicaltrials.gov/api/v2/studies"
OSF_API_BASE = "https://api.osf.io/v2/registrations/"
CT_PAGE_SIZE = 100  # Max allowed by API
OSF_PAGE_SIZE = 20  # Max allowed by API

# Keywords for inclusion in meta-analysis (ASD + Mindfulness/Social Skills)
# We fetch broadly and filter later in the cleaner to avoid missing edge cases
SEARCH_QUERY_CT = "(Mindfulness OR 'Social Skills' OR 'Social Interaction') AND (Autism OR ASD)"
SEARCH_QUERY_OSF = "mindfulness autism social skills"

class APICollector:
    """
    Collects study metadata from ClinicalTrials.gov and OSF.
    Handles rate limiting, exponential backoff, and error recovery.
    """

    def __init__(self):
        self.session = self._create_session()
        self.collected_studies: List[Dict[str, Any]] = []
        self.excluded_studies: List[Dict[str, Any]] = []

    def _create_session(self) -> requests.Session:
        """
        Creates a requests session with retry logic for robustness.
        """
        session = requests.Session()
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _rate_limit_wait(self, retry_after: Optional[int] = None):
        """
        Implements exponential backoff and respects Retry-After headers.
        """
        if retry_after:
            wait_time = int(retry_after)
            logger.warning(f"Rate limited. Waiting {wait_time} seconds as per Retry-After header.")
        else:
            # Exponential backoff: 1s, 2s, 4s...
            wait_time = min(30, BACKOFF_FACTOR * (2 ** len(self.collected_studies) % 5))
            logger.warning(f"Rate limited or transient error. Waiting {wait_time:.1f} seconds (backoff).")
        
        time.sleep(wait_time)

    def _fetch_clinicaltrials(self) -> List[Dict[str, Any]]:
        """
        Fetches studies from ClinicalTrials.gov API v2.
        """
        studies = []
        page_token = None
        has_more = True

        logger.info("Starting ClinicalTrials.gov collection...")

        while has_more:
            params = {
                "query": SEARCH_QUERY_CT,
                "pageSize": CT_PAGE_SIZE,
                "format": "json",
                "fields": "nctId,basicInfo,protocolSection,conditions,armsInterventions,studyStatus"
            }
            
            if page_token:
                params["pageToken"] = page_token

            try:
                url = f"{CT_API_BASE}?{urlencode(params)}"
                logger.debug(f"Fetching CT page: {url}")
                resp = self.session.get(url, timeout=30)
                
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    self._rate_limit_wait(retry_after)
                    continue
                
                resp.raise_for_status()
                data = resp.json()
                
                if "studies" not in data:
                    logger.warning("No 'studies' key in response.")
                    break

                current_batch = data["studies"]
                studies.extend(current_batch)
                logger.info(f"Retrieved {len(current_batch)} studies from CT (Total: {len(studies)}).")

                page_token = data.get("nextPageToken")
                has_more = bool(page_token)
                
                # Safety break for demo purposes if we have enough, 
                # but for real research we might want to fetch all or a specific limit.
                # Let's cap at 500 to avoid infinite loops if API behaves oddly, 
                # though real usage might need more.
                if len(studies) >= 500:
                    logger.info("Reached safety cap of 500 studies for CT.")
                    break

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching ClinicalTrials.gov: {e}")
                self._rate_limit_wait()
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error from CT: {e}")
                break

        return studies

    def _fetch_osf(self) -> List[Dict[str, Any]]:
        """
        Fetches registrations from OSF API.
        Note: OSF search is less structured than CT, so we fetch recent 
        registrations and filter by title/description keywords.
        """
        registrations = []
        next_url = OSF_API_BASE
        
        # OSF doesn't support complex boolean search in the same way, 
        # so we fetch a batch and filter client-side.
        # We limit to 5 pages to avoid excessive API calls.
        max_pages = 5
        pages_fetched = 0

        logger.info("Starting OSF collection...")

        while next_url and pages_fetched < max_pages:
            try:
                logger.debug(f"Fetching OSF page: {next_url}")
                resp = self.session.get(next_url, params={"filter[tags]": "mindfulness,autism"}, timeout=30)
                
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    self._rate_limit_wait(retry_after)
                    continue
                
                resp.raise_for_status()
                data = resp.json()
                
                if "data" not in data:
                    break

                current_batch = data["data"]
                # Filter client-side for relevance
                relevant = [
                    item for item in current_batch 
                    if any(kw in (item.get("attributes", {}).get("title", "") + 
                                  item.get("attributes", {}).get("description", "")).lower() 
                           for kw in ["mindfulness", "autism", "asd", "social skill"])
                ]
                registrations.extend(relevant)
                logger.info(f"Retrieved {len(relevant)} relevant registrations from OSF (Total: {len(registrations)}).")

                next_url = data.get("links", {}).get("next")
                pages_fetched += 1

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching OSF: {e}")
                self._rate_limit_wait()
                break
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error from OSF: {e}")
                break

        return registrations

    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Orchestrates the collection from both sources.
        Returns a dictionary with 'clinicaltrials' and 'osf' keys.
        """
        logger.info("Starting full data collection pipeline.")
        
        ct_data = self._fetch_clinicaltrials()
        osf_data = self._fetch_osf()
        
        log_event("data_collection_complete", {
            "clinicaltrials_count": len(ct_data),
            "osf_count": len(osf_data),
            "total": len(ct_data) + len(osf_data)
        })

        return {
            "clinicaltrials": ct_data,
            "osf": osf_data
        }

    def save_raw_data(self, output_dir: Optional[str] = None):
        """
        Saves the collected raw data to JSON files in data/raw/.
        """
        if output_dir is None:
            output_dir = get_output_path("data/raw")
        
        import os
        os.makedirs(output_dir, exist_ok=True)

        raw_data = self.collect()
        
        # Save ClinicalTrials.gov data
        ct_path = os.path.join(output_dir, "clinicaltrials_raw.json")
        with open(ct_path, "w", encoding="utf-8") as f:
            json.dump(raw_data["clinicaltrials"], f, indent=2)
        logger.info(f"Saved ClinicalTrials.gov data to {ct_path}")

        # Save OSF data
        osf_path = os.path.join(output_dir, "osf_raw.json")
        with open(osf_path, "w", encoding="utf-8") as f:
            json.dump(raw_data["osf"], f, indent=2)
        logger.info(f"Saved OSF data to {osf_path}")

        return ct_path, osf_path

def main():
    """
    Entry point for the collector script.
    """
    collector = APICollector()
    try:
        ct_path, osf_path = collector.save_raw_data()
        print(f"Collection complete. Files saved:")
        print(f"  - {ct_path}")
        print(f"  - {osf_path}")
    except Exception as e:
        logger.critical(f"Collection failed: {e}")
        raise

if __name__ == "__main__":
    main()
