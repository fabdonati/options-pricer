# Architecture Notes

## Design goals

- Keep the core formulas readable and testable
- Separate pricing, Greeks, and root-finding concerns
- Provide both lattice and simulation baselines for sanity checks
- Keep model-comparison reporting in a thin layer above the pricing functions

## Components

- `models.py`: option contract specification
- `black_scholes.py`: closed-form pricing
- `binomial_tree.py`: Cox-Ross-Rubinstein lattice pricing
- `greeks.py`: first- and second-order sensitivities
- `implied_vol.py`: Newton-Raphson solver
- `monte_carlo.py`: terminal-price simulation
- `reporting.py`: model-comparison report builder and CSV export
- `cli.py`: shell-friendly entrypoint

## Numerical assumptions

- Black-Scholes dynamics with constant volatility
- Continuous compounding for the risk-free rate
- Optional continuous dividend yield
- European exercise only
- No discrete-dividend schedule support

## Validation approach

The repo uses two kinds of checks:

- reference-value tests against well-known Black-Scholes outputs
- binomial-tree convergence checks against Black-Scholes
- Monte Carlo comparisons to make sure the simulation path stays in the right neighborhood
- CLI comparison-report checks for terminal output and CSV export

## Comparison report conventions

- Black-Scholes is the reference baseline for model-error rows
- Greeks in the report are analytic Black-Scholes Greeks
- Implied volatility is only shown when the caller provides a market price
- Monte Carlo rows can be made reproducible from the CLI via an explicit seed
- Runtime in the report is a rough CLI diagnostic, not a benchmark-quality measurement
