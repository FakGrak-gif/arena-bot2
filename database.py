import discord

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
        if role.name.startswith(f"{role_prefix}"):
            try:
                return int(role.name.split()[-1])
            except:
                pass
    return 0