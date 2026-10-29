import discord
from config import DISCORD_TOKEN, CHANNEL_ID_1, CHANNEL_ID_2, ARENA_CHANNEL_ID, WORK_CHANNEL_ID, SHOP_ITEMS
from database import get_balance
from arena import RaceView, process_arena_action
from casino import ExchangeView, play_casino
from work import do_work
from shop import ShopView

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True 
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} успешно запущен!')
    for guild in bot.guilds:
        await guild.chunk()
    print("Кэш участников обновлен.")

@bot.event
async def on_message(message):
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
        await do_work(message)
        return

    if clean_text.startswith("!") and message.channel.id in [CHANNEL_ID_1, CHANNEL_ID_2]:
        import re
        if re.match(r'^!(?:\s*)(\d+)?$', clean_lower):
            bet = int(clean_lower.replace("!", "").strip() or 1)
            await play_casino(message, bet)
            return

    if clean_lower == "!топ":
        top_text = "🏆 **ТАБЛИЦА ЛИДЕРОВ** 🏆\n\n"
        players_money = []
        players_arena = []
        for m in message.guild.members:
            if not m.bot:
                coins = get_balance(m, "💰")
                if coins > 0: players_money.append((m.display_name, coins))
                arena_lvl = get_balance(m, "Арена")
                if arena_lvl > 0: players_arena.append((m.display_name, arena_lvl))
                    
        players_money.sort(key=lambda x: x[1], reverse=True)
        players_arena.sort(key=lambda x: x[1], reverse=True)
        
        top_text += "💰 **Самые богатые:**\n"
        if players_money:
            for i, p in enumerate(players_money[:5], 1):
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

    if bot.user.mentioned_in(message) or any(w in clean_lower for w in ["сброс", "старт", "начать"]):
        if any(w in clean_lower for w in ["сброс", "старт", "начать"]):
            await message.reply("Начинаем! Выбери расу:", view=RaceView())
        else:
            await process_arena_action(message.channel, message.author, clean_text)

bot.run(DISCORD_TOKEN)