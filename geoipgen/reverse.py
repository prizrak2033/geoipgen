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
import threading
from array import array
from bisect import bisect_right
from typing import Optional, NamedTuple, Tuple

from .generate import cidrs, countries
from .subnetCal import AddressLike


class Allocation(NamedTuple):
    """The block an address falls in, and the country holding it."""

    ip: str
    country: str
    cidr: str


class _Index(NamedTuple):
    """Parallel arrays of block bounds, sorted by start address."""

    starts: "array[int]"
    ends: "array[int]"
    codes: Tuple[str, ...]
    blocks: Tuple[str, ...]


_INDEX_LOCK = threading.Lock()
_INDEX = None  # type: Optional[_Index]


def _build_index() -> _Index:
    """Read every shipped block into a sorted interval index."""
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


def _index() -> _Index:
    """Return the interval index, building it on first use.

    A :func:`functools.lru_cache` is not enough here. On a cache miss it runs
    the decorated body in *every* concurrent caller, so threads racing the
    first lookup would each build the whole index: measured at 1.2s for one
    thread but 64s for eight, because the redundant builds also contend for
    the GIL. The lock makes the first caller build it while the rest wait.

    The unlocked read on the fast path is deliberate: rebinding a module
    global is atomic, so a caller either sees a fully built index or ``None``
    and takes the slow path.
    """
    global _INDEX
    index = _INDEX
    if index is not None:
        return index
    with _INDEX_LOCK:
        if _INDEX is None:
            _INDEX = _build_index()
        return _INDEX


def _reset_index() -> None:
    """Drop the cached index. For tests that need a cold start."""
    global _INDEX
    with _INDEX_LOCK:
        _INDEX = None


def warm() -> int:
    """Build the index ahead of time and return the number of blocks in it.

    The index is built lazily on the first lookup, which reads every data file
    and takes on the order of a second. Calling this at startup keeps that
    cost off your first request. It matters most in a threaded server: the
    build is serialised, so concurrent first requests queue behind one build
    rather than racing, but they still all wait for it.
    """
    return len(_index().starts)


def _address(ip: AddressLike) -> ipaddress.IPv4Address:
    if isinstance(ip, ipaddress.IPv4Address):
        return ip
    try:
        return ipaddress.IPv4Address(ip if isinstance(ip, int) else str(ip).strip())
    except ValueError as exc:
        raise ValueError("invalid IPv4 address: {!r}".format(ip)) from exc


def lookup(ip: AddressLike) -> Optional[Allocation]:
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


def countryOf(ip: AddressLike) -> Optional[str]:
    """Return the two-letter country code holding ``ip``, or ``None``.

    Note that ``zz`` is a placeholder in the dataset rather than a real
    country, and is returned as-is when an address falls in one of its blocks.
    """
    found = lookup(ip)
    return found.country if found is not None else None


def blockOf(ip: AddressLike) -> Optional[str]:
    """Return the CIDR block containing ``ip``, or ``None``."""
    found = lookup(ip)
    return found.cidr if found is not None else None
