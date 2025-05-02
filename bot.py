import os

import hikari
import arc
import logging
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = hikari.GatewayBot(
    token=TOKEN,
    allow_color=True
)

# Setup the arc client object
client: arc.GatewayClient = arc.GatewayClient(bot)

client.load_extensions_from("exts")

@client.add_startup_hook
async def startup_hook(client: arc.GatewayClient) -> None:
    logging.info("Bot is starting up")
    await client.app.update_presence(
        status=hikari.Status.ONLINE,
        activity=hikari.Activity(
            name=f"your reactions",
            type=hikari.ActivityType.WATCHING
        )
    )

@client.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.ADMINISTRATOR))
@arc.slash_command(
    name="load_extension",
    description="Load extensions to the bot. Admin Command.",
    default_permissions=hikari.Permissions.ADMINISTRATOR
)
async def load_ext_slash(
    ctx: arc.GatewayContext,
    extension: arc.Option[str,
        arc.StrParams(
            "Extension to load",
            choices={"Misc": "exts.misc", "Metar": "exts.metar"}
        )
    ]
) -> None:
    client.load_extension(extension)
    await ctx.respond(f"Loaded {extension}")


@client.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.ADMINISTRATOR))
@arc.slash_command(
    name="unload_extension",
    description="Unload extensions to the bot. Admin Command.",
    default_permissions=hikari.Permissions.ADMINISTRATOR
)
async def unload_ext_slash(
    ctx: arc.GatewayContext,
    extension: arc.Option[str,
    arc.StrParams(
        "Extension to unload",
        choices={"Misc": "exts.misc", "Metar": "exts.metar"}
    )]
) -> None:
    client.unload_extension(extension)
    await ctx.respond(f"Unloaded: {extension}")


@client.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.ADMINISTRATOR))
@arc.slash_command(
    "shutdown",
    "Turn the bot off. Admin command. If you can see this and are not an admin, ZeusAbhijeet screwed up",
    default_permissions=hikari.Permissions.ADMINISTRATOR
)
async def shutdown_slash(
    ctx: arc.GatewayContext
) -> None:
    await ctx.respond("Bot is shutting down")
    await bot.close()
