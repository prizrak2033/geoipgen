# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added
- `geoipgen.reverse`: reverse lookup of which country holds an address, via a
  sorted interval index over every bundled block. `countryOf(ip)`,
  `lookup(ip)` (returning an `Allocation`), `blockOf(ip)`, and `warm()` to
  build the index ahead of time. Roughly 5 µs per lookup.
- Optional `rng` argument on `IP()`, `randomCIDR()` and `randomIP()`, plus an
  exported `SYSTEM_RNG` for callers who need unpredictable output. The default
  generator is unchanged.
- `iterIP(cidr)` and `functions.iter_ips(start, end)`: lazy generators for
  ranges too large to hold in memory.
- `cidrs(country)`, `countries()` and `randomIP(country)` helpers.
- Complete type annotations, checked under `mypy --strict`, with a `py.typed`
  marker so type checkers use them.
- A `unittest` suite, and CI running it across Python 3.8–3.13 alongside a
  type check and a data-integrity check.
- `pyproject.toml`, so the package installs with its `.cidr` data.

### Fixed
- The reverse-lookup index was cached with `functools.lru_cache`, which does
  not serialise: on a cache miss it runs the body in every concurrent caller,
  so threads racing the first lookup each built the whole index. Eight
  concurrent cold lookups took ~64s instead of ~1.2s. The build is now guarded
  by a lock.
- `randomCIDR()` used `randint(0, len(lines))`, inclusive at both ends, and
  raised `IndexError` on roughly one call in N.
- `randomCIDR()` resolved its data path relative to the working directory, so
  it only worked when run from the repository root. It now resolves relative
  to the package, and closes the file handle.
- `IP()` randomised each octet independently, so it could never generate an
  address ending in `.0` or `.255`, and was not uniform over the block.
- `simpleCalculate()` did not mask off the host bits of the given address, so
  `172.16.5.7/20` reported the wrong host range.
- `/31` reported an inverted range and `/32` a host count of `-1`. `/31` now
  follows RFC 3021 and `/32` is treated as a single host.
- Malformed CIDRs were accepted silently and produced garbage; they now raise
  `ValueError`.

### Changed
- The subnet calculator is built on the standard library `ipaddress` module
  rather than hand-rolled binary-string arithmetic. `printCalculate()` shares
  that one implementation and its output is byte-identical to before.
- `simpleCalculate()` returns a `SubnetInfo` named tuple. It is still a tuple,
  so positional access such as `info[3]` keeps working.

### Removed
- Committed `__pycache__/*.pyc` bytecode.

## [Pre-1.0] - 2020-08-30

Initial release: `IP()`, `rangeIP()`, `randomCIDR()`, and the bundled IPv4
CIDR allocations for 240 country codes.
