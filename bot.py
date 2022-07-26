import asyncio
import random

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot import types
from telebot.asyncio_filters import StateFilter, IsDigitFilter

from config import token, rulestext


bot = AsyncTeleBot(token, state_storage=StateMemoryStorage())

g = {
    "0":{
        "gamemaster": 0,
        "message": 0,
        "players": [],
        "settings": {

        }
    }
}

class States(StatesGroup):
    gamemaster = State()
    player = State()
    connecting = State()
    ingame = State()

def menu():
    return types.InlineKeyboardMarkup(
        keyboard=[
            [
                types.InlineKeyboardButton(
                    text='Новая игра',
                    callback_data='newgame'
                )
            ],
            [
                types.InlineKeyboardButton(
                    text='Присоедениться к игре',
                    callback_data='connect'
                )
            ],
            [
                types.InlineKeyboardButton(
                    text='О боте',
                    callback_data='about'
                )
            ],
        ])

def gamemastermarkup():
    return types.InlineKeyboardMarkup(
        keyboard=[
            [
                types.InlineKeyboardButton(
                    text='Разослать роли',
                    callback_data='sendroles'
                )
            ],
            [
                types.InlineKeyboardButton(
                    text='Настройки игры',
                    callback_data='settings'
                )
            ],
            [
                types.InlineKeyboardButton(
                    text='Завершить игру',
                    callback_data='endgame'
                )
            ],
        ])

async def checkGame(gid):
    if gid in g:
        return True
    return False

async def pickId():
    id = random.randint(1000, 9999)
    if await checkGame(id):
        return await pickId()
    else:
        return id

async def createGame(gamemaster):
    gameid = await pickId()
    g[str(gameid)] = {
        "gamemaster": gamemaster,
        "message": 0,
        "players": [],
        "settings": {

        }
    }
    return gameid



async def regUser(gid, uid):
    g[gid]["players"].append(uid)

@bot.message_handler(commands=['start'])
async def start(msg):
    await bot.send_message(msg.chat.id, 'Привет, этот бот создан для игры в мафию. Здесь ты можешь быть как ведущим, так и участником игры.')
    await bot.send_message(msg.chat.id, 'Меню', reply_markup=menu())

@bot.message_handler(commands=['rules'])
async def rules(msg):
    await bot.send_message(msg.chat.id, rulestext)

# menu

@bot.callback_query_handler(func=lambda c: c.data == 'newgame')
async def newgame_callback(call: types.CallbackQuery):
    if await findmygame(call.from_user.id) is None:
        gameid = await createGame(call.from_user.id)
        await bot.set_state(call.from_user.id, States.gamemaster, call.message.chat.id)
        mid = await bot.send_message(call.from_user.id, """Игра %s\nВ твоей игре 0 чел."""%gameid, reply_markup=gamemastermarkup())
        g[str(gameid)]["message"] = mid.id
    else:
        await bot.answer_callback_query(callback_query_id=call.id, text='Заверши сначала старую игру!', show_alert=False)
    pass

# gamemaster

async def findmygame(gm):
    for key in g:
        if g[key]["gamemaster"] == gm:
            return key
    return None

async def sendroles(gid, call):
    mafia = False
    doc = False
    comm = False
    for pl in g[str(gid)]["players"]:
        if not mafia:
            if random.randint(1, len(g[str(gid)]["players"])) == len(g[str(gid)]["players"]):
                await bot.send_message(pl, "Ты Мафия!")
                mafia = True
                continue
        if not doc:
            if random.randint(1, len(g[str(gid)]["players"])) == len(g[str(gid)]["players"]):
                await bot.send_message(pl, "Ты Доктор!")
                doc = True
                continue
        if not comm:
            if random.randint(1, len(g[str(gid)]["players"])) == len(g[str(gid)]["players"]):
                await bot.send_message(pl, "Ты Комиссар!")
                comm = True
                continue
        await bot.send_message(pl, "Ты Мирный!")
        await asyncio.sleep(0.1)
    if not mafia:
        await bot.send_message(g[str(gid)]["players"][len(g[str(gid)]["players"]) - 1], "Ты Мафия!")
    if not doc:
        await bot.send_message(g[str(gid)]["players"][len(g[str(gid)]["players"]) - 2], "Ты Доктор!")
    if not comm:
        await bot.send_message(g[str(gid)]["players"][len(g[str(gid)]["players"]) - 3], "Ты Комиссар!")

    await bot.answer_callback_query(callback_query_id=call, text='Роли разосланы!', show_alert=True)

async def endgame(gid):
    g.pop(str(gid))

@bot.callback_query_handler(func=lambda c: c.data == 'sendroles')
async def sendroles_callback(call: types.CallbackQuery):
    if len(g[await findmygame(call.from_user.id)]["players"]) > 5:
        await sendroles(await findmygame(call.from_user.id), call.id)
    else:
        await bot.answer_callback_query(callback_query_id=call.id, text='Для игры необходимо минимум 6 человек!', show_alert=False)

@bot.callback_query_handler(func=lambda c: c.data == 'settings')
async def settings_callback(call: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=call.id, text='В разработке...', show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == 'endgame')
async def endgame_callback(call: types.CallbackQuery):
    await endgame(await findmygame(call.from_user.id))
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Игра заврешена!")
    await asyncio.sleep(2)
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)

# player

@bot.callback_query_handler(func=lambda c: c.data == 'connect')
async def connect_callback(call: types.CallbackQuery):
    await bot.set_state(call.message.chat.id, States.connecting, call.message.chat.id)
    await bot.send_message(call.from_user.id, "Напиши номер игры (четырехзначное число)")

@bot.message_handler(state=States.connecting)
async def connecting_step(msg):
    if msg.text.isdigit() and await checkGame(msg.text):
        await bot.set_state(msg.from_user.id, States.player, msg.chat.id)
        await bot.send_message(msg.chat.id, "Ты зарегистрирован в игре. Выйти: /exit %s"%msg.text)
        game = msg.text
        await regUser(msg.text, msg.from_user.id)
        await bot.edit_message_text(chat_id=g[game]["gamemaster"], message_id=g[game]["message"], text="""Игра %s\nВ твоей игре %s чел."""%(msg.text, len(g[game]["players"])), reply_markup=gamemastermarkup())
    else:
        await bot.send_message(msg.chat.id, "Такой игры нет. Попробуй еще раз.")


@bot.callback_query_handler(func=lambda c: c.data == 'about')
async def about_callback(call: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=call.id, text='Бот для игры в мафию там, где картишки не приветствуются.\nby @OllyHearn\nGithub: https://github.com/ollyhearn \n\nv0.0.1', show_alert=True)


print("Bot started")
bot.add_custom_filter(StateFilter(bot))
bot.add_custom_filter(IsDigitFilter())
asyncio.run(bot.polling())
