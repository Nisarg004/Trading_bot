"""Order placement logic for Binance Futures — market, limit, and stop-limit orders."""

from typing import Any

from bot.client import BinanceClient
from bot.logging_config import get_logger

logger = get_logger(__name__)

# Keys expected in a normalised order response; missing keys default to "N/A".
_RESPONSE_KEYS = (
    "orderId",
    "status",
    "symbol",
    "side",
    "type",
    "origQty",
    "executedQty",
    "avgPrice",
    "price",
    "updateTime",
)


def _normalise(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a dict containing only the standard order keys, defaulting missing ones to 'N/A'."""
    return {key: raw.get(key, "N/A") for key in _RESPONSE_KEYS}


class OrderManager:
    """High-level order placement interface backed by a BinanceClient."""

    def __init__(self, client: BinanceClient) -> None:
        """Initialise with an existing BinanceClient instance."""
        self._client = client

    def place_market_order(
        self, symbol: str, side: str, quantity: str, reduce_only: bool = False
    ) -> dict[str, Any]:
        """Place a MARKET order on Binance Futures.

        Args:
            symbol:      Trading pair, e.g. ``"BTCUSDT"``.
            side:        ``"BUY"`` or ``"SELL"``.
            quantity:    Order quantity as a string (e.g. ``"0.01"``).
            reduce_only: If True, the order can only reduce an existing position.

        Returns:
            Normalised order response dict.
        """
        logger.debug(
            "place_market_order() → symbol=%s side=%s quantity=%s reduce_only=%s",
            symbol, side, quantity, reduce_only,
        )
        params: dict[str, Any] = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "MARKET",
            "quantity": quantity,
        }
        if reduce_only:
            params["reduceOnly"] = "true"
        raw = self._client.place_order(**params)
        result = _normalise(raw)
        logger.debug("place_market_order() ← normalised=%s", result)
        return result

    def close_position(self, symbol: str, side: str, quantity: str) -> dict[str, Any]:
        """Close an existing futures position using a reduceOnly MARKET order.

        Args:
            symbol:   Trading pair, e.g. ``"BTCUSDT"``.
            side:     Opposing side of the position to close — ``"SELL"`` to close a long,
                      ``"BUY"`` to close a short.
            quantity: Full position quantity as a string.

        Returns:
            Normalised order response dict.
        """
        logger.info(
            "close_position() → symbol=%s side=%s quantity=%s",
            symbol, side, quantity,
        )
        return self.place_market_order(symbol, side, quantity, reduce_only=True)

    def place_limit_order(
        self, symbol: str, side: str, quantity: str, price: str
    ) -> dict[str, Any]:
        """Place a LIMIT GTC order on Binance Futures.

        Args:
            symbol:   Trading pair, e.g. ``"BTCUSDT"``.
            side:     ``"BUY"`` or ``"SELL"``.
            quantity: Order quantity as a string.
            price:    Limit price as a string.

        Returns:
            Normalised order response dict.
        """
        logger.debug(
            "place_limit_order() → symbol=%s side=%s quantity=%s price=%s",
            symbol, side, quantity, price,
        )
        params: dict[str, Any] = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "LIMIT",
            "quantity": quantity,
            "price": price,
            "timeInForce": "GTC",
        }
        raw = self._client.place_order(**params)
        result = _normalise(raw)
        logger.debug("place_limit_order() ← normalised=%s", result)
        return result

    def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: str,
        price: str,
        stop_price: str,
    ) -> dict[str, Any]:
        """Place a STOP (stop-limit) order on Binance Futures.

        The order triggers when the market reaches *stop_price*, then submits
        a limit order at *price*.

        Args:
            symbol:     Trading pair, e.g. ``"BTCUSDT"``.
            side:       ``"BUY"`` or ``"SELL"``.
            quantity:   Order quantity as a string.
            price:      Limit price (executed after trigger) as a string.
            stop_price: Trigger price as a string.

        Returns:
            Normalised order response dict.
        """
        logger.debug(
            "place_stop_limit_order() → symbol=%s side=%s quantity=%s price=%s stopPrice=%s",
            symbol, side, quantity, price, stop_price,
        )
        params: dict[str, Any] = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "STOP",
            "quantity": quantity,
            "price": price,
            "stopPrice": stop_price,
            "timeInForce": "GTC",
        }
        raw = self._client.place_order(**params)
        result = _normalise(raw)
        logger.debug("place_stop_limit_order() ← normalised=%s", result)
        return result
