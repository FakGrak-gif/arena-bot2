import discord
import random
import time
from database import update_role, get_balance

work_cooldowns = {}

async def do_work(message):
    if time.time() - work_cooldowns.get(message.author.id, 0) < 3600:
        remain = int((3600 - (time.time() - work_cooldowns.get(message.author.id, 0))) / 60)
        await message.reply(f"❌ Ты устал. Отдохни еще {remain} минут.")
        return
        
    event_roll = random.randint(1, 100)
    current_dollars = get_balance(message.author, "💵")
    
    if event_roll <= 45:
        earnings = random.randint(50, 200)
        await update_role(message.author, "💵", current_dollars + earnings)
        msg = f"💼 Вам удалось найти подработку, и вы заработали **{earnings}$**!"
    elif event_roll <= 75:
        earnings = random.randint(100, 300)
        await update_role(message.author, "💵", current_dollars + earnings)
        msg = f"🤝 Пока вы работали, щедрый клиент оставил на чай **{earnings}$**!"
    elif event_roll <= 95:
        earnings = random.randint(150, 400)
        await update_role(message.author, "💵", current_dollars + earnings)
        msg = f"🌟 Вам удалось найти выгодное предложение о работе! Вы получили **{earnings}$**!"
    else:
        loss = min(100, current_dollars)
        await update_role(message.author, "💵", current_dollars - loss)
        msg = f"💀 В поисках работы вас обманули! Вы потеряли **{loss}$**."

    work_cooldowns[message.author.id] = time.time()
    final_dollars = get_balance(message.author, "💵")
    await message.reply(f"{msg}\n*(Текущий баланс: {final_dollars}$)*")