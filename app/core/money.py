from decimal import Decimal, ROUND_HALF_EVEN

# Standard financial quantization for EUR: 2 decimal places (0.01)
CENT = Decimal("0.01")


def quantize_amount(value: Decimal) -> Decimal:
    """
    Strictly quantizes any monetary value to 2 decimal places
    using standard banking rounding (ROUND_HALF_EVEN).
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(CENT, rounding=ROUND_HALF_EVEN)
