REGION_MAP = {
    "청주": {
        "airkorea_station": "복대동",
        "nx": 69,
        "ny": 106,
    },
    "서울": {
        "airkorea_station": "중구",
        "nx": 60,
        "ny": 127,
    },
}


def get_region_info(region_name: str) -> dict:
    if region_name not in REGION_MAP:
        raise ValueError(f"지원하지 않는 지역입니다: {region_name}")

    return REGION_MAP[region_name]


def get_available_regions():
    return list(REGION_MAP.keys())