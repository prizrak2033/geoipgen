# geoipgen

Generator of valid IPv4 addresses by country.

Ships the IPv4 CIDR allocations of 240 country codes and picks random,
uniformly distributed addresses out of them. Pure standard library, no
dependencies.

Subnet maths inspired by [subnet-calculator-cidr](https://github.com/christivn/subnet-calculator-cidr).

## Install

```bash
pip install .
```

Or just drop the `geoipgen/` folder next to your script.

## Usage

```python
import geoipgen

geoipgen.randomIP("es")                  # '62.36.125.121'
geoipgen.randomCIDR("es")                # '185.26.4.0/22'
geoipgen.IP("45.9.132.0/22")             # '45.9.133.177'
len(geoipgen.rangeIP("45.9.132.0/22"))   # 1022
```

## API

### Generating

#### `geoipgen.IP(cidr, rng=None)`
Returns a uniformly random usable address from a CIDR block.

#### `geoipgen.randomCIDR(country_code, rng=None)`
Returns a random CIDR block allocated to a two-letter country code.

#### `geoipgen.randomIP(country_code, rng=None)`
Returns a random address from a random CIDR block of a country.

#### `geoipgen.rangeIP(cidr)`
Returns the list of every usable address in a CIDR block.

#### `geoipgen.iterIP(cidr)`
Same, but yields addresses lazily. Prefer it for short prefixes — a `/8`
holds over sixteen million addresses.

#### `geoipgen.cidrs(country_code)`
Returns every CIDR block allocated to a country, as a tuple. Cached.

#### `geoipgen.countries()`
Returns every available country code, sorted.

### Calculating

#### `geoipgen.simpleCalculate(cidr)`
Returns a `SubnetInfo` named tuple:

```python
>>> geoipgen.simpleCalculate("45.9.132.0/22")
SubnetInfo(cidr='45.9.132.0/22', ip='45.9.132.0', mask='255.255.252.0',
           min_host='45.9.132.1', max_host='45.9.135.254', total_host=1022)
```

It is still a tuple, so the historical `info[3]` / `info[4]` positional
access keeps working.

#### `geoipgen.printCalculate(cidr)`
Prints a detailed report (binary IP, mask, wildcard, host range) and returns
the same `SubnetInfo`.

![screenshot](https://i.ibb.co/WnsxBNQ/Screenshot-2.png)

## Randomness

By default the generators draw from Python's `random` module, a Mersenne
Twister. It is fast and reproducible under `random.seed()`, which is what you
want for test fixtures — but it is **not cryptographically secure**. An
observer who sees enough output can recover its internal state and predict
every address that follows.

If unpredictability matters for your use case, pass a generator backed by the
OS entropy pool:

```python
geoipgen.randomIP("es", rng=geoipgen.SYSTEM_RNG)
geoipgen.IP("45.9.132.0/22", rng=geoipgen.SYSTEM_RNG)
```

`rng` accepts any object with the `randint`/`choice` methods, so
`random.Random(seed)` works too when you want reproducible output:

```python
import random
geoipgen.randomIP("es", rng=random.Random(42))   # same result every run
```

## Notes

- Country codes are case-insensitive; an unknown code raises `ValueError`.
- Country codes are validated against `[a-z]{2}` before touching the
  filesystem, so a code can never escape the bundled data directory.
- Unaligned blocks are normalised, so `172.16.5.7/20` is treated as
  `172.16.0.0/20`.
- `/31` is handled per RFC 3021 (both addresses usable) and `/32` as a single
  host.

## Tests

```bash
python -m unittest discover -s tests
```

## Example

```bash
python example.py
```
