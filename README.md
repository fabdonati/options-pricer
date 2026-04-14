# options-pricer

`options-pricer` is a small Python library for pricing vanilla European options with
analytic Black-Scholes formulas, a Cox-Ross-Rubinstein binomial tree, and Monte Carlo
simulation. The pricing inputs include an optional continuous dividend yield.

## Features

- Black-Scholes pricing for calls and puts
- Binomial tree pricing for calls and puts
- Greeks computation
- Implied-volatility solving with Newton-Raphson
- Monte Carlo pricing baseline for comparison
- Monte Carlo diagnostics with confidence intervals and convergence charts
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
optprice compare --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call --steps 200 --paths 20000 --seed 42
```

Compare models for a dividend-paying option and include an implied-vol section from a market price:

```bash
optprice compare --spot 100 --strike 100 --rate 0.05 --dividend-yield 0.02 --volatility 0.2 --maturity 1 --type call --steps 200 --paths 20000 --seed 42 --market-price 9.227005508154036
```

Write the comparison report to CSV while still printing the terminal summary:

```bash
optprice compare --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call --steps 200 --paths 20000 --seed 42 --report-output reports/compare.csv
```

Sweep spot across a range and export a plot-ready comparison table:

```bash
optprice sweep --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call --axis spot --start 90 --stop 110 --points 5 --steps 200 --paths 20000 --seed 42 --output reports/spot_sweep.csv
```

The CSV contains:

- `axis`
- `value`
- `black_scholes`
- `binomial_tree`
- `monte_carlo`
- `tree_error_vs_black_scholes`
- `monte_carlo_error_vs_black_scholes`

Run Monte Carlo convergence diagnostics across multiple simulation sizes:

```bash
optprice mc-report --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call --path-grid 1000,5000,10000,20000,50000 --seed 42 --report-output reports/mc_report.csv --chart-output reports/mc_report.svg
```

The Monte Carlo diagnostics CSV contains:

- `paths`
- `seed`
- `monte_carlo_price`
- `black_scholes_price`
- `abs_error_vs_black_scholes`
- `sample_variance`
- `standard_error`
- `ci_lower_95`
- `ci_upper_95`

`--path-grid` is the convergence grid. Each value is the number of simulated price paths used in one Monte Carlo run. Larger path counts should reduce sampling noise and narrow the confidence interval, but they cost more runtime.

For a simple convergence sanity check, compare a few `compare` runs while increasing `--steps`
and keeping `--seed` fixed for Monte Carlo.

## How to read the comparison outputs

The repo now exposes three different analysis views:

- `compare`
  - answers how the three pricing methods differ for one contract
  - Black-Scholes is the analytic reference
  - binomial-tree and Monte Carlo rows are measured relative to that baseline
  - runtime values are useful for quick diagnostics, not formal benchmarking
- `compare --report-output`
  - writes the same comparison as a flat CSV so the output can be inspected in spreadsheets or downstream scripts
- `sweep`
  - answers how model prices and approximation error move when one input changes across a range
- `mc-report`
  - answers how the Monte Carlo estimator stabilizes as the number of simulated paths increases
  - reports uncertainty explicitly through standard error and a 95% confidence interval
  - exports both a flat CSV and an SVG convergence chart

The most useful columns in the sweep CSV are:

- `black_scholes`
  - the analytic reference price at each point
- `binomial_tree`
  - the lattice estimate at the same point
- `monte_carlo`
  - the simulation estimate at the same point
- `tree_error_vs_black_scholes`
  - approximation error from the tree
- `monte_carlo_error_vs_black_scholes`
  - approximation error from Monte Carlo

For a quick plot-ready workflow, generate a sweep CSV and inspect the first rows:

```bash
optprice sweep \
  --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call \
  --axis volatility --start 0.15 --stop 0.35 --points 5 \
  --steps 200 --paths 20000 --seed 42 \
  --output reports/vol_sweep.csv

sed -n '1,10p' reports/vol_sweep.csv
```

If you want a quick visual comparison, this minimal script turns that CSV into a price and error plot:

```bash
python - <<'PY'
import csv
from pathlib import Path

source = Path("reports/vol_sweep.csv")
with source.open(newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))

for row in rows:
    print(
        row["value"],
        row["black_scholes"],
        row["binomial_tree"],
        row["monte_carlo"],
        row["tree_error_vs_black_scholes"],
        row["monte_carlo_error_vs_black_scholes"],
    )
PY
```

That output is intentionally simple: the repo gives you a clean numerical table first, and that table
is already in the right shape for plotting or convergence notebooks.

For a self-contained convergence workflow, generate the Monte Carlo diagnostics CSV and SVG:

```bash
optprice mc-report \
  --spot 100 --strike 100 --rate 0.05 --volatility 0.2 --maturity 1 --type call \
  --path-grid 1000,5000,10000,20000,50000 \
  --seed 42 \
  --report-output reports/mc_report.csv \
  --chart-output reports/mc_report.svg

sed -n '1,10p' reports/mc_report.csv
```

The chart plots:

- the Monte Carlo price estimate at each path count
- the 95% confidence band around that estimate
- the Black-Scholes benchmark as a reference line

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
- Use `--seed` on `compare` when you want reproducible Monte Carlo rows from the CLI
- `mc-report` uses repeated full reruns at each path count, so it is a convergence diagnostic rather than a variance-reduction engine
