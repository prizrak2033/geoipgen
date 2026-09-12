# geoipgen

[![CI](https://github.com/prizrak2033/geoipgen/actions/workflows/ci.yml/badge.svg)](https://github.com/prizrak2033/geoipgen/actions/workflows/ci.yml)

Generator of valid IPv4 addresses by country.

Ships the IPv4 CIDR allocations of 240 country codes. Picks random, uniformly
distributed addresses out of them — and looks addresses back up to find which
country holds them. Pure standard library, no dependencies, fully type-hinted.

Runs on Python 3.8+.

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

geoipgen.countryOf("8.8.8.8")            # 'us'
geoipgen.lookup("8.8.8.8")               # Allocation(ip='8.8.8.8', country='us', cidr='8.0.0.0/9')
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

### Reverse lookup

The inverse of the generator: given an address, which country holds it. The
bundled blocks are read once into a sorted interval index and each lookup is a
binary search — about 5 µs per call.

#### `geoipgen.countryOf(ip)`
Returns the two-letter country code holding `ip`, or `None`.

#### `geoipgen.lookup(ip)`
Returns an `Allocation` named tuple, or `None`:

```python
>>> geoipgen.lookup("45.9.132.5")
Allocation(ip='45.9.132.5', country='es', cidr='45.9.132.0/22')
```

#### `geoipgen.blockOf(ip)`
Returns just the CIDR block containing `ip`, or `None`.

#### `geoipgen.warm()`
Builds the index up front and returns the number of blocks in it. The index is
built lazily on the first lookup, which reads every data file and takes about a
second; call this at startup if you would rather not pay it on the first
request.

The build is serialised, so concurrent first requests queue behind a single
build rather than racing to repeat it — but they all still wait for it. In a
threaded server, calling `warm()` at startup keeps that second off your
request path entirely.

Accepts a dotted string, an `int`, or an `ipaddress.IPv4Address`. A malformed
address raises `ValueError`; a well-formed one that simply is not in the data
returns `None`.

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
- The dataset covers about 86% of the IPv4 space. Private, reserved and
  unallocated addresses return `None` from the lookup functions.
- `zz` is a placeholder code in the dataset rather than a real country; it is
  returned as-is when an address falls in one of its blocks.
- The shipped blocks are disjoint, so an address matches at most one. The test
  suite asserts this, so a data update that introduced an overlap would fail
  rather than silently return an arbitrary match.

## Development

```bash
python -m unittest discover -s tests   # the test suite
python -m mypy geoipgen/ --strict      # type check (clean)
```

CI runs the suite on Python 3.8 through 3.13, type-checks the package, and
re-validates the bundled data on every push and pull request.

The package ships a `py.typed` marker, so type checkers use its annotations
in your code rather than falling back to `Any`.

## Example

```bash
python example.py
```
