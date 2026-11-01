import discord

async def update_role(member, role_prefix, amount):
    amount = int(round(amount))
    guild = member.guild
    role_name = f"{role_prefix} {amount}"
    
    # Ищем новую роль
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        color = discord.Color.red() if amount < 0 else (discord.Color.gold() if role_prefix == "💰" else discord.Color.green())
        try:
            role = await guild.create_role(name=role_name, color=color)
        except discord.HTTPException:
            # Если лимит ролей достигнут, просто не создаем новую (или обрабатываем ошибку)
            return

    # Собираем старые роли для удаления
    roles_to_remove = []
    for old_role in member.roles:
        if old_role.name.startswith(f"{role_prefix} ") and old_role.name != role_name:
            roles_to_remove.append(old_role)
    
    # Снимаем старые роли с игрока
    if roles_to_remove:
        try:
            await member.remove_roles(*roles_to_remove)
        except:
            pass
            
        # ТЕПЕРЬ ГЛАВНОЕ: Проверяем, остались ли у кого-то еще эти роли
        for old_role in roles_to_remove:
            # Если у роли больше нет носителей (кроме самого бота, если он есть)
            if len(old_role.members) == 0:
                try:
                    await old_role.delete()
                except:
                    pass # Если бот не может удалить, просто пропускаем

    # Выдаем новую роль
    try:
        await member.add_roles(role)
    except:
        pass

def get_balance(member, role_prefix):
    for role in member.roles:
        if role.name.startswith(f"{role_prefix}"):
            try:
                return int(role.name.split()[-1])
            except:
                pass
    return 0
