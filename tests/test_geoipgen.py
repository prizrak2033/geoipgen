"""Tests for geoipgen. Run with `python -m unittest discover` or `pytest`."""

import ipaddress
import random
import unittest

import geoipgen
from geoipgen import functions, generate, subnetCal


class SubnetCalculationTests(unittest.TestCase):
    def test_matches_the_standard_library_for_every_prefix_length(self):
        for prefix in range(33):
            cidr = "10.20.30.40/{}".format(prefix)
            with self.subTest(cidr=cidr):
                network = ipaddress.ip_network(cidr, strict=False)
                info = subnetCal.simpleCalculate(cidr)
                self.assertEqual(info.mask, str(network.netmask))
                if prefix <= 30:
                    self.assertEqual(info.min_host, str(network.network_address + 1))
                    self.assertEqual(info.max_host, str(network.broadcast_address - 1))
                else:
                    self.assertEqual(info.min_host, str(network.network_address))
                    self.assertEqual(info.max_host, str(network.broadcast_address))

    def test_masks_off_host_bits_of_an_unaligned_block(self):
        info = subnetCal.simpleCalculate("172.16.5.7/20")
        self.assertEqual(info.ip, "172.16.5.7")
        self.assertEqual((info.min_host, info.max_host), ("172.16.0.1", "172.16.15.254"))

    def test_total_host_is_never_negative(self):
        for cidr, expected in [
            ("192.168.1.0/24", 254),
            ("10.0.0.0/8", 16777214),
            ("1.2.3.4/30", 2),
            ("1.2.3.4/31", 2),
            ("1.2.3.4/32", 1),
        ]:
            with self.subTest(cidr=cidr):
                self.assertEqual(subnetCal.simpleCalculate(cidr).total_host, expected)

    def test_result_is_still_indexable_like_the_old_list(self):
        info = subnetCal.simpleCalculate("45.9.132.0/22")
        self.assertEqual(len(info), 6)
        self.assertEqual(info[3], info.min_host)
        self.assertEqual(info[4], info.max_host)

    def test_rejects_malformed_input(self):
        for cidr in ["", "not-an-ip", "10.0.0.0/33", "999.1.1.1/24", "10.0.0.0/-1"]:
            with self.subTest(cidr=cidr), self.assertRaises(ValueError):
                subnetCal.simpleCalculate(cidr)

    def test_a_bare_address_is_a_single_host(self):
        info = subnetCal.simpleCalculate("8.8.8.8")
        self.assertEqual((info.min_host, info.max_host, info.total_host), ("8.8.8.8", "8.8.8.8", 1))

    def test_print_calculate_reports_the_same_numbers(self, ):
        info = subnetCal.printCalculate("45.9.132.0/22")
        self.assertEqual(info, subnetCal.simpleCalculate("45.9.132.0/22"))

    def test_decimal_to_binary(self):
        self.assertEqual(subnetCal.decimalToBinary(0), "0")
        self.assertEqual(subnetCal.decimalToBinary(5), "101")
        self.assertEqual(subnetCal.decimalToBinary(255), "11111111")
        self.assertEqual(subnetCal.decimalToBinary(-1), "Not positive")


class AddressExpansionTests(unittest.TestCase):
    def test_range_is_inclusive_at_both_ends(self):
        self.assertEqual(
            functions.ips("10.0.0.254", "10.0.1.2"),
            ["10.0.0.254", "10.0.0.255", "10.0.1.0", "10.0.1.1", "10.0.1.2"],
        )

    def test_a_single_address_range(self):
        self.assertEqual(functions.ips("10.0.0.1", "10.0.0.1"), ["10.0.0.1"])

    def test_reversed_range_is_rejected(self):
        with self.assertRaises(ValueError):
            functions.ips("10.0.0.5", "10.0.0.1")

    def test_range_ip_covers_the_whole_usable_block(self):
        addresses = generate.rangeIP("192.168.1.0/24")
        self.assertEqual(len(addresses), 254)
        self.assertEqual(addresses[0], "192.168.1.1")
        self.assertEqual(addresses[-1], "192.168.1.254")
        self.assertEqual(len(set(addresses)), len(addresses))

    def test_iter_ip_is_lazy_and_agrees_with_range_ip(self):
        stream = generate.iterIP("10.0.0.0/8")
        self.assertEqual(next(stream), "10.0.0.1")
        self.assertEqual(generate.rangeIP("203.0.113.0/29"), list(generate.iterIP("203.0.113.0/29")))


class RandomGenerationTests(unittest.TestCase):
    def test_generated_address_always_falls_inside_the_block(self):
        for cidr in ["45.9.132.0/22", "192.168.1.0/24", "1.2.3.4/31", "1.2.3.4/32", "10.0.0.0/8"]:
            network = ipaddress.ip_network(cidr, strict=False)
            first, last = subnetCal.hostRange(cidr)
            with self.subTest(cidr=cidr):
                for _ in range(200):
                    address = ipaddress.IPv4Address(generate.IP(cidr))
                    self.assertIn(address, network)
                    self.assertTrue(first <= address <= last)

    def test_every_usable_address_of_a_small_block_is_reachable(self):
        random.seed(12345)
        generated = {generate.IP("192.168.1.0/29") for _ in range(500)}
        self.assertEqual(generated, set(generate.rangeIP("192.168.1.0/29")))


class CountryDataTests(unittest.TestCase):
    def test_country_data_ships_with_the_package(self):
        codes = generate.countries()
        self.assertGreater(len(codes), 200)
        for code in ["es", "us", "jp"]:
            self.assertIn(code, codes)

    def test_every_shipped_block_parses(self):
        for code in generate.countries():
            blocks = generate.cidrs(code)
            self.assertTrue(blocks, "{} has no blocks".format(code))
            for block in blocks:
                ipaddress.ip_network(block, strict=True)

    def test_random_cidr_is_stable_across_many_draws(self):
        blocks = set(generate.cidrs("zw"))
        for _ in range(5000):
            self.assertIn(generate.randomCIDR("zw"), blocks)

    def test_country_code_is_case_and_whitespace_insensitive(self):
        self.assertEqual(generate.cidrs("ES"), generate.cidrs(" es "))

    def test_unknown_country_code_raises(self):
        for code in ["", "e", "esp", "zq", "../etc/passwd", "es/../us"]:
            with self.subTest(code=code), self.assertRaises(ValueError):
                generate.cidrs(code)

    def test_random_ip_belongs_to_the_country(self):
        random.seed(7)
        blocks = [ipaddress.ip_network(block) for block in generate.cidrs("es")]
        for _ in range(100):
            address = ipaddress.IPv4Address(generate.randomIP("es"))
            self.assertTrue(any(address in block for block in blocks))


class PublicApiTests(unittest.TestCase):
    def test_documented_names_are_exported(self):
        for name in ["IP", "rangeIP", "randomCIDR", "simpleCalculate", "printCalculate"]:
            self.assertTrue(hasattr(geoipgen, name), name)

    def test_submodules_remain_reachable(self):
        self.assertIs(geoipgen.generate.IP, geoipgen.IP)
        self.assertTrue(callable(geoipgen.subnetCal.simpleCalculate))


if __name__ == "__main__":
    unittest.main()
