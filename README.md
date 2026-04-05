# options-pricer

`options-pricer` is a small Python library for pricing vanilla European options with both
analytic Black-Scholes formulas and Monte Carlo simulation.

## Why this project

Pricing code is a good place to show numerical discipline: clear assumptions, reference-value
tests, and simple comparison tooling. This repo focuses on the parts that are easy to audit
and useful in interviews or small research workflows.

## Features

- Black-Scholes pricing for calls and puts
- Greeks computation
- Implied-volatility solving with Newton-Raphson
- Monte Carlo pricing baseline for comparison
- CLI for pricing, implied vol, and model comparisons

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## CLI usage

Price a call:

```bash
optprice price --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call
```

Infer implied volatility:

```bash
optprice iv --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call --market-price 10.45
```

Compare analytic and Monte Carlo prices:

```bash
optprice compare --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call --paths 20000
```

## Package usage

```python
from options_pricer import OptionSpec, black_scholes_price, implied_volatility

spec = OptionSpec(
    spot=100.0,
    strike=100.0,
    rate=0.05,
    volatility=0.2,
    maturity=1.0,
    option_type="call",
)

price = black_scholes_price(spec)
sigma = implied_volatility(price, spec)
```

## Limitations

- v0.1.0 only supports vanilla European options
- No dividends or stochastic-volatility extensions
- Monte Carlo is designed as a comparison baseline, not a low-latency engine
