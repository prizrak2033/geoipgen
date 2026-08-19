"""Small demo of the geoipgen API."""

import geoipgen

YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[01m"
RESET = "\033[0m"


def show(color, label, value):
    print("{}{}{}:{} {}{}".format(color, BOLD, label, RESET + color, value, RESET))


cidr = "45.9.132.0/22"
show(YELLOW, "Random IP from ({})".format(cidr), geoipgen.IP(cidr))
show(YELLOW, "Hosts in ({})".format(cidr), len(geoipgen.rangeIP(cidr)))

country = "es"
country_cidr = geoipgen.randomCIDR(country)
print()
show(CYAN, "Random CIDR from '{}'".format(country), country_cidr)
show(CYAN, "Random IP from '{}'".format(country), geoipgen.IP(country_cidr))
show(CYAN, "Hosts in that CIDR", len(geoipgen.rangeIP(country_cidr)))
show(CYAN, "Random IP from '{}' in one call".format(country), geoipgen.randomIP(country))

print()
geoipgen.printCalculate(country_cidr)
