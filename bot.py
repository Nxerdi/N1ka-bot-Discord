import discord
from cogs.events import Events
from discord.ext import commands
from config import (
    TOKEN,
    TG_LINK,
    ZAPRET_LINK,
    ROLE_NAMES,
    VOICE_ROLE_MAP,
    AFK_CHANNEL_NAME,
    DRUNK_ROLE_NAME
)

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.guilds = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)


@bot.event
async def on_ready():
    await bot.add_cog(Events(bot))

    await bot.change_presence(
        activity=discord.Game(name="🍻 в GameTavern")
    )

    await bot.tree.sync()
    print("🍻 N1ka готова к работе (events cog загружен)")


# ---------- COMMANDS ----------

@bot.tree.command(name="ping", description="Проверка пинга")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(
        f"🟢 **N1ka онлайн**\nЗадержка: `{latency} ms`",
        ephemeral=True
    )


@bot.tree.command(name="zapret", description="Zapret для Discord и YouTube")
async def zapret(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🚫 **Zapret**\n🔗 {ZAPRET_LINK}",
        ephemeral=True
    )


@bot.tree.command(name="tg", description="Telegram GameTavern")
async def tg(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"📣 **Telegram GameTavern**\n🔗 {TG_LINK}",
        ephemeral=True
    )

# ---------- ROLES ----------

class RoleButton(discord.ui.Button):
    def __init__(self, role_name: str):
        super().__init__(
            label=role_name,
            style=discord.ButtonStyle.secondary
        )
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        target_role = discord.utils.get(guild.roles, name=self.role_name)
        if not target_role:
            await interaction.response.send_message(
                f"❌ Роль `{self.role_name}` не найдена",
                ephemeral=True
            )
            return

        # Все тавернские роли
        tavern_roles = [
            role for role in guild.roles
            if role.name in ROLE_NAMES
        ]

        # Снимаем все другие тавернские роли
        roles_to_remove = [
            role for role in tavern_roles
            if role in member.roles and role != target_role
        ]

        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)

        # Если роль уже была — просто снимаем её
        if target_role in member.roles:
            await member.remove_roles(target_role)
            await interaction.response.send_message(
                f"➖ Роль `{self.role_name}` снята",
                ephemeral=True
            )
            return

        # Иначе выдаём выбранную
        await member.add_roles(target_role)
        await interaction.response.send_message(
            f"➕ Роль `{self.role_name}` выдана (предыдущая заменена)",
            ephemeral=True
        )


class TavernRoles(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        for role_name in ROLE_NAMES:
            self.add_item(RoleButton(role_name))


@bot.tree.command(name="roles", description="Роли таверны")
async def roles(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🍻 **Выбери своё место в таверне:**",
        view=TavernRoles(),
        ephemeral=True
    )

bot.run(TOKEN)