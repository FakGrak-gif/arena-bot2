import discord
from openai import OpenAI
import random
import time
import re
import os

# --- ВСТАВЬ СВОИ ДАННЫЕ СЮДА ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
POLLINATIONS_KEY = "sk_Hm0rVyHlZktpjZ6FDrHFq2K0XBGCdOh5"
AGENT_ID = "community/FakGrak-gif/arena-bot" 

# --- НИЖЕ НИЧЕГО МЕНЯТЬ НЕ НУЖНО ---

# --- ID КАНАЛОВ ---
CHANNEL_ID_1 = 1563607580406710473 # Обычное казино
CHANNEL_ID_2 = 1564183939495624764 # VIP казино
ARENA_CHANNEL_ID = 1564187640805458002 # Канал для Арены
WORK_CHANNEL_ID = 1564224730217582623 # Канал для работы

client = OpenAI(
    base_url="https://gen.pollinations.ai/v1",
    api_key=POLLINATIONS_KEY,
)

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True 
bot = discord.Client(intents=intents)

chat_histories = {}
last_win_state = {}
arena_cooldowns = {}
user_choices = {}
work_cooldowns = {}

casino_jackpot = 0 

SHOP_ITEMS = {
    "1": ("Кейс в кс2", 50, "🛒 Куплено: Кейс КС2"),
    "2": ("Сменить цвет ника", 60, "🛒 Куплено: Цвет ника"),
    "3": ("Похвала от админа", 70, "🛒 Куплено: Похвала"),
    "4": ("Скин в кс2 (дешевый)", 120, "🛒 Куплено: Скин КС2"),
    "5": ("Своя роль", 200, "🛒 Куплено: Кастомная роль"),
    "6": ("Право отправлять сообщение с озвучкой", 250, "🛒 Куплено: Озвучка"),
    "7": ("Скин в кс2 (дорогой)", 400, "🛒 Куплено: Дорогой скин"),
    "8": ("Личный канал", 500, "🛒 Куплено: Личный канал"),
    "9": ("Право перемещать участников", 600, "🛒 Куплено: Мув"),
    "10": ("Право глушить людей", 800, "🛒 Куплено: Мут"),
    "11": ("Право кикать людей", 1200, "🛒 Куплено: Кик"),
    "12": ("Судья", 2000, "🛒 Куплено: Судья"),
    "13": ("Роль админа", 4000, "🛒 Куплено: Админ"),
}

ARENA_REWARDS = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7, 10: 9}

async def update_role(member, role_prefix, amount):
    amount = int(round(amount))
    guild = member.guild
    role_name = f"{role_prefix} {amount}"
    
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        color = discord.Color.red() if amount < 0 else (discord.Color.gold() if role_prefix == "💰" else discord.Color.green())
        role = await guild.create_role(name=role_name, color=color)
    
    for old_role in member.roles:
        if old_role.name.startswith(f"{role_prefix} "):
            await member.remove_roles(old_role)
            
    await member.add_roles(role)

def get_balance(member, role_prefix):
    for role in member.roles:
        if role.name.startswith(f"{role_prefix} "):
            try:
                return int(role.name.split(" ")[1].strip())
            except:
                pass
    return 0

class ExchangeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def exchange(self, interaction: discord.Interaction, amount: int):
        current_dollars = get_balance(interaction.user, "💵")
        if current_dollars < amount:
            await interaction.response.send_message(f"❌ Недостаточно долларов!", ephemeral=True)
            return
        coins_to_add = amount // 1000
        current_coins = get_balance(interaction.user, "💰")
        await update_role(interaction.user, "💵", current_dollars - amount)
        await update_role(interaction.user, "💰", current_coins + coins_to_add)
        await interaction.response.send_message(f"✅ Обменяно **{amount}$** на **{coins_to_add} монет**!", ephemeral=True)
    @discord.ui.button(label="1000$", style=discord.ButtonStyle.primary)
    async def btn_1000(self, interaction: discord.Interaction, button: discord.ui.Button): await self.exchange(interaction, 1000)
    @discord.ui.button(label="2000$", style=discord.ButtonStyle.success)
    async def btn_2000(self, interaction: discord.Interaction, button: discord.ui.Button): await self.exchange(interaction, 2000)
    @discord.ui.button(label="5000$", style=discord.ButtonStyle.success)
    async def btn_5000(self, interaction: discord.Interaction, button: discord.ui.Button): await self.exchange(interaction, 5000)
    @discord.ui.button(label="10000$", style=discord.ButtonStyle.danger)
    async def btn_10000(self, interaction: discord.Interaction, button: discord.ui.Button): await self.exchange(interaction, 10000)

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
    async def take_money(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_action(interaction, "Уйти")
    @discord.ui.button(label="Идти дальше", style=discord.ButtonStyle.primary, emoji="🚪")
    async def continue_run(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_action(interaction, "Продолжить")

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Кейс (50)", style=discord.ButtonStyle.primary, emoji="📦")
    async def buy_case(self, interaction: discord.Interaction, button: discord.ui.Button): await process_purchase(interaction, "1")
    @discord.ui.button(label="Цвет (60)", style=discord.ButtonStyle.secondary, emoji="🎨")
    async def buy_color(self, interaction: discord.Interaction, button: discord.ui.Button): await process_purchase(interaction, "2")
    @discord.ui.button(label="Скин (120)", style=discord.ButtonStyle.success, emoji="🔫")
    async def buy_skin(self, interaction: discord.Interaction, button: discord.ui.Button): await process_purchase(interaction, "4")
    @discord.ui.button(label="Роль (200)", style=discord.ButtonStyle.danger, emoji="👑")
    async def buy_role(self, interaction: discord.Interaction, button: discord.ui.Button): await process_purchase(interaction, "5")

async def process_purchase(interaction: discord.Interaction, item_id: str):
    item_name, price, role_name = SHOP_ITEMS[item_id]
    current_coins = get_balance(interaction.user, "💰")
    if current_coins < price:
        await interaction.response.send_message(f"❌ Нужно {price}, у вас {current_coins}.", ephemeral=True)
        return
    new_coins = current_coins - price
    await update_role(interaction.user, "💰", new_coins)
    role = discord.utils.get(interaction.guild.roles, name=role_name)
    if role is None:
        role = await interaction.guild.create_role(name=role_name, color=discord.Color.blue())
    await interaction.user.add_roles(role)
    await interaction.response.send_message(f"✅ Куплено **{item_name}**! (Баланс: {new_coins})", ephemeral=True)

async def process_arena_action(channel, user, user_text):
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
            if "Уйти" in bot_reply or "Продолжить" in bot_reply:
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
                
                # --- СОХРАНЕНИЕ РЕКОРДА АРЕНЫ ---
                current_record = get_balance(user, "🏆 Арена")
                if level > current_record:
                    await update_role(user, "🏆 Арена", level)
                    await channel.send(f"🏆 *Новый рекорд Арены: {level} уровень!*")

            elif "Твоя история окончена" in bot_reply:
                await update_role(user, "💰", current_coins // 2)
        except Exception as e:
            print(f"Ошибка: {e}")

@bot.event
async def on_message(message):
    global casino_jackpot
    if message.author == bot.user:
        return

    clean_text = message.content.replace(f'<@{bot.user.id}>', '').strip()
    clean_lower = clean_text.lower()

    if clean_lower == "!магазин":
        shop_text = "🛒 **Магазин**\n"
        for key, item in SHOP_ITEMS.items():
            shop_text += f"**{key}.** {item[0]} — `{item[1]}` монет\n"
        await message.reply(shop_text, view=ShopView())
        return

    if clean_lower in ["!обмен", "!обменять"]:
        dollars = get_balance(message.author, "💵")
        await message.reply(f"💱 Баланс: {dollars}$\nКурс: 1000$ = 1 монета", view=ExchangeView())
        return

    if message.channel.id == WORK_CHANNEL_ID and clean_text == "!":
        if time.time() - work_cooldowns.get(message.author.id, 0) < 3600:
            await message.reply("❌ Отдохни еще час.")
            return
        earnings = random.randint(50, 400)
        current_dollars = get_balance(message.author, "💵")
        await update_role(message.author, "💵", current_dollars + earnings)
        work_cooldowns[message.author.id] = time.time()
        await message.reply(f"💼 Вы заработали **{earnings}$**!")
        return

    # --- КАЗИНО ---
    if clean_text.startswith("!") and message.channel.id in [CHANNEL_ID_1, CHANNEL_ID_2]:
        if re.match(r'^!(?:\s*)(\d+)?$', clean_lower):
            bet = int(clean_lower.replace("!", "").strip() or 1)
            current_coins = get_balance(message.author, "💰")
            if current_coins < bet:
                await message.reply("❌ Недостаточно монет.")
                return
            await update_role(message.author, "💰", current_coins - bet)
            
            roll = random.randint(1, 200)
            if roll == 1:
                casino_jackpot += 20
                await update_role(message.author, "💰", current_coins + bet + casino_jackpot)
                await message.reply(f"🏆 **ДЖЕКПОТ!** Вы забрали {casino_jackpot} монет!")
                casino_jackpot = 0
            elif roll <= 90:
                await update_role(message.author, "💰", current_coins + bet + 2)
                await message.reply(f"🎉 Вы выиграли +2 монеты! (Джекпот: {casino_jackpot})")
            else:
                casino_jackpot += 1
                await message.reply(f"🎲 Вы проиграли. (Джекпот: {casino_jackpot})")
            return

    # --- ЕДИНЫЙ ТОП ---
    if clean_lower == "!топ":
        top_text = "🏆 **ТАБЛИЦА ЛИДЕРОВ** 🏆\n\n"
        
        # Топ по деньгам
        players_money = []
        players_arena = []
        for m in message.guild.members:
            if not m.bot:
                coins = get_balance(m, "💰")
                if coins > 0: 
                    players_money.append((m.display_name, coins))
                
                arena_lvl = get_balance(m, "🏆 Арена")
                if arena_lvl > 0:
                    players_arena.append((m.display_name, arena_lvl))
                    
        players_money.sort(key=lambda x: x[1], reverse=True)
        players_arena.sort(key=lambda x: x[1], reverse=True)
        
        top_text += "💰 **Самые богатые:**\n"
        if players_money:
            for i, p in enumerate(players_money[:5], 1): # Топ-5, чтобы не растягивать
                top_text += f"{i}. **{p[0]}** — {p[1]} монет\n"
        else:
            top_text += "*Пока ни у кого нет монет.*\n"
            
        top_text += "\n⚔️ **Лучшие бойцы Арены:**\n"
        if players_arena:
            for i, p in enumerate(players_arena[:5], 1):
                top_text += f"{i}. **{p[0]}** — {p[1]} уровень\n"
        else:
            top_text += "*Пока никто не проходил Арену.*\n"
            
        await message.reply(top_text)
        return

    if message.channel.id == ARENA_CHANNEL_ID and (bot.user.mentioned_in(message) or any(w in clean_lower for w in ["сброс", "старт", "начать"])):
        if any(w in clean_lower for w in ["сброс", "старт", "начать"]):
            await message.reply("Начинаем! Выбери расу:", view=RaceView())
        else:
            await process_arena_action(message.channel, message.author, clean_text)

bot.run(DISCORD_TOKEN)
