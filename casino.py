import discord
import random
from config import CHANNEL_ID_1, CHANNEL_ID_2
from database import update_role, get_balance

# Глобальная переменная для джекпота
casino_jackpot = 0

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

async def play_casino(message, bet):
    global casino_jackpot # Объявляем, что меняем глобальную переменную
    
    # --- ПРОВЕРКА КАНАЛА И СТАВКИ ---
    if message.channel.id == CHANNEL_ID_1:
        if bet < 1 or bet > 50:
            await message.reply("❌ В этом канале ставка должна быть от **1** до **50** монет!")
            return
    elif message.channel.id == CHANNEL_ID_2:
        if bet < 10 or bet > 1000:
            await message.reply("❌ В VIP-казино ставка должна быть от **10** до **1000** монет!")
            return
    else:
        return

    current_coins = get_balance(message.author, "💰")
    if current_coins < bet:
        await message.reply("❌ Недостаточно монет.")
        return
        
    await update_role(message.author, "💰", current_coins - bet)
    
    emoji_map = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣"}
    roll = random.randint(1, 200)
    
    if roll == 1:
        slot_text = "7️⃣ 7️⃣ 7️⃣"
        casino_jackpot += 20
        await update_role(message.author, "💰", current_coins + bet + casino_jackpot)
        await message.reply(f"🏆 **ДЖЕКПОТ!** {slot_text}\nВы забрали {casino_jackpot} монет!")
        casino_jackpot = 0
    elif roll <= 90:
        d1 = random.randint(1, 9)
        d2 = random.randint(1, 9)
        if d1 == d2: d2 = (d2 % 9) + 1
        slot_text = f"{emoji_map[d1]} {emoji_map[d1]} {emoji_map[d2]}"
        await update_role(message.author, "💰", current_coins + bet + 2)
        await message.reply(f"🎉 {slot_text}\nВы выиграли +2 монеты! (Джекпот: {casino_jackpot})")
    else:
        d1 = random.randint(1, 9)
        d2 = random.randint(1, 9)
        d3 = random.randint(1, 9)
        while d1 == d2 or d2 == d3 or d1 == d3:
            d1 = random.randint(1, 9)
            d2 = random.randint(1, 9)
            d3 = random.randint(1, 9)
        slot_text = f"{emoji_map[d1]} {emoji_map[d2]} {emoji_map[d3]}"
        casino_jackpot += 1
        await message.reply(f"🎲 {slot_text}\nВы проиграли. (Джекпот: {casino_jackpot})")
