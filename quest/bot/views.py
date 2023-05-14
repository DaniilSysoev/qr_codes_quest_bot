from django.shortcuts import HttpResponse
import telebot
from django.conf import settings
from .models import User, Question, Game
import os
from django.views.decorators.csrf import csrf_exempt


bot = telebot.TeleBot(settings.BOT_TOKEN)
# https://api.telegram.org/bot6180293008:AAGqnW0xsH8jfx9HqZjAp24WR-H7Kbb-j2k/setWebhook?url=https://f6d0-217-151-229-99.ngrok-free.app
# https://api.telegram.org/bot5813570276:AAHVVgjcZZzmYr0Vrb-X9DXq-WHsrsXqLdo/setWebhook?url=https://e743-217-151-229-99.ngrok-free.app

@csrf_exempt
def index(request):
    if request.method == "POST":
        update = telebot.types.Update.de_json(request.body.decode('utf-8'))
        bot.process_new_updates([update])

    return HttpResponse('<h1>Ты подключился!</h1>')


@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    if User.objects.filter(tg_id=message.from_user.id).exists():
        user = User.objects.get(tg_id=message.from_user.id)
        #если stage <=12, то добавить кнопку продолжить
        if user.stage <= 12:
            keyboard = telebot.types.InlineKeyboardMarkup()
            key1 = telebot.types.InlineKeyboardButton(text='Продолжить', callback_data='Продолжить')
            keyboard.add(key1)
            bot.send_message(message.chat.id, f'Привет, ты уже зареган, твой результат: {user.score} очков', reply_markup=keyboard)
            return
        bot.send_message(message.chat.id, f'Привет, ты уже зареган, твой результат: {user.score} очков')
        return
    else:
        User.objects.create(tg_id=message.from_user.id, start=Game.objects.all().values('start_question')[0]['start_question'], stage=0, wave=Game.objects.all().values('wave')[0]['wave'])
        bot.send_message(message.chat.id, "Вот правила")
    game = Game.objects.all()[0]
    game.start_question = game.start_question - 1 if game.start_question > 1 else 12
    game.save()
    bot.send_message(message.chat.id, "Привет, давай познакомимся, напиши свое имя")
    bot.register_next_step_handler(message, get_name)


def get_name(message: telebot.types.Message):
    user = User.objects.get(tg_id=message.from_user.id)
    user.name = message.text
    user.save()
    bot.send_message(message.chat.id, "Отлично, теперь фамилию")
    bot.register_next_step_handler(message, get_surname)


def get_surname(message: telebot.types.Message):
    user = User.objects.get(tg_id=message.from_user.id)
    user.surname = message.text
    user.save()
    flag = True
    keyboard = telebot.types.InlineKeyboardMarkup()
    if flag:
        key1 = telebot.types.InlineKeyboardButton(text='МИЭМ', callback_data='МИЭМ')
        keyboard.add(key1)
        key2 = telebot.types.InlineKeyboardButton(text='Покровка', callback_data='Покровка')
        keyboard.add(key2)
        bot.send_message(message.chat.id, text='Выбери кампус', reply_markup=keyboard)
    else:
        user.campus = 'Старая Басманная'
        user.save()
        keyboard = telebot.types.InlineKeyboardMarkup()
        key2 = telebot.types.InlineKeyboardButton(text='Начать', callback_data='Начать')
        keyboard.add(key2)
        bot.send_message(message.chat.id, f'Имя: {user.name}\nФамилия: {user.surname}\n', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call: telebot.types.CallbackQuery):
    if call.data == 'МИЭМ' or call.data == 'Покровка':
        user = User.objects.get(tg_id=call.from_user.id)
        user.campus = call.data
        user.save()
        keyboard = telebot.types.InlineKeyboardMarkup()
        key1 = telebot.types.InlineKeyboardButton(text='Изменить кампус', callback_data='Изменить кампус')
        key2 = telebot.types.InlineKeyboardButton(text='Начать', callback_data='Начать')
        keyboard.add(key2)
        keyboard.add(key1)
        bot.send_message(call.message.chat.id, f'Имя: {user.name}\nФамилия: {user.surname}\nКампус: {user.campus}', reply_markup=keyboard)
    elif call.data == 'Изменить кампус':
        keyboard = telebot.types.InlineKeyboardMarkup()
        key1 = telebot.types.InlineKeyboardButton(text='МИЭМ', callback_data='МИЭМ')
        keyboard.add(key1)
        key2 = telebot.types.InlineKeyboardButton(text='Покровка', callback_data='Покровка')
        keyboard.add(key2)
        bot.send_message(call.message.chat.id, text='Выбери кампус', reply_markup=keyboard)
    elif call.data == 'Начать' or call.data == 'Продолжить':
        user = User.objects.get(tg_id=call.from_user.id)
        question = Question.objects.get(number=(user.start-1+user.stage)%12+1)
        keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
        keyboard.row('Пропустить')
        keyboard.row('Счёт')
        if user.stage == 0:
            if user.campus == 'МИЭМ':
                bot.send_message(call.message.chat.id, f'Чтобы получить первый вопрос, {question.place_miem}  и отсканируй его', reply_markup=keyboard)
            elif user.campus == 'Покровка':
                bot.send_message(call.message.chat.id, f'Чтобы получить первый вопрос, {question.place_pokrovka} и отсканируй его', reply_markup=keyboard)
            elif user.campus == 'Старая Басманная':
                bot.send_message(call.message.chat.id, f'Чтобы получить первый вопрос, {question.place_basmach} и отсканируй его', reply_markup=keyboard)
        else:
            if user.campus == 'МИЭМ':
                bot.send_message(call.message.chat.id, f'Чтобы получить следующий вопрос, {question.place_miem} и отсканируй его', reply_markup=keyboard)
            elif user.campus == 'Покровка':
                bot.send_message(call.message.chat.id, f'Чтобы получить следующий вопрос, {question.place_pokrovka} и отсканируй его', reply_markup=keyboard)
            elif user.campus == 'Старая Басманная':
                bot.send_message(call.message.chat.id, f'Чтобы получить следующий вопрос, {question.place_basmach} и отсканируй его', reply_markup=keyboard)
        bot.register_next_step_handler(call.message, play)


def play(message: telebot.types.Message):
    user = User.objects.get(tg_id=message.from_user.id)
    question = Question.objects.get(number=(user.start-1+user.stage)%12+1)

    if message.text == 'Счёт':
        bot.send_message(message.chat.id, f'Твой счет: {user.score}\nОсталось вопросов: {12-user.stage}')
    elif message.text == '/stop':
        bot.send_message(message.chat.id, 'Ты вышел из игры')
        return
    elif message.text == 'Пропустить':
        user.stage += 1
        user.tries = 0
        user.save()
        user = User.objects.get(tg_id=message.from_user.id)
        question = Question.objects.get(number=(user.start-1+user.stage)%12+1)
        if user.stage >= 12:
            if int(user.wave) != int(Game.objects.all().values('wave')[0]['wave']):
                bot.send_message(message.chat.id, f'К сожалению уже другая волна\nТвой счет: {user.score}')
                return
            win = 10
            if user.score >= win:
                #если количество людей с score>10 на одном месте <= 8 и в одну волну, то выиграл иначе призов нет
                if len(User.objects.filter(score__gte=win, campus=user.campus, wave=user.wave)) <= 8:
                    bot.send_message(message.chat.id, f'Ты выиграл!\nТвой счет: {user.score}')
                    return
                else:
                    bot.send_message(message.chat.id, f'Призы закончились(\nТвой счет: {user.score}')
                    return
            else:
                bot.send_message(message.chat.id, f'Ты проиграл!\nТвой счет: {user.score}')
                return
    elif message.text.lower() == question.answer.lower():
        user.score += 1
        user.stage += 1
        user.tries = 0
        user.save()
        user = User.objects.get(tg_id=message.from_user.id)
        question = Question.objects.get(number=(user.start-1+user.stage)%12+1)
        if user.stage >= 12:
            if int(user.wave) != int(Game.objects.all().values('wave')[0]['wave']):
                bot.send_message(message.chat.id, f'К сожалению уже другая волна\nТвой счет: {user.score}')
                return
            win = 10
            if user.score >= win:
                #если количество людей с score>10 на одном месте <= 8 и в одну волну, то выиграл иначе призов нет
                if len(User.objects.filter(score__gte=win, campus=user.campus, wave=user.wave)) <= 8:
                    bot.send_message(message.chat.id, f'Ты выиграл!\nТвой счет: {user.score}')
                    return
                else:
                    bot.send_message(message.chat.id, f'Призы закончились(\nТвой счет: {user.score}')
                    return
            else:
                bot.send_message(message.chat.id, f'Ты проиграл!\nТвой счет: {user.score}')
                return
        bot.send_message(message.chat.id, f'Правильно, следующий вопрос..')
    elif message.text.lower() != question.answer.lower() and message.text != 'Начать':
        user.tries += 1
        user.save()
        user = User.objects.get(tg_id=message.from_user.id)
        if user.tries == 2:
            user.stage += 1
            user.tries = 0
            user.save()
            user = User.objects.get(tg_id=message.from_user.id)
            question = Question.objects.get(number=(user.start-1+user.stage)%12+1)
            if user.stage >= 12:
                if int(user.wave) != int(Game.objects.all().values('wave')[0]['wave']):
                    bot.send_message(message.chat.id, f'К сожалению уже другая волна\nТвой счет: {user.score}')
                    return
                win = 10
                if user.score >= win:
                    #если количество людей с score>10 на одном месте <= 8 и в одну волну, то выиграл иначе призов нет
                    if len(User.objects.filter(score__gte=win, campus=user.campus, wave=user.wave)) <= 8:
                        bot.send_message(message.chat.id, f'Ты выиграл!\nТвой счет: {user.score}')
                        return
                    else:
                        bot.send_message(message.chat.id, f'Призы закончились(\nТвой счет: {user.score}')
                        return
                else:
                    bot.send_message(message.chat.id, f'Ты проиграл!\nТвой счет: {user.score}')
                    return
            bot.send_message(message.chat.id, f'Неправильно, следующий вопрос..')
        elif user.tries == 1:
            bot.send_message(message.chat.id, f'Неправильно, попробуй еще раз.')
    
    keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    keyboard.row('Пропустить')
    keyboard.row('Счёт')

    if user.stage == 0:
        if user.campus == 'МИЭМ':
            bot.send_message(message.chat.id, f'Чтобы получить первый вопрос, {question.place_miem}  и отсканируй его', reply_markup=keyboard)
        elif user.campus == 'Покровка':
            bot.send_message(message.chat.id, f'Чтобы получить первый вопрос, {question.place_pokrovka} и отсканируй его', reply_markup=keyboard)
        elif user.campus == 'Старая Басманная':
            bot.send_message(message.chat.id, f'Чтобы получить первый вопрос, {question.place_basmach} и отсканируй его', reply_markup=keyboard)
    else:
        if user.campus == 'МИЭМ':
            bot.send_message(message.chat.id, f'Чтобы получить следующий вопрос, {question.place_miem} и отсканируй его', reply_markup=keyboard)
        elif user.campus == 'Покровка':
            bot.send_message(message.chat.id, f'Чтобы получить следующий вопрос, {question.place_pokrovka} и отсканируй его', reply_markup=keyboard)
        elif user.campus == 'Старая Басманная':
            bot.send_message(message.chat.id, f'Чтобы получить следующий вопрос, {question.place_basmach} и отсканируй его', reply_markup=keyboard)
    bot.register_next_step_handler(message, play)