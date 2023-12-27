"""Constants for the InWarmte integration."""
DATA_COORDINATOR = "coordinator"

DOMAIN = "inwarmte"

"""Interval in seconds between polls to inwarmte."""
POLLING_INTERVAL = 1800

"""Timeout for fetching sensor data"""
FETCH_TIMEOUT = 10

SENSOR_TYPE_THIS_MONTH = "this_month"
SENSOR_TYPE_THIS_YEAR = "this_year"

SOURCE_TYPES = [
    "hot",
    "hot_tap",
    "electra",
    "cold",
]

SOURCE_TYPE_HOT = "hot"
SOURCE_TYPE_HOT_TAP = "hot_tap"
SOURCE_TYPE_ELECTRA = "electra"
SOURCE_TYPE_COLD = "cold"