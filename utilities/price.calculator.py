#price calculator


REG_HAIRSTYLES_PRICES = {
    "Wash and Perm": 65.00,
    "Color": 65.00,
    "Wash and Blow Dry": 45.00,
    "PonyTail": 50.00,
    "Blow-Out": 85.00,
    "Press - out": 45.00,
    "All Kid styles": 50.00,
    "Wash and curl": 35.00,
    "Deep Conditioning": 5.00,
    "Trim": 3.00,
}

WEAVE_HAIRSTYLES_PRICES = {
    "Weave Install with leave out": 135.00,
    "Quick Weave": 75.00,
    "Weave -Install w/ Closure": 175.00,
    "Custom made unit": 300.00
}

BRAIDS_AND_LOCS_PRICES = {
    "Knotless Braids": 170.00,
    "Cornrows": 60.00,
    "BohoLocs": 185.00,
    "Locs": 75.00,
    "Box Braids": 175.00,
    "Locs Retwist": 50.00,
    "Kid Styles": 50.00
}

HAIRCUT_STYLES_PRICES = {
    "Adult": 40.00,
    "HighTopFade": 35.00,
    "Design": 20.00,
    "Kids": 20.00,
    "Women": 35.00,
}

def calculate_total_price(selected_services):
    total_price = 0.00
    for service in selected_services:
        if service in REG_HAIRSTYLES_PRICES:
            total_price += REG_HAIRSTYLES_PRICES[service]
        elif service in WEAVE_HAIRSTYLES_PRICES:
            total_price += WEAVE_HAIRSTYLES_PRICES[service]
        elif service in BRAIDS_AND_LOCS_PRICES:
            total_price += BRAIDS_AND_LOCS_PRICES[service]
        elif service in HAIRCUT_STYLES_PRICES:
            total_price += HAIRCUT_STYLES_PRICES[service]
    return total_price
