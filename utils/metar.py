import re

weather_codes = {
    "TS": "Thunderstorm",
    "RA": "Rain",
    "SN": "Snow",
    "DZ": "Drizzle",
    "FG": "Fog",
    "BR": "Mist",
    "HZ": "Haze",
    "SH": "Showers",
    "VC": "Vicinity",
    "MI": "Shallow",
    "BC": "Patches",
    "DR": "Low Drifting",
    "BL": "Blowing",
    "FZ": "Freezing",
    "PR": "Partial",
    "TSRA": "Thunderstorm with Rain",
    "TSSN": "Thunderstorm with Snow",
    "TSPL": "Thunderstorm with Ice Pellets",
    "TSGR": "Thunderstorm with Hail",
    "TSSG": "Thunderstorm with Snow Grains",
    "IC": "Ice Crystals (diamond dust)",
    "PL": "Ice Pellets",
    "GR": "Hail",
    "GS": "Small Hail or Snow Pellets",
    "UP": "Unknown Precipitation",
    "FU": "Smoke",
    "DU": "Dust",
    "SA": "Sand",
    "PY": "Spray",
    "VA": "Volcanic Ash",
    "PO": "Dust/sand whirls",
    "SQ": "Squalls",
    "FC": "Funnel Cloud",
    "+FC": "Tornado or Waterspout",
    "SS": "Sandstorm",
    "DS": "Duststorm",
    "+": "Heavy",
    "-": "Light",
}

cloud_codes = {
    "FEW": "Few",
    "SCT": "Scattered",
    "BKN": "Broken",
    "OVC": "Overcast"
}

"""Various functions to decode METARs"""
def translate_metar(metar):
    """Translates a METAR report into plain language, separating current, BECMG, and TEMPO weather.

    Args:
        metar: A string containing the METAR report.

    Returns:
        A string containing the plain language translation.
    """

    translation = f"METAR for {get_station(metar)} at {get_time(metar)} UTC: "

    # Extract main wind (before BECMG or TEMPO)
    parts_before_forecast = []
    if "BECMG" in metar:
        parts_before_forecast = metar.split("BECMG")[0].split()
    elif "TEMPO" in metar:
        parts_before_forecast = metar.split("TEMPO")[0].split()
    else:
        parts_before_forecast = metar.split()

    main_wind_metar = " ".join(parts_before_forecast)
    wind = get_wind(main_wind_metar)
    if wind:
        translation += wind + ", "

    visibility = get_visibility(metar)
    if visibility:
        translation += visibility + ", "

    clouds = get_clouds(metar)
    if clouds:
        translation += clouds + ", "

    temperature_dewpoint = get_temperature_dewpoint(metar)
    if temperature_dewpoint:
        translation += temperature_dewpoint + ", "

    pressure = get_pressure(metar)
    if pressure:
        translation += pressure + ". "

    current_weather = _get_current_weather(metar)
    if current_weather:
        translation += "Current weather: " + current_weather + ". "

    becoming_conditions = _get_forecast_conditions(metar, "BECMG")
    if becoming_conditions and becoming_conditions["weather"]:
        translation += "Becoming (BECMG): "
        if becoming_conditions["wind"]:
            translation += "Wind " + becoming_conditions["wind"] + ", "
        if becoming_conditions["visibility"]:
            translation += becoming_conditions["visibility"] + ", "
        if becoming_conditions["clouds"]:
            translation += becoming_conditions["clouds"] + ", "
        translation += becoming_conditions["weather"] + ". "

    tempo_conditions = _get_forecast_conditions(metar, "TEMPO")
    if tempo_conditions and tempo_conditions["weather"]:
        translation += "Temporary conditions (TEMPO): "
        if tempo_conditions["wind"]:
            translation += "Wind " + tempo_conditions["wind"] + ", "
        if tempo_conditions["visibility"]:
            translation += tempo_conditions["visibility"] + ", "
        if tempo_conditions["clouds"]:
            translation += tempo_conditions["clouds"] + ", "
        translation += tempo_conditions["weather"] + ". "

    return translation.rstrip(",. ")


def get_station(metar):
    """Extracts the station identifier."""
    match = re.match(r"([A-Z]{4})", metar)
    return match.group(1) if match else "Unknown Station"

def get_time(metar):
    """Extracts the observation time."""
    match = re.search(r"(\d{6}Z)", metar)
    if match:
        day = match.group(1)[:2]
        hour = match.group(1)[2:4]
        minute = match.group(1)[4:6]
        return f"{hour}:{minute} UTC on the {day}th"
    return "Unknown Time"

def get_wind(metar):
    """Extracts and translates wind information, including no wind and variable wind."""
    match_no_wind = re.search(r"00000KT", metar)
    if match_no_wind:
        return "Wind calm"

    match_variable = re.search(r"(\d{3})(\d{2,3})KT (\d{3})V(\d{3})", metar)
    if match_variable:
        direction = int(match_variable.group(1))
        speed = int(match_variable.group(2))
        from_dir = int(match_variable.group(3))
        to_dir = int(match_variable.group(4))
        return f"Wind variable between {from_dir} and {to_dir} degrees at {speed} knots"

    match_gust = re.search(r"(\d{3})(\d{2,3})G(\d{2,3})KT", metar)
    if match_gust:
        direction = int(match_gust.group(1))
        speed = int(match_gust.group(2))
        gust = int(match_gust.group(3))
        return f"Wind from {direction} degrees at {speed} knots, gusting to {gust} knots"

    match_steady = re.search(r"(\d{3})(\d{2,3})KT", metar)
    if match_steady:
        direction = int(match_steady.group(1))
        speed = int(match_steady.group(2))
        return f"Wind from {direction} degrees at {speed} knots"

    match_variable_light = re.search(r"VRB(\d{2})KT", metar)
    if match_variable_light:
        speed = int(match_variable_light.group(1))
        return f"Wind variable at {speed} knots"

    return None

def get_visibility(metar):
    """Extracts and translates visibility, handling meter/kilometer pronunciation."""
    match_meters = re.search(r"(\d{4})\b", metar)  # Four digits, word boundary
    if match_meters:
        visibility_meters = int(match_meters.group(1))
        if visibility_meters <= 5000:
            return f"Visibility {visibility_meters} meters"
        elif visibility_meters == 9999:
            return "Visibility greater than 10 kilometers"
        else:
            return f"Visibility {visibility_meters // 1000} kilometers"
    match_sm = re.search(r"(\d+)(SM)", metar)
    if match_sm:
        return f"Visibility {match_sm.group(1)} statute miles"
    match_fraction = re.search(r"(\d)/(\d)SM", metar)
    if match_fraction:
        return f"Visibility {match_fraction.group(1)}/{match_fraction.group(2)} statute miles"
    return None

def get_clouds(metar):
    """Extracts and translates cloud information."""
    if "NSC" in metar:
        return "No significant cloud"
    cloud_matches = re.findall(r"(CLR|FEW|SCT|BKN|OVC)(\d{3})?", metar)
    if cloud_matches:
        cloud_str = "Clouds: "
        for cloud in cloud_matches:
            coverage = cloud[0]
            altitude = cloud[1]
            if coverage == "CLR":
                cloud_str += "Clear"
            else:
                if coverage in cloud_codes:
                    cloud_str += cloud_codes[coverage]
                if altitude:
                    cloud_str += f" at {int(altitude) * 100} feet"
            cloud_str += ", "
        return cloud_str.rstrip(", ")
    return None

def get_temperature_dewpoint(metar):
    """Extracts and translates temperature and dewpoint."""
    match = re.search(r"(M?\d{2})/(M?\d{2})", metar)
    if match:
        temp = int(match.group(1).replace("M", "-"))
        dewpoint = int(match.group(2).replace("M", "-"))
        return f"Temperature {temp}°C, dewpoint {dewpoint}°C"
    return None

def get_pressure(metar):
    """Extracts and translates atmospheric pressure (QNH)."""
    match_q = re.search(r"Q(\d{4})", metar)
    if match_q:
        pressure = int(match_q.group(1))
        return f"Altimeter setting {pressure} hPa"
    match_a = re.search(r"A(\d{4})", metar)
    if match_a:
        pressure_inhg = int(match_a.group(1)) / 100.0
        return f"Altimeter setting {pressure_inhg:.2f} inHg"
    return None

def _extract_weather_elements(parts):
    """Helper function to extract weather phenomena from a list of METAR parts."""
    weather_str = ""
    seen_phenomena = set()
    for part in parts:
        match = re.search(r"([-+]?)(VC)?(MI|BC|DR|BL|SH|TS|FZ|PR)?(?:(TSRA|TSSN|TSPL|TSGR|TSSG|RA|SN|DZ|FG|BR|HZ|SH|IC|PL|GR|GS|UP|FU|DU|SA|PY|VA|PO|SQ|FC|\+FC|SS|DS)|(TS|RA|SN|DZ|FG|BR|HZ|SH|IC|PL|GR|GS|UP|FU|DU|SA|PY|VA|PO|SQ|FC|\+FC|SS|DS))\b", part)
        if match:
            intensity = match.group(1) or ""
            vicinity = match.group(2) or ""
            descriptor = match.group(3) or ""
            phenomenon = match.group(4) or match.group(5)
            description = ""
            if intensity == "+":
                description += "Heavy "
            elif intensity == "-":
                description += "Light "
            if vicinity == "VC":
                description += "Vicinity "
            if descriptor == "MI":
                description += "Shallow "
            elif descriptor == "BC":
                description += "Patches of "
            elif descriptor == "DR":
                description += "Low Drifting "
            elif descriptor == "BL":
                description += "Blowing "
            elif descriptor == "SH":
                description += "Showers "
            elif descriptor == "TS":
                description += "Thunderstorm "
            elif descriptor == "FZ":
                description += "Freezing "
            elif descriptor == "PR":
                description += "Partial "
            if phenomenon in weather_codes and phenomenon not in seen_phenomena:
                description += weather_codes[phenomenon]
                weather_str += description + ", "
                seen_phenomena.add(phenomenon)
    return weather_str.rstrip(", ") if weather_str else None

def _get_current_weather(metar):
    """Extracts the current significant weather phenomena before forecast indicators."""
    parts = metar.split()
    forecast_indicators = ["TEMPO", "BECMG", "RMK"]
    end_of_current_weather = -1
    for i, part in enumerate(parts):
        if part in forecast_indicators:
            end_of_current_weather = i
            break
    current_weather_parts = parts[:end_of_current_weather] if end_of_current_weather != -1 else parts
    return _extract_weather_elements(current_weather_parts)

def _get_forecast_conditions(metar, indicator):
    """Extracts the significant weather phenomena and other conditions within a forecast section."""
    parts = metar.split()
    start_index = -1
    conditions = {"wind": None, "visibility": None, "clouds": None, "weather": None}

    for i, part in enumerate(parts):
        if part == indicator:
            start_index = i
            break

    if start_index != -1:
        forecast_parts = parts[start_index + 1:]
        conditions["wind"] = get_wind(" ".join(forecast_parts))
        conditions["visibility"] = get_visibility(" ".join(forecast_parts))
        conditions["clouds"] = get_clouds(" ".join(forecast_parts))

        weather_relevant_parts = []
        stop_indicators = ["BECMG", "RMK"] if indicator == "TEMPO" else ["TEMPO", "RMK"]
        for part in forecast_parts:
            if part in stop_indicators:
                break
            weather_relevant_parts.append(part)
        conditions["weather"] = _extract_weather_elements(weather_relevant_parts)

    return conditions
