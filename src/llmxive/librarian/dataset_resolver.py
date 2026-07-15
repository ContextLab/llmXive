"""Deterministic dataset resolver (spec: dataset-resolver design).

Finds real datasets via dataset_sources, verifies reachability (reusing
librarian.verify) + a sample-stream format sniff, ranks, and returns the top-N
verified candidates per dataset intent for injection into the Planner prompt.
"""
from __future__ import annotations

import csv as _csv
import io
import json
import re
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import requests  # type: ignore[import-untyped]  # no stub package available
import urllib3  # bundled with requests; ``r.raw.read`` raises RAW urllib3 errors
import yaml

from llmxive.librarian import dataset_sources as _sources
from llmxive.librarian import verify as _verify
from llmxive.librarian.dataset_sources import USER_AGENT, DatasetCandidate
from llmxive.librarian.verify import query_relevance_score

_SAMPLE_BYTES = 256 * 1024   # cap the sample download at 256 KB
_SNIFF_TIMEOUT = 20


@dataclass(frozen=True)
class FormatReport:
    parsed: bool
    format: str | None
    downloaded_bytes: int
    error: str | None = None


def _detect_and_parse(sample: bytes, url: str) -> tuple[bool, str | None]:
    # Binary container formats by magic bytes.
    if sample[:2] == b"PK":
        try:
            zipfile.ZipFile(io.BytesIO(sample))  # may raise on a truncated sample
            return True, "zip"
        except zipfile.BadZipFile:
            # A truncated-but-valid zip header still indicates a zip download.
            return True, "zip"
    if sample[:2] == b"\x1f\x8b":
        return True, "gzip"
    if sample[:8] == b"\x89HDF\r\n\x1a\n":
        return True, "hdf5"
    if sample[:4] == b"PAR1":
        return True, "parquet"
    # tar: the POSIX "ustar" magic lives at byte offset 257 (the 256 KB sample
    # always includes it for a real tar). gzip-wrapped tars are caught above by
    # the gzip magic. FIX 1: keeps the picker (._HF_DATA_EXTS) and sniffer in sync.
    if len(sample) >= 263 and sample[257:262] == b"ustar":
        return True, "tar"
    # Text formats.
    try:
        text = sample.decode("utf-8")
    except UnicodeDecodeError:
        return False, None
    stripped = text.lstrip()
    if stripped[:1] in "{[":
        try:
            json.loads(text)
            return True, "json"
        except ValueError:
            # JSON Lines: each non-empty line parses.
            lines = [ln for ln in text.splitlines() if ln.strip()][:-1]
            if lines and all(_is_json(ln) for ln in lines):
                return True, "jsonl"
            return False, None
    if "<html" in stripped[:200].lower():
        return False, None
    # SDF/MOL chemical tables: V2000/V3000 connection-table marker or a "$$$$"
    # record delimiter. Checked before CSV so molecule files aren't mis-sniffed.
    # FIX 1: SDF/MOL are advertised in _HF_DATA_EXTS, so they must be detectable.
    if "V2000" in text or "V3000" in text or "$$$$" in text:
        return True, "sdf"
    # XYZ molecular geometry: first non-empty line is an integer atom count, OR a
    # data line looks like "<Element> <float> <float> <float>". QM9 is natively
    # .xyz, which _HF_DATA_EXTS advertises, so the sniffer must recognize it.
    if _looks_like_xyz(text):
        return True, "xyz"
    # CSV/TSV: csv.Sniffer + >=2 columns on the first full row.
    try:
        dialect = _csv.Sniffer().sniff(text[:4096])
        rows = list(_csv.reader(io.StringIO(text), dialect))
        if rows and len(rows[0]) >= 2:
            return True, "tsv" if dialect.delimiter == "\t" else "csv"
    except _csv.Error:
        pass
    return False, None


_XYZ_ATOM_RE = re.compile(
    r"^\s*[A-Za-z]{1,3}\d?\s+"
    r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\s+"
    r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\s+"
    r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\s*$"
)


def _looks_like_xyz(text: str) -> bool:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False
    # Standard XYZ: first non-empty line is a bare integer atom count, and at
    # least one subsequent line matches the "<El> x y z" coordinate pattern.
    first = lines[0].strip()
    if first.isdigit():
        return any(_XYZ_ATOM_RE.match(ln) for ln in lines[1:])
    # Headerless XYZ-like coordinate block: a run of "<El> x y z" lines.
    atom_lines = sum(1 for ln in lines if _XYZ_ATOM_RE.match(ln))
    return atom_lines >= 2 and atom_lines == len(lines)


def _is_json(line: str) -> bool:
    try:
        json.loads(line)
        return True
    except ValueError:
        return False


def sniff_format(url: str) -> FormatReport:
    try:
        with requests.get(url, stream=True, headers={"User-Agent": USER_AGENT}, timeout=_SNIFF_TIMEOUT) as r:
            if r.status_code >= 400:
                return FormatReport(False, None, 0, f"HTTP {r.status_code}")
            sample = r.raw.read(_SAMPLE_BYTES, decode_content=True) or b""
    # ``r.raw.read`` reads the RAW urllib3 stream, so a read-timeout there raises
    # a urllib3 error (ReadTimeoutError / ProtocolError) that is NOT a
    # requests.RequestException NOR an OSError — the live PROJ-492 run-22 crash
    # (`us.aws.cdn.hf.co Read timed out` while verifying a cited HF dataset took
    # down the whole pipeline run). Verifying a dataset URL is best-effort: a
    # transient network failure must yield "couldn't verify", never crash the run.
    except (requests.RequestException, OSError, urllib3.exceptions.HTTPError) as exc:
        return FormatReport(False, None, 0, str(exc))
    ok, fmt = _detect_and_parse(sample, url)
    return FormatReport(ok, fmt, len(sample), None if ok else "unrecognized/non-dataset content")


@dataclass(frozen=True)
class VerifiedDataset:
    intent: str
    url: str
    source: str
    format: str
    relevance: float
    downloaded_bytes: int
    hf_id: str | None = None


@dataclass(frozen=True)
class VerifyResult:
    """Outcome of probing a single candidate (FIX 2: audit granularity).

    ``status`` is one of:
      - "verified"     : reachable AND a sample parsed as a known dataset format.
      - "unreachable"  : the reachability step (verify._head_with_get_fallback)
                         failed (404/timeout/DNS/etc.).
      - "wrong_format" : reachable, but the sample did not sniff as a dataset.
    ``dataset`` is populated only when ``status == "verified"``; ``url`` is the
    final (post-redirect) URL when known, else the candidate URL; ``reason`` is a
    human-readable explanation for the manifest's ``candidates_tried`` audit.
    """
    status: str
    url: str
    reason: str | None = None
    dataset: VerifiedDataset | None = None


def verify_candidate(c: DatasetCandidate, *, relevance: float = 0.0) -> VerifiedDataset | None:
    """Return a VerifiedDataset iff the candidate is reachable AND a sample
    parses as a recognized dataset format; else None.

    Thin wrapper over :func:`probe_candidate` preserving the original return
    contract (callers/tests that only need the verified result).
    """
    return probe_candidate(c, relevance=relevance).dataset


def probe_candidate(c: DatasetCandidate, *, relevance: float = 0.0) -> VerifyResult:
    """Probe a candidate and report the precise outcome (FIX 2).

    Distinguishes "unreachable" (reachability failed) from "wrong_format"
    (reachable but the sample didn't sniff as a dataset) so the resolver can
    record an accurate per-candidate status in ``candidates_tried``.
    """
    head = _verify._head_with_get_fallback(c.url, timeout=20.0)
    if head.outcome == "unreachable":
        detail = head.error or (f"HTTP {head.http_status}" if head.http_status else "no response")
        return VerifyResult("unreachable", c.url, f"reachability failed: {detail}")
    # Sniff the final (post-redirect) URL.
    rep = sniff_format(head.final_url)
    if not rep.parsed or rep.format is None:
        return VerifyResult(
            "wrong_format", head.final_url,
            rep.error or "reachable but sample did not parse as a dataset",
        )
    # Store the STABLE original URL (c.url), NOT head.final_url. For a
    # HuggingFace resolve URL, head.final_url is a short-lived presigned
    # cas-bridge URL (X-Amz-Expires=3600); citing it produces a 403 once it
    # expires (observed on PROJ-262). The stable resolve URL is re-signed by HF
    # on every access, so a downstream FR-006 reachability check passes
    # durably. The sniff above used the live final_url for the sample.
    dataset = VerifiedDataset(
        intent=c.intent, url=c.url, source=c.source,
        format=rep.format, relevance=relevance,
        downloaded_bytes=rep.downloaded_bytes, hf_id=c.hf_id,
    )
    return VerifyResult("verified", c.url, None, dataset)


_DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s)\]\"'>}]+)", re.IGNORECASE)
# Capitalized/alnum dataset-name tokens, e.g. QM9, ImageNet, CIFAR-10, MD17.
# Matches acronym/cap+digit dataset names (MNIST, QM9, CIFAR10, HCP, S1200) AND
# multi-hump CamelCase names (ImageNet, WikiText, OpenWebText) — the latter are
# common ML/NLP datasets the old regex silently missed, so those specs resolved to
# nothing and the project fabricated.
_NAME_RE = re.compile(
    r"\b([A-Z][A-Za-z]*\d[\w-]*|[A-Z]{2,}[A-Za-z0-9-]*|[A-Z][a-z]+(?:[A-Z][a-z0-9]+)+)\b"
)

# Tokens ``_NAME_RE`` matches but that are NEVER dataset names — requirement/task
# IDs, RFC-2119 keywords, file formats, and generic tech acronyms. Without this
# filter the resolver "searches" real sources for garbage like ``FR-001`` / ``MUST``
# / ``CSV`` / ``PNG`` (all of which appear on lines containing the word "dataset"),
# finds nothing, and the project — lacking a verified real source — fabricates. This
# is the single biggest driver of empty resolution, upstream of which sources exist.
_INTENT_ID_RE = re.compile(
    r"^(?:FR|NFR|SC|US|AC|UC)-?\d+[a-z]?$|^T\d{2,}[a-z]?$", re.IGNORECASE
)
_INTENT_STOPWORDS = frozenset({
    # RFC-2119 / spec keywords
    "must", "should", "may", "shall", "required", "recommended", "optional",
    "note", "notes", "todo", "tbd", "tba", "na", "nan", "null", "none",
    # file formats / extensions
    "csv", "tsv", "json", "jsonl", "ndjson", "png", "jpg", "jpeg", "svg", "pdf",
    "yaml", "yml", "xml", "html", "htm", "txt", "md", "parquet", "arff", "npy",
    "npz", "hdf5", "h5", "feather", "zip", "gz", "tar", "sqlite", "db", "xlsx",
    "pkl", "pickle", "tex", "bib",
    # generic tech / non-dataset acronyms
    "api", "url", "uri", "cli", "cpu", "gpu", "ram", "id", "ids", "http", "https",
    "readme", "license", "doi", "arxiv", "sha", "md5", "uuid", "rng", "llm", "ai",
    "ml", "nlp", "ci", "cd", "ok", "pr", "os", "io", "fr", "sc", "us", "uc",
    # CamelCase tools / libraries / orgs / classes that are NOT datasets
    "github", "gitlab", "huggingface", "pytorch", "tensorflow", "openml",
    "scikitlearn", "jupyterlab", "deepmind", "openai", "wandb", "dataframe",
    "dataloader", "dataframes", "dataloaders", "numpy", "pandas", "matplotlib",
    # DOMAIN file-format acronyms — a format is NOT a dataset. Extracting e.g.
    # "CIF" (crystallographic format) fuzzy-matched the real `cifar10` image set
    # and was "verified" as the wrong dataset; the study then loaded garbage.
    # (Note: real datasets whose NAME embeds a format token — CIFAR10 — are NOT
    # here; only the bare format acronym is filtered.)
    "cif", "vcf", "sdf", "mol", "bam", "sam", "cram", "fasta", "fastq", "nifti",
    "nii", "dicom", "dcm", "pdb", "mtx", "wav", "midi", "edf", "bids", "gff",
    "gtf", "bed", "bigwig", "netcdf", "geojson", "shp", "las", "obj", "ply",
    # STATISTICAL / ML MODEL, METHOD, and METRIC acronyms — a method or a metric
    # is NOT a dataset. "ARIMA"→an anime dataset, "GMM"→GMM-Sefai, "MSE"→alpaca-es,
    # "ADVI"/"DP-GMM" unresolved: extracting these produced junk fuzzy-matches.
    "arima", "sarima", "sarimax", "garch", "gmm", "dpgmm", "dp-gmm", "hmm", "hdp",
    "pca", "ica", "lda", "qda", "svm", "svr", "knn", "cnn", "rnn", "lstm", "gru",
    "gan", "vae", "mlp", "gnn", "gcn", "gat", "mcmc", "hmc", "advi", "elbo",
    "vi", "em", "map", "mle", "mse", "rmse", "mae", "mape", "smape", "auc",
    "auroc", "auprc", "roc", "sgd", "adam", "adamw", "rmsprop", "relu", "gelu",
    "anova", "ancova", "manova", "ols", "gls", "wls", "glm", "gam", "ridge",
    "lasso", "elasticnet", "xgboost", "lightgbm", "catboost", "ppca", "tsne",
    "umap", "kmeans", "dbscan", "rl", "ppo", "dqn", "sac", "a2c", "trpo",
})


def _is_dataset_intent(nm: str) -> bool:
    """A ``_NAME_RE`` token is a plausible dataset intent only if it is not a
    requirement/task ID, a spec keyword, a file format, or a generic acronym."""
    if len(nm) < 3:
        return False
    if _INTENT_ID_RE.match(nm):
        return False
    return nm.lower() not in _INTENT_STOPWORDS
# Source authority for tie-breaking (higher = preferred).
_AUTHORITY = {"huggingface": 4, "zenodo": 3, "figshare": 3, "datacite": 2, "semantic_scholar": 1}


@dataclass
class ResolvedIntent:
    intent: str
    status: str                       # "verified" | "unresolved"
    candidates: list[dict[str, object]] = field(default_factory=list)        # top-N verified
    candidates_tried: list[dict[str, object]] = field(default_factory=list)  # audit


@dataclass
class ResolvedDatasets:
    datasets: list[ResolvedIntent]


def extract_dataset_intents(spec_text: str) -> list[str]:
    """Deterministic-first extraction of dataset intents from spec.md: DOIs +
    capitalized dataset-name tokens near the word 'dataset'."""
    intents: list[str] = []
    for m in _DOI_RE.finditer(spec_text):
        intents.append(m.group(1).rstrip(".,);]"))
    for line in spec_text.splitlines():
        if "dataset" in line.lower():
            for nm in _NAME_RE.findall(line):
                if _is_dataset_intent(nm):
                    intents.append(nm)
    # De-dup, preserve order.
    seen: set[str] = set()
    out: list[str] = []
    for i in intents:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def _gather_candidates(intent: str) -> list[DatasetCandidate]:
    # FIX 4 / design "out of scope / future": the Semantic Scholar + arXiv
    # paper-linked-data source sketched in the design is intentionally DEFERRED.
    # Those APIs yield *paper pages* (HTML landing pages), not directly
    # sample-streamable dataset files, so they would fail the format sniff and
    # add no verified candidates today. The registries below (HF Hub, figshare,
    # Zenodo, DataCite, OpenML) cover the in-scope cases (e.g. QM9). OpenML adds
    # thousands of curated tabular ML datasets with a directly-verifiable CSV
    # export — the most common gap for the tabular/ML projects that otherwise find
    # NO verified source and fabricate. A paper-linked source can be appended here
    # later without changing any interface (see design "Out of scope / future").
    cands: list[DatasetCandidate] = []
    for fn in (_sources.search_huggingface, _sources.search_figshare,
               _sources.search_zenodo, _sources.search_datacite,
               _sources.search_openml):
        try:
            cands.extend(fn(intent, limit=5))
        except Exception:
            continue
    return cands


def resolve_datasets(spec_text: str, *, project_dir: Path, repo_root: Path,
                     top_n: int = 3, budget_s: int = 300) -> ResolvedDatasets:
    # ``repo_root`` is intentionally retained (Task 7's plan_cmd.mechanical_step
    # passes it) even though it is currently unused: it is RESERVED for the
    # deferred Semantic Scholar/arXiv paper-linked-data source (see
    # _gather_candidates and the design's "Out of scope / future"), which would
    # resolve repo-relative source-paper links. Do not remove it.
    import time
    deadline = time.monotonic() + budget_s
    resolved: list[ResolvedIntent] = []
    for intent in extract_dataset_intents(spec_text):
        tried: list[dict[str, object]] = []
        verified: list[VerifiedDataset] = []
        for c in _gather_candidates(intent):
            if time.monotonic() > deadline:
                break
            rel = query_relevance_score(intent, f"{c.title} {c.hf_id or ''}")
            # FIX 2: probe_candidate distinguishes "unreachable" (reachability
            # failed) from "wrong_format" (reachable but unrecognized) so the
            # audit records the precise status+reason rather than a generic
            # "rejected". Verified-selection behavior is unchanged.
            pr = probe_candidate(c, relevance=rel)
            if pr.status == "verified" and pr.dataset is not None:
                v = pr.dataset
                tried.append({"url": v.url, "source": v.source, "status": "verified",
                              "format": v.format})
                verified.append(v)
            else:
                tried.append({"url": pr.url, "source": c.source,
                              "status": pr.status, "reason": pr.reason})
        verified.sort(key=lambda v: (_AUTHORITY.get(v.source, 0), v.relevance), reverse=True)
        top = verified[:top_n]
        resolved.append(ResolvedIntent(
            intent=intent,
            status="verified" if top else "unresolved",
            candidates=[{"url": v.url, "source": v.source, "format": v.format,
                         "relevance": round(v.relevance, 3),
                         "sample_check": {"downloaded_bytes": v.downloaded_bytes, "parsed": True}}
                        for v in top],
            candidates_tried=tried,
        ))
    return ResolvedDatasets(datasets=resolved)


def write_manifest(rd: ResolvedDatasets, *, project_dir: Path) -> Path:
    out = Path(project_dir) / ".specify" / "memory" / "resolved_datasets.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "resolved_at": datetime.now(UTC).isoformat(),
        "datasets": [
            {"intent": d.intent, "status": d.status,
             "candidates": d.candidates, "candidates_tried": d.candidates_tried}
            for d in rd.datasets
        ],
    }
    out.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return out


def unresolved_intents(rd: ResolvedDatasets) -> list[str]:
    return [d.intent for d in rd.datasets if d.status == "unresolved"]


def render_planner_block(rd: ResolvedDatasets) -> str:
    """The 'cite ONLY these' block injected into the Planner user prompt."""
    if not rd.datasets:
        return ""
    lines = ["# Verified datasets (cite ONLY these URLs in research.md — do NOT invent any dataset URL)"]
    for d in rd.datasets:
        if d.status != "verified":
            lines.append(f"- {d.intent}: NO verified source found (do NOT cite a URL for it).")
            continue
        urls = ", ".join(str(c["url"]) for c in d.candidates)
        lines.append(f"- {d.intent} ({d.candidates[0]['format']}): {urls}")
    return "\n".join(lines)
