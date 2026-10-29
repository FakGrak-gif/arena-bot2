import discord
from config import SHOP_ITEMS
from database import update_role, get_balance

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def process_purchase(self, interaction: discord.Interaction, item_id: str):
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
    @discord.ui.button(label="Кейс (50)", style=discord.ButtonStyle.primary, emoji="📦")
    async def buy_case(self, interaction: discord.Interaction, button: discord.ui.Button): await self.process_purchase(interaction, "1")
    @discord.ui.button(label="Цвет (60)", style=discord.ButtonStyle.secondary, emoji="🎨")
    async def buy_color(self, interaction: discord.Interaction, button: discord.ui.Button): await self.process_purchase(interaction, "2")
    @discord.ui.button(label="Скин (120)", style=discord.ButtonStyle.success, emoji="🔫")
    async def buy_skin(self, interaction: discord.Interaction, button: discord.ui.Button): await self.process_purchase(interaction, "4")
    @discord.ui.button(label="Роль (200)", style=discord.ButtonStyle.danger, emoji="👑")
    async def buy_role(self, interaction: discord.Interaction, button: discord.ui.Button): await self.process_purchase(interaction, "5")