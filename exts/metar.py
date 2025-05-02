from random import randint

import arc
import hikari
import requests
from utils.metar import translate_metar

metar_plugin = arc.GatewayPlugin("Metar")

@metar_plugin.include
@arc.slash_command("metar", "Fetch METAR for the given ICAO code", autodefer=True)
async def metar_cmd(
        ctx: arc.GatewayContext,
        icao: arc.Option[str, arc.StrParams("ICAO code of the airport", min_length=4, max_length=4)]
) -> None:
    await ctx.defer()
    url = "https://metar.vatsim.net/" + icao
    payload = {}
    headers = {
        'Accept': 'text/plain'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        if response.text == "":
            await ctx.respond(f"No METAR available for {icao.upper()}")
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
                        hikari.impl.SeparatorComponentBuilder(divider=True, spacing=hikari.SpacingType.SMALL, ),
                        hikari.impl.TextDisplayComponentBuilder(
                            content="-# METAR Source: VATSIM"
                        )
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

