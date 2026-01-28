import discord
from discord.ext import commands
from config import ROLE_NAMES, VOICE_ROLE_MAP, AFK_CHANNEL_NAME, DRUNK_ROLE_NAME


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- УЧАСТНИК ЗАШЁЛ НА СЕРВЕР ----------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        role = discord.utils.get(
            member.guild.roles,
            name="🧙 Завсегдатай"
        )

        if role:
            try:
                await member.add_roles(role)
                print(f"🍻 {member.name} стал завсегдатаем")
            except Exception as e:
                print(f"Ошибка выдачи роли новичку: {e}")

    # ---------- ГОЛОСОВЫЕ СОБЫТИЯ ----------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild = member.guild

        tavern_roles = [
            role for role in guild.roles
            if role.name in ROLE_NAMES
        ]

        drunk_role = discord.utils.get(
            guild.roles,
            name=DRUNK_ROLE_NAME
        )

        # Вышел из голосового
        if before.channel and after.channel is None:
            if tavern_roles:
                await member.remove_roles(*tavern_roles)
            return

        # Перешёл в AFK (Уборная)
        if after.channel and after.channel.name == AFK_CHANNEL_NAME:
            if tavern_roles:
                await member.remove_roles(*tavern_roles)

            if drunk_role and drunk_role not in member.roles:
                await member.add_roles(drunk_role)

            return

        # Зашёл в обычный голос
        if after.channel:
            channel_name = after.channel.name

            # Снимаем "Напился"
            if drunk_role and drunk_role in member.roles:
                await member.remove_roles(drunk_role)

            if channel_name in VOICE_ROLE_MAP:
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
