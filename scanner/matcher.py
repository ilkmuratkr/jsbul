from urllib.parse import urlparse
from typing import Iterable


def hostname_of(url: str) -> str:
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""


def matches_any_domain(url: str, target_domains: Iterable[str]) -> str | None:
    host = hostname_of(url)
    if not host:
        return None
    for domain in target_domains:
        if host == domain or host.endswith("." + domain):
            return domain
    return None


