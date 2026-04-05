from __future__ import annotations

import subprocess
import sys


def test_price_command_prints_option_value() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "options_pricer.cli",
            "price",
            "--spot",
            "100",
            "--strike",
            "100",
            "--rate",
            "0.05",
            "--volatility",
            "0.2",
            "--maturity",
            "1",
            "--type",
            "call",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "10.450584" in result.stdout


def test_compare_command_prints_analytic_and_simulated_prices() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "options_pricer.cli",
            "compare",
            "--spot",
            "100",
            "--strike",
            "100",
            "--rate",
            "0.05",
            "--volatility",
            "0.2",
            "--maturity",
            "1",
            "--type",
            "call",
            "--paths",
            "5000",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Black-Scholes" in result.stdout
    assert "Monte Carlo" in result.stdout
