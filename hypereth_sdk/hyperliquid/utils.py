"""
HyperLiquid utility functions
"""


def round_size(size: float, sz_decimals: int) -> float:
    """
    Round size to the correct number of decimals for an asset.

    Args:
        size: The size to round
        sz_decimals: Number of decimals for the asset

    Returns:
        Properly rounded size
    """
    return round(size, sz_decimals)


def round_price(price: float, sz_decimals: int, is_spot: bool = False) -> float:
    """
    Round price according to Hyperliquid rules.
    Prices can have up to 5 significant figures, but no more than
    MAX_DECIMALS - szDecimals decimal places where MAX_DECIMALS is 6 for perps and 8 for spot.

    Args:
        price: The price to round
        sz_decimals: Number of decimals for the asset
        is_spot: Whether this is spot trading (8 max decimals) or perps (6 max decimals)

    Returns:
        Properly rounded price
    """
    max_decimals = 8 if is_spot else 6

    # If price is greater than 100k, round to integer
    if price > 100_000:
        return float(round(price))

    # Otherwise round to 5 significant figures and max_decimals - szDecimals decimal places
    rounded_sig_figs = float(f"{price:.5g}")
    max_decimal_places = max_decimals - sz_decimals
    return round(rounded_sig_figs, max_decimal_places)