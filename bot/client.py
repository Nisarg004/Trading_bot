"""Binance Futures Testnet client wrapper — abstracts all API communication."""

import os
from typing import Any

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv

from bot.logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error or a network failure occurs."""

    def __init__(self, message: str, raw_error: Exception | None = None) -> None:
        """Initialise with a human-readable message and the original exception."""
        super().__init__(message)
        self.raw_error = raw_error


class BinanceClient:
    """Thin wrapper around python-binance targeting the Futures Testnet (USDT-M)."""

    def __init__(self) -> None:
        """Load credentials from environment and initialise the Binance client."""
        api_key = os.getenv("BINANCE_API_KEY", "")
        api_secret = os.getenv("BINANCE_API_SECRET", "")

        if not api_key or not api_secret:
            raise BinanceClientError(
                "BINANCE_API_KEY and BINANCE_API_SECRET must be set in the environment."
            )

        logger.debug(
            "Initialising BinanceClient | key=%s...%s | testnet=True",
            api_key[:4],
            api_key[-4:],
        )

        try:
            self._client = Client(
                api_key=api_key,
                api_secret=api_secret,
                testnet=True,
                tld="com",
            )
        except Exception as exc:
            logger.error("Failed to initialise Binance client: %s", exc)
            raise BinanceClientError("Client initialisation failed.", exc) from exc

        logger.info("BinanceClient initialised successfully (Futures Testnet).")

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_account_info(self) -> dict[str, Any]:
        """Fetch USDT-M Futures account balance and position information."""
        logger.debug("Request → futures_account()")
        try:
            response: dict[str, Any] = self._client.futures_account()
        except BinanceAPIException as exc:
            logger.error("API error in get_account_info: %s", exc)
            raise BinanceClientError("Failed to fetch account info.", exc) from exc
        except BinanceRequestException as exc:
            logger.error("Network error in get_account_info: %s", exc)
            raise BinanceClientError("Network failure fetching account info.", exc) from exc

        logger.debug("Response ← futures_account(): %s", response)
        logger.info(
            "Account info fetched | totalWalletBalance=%s USDT",
            response.get("totalWalletBalance", "N/A"),
        )
        return response

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        """Fetch exchange info for a specific futures symbol.

        Args:
            symbol: Trading pair, e.g. ``"BTCUSDT"``.

        Returns:
            The symbol's exchange-info dict from Binance.

        Raises:
            BinanceClientError: If the symbol is not found or an API/network error occurs.
        """
        logger.debug("Request → futures_exchange_info() for symbol=%s", symbol)
        try:
            exchange_info: dict[str, Any] = self._client.futures_exchange_info()
        except BinanceAPIException as exc:
            logger.error("API error in get_symbol_info(%s): %s", symbol, exc)
            raise BinanceClientError(f"Failed to fetch exchange info for {symbol}.", exc) from exc
        except BinanceRequestException as exc:
            logger.error("Network error in get_symbol_info(%s): %s", symbol, exc)
            raise BinanceClientError(f"Network failure fetching exchange info for {symbol}.", exc) from exc

        symbols: list[dict[str, Any]] = exchange_info.get("symbols", [])
        matched = next((s for s in symbols if s["symbol"] == symbol.upper()), None)

        if matched is None:
            raise BinanceClientError(f"Symbol '{symbol}' not found on Futures Testnet.")

        logger.debug("Response ← get_symbol_info(%s): %s", symbol, matched)
        logger.info("Symbol info fetched | symbol=%s | status=%s", symbol, matched.get("status"))
        return matched

    def place_order(self, **kwargs: Any) -> dict[str, Any]:
        """Submit a futures order to Binance.

        All keyword arguments are forwarded directly to ``futures_create_order``.
        Monetary values (price, quantity, stopPrice) must already be strings.

        Returns:
            Raw order response dict from Binance.

        Raises:
            BinanceClientError: On API or network failure.
        """
        # Redact nothing sensitive here (no secret in params), but log all params.
        logger.debug("Request → futures_create_order() | params=%s", kwargs)
        try:
            response: dict[str, Any] = self._client.futures_create_order(**kwargs)
        except BinanceAPIException as exc:
            logger.error(
                "API error placing order | params=%s | error=%s", kwargs, exc
            )
            raise BinanceClientError(f"Order placement failed: {exc}", exc) from exc
        except BinanceRequestException as exc:
            logger.error(
                "Network error placing order | params=%s | error=%s", kwargs, exc
            )
            raise BinanceClientError("Network failure during order placement.", exc) from exc

        logger.debug("Response ← futures_create_order(): %s", response)
        logger.info(
            "Placed %s %s %s %s → orderId: %s | status: %s",
            response.get("type", "?"),
            response.get("side", "?"),
            response.get("origQty", "?"),
            response.get("symbol", "?"),
            response.get("orderId", "?"),
            response.get("status", "?"),
        )
        return response
