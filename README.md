# options-pricer

`options-pricer` is a small Python library for pricing vanilla European options with
analytic Black-Scholes formulas, a Cox-Ross-Rubinstein binomial tree, and Monte Carlo
simulation. The pricing inputs include an optional continuous dividend yield.

## Why this project

Pricing code is a good place to show numerical discipline: clear assumptions, reference-value
tests, and simple comparison tooling. This repo focuses on the parts that are easy to audit
and useful in interviews or small research workflows.

## Features

- Black-Scholes pricing for calls and puts
- Binomial tree pricing for calls and puts
- Greeks computation
- Implied-volatility solving with Newton-Raphson
- Monte Carlo pricing baseline for comparison
- CLI for pricing, implied vol, and model comparison reports

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

Price a dividend-paying call:

```bash
optprice price --spot 100 --strike 100 --rate 0.05 --dividend-yield 0.02 --volatility 0.2 --maturity 1 --type call
```

Infer implied volatility:

```bash
optprice iv --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call --market-price 10.45
```

Price with the binomial tree:

```bash
optprice tree --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call --steps 200
```

Compare analytic, tree, and Monte Carlo prices:

```bash
optprice compare --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call --steps 200 --paths 20000
```

Compare models for a dividend-paying option and include an implied-vol section from a market price:

```bash
optprice compare --spot 100 --strike 100 --rate 0.05 --dividend-yield 0.02 --volatility 0.2 --maturity 1 --type call --steps 200 --paths 20000 --market-price 9.227005508154036
```

Write the comparison report to CSV while still printing the terminal summary:

```bash
optprice compare --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call --steps 200 --paths 20000 --report-output reports/compare.csv
```

## Package usage

```python
from options_pricer import OptionSpec, binomial_tree_price, black_scholes_price, implied_volatility

spec = OptionSpec(
    spot=100.0,
    strike=100.0,
    rate=0.05,
    volatility=0.2,
    maturity=1.0,
    option_type="call",
    dividend_yield=0.02,
)

price = black_scholes_price(spec)
tree_price = binomial_tree_price(spec, steps=200)
sigma = implied_volatility(price, spec)
```

## Limitations

- v0.1.0 only supports vanilla European options
- Dividend support is modeled as a continuous yield input rather than sourced reference data
- Binomial tree support is limited to European exercise in this stage
- Monte Carlo is designed as a comparison baseline, not a low-latency engine
- Runtime values in `compare` are rough in-process diagnostics, not benchmark-quality timings
