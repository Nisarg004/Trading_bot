"""Standalone connection test — verifies API credentials and Futures Testnet reachability.

Does NOT place any orders.
Run: python test_connection.py
"""

from bot.client import BinanceClient, BinanceClientError


def main() -> None:
    """Instantiate BinanceClient and call get_account_info() as a connectivity check."""
    try:
        client = BinanceClient()
        info = client.get_account_info()
        print("Connection OK")
        print(f"  totalWalletBalance : {info.get('totalWalletBalance', 'N/A')} USDT")
        print(f"  totalUnrealizedProfit: {info.get('totalUnrealizedProfit', 'N/A')} USDT")
        print(f"  canTrade           : {info.get('canTrade', 'N/A')}")
    except BinanceClientError as exc:
        print(f"Connection FAILED: {exc}")


if __name__ == "__main__":
    main()
