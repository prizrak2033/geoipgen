"""geoipgen - generator of valid IPv4 addresses by country."""

from . import functions, generate, reverse, subnetCal
from .generate import (
    IP,
    SYSTEM_RNG,
    cidrs,
    countries,
    iterIP,
    randomCIDR,
    randomIP,
    rangeIP,
)
from .reverse import Allocation, blockOf, countryOf, lookup, warm
from .subnetCal import SubnetInfo, printCalculate, simpleCalculate

__version__ = "1.0.0"

__all__ = [
    "IP",
    "SYSTEM_RNG",
    "Allocation",
    "SubnetInfo",
    "blockOf",
    "cidrs",
    "countries",
    "countryOf",
    "functions",
    "generate",
    "iterIP",
    "lookup",
    "printCalculate",
    "randomCIDR",
    "randomIP",
    "rangeIP",
    "reverse",
    "simpleCalculate",
    "subnetCal",
    "warm",
]
