from datetime import datetime


def parse_date(date_string):
    """Parse date string in YYYY-MM-DD format"""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got: {date_string}")


def validate_parameters(data):
    """Validate request parameters"""
    required_fields = ['scan_date', 'harvest_date', 'growth_rate', 'min_diameter', 'max_diameter']

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required parameter: {field}")

    # Parse and validate dates
    scan_date = parse_date(data['scan_date'])
    harvest_date = parse_date(data['harvest_date'])

    if harvest_date <= scan_date:
        raise ValueError("Harvest date must be after scan date")

    # Validate numeric parameters
    try:
        growth_rate = float(data['growth_rate'])
        min_diameter = float(data['min_diameter'])
        max_diameter = float(data['max_diameter'])
    except (ValueError, TypeError):
        raise ValueError("growth_rate, min_diameter, and max_diameter must be valid numbers")

    if growth_rate < 0:
        raise ValueError("Growth rate must be non-negative")

    if min_diameter < 0 or max_diameter < 0:
        raise ValueError("Diameter values must be non-negative")

    if min_diameter >= max_diameter:
        raise ValueError("Minimum diameter must be less than maximum diameter")

    return scan_date, harvest_date, growth_rate, min_diameter, max_diameter