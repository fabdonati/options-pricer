from __future__ import annotations

import subprocess
import sys

import pytest


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


def test_price_command_accepts_dividend_yield() -> None:
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
            "--dividend-yield",
            "0.02",
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

    assert "9.227006" in result.stdout


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
            "--steps",
            "150",
            "--paths",
            "5000",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Black-Scholes" in result.stdout
    assert "Binomial tree" in result.stdout
    assert "Monte Carlo" in result.stdout


def test_compare_command_accepts_dividend_yield() -> None:
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
            "--dividend-yield",
            "0.02",
            "--volatility",
            "0.2",
            "--maturity",
            "1",
            "--type",
            "call",
            "--steps",
            "150",
            "--paths",
            "5000",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Black-Scholes" in result.stdout
    assert "Binomial tree" in result.stdout
    assert "Monte Carlo" in result.stdout


def test_tree_command_prints_option_value() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "options_pricer.cli",
            "tree",
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
            "--steps",
            "200",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert float(result.stdout.strip()) == pytest.approx(10.450584, abs=0.05)
