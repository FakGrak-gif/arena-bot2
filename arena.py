import discord
import re
import os
import time
from openai import OpenAI
from config import POLLINATIONS_KEY, AGENT_ID, ARENA_REWARDS
from database import update_role, get_balance

client = OpenAI(base_url="https://gen.pollinations.ai/v1", api_key=POLLINATIONS_KEY)

chat_histories = {}
user_choices = {}
arena_cooldowns = {} # Кулдаун арены
game_active = {}     # Флаг: идет ли игра

# --- ВЬЮШКИ ДЛЯ АРЕНЫ ---
class RaceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def pick_race(self, interaction: discord.Interaction, race_name: str):
        user_choices[interaction.user.id] = {"race": race_name, "class": None}
        await interaction.response.send_message(f"✅ Ты выбрал: **{race_name}**", ephemeral=True)
        await interaction.channel.send(f"{interaction.user.mention}, выбери класс:", view=ClassView())
    @discord.ui.button(label="Человек", style=discord.ButtonStyle.secondary)
    async def human(self, interaction: discord.Interaction, button: discord.ui.Button): await self.pick_race(interaction, "Человек")
    @discord.ui.button(label="Эльф", style=discord.ButtonStyle.secondary)
    async def elf(self, interaction: discord.Interaction, button: discord.ui.Button): await self.pick_race(interaction, "Эльф")
    @discord.ui.button(label="Орк", style=discord.ButtonStyle.secondary)
    async def orc(self, interaction: discord.Interaction, button: discord.ui.Button): await self.pick_race(interaction, "Орк")
    @discord.ui.button(label="Дворф", style=discord.ButtonStyle.secondary)
    async def dwarf(self, interaction: discord.Interaction, button: discord.ui.Button): await self.pick_race(interaction, "Дворф")
    @discord.ui.button(label="Вампир", style=discord.ButtonStyle.secondary)
    async def vampire(self, interaction: discord.Interaction, button: discord.ui.Button): await self.pick_race(interaction, "Вампир")

class ClassView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def pick_class(self, interaction: discord.Interaction, class_name: str):
        race = user_choices[interaction.user.id]["race"]
        await interaction.response.send_message(f"✅ Твой выбор: **{race} {class_name}**", ephemeral=True)
        text_to_ai = f"Я выбираю расу {race} и класс {class_name}"
        chat_histories[interaction.channel.id] = [{"role": "user", "content": text_to_ai}]
        game_active[interaction.user.id] = True
        await process_arena_action(interaction.channel, interaction.user, text_to_ai)
    @discord.ui.button(label="Воин", style=discord.ButtonStyle.primary)
    async def warrior(self, interaction: discord.Interaction, button: discord.ui.Button): await self.pick_class(interaction, "Воин")
    @discord.ui.button(label="Маг", style=discord.ButtonStyle.primary)
    async def mage(self, interaction: discord.Interaction, button: discord.ui.Button): await self.pick_class(interaction, "Маг")
    @discord.ui.button(label="Лучник", style=discord.ButtonStyle.primary)
    async def archer(self, interaction: discord.Interaction, button: discord.ui.Button): await self.pick_class(interaction, "Лучник")
    @discord.ui.button(label="Вор", style=discord.ButtonStyle.primary)
    async def rogue(self, interaction: discord.Interaction, button: discord.ui.Button): await self.pick_class(interaction, "Вор")

class SkillChoiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def use_skill(self, interaction: discord.Interaction, skill_text: str):
        await interaction.response.defer()
        await process_arena_action(interaction.channel, interaction.user, skill_text)
    @discord.ui.button(label="Классовый скилл", style=discord.ButtonStyle.success)
    async def class_skill(self, interaction: discord.Interaction, button: discord.ui.Button): await self.use_skill(interaction, "Использую свой классовый скилл")
    @discord.ui.button(label="Расовый скилл", style=discord.ButtonStyle.primary)
    async def race_skill(self, interaction: discord.Interaction, button: discord.ui.Button): await self.use_skill(interaction, "Использую свой расовый скилл")
    @discord.ui.button(label="Отмена", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button): await interaction.response.send_message("Отменено.", ephemeral=True)

class CombatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def send_action(self, interaction: discord.Interaction, action_text: str):
        await interaction.response.defer()
        await process_arena_action(interaction.channel, interaction.user, action_text)
    @discord.ui.button(label="Атака", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_action(interaction, "Атакую мечом")
    @discord.ui.button(label="Защита", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def defend(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_action(interaction, "Защищаюсь")
    @discord.ui.button(label="Уклонение", style=discord.ButtonStyle.secondary, emoji="💨")
    async def dodge(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_action(interaction, "Уклоняюсь")
    @discord.ui.button(label="Скилл", style=discord.ButtonStyle.success, emoji="✨")
    async def skill(self, interaction: discord.Interaction, button: discord.ui.Button): await interaction.response.send_message("Выбери скилл:", view=SkillChoiceView(), ephemeral=True)

class VictoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def send_action(self, interaction: discord.Interaction, action_text: str):
        await interaction.response.defer()
        await process_arena_action(interaction.channel, interaction.user, action_text)
    @discord.ui.button(label="Забрать монеты", style=discord.ButtonStyle.success, emoji="💰")
    async def take_money(self, interaction: discord.Interaction, button: discord.ui.Button): 
        game_active[interaction.user.id] = False # Игра окончена
        await self.send_action(interaction, "Уйти")
    @discord.ui.button(label="Идти дальше", style=discord.ButtonStyle.primary, emoji="🚪")
    async def continue_run(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_action(interaction, "Продолжить")

# --- КНОПКА ВЫХОДА ИЗ ОГЛУШЕНИЯ ---
class StunnedView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Выйти из оглушения", style=discord.ButtonStyle.secondary, emoji="💫")
    async def wake_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await process_arena_action(interaction.channel, interaction.user, "Я выхожу из оглушения")

# --- ЛОГИКА АРЕНЫ ---
async def process_arena_action(channel, user, user_text):
    if not game_active.get(user.id, False):
        await channel.send("❌ Твоя история окончена. Напиши `@Fbot старт`, чтобы начать заново.")
        return
        
    if channel.id not in chat_histories:
        chat_histories[channel.id] = []
    chat_histories[channel.id].append({"role": "user", "content": user_text})
    history_to_send = chat_histories[channel.id][-10:]

    async with channel.typing():
        try:
            response = client.chat.completions.create(
                model=AGENT_ID,
                messages=history_to_send,
                timeout=20.0
            )
            bot_reply = response.choices[0].message.content
            chat_histories[channel.id].append({"role": "assistant", "content": bot_reply})
            
            view_to_send = None
            
            # Проверка на оглушение игрока
            if "оглушен" in bot_reply.lower() or "пропускаешь ход" in bot_reply.lower():
                view_to_send = StunnedView()
            elif "Уйти" in bot_reply or "Продолжить" in bot_reply:
                view_to_send = VictoryView()
            elif "действия" in bot_reply.lower() or "[Противник]" in bot_reply:
                view_to_send = CombatView()
            
            if view_to_send:
                await channel.send(bot_reply, view=view_to_send)
            else:
                await channel.send(bot_reply)

            current_coins = get_balance(user, "💰")
            if "Толпа ликует" in bot_reply or "награду за уровень" in bot_reply:
                level_match = re.search(r'уровень\s*(\d+)', bot_reply.lower())
                level = int(level_match.group(1)) if level_match else 1
                reward = ARENA_REWARDS.get(level, 1)
                await update_role(user, "💰", current_coins + reward)
                await channel.send(f"💰 *Начислено {reward} монет!*")
                
                current_record = get_balance(user, "Арена")
                if level > current_record:
                    await update_role(user, "Арена", level)
                    await channel.send(f"🏆 *Новый рекорд Арены: {level} уровень!*")

            elif "Твоя история окончена" in bot_reply or "Ты пал" in bot_reply:
                game_active[user.id] = False # Игра окончена
                await update_role(user, "💰", current_coins // 2)
        except Exception as e:
            print(f"Ошибка ИИ: {e}")
