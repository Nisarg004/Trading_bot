"""Input validation helpers — validate symbol, side, order type, quantity, price, and stop price."""

import re

from bot.logging_config import get_logger

logger = get_logger(__name__)

_SYMBOL_RE = re.compile(r"^[A-Z]{2,10}(USDT|BUSD)$")
_VALID_SIDES = {"BUY", "SELL"}
_VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}


class InputValidator:
    """Collection of static validation methods for CLI order parameters."""

    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """Uppercase and validate a trading pair symbol.

        Must be 2-10 uppercase letters followed by 'USDT' or 'BUSD'.

        Args:
            symbol: Raw symbol string from the user, e.g. ``"btcusdt"``.

        Returns:
            Normalised uppercase symbol, e.g. ``"BTCUSDT"``.

        Raises:
            ValueError: If the symbol does not match the required pattern.
        """
        normalised = symbol.strip().upper()
        if not _SYMBOL_RE.match(normalised):
            raise ValueError(
                f"Invalid symbol '{symbol}'. "
                "Expected 2-10 uppercase letters followed by 'USDT' or 'BUSD' "
                "(e.g. BTCUSDT, ETHUSDT)."
            )
        logger.debug("validate_symbol: '%s' → '%s'", symbol, normalised)
        return normalised

    @staticmethod
    def validate_side(side: str) -> str:
        """Normalise and validate an order side.

        Args:
            side: Raw side string, e.g. ``"buy"`` or ``"SELL"``.

        Returns:
            Uppercase side: ``"BUY"`` or ``"SELL"``.

        Raises:
            ValueError: If the side is not 'BUY' or 'SELL'.
        """
        normalised = side.strip().upper()
        if normalised not in _VALID_SIDES:
            raise ValueError(
                f"Invalid side '{side}'. Must be one of: {', '.join(sorted(_VALID_SIDES))}."
            )
        logger.debug("validate_side: '%s' → '%s'", side, normalised)
        return normalised

    @staticmethod
    def validate_order_type(order_type: str) -> str:
        """Normalise and validate an order type.

        Args:
            order_type: Raw order type string, e.g. ``"limit"`` or ``"MARKET"``.

        Returns:
            Uppercase order type: ``"MARKET"``, ``"LIMIT"``, or ``"STOP_LIMIT"``.

        Raises:
            ValueError: If the order type is not recognised.
        """
        normalised = order_type.strip().upper()
        if normalised not in _VALID_ORDER_TYPES:
            raise ValueError(
                f"Invalid order type '{order_type}'. "
                f"Must be one of: {', '.join(sorted(_VALID_ORDER_TYPES))}."
            )
        logger.debug("validate_order_type: '%s' → '%s'", order_type, normalised)
        return normalised

    @staticmethod
    def validate_quantity(quantity: str) -> float:
        """Parse and validate an order quantity.

        Args:
            quantity: Quantity as a string, e.g. ``"0.01"``.

        Returns:
            Quantity as a positive float.

        Raises:
            ValueError: If the value is not a valid positive number.
        """
        try:
            value = float(quantity)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid quantity '{quantity}'. Must be a numeric value (e.g. 0.01)."
            ) from exc
        if value <= 0:
            raise ValueError(
                f"Quantity must be greater than 0, got '{quantity}'."
            )
        logger.debug("validate_quantity: '%s' → %s", quantity, value)
        return value

    @staticmethod
    def validate_price(price: str | None, order_type: str) -> float | None:
        """Validate the limit price against the order type.

        Args:
            price:      Price as a string, or ``None``.
            order_type: Normalised order type (``"MARKET"``, ``"LIMIT"``, ``"STOP_LIMIT"``).

        Returns:
            Price as a positive float for LIMIT/STOP_LIMIT, or ``None`` for MARKET.

        Raises:
            ValueError: If price is missing when required, or present and invalid.
        """
        if order_type == "MARKET":
            logger.debug("validate_price: MARKET order — price ignored.")
            return None

        # LIMIT or STOP_LIMIT — price is required.
        if price is None:
            raise ValueError(
                f"--price is required for {order_type} orders."
            )
        try:
            value = float(price)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid price '{price}'. Must be a numeric value (e.g. 45000.00)."
            ) from exc
        if value <= 0:
            raise ValueError(
                f"Price must be greater than 0, got '{price}'."
            )
        logger.debug("validate_price: '%s' → %s (order_type=%s)", price, value, order_type)
        return value

    @staticmethod
    def validate_stop_price(stop_price: str | None, order_type: str) -> float | None:
        """Validate the stop trigger price for STOP_LIMIT orders.

        Args:
            stop_price: Stop price as a string, or ``None``.
            order_type: Normalised order type.

        Returns:
            Stop price as a positive float for STOP_LIMIT, or ``None`` otherwise.

        Raises:
            ValueError: If stop_price is missing or invalid for a STOP_LIMIT order.
        """
        if order_type != "STOP_LIMIT":
            logger.debug("validate_stop_price: not a STOP_LIMIT order — stop_price ignored.")
            return None

        if stop_price is None:
            raise ValueError("--stop-price is required for STOP_LIMIT orders.")

        try:
            value = float(stop_price)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid stop price '{stop_price}'. Must be a numeric value (e.g. 44500.00)."
            ) from exc
        if value <= 0:
            raise ValueError(
                f"Stop price must be greater than 0, got '{stop_price}'."
            )
        logger.debug("validate_stop_price: '%s' → %s", stop_price, value)
        return value
