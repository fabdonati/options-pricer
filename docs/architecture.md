# Architecture Notes

## Design goals

- Keep the core formulas readable and testable
- Separate pricing, Greeks, and root-finding concerns
- Provide a simulation baseline for sanity checks

## Components

- `models.py`: option contract specification
- `black_scholes.py`: closed-form pricing
- `greeks.py`: first- and second-order sensitivities
- `implied_vol.py`: Newton-Raphson solver
- `monte_carlo.py`: terminal-price simulation
- `cli.py`: shell-friendly entrypoint

## Numerical assumptions

- Black-Scholes dynamics with constant volatility
- Continuous compounding for the risk-free rate
- European exercise only
- No dividends in v0.1.0

## Validation approach

The repo uses two kinds of checks:

- reference-value tests against well-known Black-Scholes outputs
- Monte Carlo comparisons to make sure the simulation path stays in the right neighborhood
