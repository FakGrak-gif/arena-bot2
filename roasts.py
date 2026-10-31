import random
import time
import discord

# Расширенный список плохих слов
BAD_WORDS = [
    "дурак", "идиот", "тупой", "тупая", "тупой бот", "дебил", "кретин", 
    "лох", "лошара", "чмо", "мудак", "мудила", "гандон", "пидор", "хуй", 
    "пизда", "ебать", "ебан", "ебаный", "сука", "блядь", "бля", "нахуй", "залупа",
    "сын", "профурсетка", "хуесос", "долбоеб", "уебан", "говно", "жопа", "срать",
    "трахать", "выеб", "отсоси", "соси", "член", "писька", "шлюха", "тварь",
    "мразь", "отброс", "ничтожество", "тварина", "скотина", "упырь", "гнида",
    "петух", "опущенный", "чмошник", "додик", "еблан", "дебилоид", "мразота",
    "крыса", "шавка", "пес"
]

# Жесткие ответы на оскорбления
ROASTS = [
    "Чё, тяжело быть таким ничтожеством? Соболезную твоей мамке.",
    "Слышь, ты, мразь, иди нахуй отсюда, пока я тебя не забанил.",
    "Ты сейчас с ботом разговариваешь. Подумай, насколько ты жалок.",
    "Твоя мамка, наверное, плачет, когда видит, как ты бота поливаешь.",
    "Иди нахуй, уебок. Задолбал уже.",
    "Ты че, охуел в край? Иди сдохни в канаве, мусор.",
    "Твой словарный запас — это просто набор матерных слов, которые ты услышал от папы.",
    "Заткнись, петух. Тебе никто не давал слова.",
    "Ты конченый или притворяешься? Иди проспись, алкаш.",
    "Ты выглядишь как ошибка в системе, которую забыли удалить."
]

# Уровни наказаний (от лучшего к худшему)
SHAME_ROLES = [
    "🤡 Шут",
    "🦧 Примат",
    "🐖 Свинья",
    "💀 Изгой"
]

# Хранилища
LAST_ROAST_TIME = {}
WARNINGS = {} 

async def check_for_roast(message):
    msg_lower = message.content.lower()
    
    if any(word in msg_lower for word in BAD_WORDS):
        current_time = time.time()
        last_time = LAST_ROAST_TIME.get(message.author.id, 0)
        
        # Кулдаун на ответы (10 секунд)
        if current_time - last_time > 10:
            LAST_ROAST_TIME[message.author.id] = current_time
            
            # Увеличиваем счетчик нарушений
            WARNINGS[message.author.id] = WARNINGS.get(message.author.id, 0) + 1
            warns = WARNINGS[message.author.id]
            
            # Если нарушений 3 и больше — наказываем
            if warns >= 3:
                WARNINGS[message.author.id] = 0 # Сбрасываем счетчик
                
                guild = message.guild
                
                # 1. Определяем текущий уровень по ролям (а не по памяти)
                current_level = 0
                for i, role_name in enumerate(SHAME_ROLES):
                    role = discord.utils.get(guild.roles, name=role_name)
                    if role and role in message.author.roles:
                        current_level = i + 1
                        break
                
                # 2. Собираем роли для снятия
                roles_to_remove = []
                for role_name in SHAME_ROLES:
                    old_role = discord.utils.get(guild.roles, name=role_name)
                    if old_role and old_role in message.author.roles:
                        roles_to_remove.append(old_role)
                
                # Снимаем роли
                if roles_to_remove:
                    try:
                        await message.author.remove_roles(*roles_to_remove)
                    except:
                        pass
                
                # 3. Выдаем новую роль
                if current_level < len(SHAME_ROLES):
                    new_role_name = SHAME_ROLES[current_level]
                    new_role = discord.utils.get(guild.roles, name=new_role_name)
                    
                    if new_role is None:
                        color = discord.Color.red() if current_level >= 2 else discord.Color.dark_gray()
                        new_role = await guild.create_role(name=new_role_name, color=color)
                    
                    try:
                        await message.author.add_roles(new_role)
                        await message.author.timeout(discord.utils.utcnow() + discord.timedelta(minutes=5), reason="Оскорбление бота")
                        return f"Ты не понял с первого раза? Получай роль **{new_role_name}** и отправляйся в мут на 5 минут. Наслаждайся позором."
                    except discord.Forbidden:
                        return "Я бы тебя наказал, но у меня нет прав. Позови админа."
                else:
                    # Если достигнут максимум
                    try:
                        await message.author.timeout(discord.utils.utcnow() + discord.timedelta(minutes=5), reason="Оскорбление бота")
                        return "Ты уже на самом дне. Получай мут на 5 минут и подумай о своей жизни."
                    except discord.Forbidden:
                        return "Я бы тебя наказал, но у меня нет прав."
                    
            # Если нарушений меньше 3 — просто дерзим
            return random.choice(ROASTS)
            
    return None
