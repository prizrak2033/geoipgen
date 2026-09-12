"""Helpers for expanding IPv4 address ranges."""

import ipaddress
from typing import Iterator, List

from .subnetCal import AddressLike


def iter_ips(start: AddressLike, end: AddressLike) -> Iterator[str]:
    """Yield every address from ``start`` to ``end``, both inclusive.

    Prefer this over :func:`ips` for wide ranges: it streams the addresses
    instead of building the whole list in memory.
    """
    first = int(ipaddress.IPv4Address(str(start).strip()))
    last = int(ipaddress.IPv4Address(str(end).strip()))
    if first > last:
        raise ValueError("start address {!r} is above end address {!r}".format(start, end))
    for value in range(first, last + 1):
        yield str(ipaddress.IPv4Address(value))


def ips(start: AddressLike, end: AddressLike) -> List[str]:
    """Return the list of addresses from ``start`` to ``end``, both inclusive."""
    return list(iter_ips(start, end))
