import discord
from openai import OpenAI
import random
import time
import re
import os

# --- ВСТАВЬ СВОИ ДАННЫЕ СЮДА ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
POLLINATIONS_KEY = os.getenv("POLLINATIONS_KEY")
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

ENEMY_IMAGES = {
    "Гоблин": "goblin.png", "Крыса": "rat.png", "Висп": "wisp.png",
    "Скелет": "skeleton.png", "Лютоволк": "wolf.png", "Гадюка": "snake.png",
    "Огр": "ogre.png", "Вор": "thief.png", "Гарпия": "harpy.png",
    "Голем": "golem.png", "Рыцарь": "knight.png", "Грифон": "griffin.png",
    "Тролль": "troll.png", "Ведьма": "witch.png", "Минотавр": "minotaur.png",
    "Змея": "big_snake.png", "Суккуб": "succubus.png", "Маг": "ogre_mage.png",
    "Элементаль": "ice_elemental.png", "Виверна": "wyvern.png", "Жрец": "dark_priest.png",
    "Демон": "demon.png", "Дракон": "dragon.png", "Бездна": "abyss_lord.png",
    "Архимаг": "archmage.png"
}

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
            await interaction.response.send_message(f"❌ У вас недостаточно долларов! Нужно {amount}$, у вас {current_dollars}$.", ephemeral=True)
            return
            
        coins_to_add = amount // 1000
        current_coins = get_balance(interaction.user, "💰")
        
        await update_role(interaction.user, "💵", current_dollars - amount)
        await update_role(interaction.user, "💰", current_coins + coins_to_add)
        
        await interaction.response.send_message(f"✅ Вы успешно обменяли **{amount}$** на **{coins_to_add} монет**!\n*(Новый баланс: {current_dollars - amount}$ и {current_coins + coins_to_add} монет)*", ephemeral=True)

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
        await interaction.response.send_message(f"✅ Ты выбрал расу: **{race_name}**. Теперь выбери класс!", ephemeral=True)
        await interaction.channel.send(f"{interaction.user.mention}, выбери свой класс:", view=ClassView())
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
        if interaction.user.id not in user_choices or user_choices[interaction.user.id].get("race") is None:
            await interaction.response.send_message("❌ Сначала выбери расу!", ephemeral=True)
            return
        user_choices[interaction.user.id]["class"] = class_name
        race = user_choices[interaction.user.id]["race"]
        await interaction.response.send_message(f"✅ Твой выбор: **{race} {class_name}**. Арена ждет!", ephemeral=True)
        channel = interaction.channel
        text_to_ai = f"Я выбираю расу {race} и класс {class_name}"
        chat_histories[channel.id] = [{"role": "user", "content": text_to_ai}]
        await process_arena_action(channel, interaction.user, text_to_ai, force_message=False)
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
        await process_arena_action(interaction.channel, interaction.user, skill_text, force_message=True)
    @discord.ui.button(label="Классовый скилл", style=discord.ButtonStyle.success)
    async def class_skill(self, interaction: discord.Interaction, button: discord.ui.Button): await self.use_skill(interaction, "Использую свой классовый скилл")
    @discord.ui.button(label="Расовый скилл", style=discord.ButtonStyle.primary)
    async def race_skill(self, interaction: discord.Interaction, button: discord.ui.Button): await self.use_skill(interaction, "Использую свой расовый скилл")
    @discord.ui.button(label="Отмена", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button): await interaction.response.send_message("Действие отменено.", ephemeral=True)

class CombatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def send_action(self, interaction: discord.Interaction, action_text: str):
        await interaction.response.defer()
        await process_arena_action(interaction.channel, interaction.user, action_text, force_message=True)
    @discord.ui.button(label="Атака", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_action(interaction, "Атакую мечом")
    @discord.ui.button(label="Защита", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def defend(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_action(interaction, "Защищаюсь")
    @discord.ui.button(label="Уклонение", style=discord.ButtonStyle.secondary, emoji="💨")
    async def dodge(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_action(interaction, "Уклоняюсь")
    @discord.ui.button(label="Скилл", style=discord.ButtonStyle.success, emoji="✨")
    async def skill(self, interaction: discord.Interaction, button: discord.ui.Button): await interaction.response.send_message("Выбери, какой скилл использовать:", view=SkillChoiceView(), ephemeral=True)

class VictoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def send_action(self, interaction: discord.Interaction, action_text: str):
        await interaction.response.defer()
        await process_arena_action(interaction.channel, interaction.user, action_text, force_message=True)
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
    if item_id not in SHOP_ITEMS:
        await interaction.response.send_message("❌ Ошибка: товар не найден.", ephemeral=True)
        return
    item_name, price, role_name = SHOP_ITEMS[item_id]
    current_coins = get_balance(interaction.user, "💰")
    if current_coins < price:
        await interaction.response.send_message(f"❌ Недостаточно монет! Нужно {price}, у вас {current_coins}.", ephemeral=True)
        return
    new_coins = current_coins - price
    await update_role(interaction.user, "💰", new_coins)
    guild = interaction.guild
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        role = await guild.create_role(name=role_name, color=discord.Color.blue())
    await interaction.user.add_roles(role)
    await interaction.response.send_message(f"✅ Вы купили **{item_name}**! Роль выдана. (Баланс: {new_coins} монет)", ephemeral=True)

async def process_arena_action(channel, user, user_text, force_message=False):
    if channel.id not in chat_histories:
        chat_histories[channel.id] = []

    if "СБРОС" in user_text.upper() or "Я выбираю расу" in user_text:
        chat_histories[channel.id] = [{"role": "user", "content": user_text}]
        last_win_state[channel.id] = False
        arena_cooldowns[user.id] = 0
    else:
        chat_histories[channel.id].append({"role": "user", "content": user_text})

    history_to_send = chat_histories[channel.id][-10:]

    async with channel.typing():
        response = None
        for attempt in range(2):
            try:
                response = client.chat.completions.create(
                    model=AGENT_ID,
                    messages=history_to_send,
                    timeout=20.0
                )
                break
            except Exception as e:
                print(f"Попытка {attempt+1} не удалась: {e}")
                if attempt == 1:
                    await channel.send("⚠️ *Мастер Арены задумался... Попробуйте еще раз.*")
                    return

        if not response:
            return

        try:
            bot_reply = response.choices[0].message.content
            
            lines = bot_reply.split('\n')
            new_lines = []
            for i, line in enumerate(lines):
                if line.strip() == "":
                    next_line = ""
                    for j in range(i+1, len(lines)):
                        if lines[j].strip() != "":
                            next_line = lines[j].strip()
                            break
                    if next_line.startswith("[Статус]"):
                        new_lines.append("")
                else:
                    new_lines.append(line.strip())
            bot_reply = '\n'.join(new_lines)
            
            if len(chat_histories[channel.id]) >= 2:
                last_bot_msg = chat_histories[channel.id][-2]["content"]
                if bot_reply.strip() == last_bot_msg.strip():
                    await channel.send("...")
                    return

            chat_histories[channel.id].append({"role": "assistant", "content": bot_reply})
            
            view_to_send = None
            if "Уйти" in bot_reply or "Продолжить" in bot_reply or "покинуть арену" in bot_reply:
                view_to_send = VictoryView()
            elif any(word in bot_reply.lower() for word in ["действия", "действие", "твой ход", "твои дейст"]):
                view_to_send = CombatView()
            elif "[Противник]" in bot_reply:
                view_to_send = CombatView()
            
            image_file = None
            for enemy_name, file_name in ENEMY_IMAGES.items():
                if enemy_name.lower() in bot_reply.lower():
                    path = os.path.join("images", file_name)
                    if os.path.exists(path):
                        image_file = discord.File(path)
                    break

            if image_file and view_to_send:
                await channel.send(bot_reply, view=view_to_send, file=image_file)
            elif image_file:
                await channel.send(bot_reply, file=image_file)
            elif view_to_send:
                await channel.send(bot_reply, view=view_to_send)
            else:
                await channel.send(bot_reply)

            current_coins = get_balance(user, "💰")
            current_time = time.time()

            if "Толпа ликует, ты победил!" in bot_reply or "Ты получаешь награду за уровень" in bot_reply:
                if not last_win_state.get(channel.id, False):
                    last_time = arena_cooldowns.get(user.id, 0)
                    if current_time - last_time < 120:
                        await channel.send("⚠️ *Слишком быстро! Подождите 2 минуты.*")
                    else:
                        level_match = re.search(r'уровень\s*(\d+)', bot_reply.lower())
                        level = int(level_match.group(1)) if level_match else 1
                        reward = ARENA_REWARDS.get(level, 1)
                        new_coins = current_coins + reward
                        await update_role(user, "💰", new_coins)
                        arena_cooldowns[user.id] = current_time
                        await channel.send(f"💰 *Система начислила {reward} монет за {level} уровень!*")
                    last_win_state[channel.id] = True

            elif "Твоя история окончена" in bot_reply or "Ты пал на арене" in bot_reply:
                new_coins = current_coins // 2 if current_coins > 0 else current_coins
                await update_role(user, "💰", new_coins)
                await channel.send(f"☠️ *Потеряно 50% монет. Осталось: {new_coins}*")
                last_win_state[channel.id] = False

            elif "Ты покидаешь арену победителем" in bot_reply:
                last_win_state[channel.id] = False
                await channel.send("🏆 *Твои монеты сохранены!*")

            elif "действия" in bot_reply.lower():
                last_win_state[channel.id] = False

        except Exception as e:
            print(f"Ошибка при обработке ответа: {e}")
            await channel.send("⚠️ *Произошла ошибка при чтении ответа мастера.*")

@bot.event
async def on_message(message):
    global casino_jackpot

    if message.author == bot.user:
        return

    clean_text = message.content.replace(f'<@{bot.user.id}>', '').strip()
    clean_lower = clean_text.lower()

    # --- ТАБЛИЦА ЛИДЕРОВ ---
    if clean_lower == "!топ":
        # Собираем всех участников сервера, у кого есть роли с валютами
        players_coins = []
        players_dollars = []
        
        for member in message.guild.members:
            if member.bot:
                continue
                
            coins = get_balance(member, "💰")
            if coins > 0:
                players_coins.append((member.display_name, coins))
                
            dollars = get_balance(member, "💵")
            if dollars > 0:
                players_dollars.append((member.display_name, dollars))
        
        # Сортируем по убыванию
        players_coins.sort(key=lambda x: x[1], reverse=True)
        players_dollars.sort(key=lambda x: x[1], reverse=True)
        
        # Формируем текст
        top_text = "🏆 **ТАБЛИЦА ЛИДЕРОВ** 🏆\n\n"
        
        top_text += "💰 **Топ по монетам:**\n"
        if players_coins:
            for i, (name, amount) in enumerate(players_coins[:10], 1):
                top_text += f"{i}. **{name}** — {amount} монет\n"
        else:
            top_text += "*Пока ни у кого нет монет.*\n"
            
        top_text += "\n💵 **Топ по долларам:**\n"
        if players_dollars:
            for i, (name, amount) in enumerate(players_dollars[:10], 1):
                top_text += f"{i}. **{name}** — {amount}$\n"
        else:
            top_text += "*Пока ни у кого нет долларов.*\n"
            
        await message.reply(top_text)
        return

    if clean_lower == "!хелп":
        help_text = (
            "📖 **Справка по командам**\n\n"
            "⚔️ **Арена:**\n"
            "`@Fbot СБРОС` — начать игру.\n\n"
            "💼 **Работа:**\n"
            "В канале работы напиши `!` чтобы заработать доллары.\n"
            "`!обмен` — открыть меню обмена долларов на монеты.\n\n"
            "🛒 **Магазин:**\n"
            "`!магазин` — кнопки для покупки.\n\n"
            "🎰 **Казино:**\n"
            "`!` — ставка 1 монета.\n"
            "`! [число]` — ставка на сумму.\n\n"
            "🏆 **Топ:**\n"
            "`!топ` — таблица лидеров."
        )
        await message.reply(help_text)
        return

    if clean_lower == "!магазин":
        shop_text = "🛒 **Магазин Арены**\nНажми на кнопку ниже, чтобы купить товар.\n\n"
        for key, item in SHOP_ITEMS.items():
            name, price, _ = item
            shop_text += f"**{key}.** {name} — `{price}` монет\n"
        await message.reply(shop_text, view=ShopView())
        return

    if clean_lower in ["!обмен", "!обменять", "!обменять 1000"]:
        current_dollars = get_balance(message.author, "💵")
        text = f"💱 **Обмен валют**\nВаш баланс: **{current_dollars}$**\nКурс: 1000$ = 1 монета\n\nЖелаете обменять доллары на монеты?"
        await message.reply(text, view=ExchangeView())
        return

    if message.channel.id == WORK_CHANNEL_ID and clean_text == "!":
        current_time = time.time()
        last_time = work_cooldowns.get(message.author.id, 0)
        
        if current_time - last_time < 3600:
            remain = int((3600 - (current_time - last_time)) / 60)
            await message.reply(f"❌ Ты устал. Отдохни еще {remain} минут перед следующей работой.")
            return
        
        event_roll = random.randint(1, 100)
        current_dollars = get_balance(message.author, "💵")
        
        if event_roll <= 40:
            earnings = random.randint(50, 200)
            new_dollars = current_dollars + earnings
            await update_role(message.author, "💵", new_dollars)
            msg = f"💼 Вам удалось найти подработку, и вы заработали **{earnings}$**!"
        elif event_roll <= 70:
            earnings = random.randint(100, 300)
            new_dollars = current_dollars + earnings
            await update_role(message.author, "💵", new_dollars)
            msg = f"🤝 Пока вы работали, щедрый клиент оставил на чай **{earnings}$**!"
        elif event_roll <= 90:
            earnings = random.randint(150, 400)
            new_dollars = current_dollars + earnings
            await update_role(message.author, "💵", new_dollars)
            msg = f"🌟 Вам удалось найти выгодное предложение о работе! Вы получили **{earnings}$**!"
        else:
            loss = 100
            new_dollars = max(0, current_dollars - loss)
            await update_role(message.author, "💵", new_dollars)
            msg = f"💀 В поисках работы вас обманули! Вы потеряли **{loss}$**."

        work_cooldowns[message.author.id] = current_time
        final_dollars = get_balance(message.author, "💵")
        await message.reply(f"{msg}\n*(Текущий баланс: {final_dollars}$)*")
        return

    if clean_text.startswith("!") and message.channel.id in [CHANNEL_ID_1, CHANNEL_ID_2]:
        match = re.match(r'^!(?:ставка\s*)?(\d+)?$', clean_lower)
        if match:
            bet_str = match.group(1)
            bet = int(bet_str) if bet_str else 1
            is_vip = False
            if message.channel.id == CHANNEL_ID_1:
                if bet < 1 or bet > 50:
                    await message.reply("❌ В этом канале ставка от **1** до **50** монет!")
                    return
            elif message.channel.id == CHANNEL_ID_2:
                if bet < 10 or bet > 1000:
                    await message.reply("❌ В VIP-казино ставка от **10** до **1000** монет!")
                    return
                is_vip = True
            else:
                return
            
            current_coins = get_balance(message.author, "💰")
            if current_coins < bet:
                await message.reply(f"❌ Недостаточно монет! Ставка: {bet}, баланс: {current_coins}.")
                return
            
            new_coins = current_coins - bet
            await update_role(message.author, "💰", new_coins)
            
            emoji_map = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣"}
            roll = random.randint(1, 200)
            
            if roll == 1:
                slot_text = "7️⃣ 7️⃣ 7️⃣"
                jackpot_win = casino_jackpot
                casino_jackpot = 0
                
                if is_vip:
                    win_amount = max(1, int(bet * 3.0))
                    total_win = win_amount + jackpot_win
                    win_coins = new_coins + bet + total_win
                    msg = f"🏆 **ДЖЕКПОТ!** {slot_text}\nВы сорвали куш — +{win_amount} монет (x3 от ставки) и **+{jackpot_win} монет из банка**!\n*(Баланс: {win_coins})*"
                else:
                    win_coins = new_coins + bet + 20 + jackpot_win
                    msg = f"🏆 **ДЖЕКПОТ!** {slot_text}\nВы сорвали куш — +20 монет и **+{jackpot_win} монет из банка**!\n*(Баланс: {win_coins})*"
                
                await update_role(message.author, "💰", win_coins)
            
            elif roll <= 20:
                digit = random.choice([1, 2, 3, 4, 5, 6, 8, 9])
                slot_text = f"{emoji_map[digit]} {emoji_map[digit]} {emoji_map[digit]}"
                
                if is_vip:
                    win_amount = max(1, int(bet * 1.0))
                    win_coins = new_coins + bet + win_amount
                    msg = f"💰 Три в ряд! {slot_text}\nВы получили +{win_amount} монет!\n*(Баланс: {win_coins})*\n*(Джекпот казино: {casino_jackpot})*"
                else:
                    win_coins = new_coins + bet + 5
                    msg = f"💰 Три в ряд! {slot_text}\nВы получили +5 монет!\n*(Баланс: {win_coins})*\n*(Джекпот казино: {casino_jackpot})*"
                
                await update_role(message.author, "💰", win_coins)
                casino_jackpot += 1
            
            elif roll <= 90:
                d1 = random.randint(1, 5)
                d2 = random.randint(1, 5)
                if d1 == d2: d2 = d2 % 5 + 1
                slot_text = f"{emoji_map[d1]} {emoji_map[d1]} {emoji_map[d2]}"
                
                if is_vip:
                    win_amount = max(1, int(bet * 0.4))
                    win_coins = new_coins + bet + win_amount
                    msg = f"🎉 Две в ряд! {slot_text}\nВы выиграли +{win_amount} монет!\n*(Баланс: {win_coins})*\n*(Джекпот казино: {casino_jackpot})*"
                else:
                    win_coins = new_coins + bet + 2
                    msg = f"🎉 Две в ряд! {slot_text}\nВы выиграли +2 монеты!\n*(Баланс: {win_coins})*\n*(Джекпот казино: {casino_jackpot})*"
                
                await update_role(message.author, "💰", win_coins)
                casino_jackpot += 1
            
            else:
                s1 = random.randint(1, 5)
                s2 = random.randint(1, 5)
                s3 = random.randint(1, 5)
                while s1 == s2 or s2 == s3 or s1 == s3:
                    s1 = random.randint(1, 5)
                    s2 = random.randint(1, 5)
                    s3 = random.randint(1, 5)
                slot_text = f"{emoji_map[s1]} {emoji_map[s2]} {emoji_map[s3]}"
                
                casino_jackpot += 1
                msg = f"🎲 {slot_text}\nУвы, ставка сгорела.\n*(Баланс: {new_coins})*\n*(Джекпот казино: {casino_jackpot})*"
            
            await message.reply(msg)
            return

    if message.channel.id == ARENA_CHANNEL_ID and (bot.user.mentioned_in(message) or any(word in clean_lower for word in ["сброс", "старт", "начать"])):
        if any(word in clean_lower for word in ["сброс", "старт", "начать"]):
            await message.reply("Начинаем! Выбери свою расу:", view=RaceView())
        else:
            await process_arena_action(message.channel, message.author, clean_text, force_message=True)

bot.run(DISCORD_TOKEN)