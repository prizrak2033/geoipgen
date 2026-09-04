"""Reverse lookup: which country an IPv4 address is allocated to.

This is the inverse of :mod:`geoipgen.generate`. The bundled ``.cidr`` files
are read once into a sorted interval index, and each lookup is a binary search
over it.

The shipped blocks are disjoint -- no block overlaps or contains another -- so
an address matches at most one block and the search needs no tie-breaking
rule. ``tests/test_geoipgen.py`` asserts that property, so a future data update
that introduced an overlap would fail the suite rather than silently return an
arbitrary one of the candidates.
"""

import ipaddress
from array import array
from bisect import bisect_right
from functools import lru_cache
from typing import Optional, NamedTuple, Tuple

from .generate import cidrs, countries


class Allocation(NamedTuple):
    """The block an address falls in, and the country holding it."""

    ip: str
    country: str
    cidr: str


class _Index(NamedTuple):
    """Parallel arrays of block bounds, sorted by start address."""

    starts: array
    ends: array
    codes: Tuple[str, ...]
    blocks: Tuple[str, ...]


@lru_cache(maxsize=1)
def _index() -> _Index:
    """Build the interval index over every shipped block, once."""
    rows = []
    for code in countries():
        for block in cidrs(code):
            network = ipaddress.IPv4Network(block)
            rows.append((
                int(network.network_address),
                int(network.broadcast_address),
                code,
                block,
            ))
    rows.sort()
    return _Index(
        starts=array("Q", [row[0] for row in rows]),
        ends=array("Q", [row[1] for row in rows]),
        codes=tuple(row[2] for row in rows),
        blocks=tuple(row[3] for row in rows),
    )


def warm() -> int:
    """Build the index ahead of time and return the number of blocks in it.

    The index is built lazily on the first lookup, which reads every data file
    and takes on the order of a second. Call this at startup if you would
    rather not pay that on the first request.
    """
    return len(_index().starts)


def _address(ip) -> ipaddress.IPv4Address:
    if isinstance(ip, ipaddress.IPv4Address):
        return ip
    try:
        return ipaddress.IPv4Address(ip if isinstance(ip, int) else str(ip).strip())
    except ValueError as exc:
        raise ValueError("invalid IPv4 address: {!r}".format(ip)) from exc


def lookup(ip) -> Optional[Allocation]:
    """Return the :class:`Allocation` covering ``ip``, or ``None``.

    ``None`` means the address is not in the bundled data, which covers about
    86% of the IPv4 space -- the remainder is reserved, unallocated, or simply
    absent from the dataset.
    """
    address = _address(ip)
    value = int(address)
    index = _index()
    position = bisect_right(index.starts, value) - 1
    if position >= 0 and value <= index.ends[position]:
        return Allocation(str(address), index.codes[position], index.blocks[position])
    return None


def countryOf(ip) -> Optional[str]:
    """Return the two-letter country code holding ``ip``, or ``None``.

    Note that ``zz`` is a placeholder in the dataset rather than a real
    country, and is returned as-is when an address falls in one of its blocks.
    """
    found = lookup(ip)
    return found.country if found is not None else None


def blockOf(ip) -> Optional[str]:
    """Return the CIDR block containing ``ip``, or ``None``."""
    found = lookup(ip)
    return found.cidr if found is not None else None
