"""IPv4 subnet calculations for CIDR blocks.

The heavy lifting is delegated to the standard library :mod:`ipaddress`, which
handles the bit twiddling correctly for every prefix length (including ``/0``,
``/31`` and ``/32``) and rejects malformed input.
"""

import ipaddress
from typing import NamedTuple, Tuple


class SubnetInfo(NamedTuple):
    """Summary of a CIDR block.

    It is a tuple, so the historical positional access still works::

        cidr, ip, mask, min_host, max_host, total_host = simpleCalculate(cidr)
    """

    cidr: str
    ip: str
    mask: str
    min_host: str
    max_host: str
    total_host: int


def parseCIDR(cidr) -> Tuple[ipaddress.IPv4Address, ipaddress.IPv4Network]:
    """Return ``(address, network)`` for ``cidr``.

    The address keeps the host bits exactly as they were written, while the
    network is the block they belong to, so ``172.16.5.7/20`` yields
    ``172.16.5.7`` and ``172.16.0.0/20``. A bare address is treated as ``/32``.
    """
    try:
        interface = ipaddress.IPv4Interface(str(cidr).strip())
    except ValueError as exc:
        raise ValueError("invalid IPv4 CIDR: {!r}".format(cidr)) from exc
    return interface.ip, interface.network


def hostRange(cidr) -> Tuple[ipaddress.IPv4Address, ipaddress.IPv4Address]:
    """Return the first and last usable address of ``cidr``, inclusive.

    Blocks of ``/30`` and larger exclude the network and broadcast addresses.
    A ``/31`` is a point-to-point link where both addresses are usable
    (RFC 3021) and a ``/32`` is the single host itself.
    """
    network = cidr if isinstance(cidr, ipaddress.IPv4Network) else parseCIDR(cidr)[1]
    if network.prefixlen >= 31:
        return network.network_address, network.broadcast_address
    return network.network_address + 1, network.broadcast_address - 1


def _binary(address) -> str:
    """Render an IPv4 address as dotted zero-padded binary octets."""
    return ".".join(format(octet, "08b") for octet in ipaddress.IPv4Address(address).packed)


def simpleCalculate(cidr) -> SubnetInfo:
    """Return a :class:`SubnetInfo` describing ``cidr``."""
    address, network = parseCIDR(cidr)
    min_host, max_host = hostRange(network)
    return SubnetInfo(
        cidr=str(cidr).strip(),
        ip=str(address),
        mask=str(network.netmask),
        min_host=str(min_host),
        max_host=str(max_host),
        total_host=int(max_host) - int(min_host) + 1,
    )


def printCalculate(cidr) -> SubnetInfo:
    """Print a detailed report for ``cidr`` and return its :class:`SubnetInfo`."""
    network = parseCIDR(cidr)[1]
    info = simpleCalculate(cidr)
    rule = "\033[34m+--------------------------------------------------------+\033[0m"

    print("""{rule}
\033[32m\033[01mNETWORK:\033[0m {info.cidr}
\033[32m\033[01mIP:\033[0m      {info.ip}
\033[32m\033[01mMASK:\033[0m    {info.mask}
\033[32m\033[01mRANGE:\033[0m   {info.min_host} / {info.max_host}
{rule} 
\033[36m\033[01mBINARY IP:\033[0m       {binary_ip}
\033[36m\033[01mBINARY MASK:\033[0m     {binary_mask}
\033[36m\033[01mBINARY WILDCARD:\033[0m {binary_wildcard}

\033[36m\033[01mBINARY MIN HOST:\033[0m {binary_min_host}
\033[36m\033[01mBINARY MAX HOST:\033[0m {binary_max_host}
{rule}
\033[95m\033[01mMIN HOST:\033[0m {info.min_host}
\033[95m\033[01mMAX HOST:\033[0m {info.max_host}
\033[95m\033[01mTOTAL NUMBER OF HOSTS:\033[0m {info.total_host}
{rule} """.format(
        rule=rule,
        info=info,
        binary_ip=_binary(info.ip),
        binary_mask=_binary(network.netmask),
        binary_wildcard=_binary(network.hostmask),
        binary_min_host=_binary(info.min_host),
        binary_max_host=_binary(info.max_host),
    ))
    return info


def decimalToBinary(number: int) -> str:
    """Return the binary digits of a non-negative ``number``, without padding."""
    if number < 0:
        return "Not positive"
    return format(number, "b")
