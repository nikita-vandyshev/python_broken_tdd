"""Order checkout.

The rules live in `src/shop/specs/checkout.md` - read it first.
Both functions below are stubs: their signature is final, the bodies are yours.
Do not change the constants: the tests rely on them.
"""

from shop.money import percent_of

PROMO_CODES = {"WELCOME10": 10, "SUMMER15": 15, "VIP35": 35}
SUPPORTED_CITIES = ("msk", "spb")
MAX_DISCOUNT_PERCENT = 30
VAT_PERCENT = 20
SHIPPING_KOPEKS = 49_000
FREE_DELIVERY_FROM_KOPEKS = 500_000
TIER_DISCOUNTS = ((10, 5), (25, 10), (50, 15))
REQUIRED_LINE_KEYS = ("sku", "qty", "unit_price_kopecks")


def _is_integer(value: str) -> bool:
    value = value.strip()

    if value.startswith(("+", "-")):
        value = value[1:]

    return value.isdigit()


def _validate_line(line: dict[str, str], seen_skus: set[str]) -> str | None:
    for key in REQUIRED_LINE_KEYS:
        if key not in line:
            return "required key is missing"

    sku = line["sku"]
    qty_text = line["qty"]
    price_text = line["unit_price_kopecks"]

    if sku == "":
        return "sku is empty"

    if not _is_integer(qty_text):
        return "quantity is not a number"

    qty = int(qty_text)
    if qty <= 0:
        return "quantity must be positive"

    if not _is_integer(price_text):
        return "price is not a number"

    price = int(price_text)
    if price < 0:
        return "price cannot be negative"

    if sku in seen_skus:
        return "duplicate sku"

    seen_skus.add(sku)
    return None


def validate_order(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> str | None:
    """Return a human readable reason why the order is invalid, or None if it is fine."""
    if not lines:
        return "order has no lines"

    seen_skus: set[str] = set()

    for line in lines:
        problem = _validate_line(line, seen_skus)
        if problem is not None:
            return problem

    if promo_code and promo_code not in PROMO_CODES:
        return "unknown promo code"

    if shipping_city and shipping_city not in SUPPORTED_CITIES:
        return "unsupported city"

    return None


def calculate_order_total(
    lines: list[dict[str, str]],
    promo_code: str = "",
    shipping_city: str = "",
) -> int | None:
    """Return the order total in kopecks, or None if the order is invalid."""
    if validate_order(lines, promo_code, shipping_city) is not None:
        return None

    subtotal = 0
    total_qty = 0

    for line in lines:
        qty = int(line["qty"])
        price = int(line["unit_price_kopecks"])

        subtotal += qty * price
        total_qty += qty

    tier_discount = 0
    for threshold, discount in TIER_DISCOUNTS:
        if total_qty >= threshold:
            tier_discount = discount

    promo_discount = PROMO_CODES.get(promo_code, 0)

    discount_percent = max(tier_discount, promo_discount)
    discount_percent = min(discount_percent, MAX_DISCOUNT_PERCENT)

    discount = percent_of(subtotal, discount_percent)
    discounted_subtotal = subtotal - discount

    shipping = 0
    if shipping_city and discounted_subtotal < FREE_DELIVERY_FROM_KOPEKS:
        shipping = SHIPPING_KOPEKS

    base = discounted_subtotal + shipping
    vat = percent_of(base, VAT_PERCENT)

    return base + vat
