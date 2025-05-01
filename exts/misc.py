import arc
import hikari
from time import time
from random import randint

misc_plugin = arc.GatewayPlugin("Misc")

@misc_plugin.include
@arc.slash_command("ping", "Shows the latency of the bot")
async def ping_cmd(
        ctx: arc.GatewayContext
) -> None:
    start = time()
    msg = await ctx.respond("Pong!")
    end = time()

    await msg.edit(
        "",
        embed=hikari.Embed(
            title="Ping!",
            description=f"**Latency:** {(end - start) * 1000:,.0f} ms",
            colour=randint(0, 0xffffff)
        )
    )

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    client.add_plugin(misc_plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    client.remove_plugin(misc_plugin)
