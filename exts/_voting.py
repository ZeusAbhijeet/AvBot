import arc
import hikari

voting_plugin = arc.GatewayPlugin("Voting")


contest = voting_plugin.include_slash_group(
    "contest",
    "Manage a contest",
    default_permissions=hikari.Permissions.MANAGE_GUILD
)

@contest.include
@arc.slash_subcommand(
    "enter",
    "Submit your entry for the contest",
    autodefer=True
)
async def enter_contest_cmd(
        ctx: arc.GatewayContext,
        attachment: arc.Option[
            hikari.Attachment,
            arc.AttachmentParams("Submission image")
        ]
) -> None:
    async with attachment.stream() as stream:
        data = await stream.read()
        mimetype = stream.mimetype




"""
@contest.include
@arc.slash_subcommand(
    "start",
    "Start a contest",
    autodefer=True
)
async def start_contest_cmd(
        ctx: arc.GatewayContext,
        name: arc.Option[
            str,
            arc.StrParams["Name of the contest"]
        ],
        description: arc.Option[
            str,
            arc.StrParams["Description of the contest"]
        ],
        channel: arc.Option[
            hikari.GuildTextChannel,
            arc.ChannelParams["Channel where the voting will be held"]
        ]
) -> None:
    await ctx.defer()
"""


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    client.add_plugin(voting_plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    client.remove_plugin(voting_plugin)