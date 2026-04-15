"""CLI entry point — parses user arguments and delegates to the bot layer."""

import sys
import traceback
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from bot.client import BinanceClient, BinanceClientError
from bot.logging_config import get_logger
from bot.orders import OrderManager
from bot.validators import InputValidator

logger = get_logger(__name__)
console = Console()
err_console = Console(stderr=True)


def _print_request_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
    stop_price: Optional[float],
) -> None:
    """Print a rich table summarising the order that is about to be placed."""
    table = Table(title="Order Request Summary", show_header=False, min_width=42)
    table.add_column("Field", style="bold cyan", min_width=16)
    table.add_column("Value", style="white")

    table.add_row("Symbol", symbol)
    table.add_row("Side", side)
    table.add_row("Type", order_type)
    table.add_row("Quantity", str(quantity))
    if price is not None:
        table.add_row("Price", f"{price:.8f}")
    if stop_price is not None:
        table.add_row("Stop Price", f"{stop_price:.8f}")

    console.print(table)


def _print_order_response(response: dict) -> None:
    """Print a rich table with the normalised order response from Binance."""
    table = Table(title="Order Response", show_header=False, min_width=42)
    table.add_column("Field", style="bold cyan", min_width=16)
    table.add_column("Value", style="white")

    table.add_row("Order ID", str(response.get("orderId", "N/A")))
    table.add_row("Status", str(response.get("status", "N/A")))
    table.add_row("Symbol", str(response.get("symbol", "N/A")))
    table.add_row("Side", str(response.get("side", "N/A")))
    table.add_row("Type", str(response.get("type", "N/A")))
    table.add_row("Orig Qty", str(response.get("origQty", "N/A")))
    table.add_row("Executed Qty", str(response.get("executedQty", "N/A")))
    table.add_row("Avg Price", str(response.get("avgPrice", "N/A")))
    table.add_row("Price", str(response.get("price", "N/A")))

    console.print(table)
    console.print("[bold green]✓ Order placed successfully[/bold green]")


@click.group()
def trade() -> None:
    """Binance Futures Testnet trading bot CLI."""


@trade.command("order")
@click.option(
    "--symbol",
    required=True,
    type=str,
    help="Trading pair symbol. Example: BTCUSDT",
)
@click.option(
    "--side",
    required=True,
    type=str,
    help="Order side. Must be BUY or SELL.",
)
@click.option(
    "--type",
    "order_type",
    required=True,
    type=str,
    help="Order type. One of: MARKET, LIMIT, STOP_LIMIT.",
)
@click.option(
    "--quantity",
    required=True,
    type=str,
    help="Order quantity. Example: 0.01",
)
@click.option(
    "--price",
    default=None,
    type=str,
    help="Limit price (required for LIMIT and STOP_LIMIT orders). Example: 45000.00",
)
@click.option(
    "--stop-price",
    default=None,
    type=str,
    help="Stop trigger price (required for STOP_LIMIT orders). Example: 44500.00",
)
def order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str],
    stop_price: Optional[str],
) -> None:
    """Place a futures order on Binance Testnet (MARKET, LIMIT, or STOP_LIMIT).

    Examples:\n
      python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01\n
      python cli.py order --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 3200.00\n
      python cli.py order --symbol BTCUSDT --side BUY --type STOP_LIMIT --quantity 0.01 --price 45000 --stop-price 44500
    """
    # ------------------------------------------------------------------ #
    # 1. Validate all inputs
    # ------------------------------------------------------------------ #
    try:
        v_symbol = InputValidator.validate_symbol(symbol)
        v_side = InputValidator.validate_side(side)
        v_order_type = InputValidator.validate_order_type(order_type)
        v_quantity = InputValidator.validate_quantity(quantity)
        v_price = InputValidator.validate_price(price, v_order_type)
        v_stop_price = InputValidator.validate_stop_price(stop_price, v_order_type)
    except ValueError as exc:
        err_console.print(f"[bold red]✗ Validation Error:[/bold red] {exc}")
        logger.error("Validation error: %s", exc)
        sys.exit(1)

    # ------------------------------------------------------------------ #
    # 2. Print request summary
    # ------------------------------------------------------------------ #
    _print_request_summary(v_symbol, v_side, v_order_type, v_quantity, v_price, v_stop_price)

    # ------------------------------------------------------------------ #
    # 3. Initialise client & place order
    # ------------------------------------------------------------------ #
    try:
        client = BinanceClient()
        manager = OrderManager(client)

        qty_str = str(round(v_quantity, 8))

        if v_order_type == "MARKET":
            response = manager.place_market_order(v_symbol, v_side, qty_str)

        elif v_order_type == "LIMIT":
            price_str = str(round(v_price, 8))  # type: ignore[arg-type]
            response = manager.place_limit_order(v_symbol, v_side, qty_str, price_str)

        else:  # STOP_LIMIT
            price_str = str(round(v_price, 8))  # type: ignore[arg-type]
            stop_str = str(round(v_stop_price, 8))  # type: ignore[arg-type]
            response = manager.place_stop_limit_order(
                v_symbol, v_side, qty_str, price_str, stop_str
            )

    except BinanceClientError as exc:
        err_console.print(f"[bold red]✗ API Error:[/bold red] {exc}")
        logger.error("BinanceClientError: %s", exc)
        sys.exit(1)

    except OSError as exc:
        err_console.print(f"[bold red]✗ Network Error:[/bold red] {exc}")
        logger.error("Network/OS error: %s", exc)
        sys.exit(1)

    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected error: %s\n%s", exc, traceback.format_exc())
        err_console.print(
            "[bold red]✗ Unexpected Error:[/bold red] An unexpected error occurred. "
            "See logs/trading_bot.log for details."
        )
        sys.exit(1)

    # ------------------------------------------------------------------ #
    # 4. Print response
    # ------------------------------------------------------------------ #
    _print_order_response(response)


def _prompt_with_validation(prompt_text: str, validator, *validator_args) -> str:
    """Loop-prompt until the validator accepts the input. Returns the raw accepted string."""
    while True:
        value = click.prompt(prompt_text)
        try:
            validator(value, *validator_args)
            return value
        except ValueError as exc:
            err_console.print(f"[bold red]✗[/bold red] {exc}")


@trade.command("interactive")
def interactive() -> None:
    """Guided interactive order entry with step-by-step prompts."""
    console.print("\n[bold cyan]Binance Futures — Interactive Order Entry[/bold cyan]\n")

    # -- symbol --
    symbol_raw = _prompt_with_validation(
        "Symbol (e.g. BTCUSDT)", InputValidator.validate_symbol
    )
    v_symbol = InputValidator.validate_symbol(symbol_raw)

    # -- side --
    while True:
        side_raw = click.prompt("Side [BUY/SELL]")
        try:
            v_side = InputValidator.validate_side(side_raw)
            break
        except ValueError as exc:
            err_console.print(f"[bold red]✗[/bold red] {exc}")

    # -- order type --
    while True:
        type_raw = click.prompt("Order type [MARKET/LIMIT/STOP_LIMIT]")
        try:
            v_order_type = InputValidator.validate_order_type(type_raw)
            break
        except ValueError as exc:
            err_console.print(f"[bold red]✗[/bold red] {exc}")

    # -- price (LIMIT / STOP_LIMIT only) --
    v_price: Optional[float] = None
    if v_order_type in ("LIMIT", "STOP_LIMIT"):
        while True:
            price_raw = click.prompt("Limit price")
            try:
                v_price = InputValidator.validate_price(price_raw, v_order_type)
                break
            except ValueError as exc:
                err_console.print(f"[bold red]✗[/bold red] {exc}")

    # -- stop price (STOP_LIMIT only) --
    v_stop_price: Optional[float] = None
    if v_order_type == "STOP_LIMIT":
        while True:
            sp_raw = click.prompt("Stop trigger price")
            try:
                v_stop_price = InputValidator.validate_stop_price(sp_raw, v_order_type)
                break
            except ValueError as exc:
                err_console.print(f"[bold red]✗[/bold red] {exc}")

    # -- quantity --
    while True:
        qty_raw = click.prompt("Quantity")
        try:
            v_quantity = InputValidator.validate_quantity(qty_raw)
            break
        except ValueError as exc:
            err_console.print(f"[bold red]✗[/bold red] {exc}")

    # -- summary + confirm --
    console.print()
    _print_request_summary(v_symbol, v_side, v_order_type, v_quantity, v_price, v_stop_price)

    confirm = click.prompt("Confirm order? [y/N]", default="N").strip().lower()
    if confirm != "y":
        console.print("[yellow]Order cancelled.[/yellow]")
        return

    # -- place order --
    try:
        client = BinanceClient()
        manager = OrderManager(client)
        qty_str = str(round(v_quantity, 8))

        if v_order_type == "MARKET":
            response = manager.place_market_order(v_symbol, v_side, qty_str)
        elif v_order_type == "LIMIT":
            response = manager.place_limit_order(
                v_symbol, v_side, qty_str, str(round(v_price, 8))  # type: ignore[arg-type]
            )
        else:  # STOP_LIMIT
            response = manager.place_stop_limit_order(
                v_symbol,
                v_side,
                qty_str,
                str(round(v_price, 8)),  # type: ignore[arg-type]
                str(round(v_stop_price, 8)),  # type: ignore[arg-type]
            )
    except BinanceClientError as exc:
        err_console.print(f"[bold red]✗ API Error:[/bold red] {exc}")
        logger.error("BinanceClientError: %s", exc)
        sys.exit(1)
    except OSError as exc:
        err_console.print(f"[bold red]✗ Network Error:[/bold red] {exc}")
        logger.error("Network/OS error: %s", exc)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected error: %s\n%s", exc, traceback.format_exc())
        err_console.print(
            "[bold red]✗ Unexpected Error:[/bold red] An unexpected error occurred. "
            "See logs/trading_bot.log for details."
        )
        sys.exit(1)

    _print_order_response(response)


@trade.command("status")
def status() -> None:
    """Show account balance and unrealised PnL from Binance Futures Testnet."""
    try:
        client = BinanceClient()
        info = client.get_account_info()
    except BinanceClientError as exc:
        err_console.print(f"[bold red]✗ API Error:[/bold red] {exc}")
        logger.error("BinanceClientError in status: %s", exc)
        sys.exit(1)
    except OSError as exc:
        err_console.print(f"[bold red]✗ Network Error:[/bold red] {exc}")
        logger.error("Network/OS error in status: %s", exc)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected error in status: %s\n%s", exc, traceback.format_exc())
        err_console.print(
            "[bold red]✗ Unexpected Error:[/bold red] An unexpected error occurred. "
            "See logs/trading_bot.log for details."
        )
        sys.exit(1)

    table = Table(title="Account Status (Futures Testnet)", show_header=False, min_width=48)
    table.add_column("Metric", style="bold cyan", min_width=28)
    table.add_column("Value", style="white")

    table.add_row(
        "Available Balance (USDT)",
        str(info.get("availableBalance", "N/A")),
    )
    table.add_row(
        "Total Wallet Balance",
        str(info.get("totalWalletBalance", "N/A")),
    )
    table.add_row(
        "Total Unrealized PnL",
        str(info.get("totalUnrealizedProfit", "N/A")),
    )

    console.print(table)


if __name__ == "__main__":
    trade()
