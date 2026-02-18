import discord
from discord.ext import commands
from datetime import datetime
import json
import os

from config import (
    INTENT_CHANNEL_NAME,
    INTENT_LOG_PATH
)


class IntentCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pending_intents = {}

        os.makedirs(os.path.dirname(INTENT_LOG_PATH), exist_ok=True)

    # ======================================================
    # LISTENER
    # ======================================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.name != INTENT_CHANNEL_NAME:
            return

        content = message.content.strip()
        lowered = content.lower()

        # Подтверждение
        if lowered in ["да", "нет"]:
            await self.handle_confirmation(message, lowered)
            return

        # Проверка обращения
        if not lowered.startswith("ника"):
            return

        await self.handle_intent(message)

    # ======================================================
    # PARSER
    # ======================================================
    def parse_intent(self, text: str):
        text = text.lower().replace("ника,", "").replace("ника", "").strip()

        result = {
            "action": None,
            "category": None,
            "channel": None,
            "new_name": None,
            "scope": None,
            "channel_name": None,
            "target_user": None
        }

        # HELP
        if any(word in text for word in ["help", "помощь", "что ты умеешь", "список команд"]):
            result["action"] = "help"
            return result

        # Создание категории
        if "создай категорию" in text:
            result["action"] = "create_category"
            result["category"] = text.split("создай категорию")[1].strip()

        # Создание голосового канала
        if "создай голосовой канал" in text:
            result["action"] = "create_voice"
            result["channel"] = text.split("создай голосовой канал")[1].strip()

        # Создание текстового канала
        if "создай текстовый канал" in text:
            result["action"] = "create_text"
            result["channel"] = text.split("создай текстовый канал")[1].strip()

        # Удаление канала
        if "удали канал" in text:
            result["action"] = "delete_channel"
            result["channel"] = text.split("удали канал")[1].strip()

        # Переименование
        if "переименуй канал" in text and " в " in text:
            result["action"] = "rename_channel"
            parts = text.split(" в ")
            result["channel"] = parts[0].replace("переименуй канал", "").strip()
            result["new_name"] = parts[1].strip()

        # Мьют
        if "выключи" in text and "микрофон" in text:
            result["action"] = "mute"

            if "мне" in text:
                result["scope"] = "self"

            elif "всем кроме меня" in text:
                result["scope"] = "all_except_me"

            elif "в канале" in text:
                result["scope"] = "channel"
                result["channel_name"] = text.split("в канале")[1].strip()

            elif "всем" in text:
                result["scope"] = "all"

        # Размьют
        if "включи микрофоны" in text:
            result["action"] = "unmute_all"

        # Модерация
        if "кикни" in text:
            result["action"] = "kick"
            result["target_user"] = text.split("кикни")[1].strip()

        if "забань" in text:
            result["action"] = "ban"
            result["target_user"] = text.split("забань")[1].strip()

        if "разбань" in text:
            result["action"] = "unban"
            result["target_user"] = text.split("разбань")[1].strip()

        # Информация
        if "покажи голосовые каналы" in text:
            result["action"] = "list_voice"

        if "покажи категории" in text:
            result["action"] = "list_categories"

        return result

    # ======================================================
    # HANDLE INTENT
    # ======================================================
    async def handle_intent(self, message: discord.Message):
        parsed = self.parse_intent(message.content)

        if parsed["action"] == "help":
            await self.send_help(message)
            return

        plan = []

        if parsed["action"] == "create_category":
            plan.append(f'Создать категорию "{parsed["category"]}"')

        if parsed["action"] == "create_voice":
            plan.append(f'Создать голосовой канал "{parsed["channel"]}"')

        if parsed["action"] == "create_text":
            plan.append(f'Создать текстовый канал "{parsed["channel"]}"')

        if parsed["action"] == "delete_channel":
            plan.append(f'Удалить канал "{parsed["channel"]}"')

        if parsed["action"] == "rename_channel":
            plan.append(f'Переименовать канал "{parsed["channel"]}" в "{parsed["new_name"]}"')

        if parsed["action"] == "mute":
            plan.append("Отключить микрофоны согласно запросу")

        if parsed["action"] == "unmute_all":
            plan.append("Включить микрофоны всем")

        if parsed["action"] in ["kick", "ban", "unban"]:
            plan.append(f'Применить модерацию к "{parsed["target_user"]}"')

        if parsed["action"] in ["list_voice", "list_categories"]:
            plan.append("Показать список каналов")

        if not plan:
            plan.append("Я не смогла определить действие")

        self.pending_intents[message.author.id] = {
            "timestamp": datetime.utcnow().isoformat(),
            "author": message.author.display_name,
            "author_id": message.author.id,
            "input": message.content,
            "parsed": parsed,
            "plan": plan
        }

        await message.channel.send(
            "🧠 **Я поняла, что нужно сделать:**\n"
            + "\n".join(f"• {step}" for step in plan)
            + "\n\nПодтверждаешь? (Да / Нет)"
        )

    # ======================================================
    # CONFIRMATION
    # ======================================================
    async def handle_confirmation(self, message: discord.Message, answer: str):
        user_id = message.author.id

        if user_id not in self.pending_intents:
            return

        intent = self.pending_intents.pop(user_id)
        parsed = intent["parsed"]

        if answer == "да":
            await self.execute_intent(message.guild, parsed, message)
            await message.channel.send("✅ Действие выполнено.")
        else:
            await message.channel.send("❌ Операция отменена.")

        self.write_log(intent, answer)

    # ======================================================
    # EXECUTION
    # ======================================================
    async def execute_intent(self, guild: discord.Guild, parsed: dict, message):

        if parsed["action"] == "create_category":
            await guild.create_category(parsed["category"])

        if parsed["action"] == "create_voice":
            await guild.create_voice_channel(parsed["channel"])

        if parsed["action"] == "create_text":
            await guild.create_text_channel(parsed["channel"])

        if parsed["action"] == "delete_channel":
            channel = discord.utils.get(guild.channels, name=parsed["channel"])
            if channel:
                await channel.delete()

        if parsed["action"] == "rename_channel":
            channel = discord.utils.get(guild.channels, name=parsed["channel"])
            if channel:
                await channel.edit(name=parsed["new_name"])

        if parsed["action"] == "mute":
            for member in guild.members:
                if member.voice:
                    await member.edit(mute=True)

        if parsed["action"] == "unmute_all":
            for member in guild.members:
                if member.voice:
                    await member.edit(mute=False)

        if parsed["action"] == "list_voice":
            channels = "\n".join([c.name for c in guild.voice_channels])
            await message.channel.send(f"🎤 Голосовые каналы:\n{channels}")

        if parsed["action"] == "list_categories":
            categories = "\n".join([c.name for c in guild.categories])
            await message.channel.send(f"📂 Категории:\n{categories}")

    # ======================================================
    # HELP
    # ======================================================
    async def send_help(self, message: discord.Message):

        help_text = """
📜 **Как общаться с N1ka**

Пиши: `Ника, команда`

🗂 Создать категорию  
• Ника, создай категорию Название  

🎤 Голосовые каналы  
• Ника, создай голосовой канал Название  
• Ника, покажи голосовые каналы  

💬 Текстовые каналы  
• Ника, создай текстовый канал Название  

🗑 Удаление  
• Ника, удали канал Название  

✏️ Переименование  
• Ника, переименуй канал Старое в Новое  

🎙 Голос  
• Ника, выключи мне микрофон  
• Ника, выключи всем микрофоны  
• Ника, включи микрофоны  

После команды я всегда спрашиваю подтверждение.
Ответ: **Да** или **Нет**
"""

        await message.channel.send(help_text)

    # ======================================================
    # LOG
    # ======================================================
    def write_log(self, intent: dict, answer: str):
        record = {
            "timestamp": intent["timestamp"],
            "author": intent["author"],
            "input": intent["input"],
            "plan": intent["plan"],
            "result": answer
        }

        with open(INTENT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")