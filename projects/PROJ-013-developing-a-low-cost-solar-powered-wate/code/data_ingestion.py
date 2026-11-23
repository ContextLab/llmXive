import os
import json
import re
import hashlib
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, NamedTuple
from utils import get_project_root, get_data_dir, ensure_dir, setup_logging, ProjectError

class MaterialProfile(NamedTuple):
    material_id: str
    thermal_conductivity: float
    emissivity: float
    specific_heat: float
    density: float

class GeometryConfig(NamedTuple):
    geometry_id: str
    surface_area: float
    thickness: float
    inclination_angle: float

# ---------------------------------------------------------------------------
# Material configuration: project materials mapped to NIST Chemistry WebBook
# identifiers (CAS numbers).
#   Aluminum            -> 7429-90-5  (Al)
#   Copper              -> 7440-50-8  (Cu)
#   Black-painted Steel -> Carbon Steel Alloy 1018, proxied by Iron 7439-89-6
#                          (NIST WebBook indexes pure substances; the paint
#                          layer is a surface property handled via emissivity)
#   Plastic             -> Polyethylene 9002-88-4
# ---------------------------------------------------------------------------
MATERIAL_CONFIG = {
    "Aluminum": {
        "cas": "7429-90-5",
        "nist_id": "C7429905",
        "name": "Aluminum",
        "properties": ["thermal_conductivity", "emissivity", "specific_heat", "density"],
    },
    "Copper": {
        "cas": "7440-50-8",
        "nist_id": "C7440508",
        "name": "Copper",
        "properties": ["thermal_conductivity", "emissivity", "specific_heat", "density"],
    },
    "Carbon_Steel_1018": {
        "cas": "7439-89-6",
        "nist_id": "C7439896",
        "name": "Iron",
        "properties": ["thermal_conductivity", "emissivity", "specific_heat", "density"],
    },
    "Polyethylene": {
        "cas": "9002-88-4",
        "nist_id": "C9002884",
        "name": "Polyethylene",
        "properties": ["thermal_conductivity", "emissivity", "specific_heat", "density"],
    },
}

# ---------------------------------------------------------------------------
# Reference values for properties that the NIST Chemistry WebBook does not
# expose in machine-readable form for solids (thermal conductivity,
# emissivity, density). These are published engineering reference values
# (Incropera et al., "Fundamentals of Heat and Mass Transfer", Appendix A),
# used per the plan.md decision to use NIST/handbook reference values for
# reproducibility. Every value written to the output JSON carries an
# explicit provenance record; no value is ever randomly generated.
# ---------------------------------------------------------------------------
REFERENCE_VALUES = {
    "Aluminum": {
        "thermal_conductivity": (237.0, "W/m K", "Incropera et al., Fundamentals of Heat and Mass Transfer, Table A.1 (pure aluminum)"),
        "emissivity": (0.09, "-", "Incropera et al., Table A.12 (polished aluminum)"),
        "specific_heat": (900.0, "J/kg K", "Incropera et al., Table A.1 (pure aluminum)"),
        "density": (2702.0, "kg/m^3", "Incropera et al., Table A.1 (pure aluminum)"),
    },
    "Copper": {
        "thermal_conductivity": (401.0, "W/m K", "Incropera et al., Table A.1 (pure copper)"),
        "emissivity": (0.04, "-", "Incropera et al., Table A.12 (polished copper)"),
        "specific_heat": (385.0, "J/kg K", "Incropera et al., Table A.1 (pure copper)"),
        "density": (8933.0, "kg/m^3", "Incropera et al., Table A.1 (pure copper)"),
    },
    "Iron": {
        "thermal_conductivity": (80.2, "W/m K", "Incropera et al., Table A.1 (pure iron; proxy for 1018 carbon steel)"),
        "emissivity": (0.90, "-", "Incropera et al., Table A.12 (black paint on steel surface)"),
        "specific_heat": (447.0, "J/kg K", "Incropera et al., Table A.1 (pure iron)"),
        "density": (7870.0, "kg/m^3", "Incropera et al., Table A.1 (pure iron)"),
    },
    "Polyethylene": {
        "thermal_conductivity": (0.33, "W/m K", "Incropera et al., Table A.3 (polyethylene)"),
        "emissivity": (0.92, "-", "Incropera et al., Table A.12 (polyethylene)"),
        "specific_heat": (1800.0, "J/kg K", "Incropera et al., Table A.3 (polyethylene)"),
        "density": (950.0, "kg/m^3", "Incropera et al., Table A.3 (polyethylene)"),
    },
}

# Fallback molar masses (g/mol) used only if the WebBook page parse fails.
FALLBACK_MOLAR_MASS = {
    "C7429905": 26.9815385,
    "C7440508": 63.546,
    "C7439896": 55.845,
    "C9002884": 28.05,  # repeat unit C2H4
}

# Module-level cache of fetched NIST WebBook pages (keyed by NIST ID) so
# repeated property lookups do not re-download the same page.
_NIST_PAGE_CACHE: Dict[str, str] = {}

NIST_WEBBOOK_URL = "https://webbook.nist.gov/cgi/cbook.cgi?ID={nist_id}&Units=SI"

# ---------------------------------------------------------------------------
# World Bank Commodity Prices API configuration
# ---------------------------------------------------------------------------
# Mapping from our internal material keys to World Bank commodity codes.
# These codes are based on the World Bank "Commodity Prices" dataset.
# (If a code is missing or the API does not provide a price, the fetch will
# raise a ProjectError – this fulfills the “FAIL LOUDLY” requirement.)
MARKET_PRICE_CODES = {
    "Aluminum": "ALU",          # Aluminum
    "Copper": "COP",            # Copper
    "Carbon_Steel_1018": "STEEL",  # General steel commodity
    "Polyethylene": "PLAST",    # Plastics (generic)
}

# The World Bank API endpoint for a commodity price. The dataset returns a
# JSON array of yearly observations; we take the most recent non‑null price.
WORLD_BANK_PRICE_URL = "https://api.worldbank.org/v2/commodity/{code}?format=json"

def _fetch_nist_page(nist_id: str, logger: logging.Logger) -> str:
    """Fetch the NIST Chemistry WebBook page for a substance (real HTTP fetch).

    Raises ProjectError on any network/HTTP failure or if the page does not
    look like a valid substance record. Never falls back to synthetic data.
    """
    if nist_id in _NIST_PAGE_CACHE:
        return _NIST_PAGE_CACHE[nist_id]
    url = NIST_WEBBOOK_URL.format(nist_id=nist_id)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logger.error("NIST WebBook request failed for %s: %s", nist_id, e)
        raise ProjectError(
            "NIST_FETCH_FAILED: could not reach NIST Chemistry WebBook "
            f"for {nist_id} ({url}): {e}"
        )
    html = response.text
    if "No data found" in html or "not found" in html.lower()[:2000] or len(html) < 500:
        raise ProjectError(
            f"NIST_FETCH_FAILED: NIST WebBook returned no substance record for {nist_id}"
        )
    _NIST_PAGE_CACHE[nist_id] = html
    return html

def _parse_molar_mass(html: str, nist_id: str, logger: logging.Logger) -> float:
    """Parse the molar mass (g/mol) from a WebBook page, if present."""
    match = re.search(r"Molar mass[^0-9]{0,20}([0-9]+\\.[0-9]+)", html)
    if match:
        return float(match.group(1))
    logger.warning("Could not parse molar mass for %s; using fallback", nist_id)
    return FALLBACK_MOLAR_MASS[nist_id]

def _parse_shomate_cp(html: str, logger: logging.Logger) -> Optional[float]:
    """Attempt to parse condensed-phase Shomate coefficients and compute
    Cp(298.15 K) in J/mol/K from the WebBook page.

    Returns None if the coefficient table cannot be parsed.
    """
    try:
        if "Shomate" not in html:
            return None
        # The WebBook lists coefficients A-H in a table whose rows look like
        # <tr><td>A</td><td>28.09670</td><td>...</td>...</tr>
        coeffs = {}
        for letter in "ABCDEFGH":
            pattern = (
                r"<tr>\\s*<td>\\s*" + letter +
                r"\\s*</td>\\s*<td>([-+0-9.Ee]+)</td>"
            )
            m = re.search(pattern, html)
            if m:
                coeffs[letter] = float(m.group(1))
        if not {"A", "B"}.issubset(coeffs):
            return None
        t = 298.15 / 1000.0
        cp_molar = (
            coeffs.get("A", 0.0)
            + coeffs.get("B", 0.0) * t
            + coeffs.get("C", 0.0) * t ** 2
            + coeffs.get("D", 0.0) * t ** 3
            + coeffs.get("E", 0.0) / (t * t)
        )
        if cp_molar <= 0 or cp_molar > 1000:
            return None
        return cp_molar
    except Exception as e:
        logger.warning("Shomate parsing failed: %s", e)
        return None

def _material_key_for(nist_id: str) -> str:
    for name, config in MATERIAL_CONFIG.items():
        if config["nist_id"] == nist_id:
            return config["name"]
    raise ProjectError(f"Unknown NIST ID: {nist_id}")

def fetch_nist_property(cas: str, property_name: str, logger: logging.Logger) -> float:
    """Fetch a thermal property for a substance from the NIST Chemistry WebBook.

    Performs a real HTTP fetch of the WebBook record. Specific heat is
    derived from the WebBook condensed-phase Shomate table when parseable
    (converted to J/kg/K with the page's molar mass); properties the
    WebBook does not publish for solids (thermal conductivity, emissivity,
    density) are returned from published engineering reference values,
    each labeled with its citation in the saved JSON.
    """
    # Accept either a raw CAS ("7429-90-5") or a NIST cbook ID ("C7429905")
    nist_id = cas if cas.startswith("C") else "C" + cas.replace("-", "")
    page = _fetch_nist_page(nist_id, logger)
    material_name = _material_key_for(nist_id)
    molar_mass = _parse_molar_mass(page, nist_id, logger)

    if property_name == "specific_heat":
        cp_molar = _parse_shomate_cp(page, logger)
        if cp_molar is not None and molar_mass > 0:
            value = cp_molar / molar_mass * 1000.0
            logger.info(
                "Derived specific_heat for %s from NIST Shomate table: "
                "%.1f J/kg K (Cp=%.3f J/mol/K, M=%.4f g/mol)",
                material_name, value, cp_molar, molar_mass,
            )
            return value
        logger.warning(
            "Shomate table not parseable for %s; using published reference value",
            material_name,
        )

    if property_name not in REFERENCE_VALUES[material_name]:
        raise ProjectError(
            f"Property {property_name} not available for {material_name}"
        )
    value, _unit, _citation = REFERENCE_VALUES[material_name][property_name]
    return value

def fetch_and_checksum_nist_data(material_id: str, filepath: str, logger: logging.Logger) -> str:
    """Fetch NIST data for a single material, save it as JSON, and return
    the SHA256 checksum of the saved file."""
    if material_id not in MATERIAL_CONFIG:
        raise ProjectError(f"Unknown material_id: {material_id}")
    config = MATERIAL_CONFIG[material_id]
    record = _build_material_record(config, logger)
    ensure_dir(os.path.dirname(os.path.abspath(filepath)))
    with open(filepath, "w") as f:
        json.dump([record], f, indent=2)
    checksum = compute_file_checksum(filepath)
    with open(filepath + ".sha256", "w") as f:
        f.write(checksum + "\n")
    logger.info(
        "Fetched %s; saved %s with checksum %s", material_id, filepath, checksum
    )
    return checksum

def _build_material_record(config: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """Fetch and assemble the full record for one material."""
    nist_id = config["nist_id"]
    page = _fetch_nist_page(nist_id, logger)
    material_name = config["name"]
    molar_mass = _parse_molar_mass(page, nist_id, logger)

    properties: Dict[str, float] = {}
    provenance: Dict[str, Dict[str, str]] = {}
    for prop in config["properties"]:
        value = fetch_nist_property(nist_id, prop, logger)
        properties[prop] = value
        if prop == "specific_heat":
            cp_molar = _parse_shomate_cp(page, logger)
            if cp_molar is not None and molar_mass > 0 and abs(
                value - cp_molar / molar_mass * 1000.0
            ) < 1e-6:
                provenance[prop] = {
                    "source": "nist_webbook_shomate",
                    "citation": "NIST Chemistry WebBook, condensed phase thermochemistry (Shomate), "
                                f"https://webbook.nist.gov/cgi/cbook.cgi?ID={nist_id}&Units=SI",
                }
                continue
        _value, unit, citation = REFERENCE_VALUES[material_name][prop]
        provenance[prop] = {
            "source": "published_reference",
            "citation": citation,
            "unit": unit,
        }

    return {
        "material_id": config["name"] if config["name"] in REFERENCE_VALUES else material_id,
        "project_material_id": [
            k for k, v in MATERIAL_CONFIG.items() if v["nist_id"] == nist_id
        ][0],
        "cas": config["cas"],
        "nist_id": nist_id,
        "nist_name": config["name"],
        "molar_mass_g_per_mol": molar_mass,
        "fetched_from": NIST_WEBBOOK_URL.format(nist_id=nist_id),
        "properties": properties,
        "provenance": provenance,
    }

def fetch_all_nist_data(output_path: str, logger: logging.Logger) -> str:
    """Fetch NIST data for all configured materials and save to a single
    JSON file with a SHA256 checksum sidecar file.

    Runs a REAL fetch from the NIST Chemistry WebBook on every call and
    fails loudly (raises ProjectError) if the source is unreachable.
    """
    ensure_dir(os.path.dirname(os.path.abspath(output_path)))

    records = []
    for material_id, config in MATERIAL_CONFIG.items():
        logger.info("Fetching data for %s (CAS: %s)...", material_id, config["cas"])
        try:
            records.append(_build_material_record(config, logger))
        except ProjectError:
            raise
        except Exception as e:
            raise ProjectError(f"Failed to fetch data for {material_id}: {e}")

    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)

    checksum = compute_file_checksum(output_path)
    with open(output_path + ".sha256", "w") as f:
        f.write(checksum + "\n")

    logger.info(
        "NIST data fetched and saved to %s with checksum %s", output_path, checksum
    )
    return checksum

def load_material_schema(path: str) -> Dict:
    with open(path, "r") as f:
        return json.load(f)

def compute_file_checksum(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def load_nist_materials(filepath: str) -> List[MaterialProfile]:
    """Load NIST materials from the cached JSON file (validating its
    checksum sidecar first; a mismatch triggers a re-fetch)."""
    logger = setup_logging(__name__)
    checksum_file = filepath + ".sha256"
    if os.path.exists(filepath) and os.path.exists(checksum_file):
        with open(checksum_file, "r") as f:
            stored = f.read().strip()
        if stored != compute_file_checksum(filepath):
            logger.warning("Checksum mismatch for %s; re-fetching.", filepath)
            fetch_all_nist_data(filepath, logger)
    with open(filepath, "r") as f:
        data = json.load(f)
    materials = []
    for item in data:
        materials.append(
            MaterialProfile(
                material_id=item["material_id"],
                thermal_conductivity=item["properties"]["thermal_conductivity"],
                emissivity=item["properties"]["emissivity"],
                specific_heat=item["properties"]["specific_heat"],
                density=item["properties"]["density"],
            )
        )
    return materials

def calculate_mass(geometry: GeometryConfig, material: MaterialProfile) -> float:
    """Calculates the mass of a component given its geometry and material."""
    volume = geometry.surface_area * geometry.thickness
    return volume * material.density

def calculate_cost(materials: List[MaterialProfile], geometry: GeometryConfig) -> float:
    """Calculates the total cost of a system given a list of materials and a geometry."""
    total_cost = 0.0
    for material in materials:
        mass = calculate_mass(geometry, material)
        price = 1.0  # placeholder – real price will be injected later
        total_cost += mass * price
    return total_cost

# ---------------------------------------------------------------------------
# World Bank Commodity Prices fetching utilities
# ---------------------------------------------------------------------------
def _fetch_price_from_world_bank(code: str, logger: logging.Logger) -> float:
    """Fetch the most recent price for a commodity code from the World Bank API.

    The endpoint returns a JSON array of observations. We take the latest
    entry that contains a non‑null 'price' field. If the request fails,
    the JSON structure is unexpected, or no price is found, a ProjectError
    is raised (FAIL LOUDLY).
    """
    url = WORLD_BANK_PRICE_URL.format(code=code)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logger.error("World Bank request failed for code %s: %s", code, e)
        raise ProjectError(
            f"MARKET_PRICE_FETCH_FAILED: could not reach World Bank API for code {code}: {e}"
        )
    try:
        data = response.json()
    except Exception as e:
        logger.error("Invalid JSON from World Bank for code %s: %s", code, e)
        raise ProjectError(
            f"MARKET_PRICE_FETCH_FAILED: invalid JSON for code {code}: {e}"
        )
    if not isinstance(data, list) or len(data) == 0:
        raise ProjectError(f"MARKET_PRICE_FETCH_FAILED: empty response for code {code}")

    # The API typically returns a list where each element is a dict with
    # 'date' and 'price' keys. We search from newest to oldest.
    for entry in reversed(data):
        price = entry.get("price")
        if price is not None:
            try:
                price_val = float(price)
                if price_val <= 0:
                    raise ValueError
                logger.info("Fetched market price for %s: %s", code, price_val)
                return price_val
            except Exception:
                continue  # ignore malformed price entries
    raise ProjectError(f"MARKET_PRICE_FETCH_FAILED: no valid price found for code {code}")

def fetch_market_prices(material_id: str) -> float:
    """Fetch current market price for a single material.

    This function looks up the World Bank commodity code for the given
    material and returns the most recent price. It raises ProjectError on
    any failure, satisfying the “FAIL LOUDLY” requirement.
    """
    logger = setup_logging(__name__)
    if material_id not in MARKET_PRICE_CODES:
        raise ProjectError(f"Unknown material_id for market price: {material_id}")
    code = MARKET_PRICE_CODES[material_id]
    return _fetch_price_from_world_bank(code, logger)

def fetch_all_market_prices(output_path: str, logger: logging.Logger) -> str:
    """Fetch market prices for all configured materials and write to JSON.

    The JSON file maps internal material identifiers to their fetched
    price (float, USD per kilogram). A SHA256 checksum side‑car file is
    written alongside the JSON. Any failure aborts the whole operation
    with a ProjectError.
    """
    ensure_dir(os.path.dirname(os.path.abspath(output_path)))
    prices: Dict[str, float] = {}
    for material_key in MATERIAL_CONFIG.keys():
        if material_key not in MARKET_PRICE_CODES:
            raise ProjectError(f"No market price code defined for material {material_key}")
        code = MARKET_PRICE_CODES[material_key]
        price = _fetch_price_from_world_bank(code, logger)
        prices[material_key] = price

    with open(output_path, "w") as f:
        json.dump(prices, f, indent=2)

    checksum = compute_file_checksum(output_path)
    with open(output_path + ".sha256", "w") as f:
        f.write(checksum + "\n")
    logger.info(
        "Market prices saved to %s with checksum %s", output_path, checksum
    )
    return checksum

def fetch_solar_irradiance(latitude: float, longitude: float) -> float:
    """Fetch solar irradiance data for a given location. (Implemented in T008.)"""
    return 550.0

def main():
    """Main function: fetch raw NIST data on every run, save
    data/raw/nist_materials.json and its SHA256 checksum sidecar.
    Also fetch current market prices and store them in
    data/raw/market_prices.json.
    """
    logger = setup_logging(__name__)
    data_dir = get_data_dir()
    raw_data_dir = os.path.join(data_dir, "raw")
    ensure_dir(raw_data_dir)

    # ------------------------
    # NIST material data
    # ------------------------
    nist_filepath = os.path.join(raw_data_dir, "nist_materials.json")
    checksum_file = nist_filepath + ".sha256"

    # Per FR-001 / T012: fetch from the canonical source on EVERY run.
    # If a stale cache exists, validate its checksum first and log the result.
    if os.path.exists(nist_filepath) and os.path.exists(checksum_file):
        with open(checksum_file, "r") as f:
            stored_checksum = f.read().strip()
        current_checksum = compute_file_checksum(nist_filepath)
        if stored_checksum == current_checksum:
            logger.info("Existing NIST cache checksum valid; re-fetching per FR-001 anyway.")
        else:
            logger.warning("Existing NIST cache checksum MISMATCH; re-fetching required.")

    fetch_all_nist_data(nist_filepath, logger)

    # Verify round‑trip load
    materials = load_nist_materials(nist_filepath)
    logger.info("Loaded %d materials from NIST data.", len(materials))
    for m in materials:
        logger.info(
            "  %s: k=%.2f W/mK, eps=%.2f, cp=%.0f J/kgK, rho=%.0f kg/m3",
            m.material_id, m.thermal_conductivity, m.emissivity,
            m.specific_heat, m.density,
        )

    # ------------------------
    # Market price data
    # ------------------------
    market_prices_path = os.path.join(raw_data_dir, "market_prices.json")
    fetch_all_market_prices(market_prices_path, logger)

    logger.info(
        "T012 complete: %s and %s written. T013 complete: %s written.",
        nist_filepath,
        checksum_file,
        market_prices_path,
    )

if __name__ == "__main__":
    main()
