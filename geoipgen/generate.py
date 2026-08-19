"""Generate IPv4 addresses from CIDR blocks or from a country's allocations."""

import ipaddress
import random
import re
from functools import lru_cache
from pathlib import Path
from typing import Iterator, List, Tuple

from . import functions, subnetCal

DATA_DIR = Path(__file__).resolve().parent / "ipv4"

_COUNTRY_CODE = re.compile(r"[a-z]{2}")


def IP(cidr) -> str:
    """Return a uniformly random usable address from ``cidr``."""
    first, last = subnetCal.hostRange(cidr)
    return str(ipaddress.IPv4Address(random.randint(int(first), int(last))))


def iterIP(cidr) -> Iterator[str]:
    """Yield every usable address of ``cidr`` in order.

    Prefer this over :func:`rangeIP` for short prefixes: a ``/8`` holds more
    than sixteen million addresses, which is a large list to hold in memory.
    """
    first, last = subnetCal.hostRange(cidr)
    return functions.iter_ips(first, last)


def rangeIP(cidr) -> List[str]:
    """Return the list of every usable address of ``cidr``."""
    return list(iterIP(cidr))


@lru_cache(maxsize=None)
def _load(code: str) -> Tuple[str, ...]:
    """Read and cache the CIDR blocks of an already normalized country code."""
    try:
        text = (DATA_DIR / "{}.cidr".format(code)).read_text(encoding="utf-8")
    except OSError:
        raise ValueError("no CIDR data for country code {!r}".format(code)) from None
    blocks = tuple(line.strip() for line in text.splitlines() if line.strip())
    if not blocks:
        raise ValueError("no CIDR data for country code {!r}".format(code))
    return blocks


def cidrs(country) -> Tuple[str, ...]:
    """Return every CIDR block allocated to ``country`` as a two-letter code.

    Lookups are case-insensitive and cached, so a data file is read only once.
    """
    code = str(country).strip().lower()
    if not _COUNTRY_CODE.fullmatch(code):
        raise ValueError("invalid country code: {!r}".format(country))
    return _load(code)


def countries() -> Tuple[str, ...]:
    """Return every country code that ships with the package, sorted."""
    return tuple(sorted(path.stem for path in DATA_DIR.glob("*.cidr")))


def randomCIDR(country) -> str:
    """Return a random CIDR block allocated to ``country``."""
    return random.choice(cidrs(country))


def randomIP(country) -> str:
    """Return a random address from a random CIDR block of ``country``."""
    return IP(randomCIDR(country))
