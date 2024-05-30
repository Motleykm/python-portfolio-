def price_calculator(selected_services):
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
