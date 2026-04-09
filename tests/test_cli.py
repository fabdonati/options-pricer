from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

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


def test_compare_command_prints_structured_report_sections() -> None:
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

    assert "Contract" in result.stdout
    assert "Price Comparison" in result.stdout
    assert "Analytic Greeks" in result.stdout
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

    assert "Dividend yield: 0.020000" in result.stdout
    assert "Analytic Greeks" in result.stdout


def test_compare_command_accepts_market_price() -> None:
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
            "--market-price",
            "10.450583572185565",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Market" in result.stdout
    assert "Implied volatility: 0.200000" in result.stdout


def test_compare_command_writes_csv_report(tmp_path: Path) -> None:
    report_path = tmp_path / "compare_report.csv"
    subprocess.run(
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
            "--market-price",
            "10.450583572185565",
            "--report-output",
            str(report_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert report_path.exists()
    with report_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert {"section": "contract", "name": "spot", "value": "100.0"} in rows
    assert any(
        row["section"] == "price:black_scholes" and row["name"] == "price" for row in rows
    )
    assert any(
        row["section"] == "price:binomial_tree"
        and row["name"] == "abs_error_vs_black_scholes"
        for row in rows
    )
    delta_row = next(row for row in rows if row["section"] == "greeks" and row["name"] == "delta")
    implied_vol_row = next(
        row for row in rows if row["section"] == "market" and row["name"] == "implied_volatility"
    )

    assert float(delta_row["value"]) == pytest.approx(0.6368306512, rel=1e-6)
    assert float(implied_vol_row["value"]) == pytest.approx(0.2, rel=1e-9)


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
