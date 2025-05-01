from random import randint

import arc
import hikari
import requests
import re

metar_plugin = arc.GatewayPlugin("Metar")

@metar_plugin.include
@arc.slash_command("metar", "Fetch METAR for the given ICAO code", autodefer=True)
async def metar_cmd(
        ctx: arc.GatewayContext,
        icao: arc.Option[str, arc.StrParams("ICAO code of the airport", min_length=4, max_length=4)]
) -> None:
    url = "https://metar.vatsim.net/" + icao
    payload = {}
    headers = {
        'Accept': 'text/plain'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        if response.text == "":
            await ctx.respond(f"No METAR available for {icao}")
        else:
            metar = translate_metar(response.text)
            components = [
                hikari.impl.ContainerComponentBuilder(
                    accent_color=hikari.Color.from_int(randint(0, 0xffffff)),
                    components=[
                        hikari.impl.TextDisplayComponentBuilder(content=f"# METAR for {icao.upper()}"),
                        hikari.impl.SeparatorComponentBuilder(divider=True, spacing=hikari.SpacingType.SMALL, ),
                        hikari.impl.TextDisplayComponentBuilder(
                            content=f"```\n{response.text}\n```"),
                        hikari.impl.SeparatorComponentBuilder(divider=True, spacing=hikari.SpacingType.SMALL, ),
                        hikari.impl.TextDisplayComponentBuilder(content="## Translated"),
                        hikari.impl.TextDisplayComponentBuilder(
                            content=metar),
                    ]
                ),
            ]
            await ctx.respond(components=components)


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    client.add_plugin(metar_plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    client.remove_plugin(metar_plugin)

"""Various functions to decode METARs"""
def translate_metar(metar) -> str:
    """Translates a METAR report into plain language, separating current and TEMPO weather.

    Args:
        metar: A string containing the METAR report.

    Returns:
        A string containing the plain language translation.
    """

    translation = f"METAR for {get_station(metar)} at {get_time(metar)}: "

    # Extract main wind (before TEMPO)
    parts_before_tempo = metar.split("TEMPO")[0].split() if "TEMPO" in metar else metar.split()
    main_wind_metar = " ".join(parts_before_tempo)
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

    current_weather = get_current_weather(metar)
    if current_weather:
        translation += "Current weather: " + current_weather + ". "

    tempo_weather = get_tempo_weather(metar)
    if tempo_weather:
        translation += "Temporary conditions (TEMPO): " + tempo_weather + ". "

    return translation.rstrip(",. ") # Remove trailing comma, period, or space

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
                cloud_str += "clear"
            else:
                cloud_str += coverage
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

def get_current_weather(metar):
    """Extracts the current significant weather phenomena before forecast indicators (with intensity)."""
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

    parts = metar.split()
    weather_str = ""
    seen_phenomena = set()
    forecast_indicators = ["TEMPO", "BECMG", "RMK"]
    end_of_current_weather = -1

    for i, part in enumerate(parts):
        if part in forecast_indicators:
            end_of_current_weather = i
            break

    current_weather_parts = parts[:end_of_current_weather] if end_of_current_weather != -1 else parts

    for part in current_weather_parts:
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

def get_tempo_weather(metar):
    """Extracts the significant weather phenomena and wind within the TEMPO section (with intensity)."""
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

    parts = metar.split()
    tempo_weather_str = ""
    seen_phenomena = set()
    tempo_start_index = -1

    for i, part in enumerate(parts):
        if part == "TEMPO":
            tempo_start_index = i
            break

    if tempo_start_index != -1:
        tempo_parts = parts[tempo_start_index + 1:]
        tempo_wind = get_wind(" ".join(tempo_parts)) # Extract wind from TEMPO section
        if tempo_wind:
            tempo_weather_str += tempo_wind + ", "

        for part in tempo_parts:
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
                    tempo_weather_str += description + ", "
                    seen_phenomena.add(phenomenon)

    return tempo_weather_str.rstrip(", ") if tempo_weather_str else None
