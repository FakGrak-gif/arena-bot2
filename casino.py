import discord
import random
from config import CHANNEL_ID_1, CHANNEL_ID_2
from database import update_role, get_balance

# Глобальная переменная для джекпота
casino_jackpot = 0

# --- КНОПКИ ОБМЕНА ВАЛЮТ ---
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

# --- КНОПКИ РУЛЕТКИ ---
class RouletteView(discord.ui.View):
    def __init__(self, bet: int):
        super().__init__(timeout=60)
        self.bet = bet

    async def play(self, interaction: discord.Interaction, choice: str):
        # Сначала списываем ставку
        current_coins = get_balance(interaction.user, "💰")
        if current_coins < self.bet:
            await interaction.response.send_message("❌ Недостаточно монет.", ephemeral=True)
            return
        
        await update_role(interaction.user, "💰", current_coins - self.bet)
        
        # Крутим рулетку (0-36, где 0 - зеро)
        result = random.randint(0, 36)
        
        # Визуал
        if result == 0:
            color = "🟢 Зеро"
            color_code = "green"
        elif result % 2 == 0:
            color = "⚫ Черное"
            color_code = "black"
        else:
            color = "🔴 Красное"
            color_code = "red"
            
        # Подсчет выигрыша
        win_amount = 0
        if choice == "red" and color_code == "red":
            win_amount = self.bet * 2 # Возврат ставки + x1
        elif choice == "black" and color_code == "black":
            win_amount = self.bet * 2
        elif choice == "green" and color_code == "green":
            win_amount = self.bet * 14 # Джекпот за зеро
            
        if win_amount > 0:
            new_coins = current_coins - self.bet + win_amount
            await update_role(interaction.user, "💰", new_coins)
            await interaction.response.send_message(f"🎲 Выпало **{color}** (число {result}).\n🎉 Вы выиграли **{win_amount}** монет!\n*(Баланс: {new_coins})*")
        else:
            await interaction.response.send_message(f"🎲 Выпало **{color}** (число {result}).\n💀 Вы проиграли ставку **{self.bet}** монет.\n*(Баланс: {current_coins - self.bet})*")

    @discord.ui.button(label="Красное", style=discord.ButtonStyle.danger, emoji="🔴")
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "red")

    @discord.ui.button(label="Черное", style=discord.ButtonStyle.secondary, emoji="⚫")
    async def black(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "black")

    @discord.ui.button(label="Зеро (x14)", style=discord.ButtonStyle.success, emoji="🟢")
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "green")

# --- ЛОГИКА СЛОТОВ ---
async def play_casino(message, bet):
    global casino_jackpot
    
    # Проверка канала и лимитов
    if message.channel.id == CHANNEL_ID_1:
        if bet < 1 or bet > 50:
            await message.reply("❌ В этом канале ставка должна быть от **1** до **50** монет!")
            return
        is_vip = False
    elif message.channel.id == CHANNEL_ID_2:
        if bet < 10 or bet > 1000:
            await message.reply("❌ В VIP-казино ставка должна быть от **10** до **1000** монет!")
            return
        is_vip = True
    else:
        return

    current_coins = get_balance(message.author, "💰")
    if current_coins < bet:
        await message.reply("❌ Недостаточно монет.")
        return
        
    await update_role(message.author, "💰", current_coins - bet)
    
    emoji_map = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣"}
    roll = random.randint(1, 200)
    
    # 1. ДЖЕКПОТ (0.5%)
    if roll == 1:
        slot_text = "7️⃣ 7️⃣ 7️⃣"
        jackpot_win = casino_jackpot
        casino_jackpot = 0 
        
        if is_vip:
            win_amount = max(1, int(bet * 3.0))
            win_coins = current_coins - bet + win_amount + jackpot_win
            await update_role(message.author, "💰", win_coins)
            await message.reply(f"🏆 **ДЖЕКПОТ!** {slot_text}\nВы сорвали куш — +{win_amount} монет (x3 от ставки) и **+{jackpot_win} монет из банка**!\n*(Баланс: {win_coins})*")
        else:
            win_coins = current_coins - bet + 20 + jackpot_win
            await update_role(message.author, "💰", win_coins)
            await message.reply(f"🏆 **ДЖЕКПОТ!** {slot_text}\nВы сорвали куш — +20 монет и **+{jackpot_win} монет из банка**!\n*(Баланс: {win_coins})*")

    # 2. ДВЕ В РЯД (44.5%)
    elif roll <= 90:
        d1 = random.randint(1, 9)
        d2 = random.randint(1, 9)
        if d1 == d2: d2 = (d2 % 9) + 1
        slot_text = f"{emoji_map[d1]} {emoji_map[d1]} {emoji_map[d2]}"
        
        if is_vip:
            win_amount = max(1, int(bet * 0.5))
        else:
            win_amount = 1
            
        win_coins = current_coins - bet + bet + win_amount
        await update_role(message.author, "💰", win_coins)
        casino_jackpot += 1
        await message.reply(f"🎉 {slot_text}\nВы выиграли +{win_amount} монет!\n*(Баланс: {win_coins})*\n*(Джекпот казино: {casino_jackpot})*")

    # 3. ПРОИГРЫШ (55%)
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
