import discord
from discord.ext import commands

from config import (
    ROLE_NAMES,
    VOICE_ROLE_MAP,
    AFK_CHANNEL_NAME,
    DRUNK_ROLE_NAME,
    LOG_CHANNEL_NAME,
    ENABLE_LOGGING
)


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ======================================================
    # ЛОГИРОВАНИЕ (тихо, централизованно)
    # ======================================================
    async def log(self, guild: discord.Guild, message: str):
        if not ENABLE_LOGGING:
            return

        channel = discord.utils.get(
            guild.text_channels,
            name=LOG_CHANNEL_NAME
        )

        if channel:
            await channel.send(message)

    # ======================================================
    # УЧАСТНИК ЗАШЁЛ НА СЕРВЕР
    # ======================================================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        role = discord.utils.get(
            member.guild.roles,
            name="🧙 Завсегдатай"
        )

        if not role:
            return

        try:
            await member.add_roles(role)
            await self.log(
                member.guild,
                f"👤 **{member.display_name}** зашёл на сервер → 🧙 Завсегдатай"
            )
            print(f"🍻 {member.name} стал завсегдатаем")
        except Exception as e:
            print(f"Ошибка выдачи роли новичку: {e}")

    # ======================================================
    # ГОЛОСОВЫЕ СОБЫТИЯ
    # ======================================================
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        guild = member.guild

        tavern_roles = [
            role for role in guild.roles
            if role.name in ROLE_NAMES
        ]

        drunk_role = discord.utils.get(
            guild.roles,
            name=DRUNK_ROLE_NAME
        )

        # --------------------------
        # ВЫХОД ИЗ ГОЛОСОВОГО
        # --------------------------
        if before.channel and after.channel is None:
            if tavern_roles:
                await member.remove_roles(*tavern_roles)

            await self.log(
                guild,
                f"🚪 **{member.display_name}** вышел из голосового"
            )
            return

        # --------------------------
        # ПЕРЕХОД В AFK (УБОРНАЯ)
        # --------------------------
        if after.channel and after.channel.name == AFK_CHANNEL_NAME:
            if tavern_roles:
                await member.remove_roles(*tavern_roles)

            if drunk_role and drunk_role not in member.roles:
                await member.add_roles(drunk_role)

                await self.log(
                    guild,
                    f"🚽 **{member.display_name}** ушёл в уборную → 🤪 Напился"
                )
            return

        # --------------------------
        # ОБЫЧНЫЙ ГОЛОСОВОЙ КАНАЛ
        # --------------------------
        if after.channel:
            channel_name = after.channel.name

            # снимаем "Напился"
            if drunk_role and drunk_role in member.roles:
                await member.remove_roles(drunk_role)

            if channel_name not in VOICE_ROLE_MAP:
                return

            target_role_name = VOICE_ROLE_MAP[channel_name]
            target_role = discord.utils.get(
                guild.roles,
                name=target_role_name
            )

            if not target_role:
                return

            roles_to_remove = [
                role for role in tavern_roles
                if role != target_role and role in member.roles
            ]

            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)

            if target_role not in member.roles:
                await member.add_roles(target_role)

                await self.log(
                    guild,
                    f"🎧 **{member.display_name}** сел в **{after.channel.name}** → `{target_role.name}`"
                )