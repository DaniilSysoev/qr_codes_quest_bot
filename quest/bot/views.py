from django.shortcuts import HttpResponse
import telebot
from django.conf import settings
from .models import User, Question, Game
import os
from django.views.decorators.csrf import csrf_exempt


bot = telebot.TeleBot(settings.BOT_TOKEN)
# https://api.telegram.org/bot6180293008:AAGqnW0xsH8jfx9HqZjAp24WR-H7Kbb-j2k/setWebhook?url=https://1452-217-151-229-99.ngrok-free.app
# https://api.telegram.org/bot5813570276:AAHVVgjcZZzmYr0Vrb-X9DXq-WHsrsXqLdo/setWebhook?url=https://ec6c-217-151-229-99.ngrok-free.app

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
        if user.stage < 12:
            keyboard = telebot.types.InlineKeyboardMarkup()
            key1 = telebot.types.InlineKeyboardButton(text='Продолжить', callback_data='Продолжить')
            keyboard.add(key1)
            bot.send_message(message.chat.id, f"""Кажется, мы с тобой уже знакомы, и ты уже начал проходить мой квест
Твой счёт на данный момент: {user.score}""", reply_markup=keyboard)
            return
        bot.send_message(message.chat.id, f"""Я вижу, что ты уже завершил прохождение моего квеста.
Возможности пройти его заново нет
Твой результат: {user.score}""")
        return
    else:
        User.objects.create(tg_id=message.from_user.id, start=Game.objects.all().values('start_question')[0]['start_question'], stage=0, wave=Game.objects.all().values('wave')[0]['wave'])
        bot.send_message(message.chat.id, """Приветствую тебя, дорогой студент!
Я — AI-навигатор, и я рад, что тебе интересно погрузиться в мир искусственного интеллекта. Я помогу тебе в этом!

Тебе предстоит ответить на несколько моих вопросов. Если быть точным, то их будет 12.
Но не расслабляйся! Я не буду тебе сразу задавать вопросы, а ты должен будешь найти их самостоятельно. Я лишь буду подсказывать тебе место, куда тебе идти.
После подсказки я буду ждать от тебя ответ.
Я понимаю, что вы, люди, склонны делать ошибки, поэтому у тебя будет целых две попытки ответить на вопрос)

Краткая инструкция по эксплуатации:
▪️Если ты во время прохождения моего квеста захочешь узнать свои текущие результаты, то тебе для этого будет доступна кнопка "Счёт"
▪️Если на какой-то вопрос ты не захочешь отвечать, то тебе для этого будет доступна кнопка "Пропустить"
▪️Если ты захочешь прекратить прохождение моего квеста, то для этого тебя нужно будет ввести команду /stop

Прохождение квеста я буду считать успешным, если ты верно ответишь на 10 моих вопросов из 12.
За успешное прохождение ты можешь получить приз, поэтому поторопись, ведь их ограниченное количество!""")
    game = Game.objects.all()[0]
    game.start_question = game.start_question - 1 if game.start_question > 1 else 12
    game.save()
    bot.send_message(message.chat.id, """Я представился, теперь твоя очередь 🫵
Напиши своё имя""")
    bot.register_next_step_handler(message, get_name)


def get_name(message: telebot.types.Message):
    user = User.objects.get(tg_id=message.from_user.id)
    user.name = message.text
    user.save()
    bot.send_message(message.chat.id, """Теперь я знаю о тебе чуть больше, но мне мало 🙃
Напиши свою фамилию""")
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
        bot.send_message(message.chat.id, text="""Ну и последнее, что я хочу о тебе знать...
Выбери корпус, в котором ты сейчас находишься""", reply_markup=keyboard)
    else:
        user.campus = 'Старая Басманная'
        user.save()
        keyboard = telebot.types.InlineKeyboardMarkup()
        key2 = telebot.types.InlineKeyboardButton(text='Начать', callback_data='Начать')
        keyboard.add(key2)
        bot.send_message(message.chat.id, f"""Итак, давай объединим то, что я о тебе узнал
Тебя зовут {user.name}
Твоя фамилия {user.surname}

Ты готов приступить к прохождению моего квеста?""", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call: telebot.types.CallbackQuery):
    if call.data == 'МИЭМ' or call.data == 'Покровка':
        user = User.objects.get(tg_id=call.from_user.id)
        user.campus = call.data
        user.save()
        keyboard = telebot.types.InlineKeyboardMarkup()
        key1 = telebot.types.InlineKeyboardButton(text='Нет, нужно поменять локацию...', callback_data='Изменить корпус')
        key2 = telebot.types.InlineKeyboardButton(text='Да, давай начнем!', callback_data='Начать')
        keyboard.add(key2)
        keyboard.add(key1)
        bot.send_message(call.message.chat.id, f"""Итак, давай объединим то, что я о тебе узнал
Тебя зовут {user.name}
Твоя фамилия {user.surname}
Твоя локация {user.campus}

Всё верно?""", reply_markup=keyboard)
    elif call.data == 'Изменить корпус':
        keyboard = telebot.types.InlineKeyboardMarkup()
        key1 = telebot.types.InlineKeyboardButton(text='МИЭМ', callback_data='МИЭМ')
        keyboard.add(key1)
        key2 = telebot.types.InlineKeyboardButton(text='Покровка', callback_data='Покровка')
        keyboard.add(key2)
        bot.send_message(call.message.chat.id, text='Выбери корпус', reply_markup=keyboard)
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
        bot.send_message(message.chat.id, f'Твой счёт на данный момент: {user.score}\nКоличество оставшихся вопросов: {12-user.stage}')
    elif message.text == '/stop':
        bot.send_message(message.chat.id, """Прохождение квеста остановлено.
Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
        return
    elif message.text == 'Пропустить':
        user.stage += 1
        user.tries = 0
        user.save()
        user = User.objects.get(tg_id=message.from_user.id)
        question = Question.objects.get(number=(user.start-1+user.stage)%12+1)
        if user.stage >= 12:
            if int(user.wave) != int(Game.objects.all().values('wave')[0]['wave']):
                bot.send_message(message.chat.id, f"""Это был последний вопрос, а значит квест окончен
Твой результат: {user.score}
К сожалению, ты не успел завершить прохождение до окончания своей волны

Надеюсь, что я помог тебе погрузиться в мир искусственного интеллекта и ты узнал что-то новое

Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
                return
            win = 10
            if user.score >= win:
                #если количество людей с score>10 на одном месте <= 8 и в одну волну, то выиграл иначе призов нет
                if len(User.objects.filter(score__gte=win, campus=user.campus, wave=user.wave)) <= 8:
                    bot.send_message(message.chat.id, f"""Поздравляю тебя! Ты успешно прошел мой квест
Твой результат: {user.score}
Подходи за призом туда, где всё началось

Надеюсь, что я помог тебе погрузиться в мир искусственного интеллекта и ты узнал что-то новое

Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
                    return
                else:
                    bot.send_message(message.chat.id, f"""Поздравляю тебя! Ты успешно прошел мой квест
Твой результат: {user.score}
К сожалению, призы уже закончились

Надеюсь, что я помог тебе погрузиться в мир искусственного интеллекта и ты узнал что-то новое

Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
                    return
            else:
                bot.send_message(message.chat.id, f"""Это был последний вопрос, а значит квест окончен
Твой результат: {user.score}
К сожалению, этого недостаточно для получения приза

Надеюсь, что я помог тебе погрузиться в мир искусственного интеллекта и ты узнал что-то новое

Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
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
                bot.send_message(message.chat.id, f"""Это был последний вопрос, а значит квест окончен
Твой результат: {user.score}
К сожалению, ты не успел завершить прохождение до окончания своей волны

Надеюсь, что я помог тебе погрузиться в мир искусственного интеллекта и ты узнал что-то новое

Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
                return
            win = 10
            if user.score >= win:
                #если количество людей с score>10 на одном месте <= 8 и в одну волну, то выиграл иначе призов нет
                if len(User.objects.filter(score__gte=win, campus=user.campus, wave=user.wave)) <= 8:
                    bot.send_message(message.chat.id, f"""Поздравляю тебя! Ты успешно прошел мой квест
Твой результат: {user.score}
Подходи за призом туда, где всё началось

Надеюсь, что я помог тебе погрузиться в мир искусственного интеллекта и ты узнал что-то новое

Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
                    return
                else:
                    bot.send_message(message.chat.id, f"""Поздравляю тебя! Ты успешно прошел мой квест
Твой результат: {user.score}
К сожалению, призы уже закончились

Надеюсь, что я помог тебе погрузиться в мир искусственного интеллекта и ты узнал что-то новое

Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
                    return
            else:
                bot.send_message(message.chat.id, f"""Это был последний вопрос, а значит квест окончен
Твой результат: {user.score}
К сожалению, этого недостаточно для получения приза

Надеюсь, что я помог тебе погрузиться в мир искусственного интеллекта и ты узнал что-то новое

Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
                return
        bot.send_message(message.chat.id, f'Ответ верный, поздравляю!')
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
                    bot.send_message(message.chat.id, f"""Это был последний вопрос, а значит квест окончен
Твой результат: {user.score}
К сожалению, ты не успел завершить прохождение до окончания своей волны

Надеюсь, что я помог тебе погрузиться в мир искусственного интеллекта и ты узнал что-то новое

Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
                    return
                win = 10
                if user.score >= win:
                    #если количество людей с score>10 на одном месте <= 8 и в одну волну, то выиграл иначе призов нет
                    if len(User.objects.filter(score__gte=win, campus=user.campus, wave=user.wave)) <= 8:
                        bot.send_message(message.chat.id, f"""Поздравляю тебя! Ты успешно прошел мой квест
Твой результат: {user.score}
Подходи за призом туда, где всё началось

Надеюсь, что я помог тебе погрузиться в мир искусственного интеллекта и ты узнал что-то новое

Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
                        return
                    else:
                        bot.send_message(message.chat.id, f"""Поздравляю тебя! Ты успешно прошел мой квест
Твой результат: {user.score}
К сожалению, призы уже закончились

Надеюсь, что я помог тебе погрузиться в мир искусственного интеллекта и ты узнал что-то новое

Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
                        return
                else:
                    bot.send_message(message.chat.id, f"""Это был последний вопрос, а значит квест окончен
Твой результат: {user.score}
К сожалению, этого недостаточно для получения приза

Надеюсь, что я помог тебе погрузиться в мир искусственного интеллекта и ты узнал что-то новое

Будем ждать тебя на юбилейном Детективе от Movement "Проект AI-13" 22 или 23 мая!
Подробную информацию ты можешь найти, перейдя по ссылке: 
https://vk.com/wall-212137529_273""")
                    return
            bot.send_message(message.chat.id, f'К сожалению, этот вариант тоже неверный...')
        elif user.tries == 1:
            bot.send_message(message.chat.id, f'К сожалению, ответ неверный\nПопробуй ещё раз!')
    
    keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    keyboard.row('Пропустить')
    keyboard.row('Счёт')

    if user.stage == 0:
        if user.campus == 'МИЭМ':
            bot.send_message(message.chat.id, f'Чтобы получить первый вопрос, {question.place_miem} и отсканируй его', reply_markup=keyboard)
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