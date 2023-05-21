import io
import re
import os
import csv
import telebot
import pymysql.cursors
import traceback
from telebot import apihelper
import pytz as ptz
from natasha import Doc, MorphVocab, Segmenter, NewsMorphTagger, NewsEmbedding
from datetime import datetime as dt
from data import config


class Porter:
    PERFECTIVEGROUND = re.compile(u"((ив|ивши|ившись|ыв|ывши|ывшись)|((?<=[ая])(в|вши|вшись)))$")
    REFLEXIVE = re.compile(u"(с[яь])$")
    ADJECTIVE = re.compile(u"(ее|ие|ые|ое|ими|ыми|ей|ий|ый|ой|ем|им|ым|ом|его|ого|ему|ому|их|ых|ую|юю|ая|яя|ою|ею)$")
    PARTICIPLE = re.compile(u"((ивш|ывш|ующ)|((?<=[ая])(ем|нн|вш|ющ|щ)))$")
    VERB = re.compile(
        u"((ила|ыла|ена|ейте|уйте|ите|или|ыли|ей|уй|ил|ыл|им|ым|ен|ило|ыло|ено|ят|ует|уют|ит|ыт|ены|ить|ыть|ишь|ую|ю)|((?<=[ая])(ла|на|ете|йте|ли|й|л|ем|н|ло|но|ет|ют|ны|ть|ешь|нно)))$")
    NOUN = re.compile(
        u"(а|ев|ов|ие|ье|е|иями|ями|ами|еи|ии|и|ией|ей|ой|ий|й|иям|ям|ием|ем|ам|ом|о|у|ах|иях|ях|ы|ь|ию|ью|ю|ия|ья|я)$")
    RVRE = re.compile(u"^(.*?[аеиоуыэюя])(.*)$")
    DERIVATIONAL = re.compile(u".*[^аеиоуыэюя]+[аеиоуыэюя].*ость?$")
    DER = re.compile(u"ость?$")
    SUPERLATIVE = re.compile(u"(ейше|ейш)$")
    I = re.compile(u"и$")
    P = re.compile(u"ь$")
    NN = re.compile(u"нн$")

    def stem(word):
        word = word.lower()
        word = word.replace(u'ё', u'е')
        m = re.match(Porter.RVRE, word)
        if m and m.groups():
            pre = m.group(1)
            rv = m.group(2)
            temp = Porter.PERFECTIVEGROUND.sub('', rv, 1)
            if temp == rv:
                rv = Porter.REFLEXIVE.sub('', rv, 1)
                temp = Porter.ADJECTIVE.sub('', rv, 1)
                if temp != rv:
                    rv = temp
                    rv = Porter.PARTICIPLE.sub('', rv, 1)
                else:
                    temp = Porter.VERB.sub('', rv, 1)
                    if temp == rv:
                        rv = Porter.NOUN.sub('', rv, 1)
                    else:
                        rv = temp
            else:
                rv = temp

            rv = Porter.I.sub('', rv, 1)

            if re.match(Porter.DERIVATIONAL, rv):
                rv = Porter.DER.sub('', rv, 1)

            temp = Porter.P.sub('', rv, 1)
            if temp == rv:
                rv = Porter.SUPERLATIVE.sub('', rv, 1)
                rv = Porter.NN.sub(u'н', rv, 1)
            else:
                rv = temp
            word = pre + rv
        return word

    stem = staticmethod(stem)


def read_file(file_name, split_symbol="\n"):
    with open(file_name, 'r') as file:
        return file.read().split(split_symbol)


def get_time(tz: str = 'Europe/Moscow', form: str = '%d-%m-%Y %H:%M:%S', strp: bool = False):
    if strp:
        if tz:
            return dt.strptime(dt.now(ptz.timezone(tz)).strftime(form), form)
        else:
            return dt.strptime(dt.now().strftime(form), form)
    else:
        if tz:
            return dt.now(ptz.timezone(tz)).strftime(form)
        else:
            return dt.now().strftime(form)


def handle_exception():
    print("-" * 120)
    string_manager = io.StringIO()
    traceback.print_exc(file=string_manager)
    error = string_manager.getvalue()
    print(error)
    print("-" * 120)


class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        handle_exception()
        return True


bot = telebot.TeleBot(config.telegram_token, exception_handler=ExceptionHandler())

work_dir = os.getcwd()
data_dir = os.path.join(work_dir, "data")
temp_dir = os.path.join(work_dir, "temp")

bot.set_my_commands([
    telebot.types.BotCommand("/menu", "Вызвать меню бота"),
    telebot.types.BotCommand("/info_plant", "Получить информацию о растениях"),
])


def gen_markup(buttons_list, buttons_dest="auto", markup_type="Reply", callback_list=None):
    def sort_buttons(markup_, buttons, callback, buttons_dest_):
        count = 0
        n = len(buttons)
        while True:
            if n - 3 >= 0 and buttons_dest_ == 3:
                if callback:
                    buttons_1 = telebot.types.InlineKeyboardButton(buttons[count],
                                                                   callback_data=callback[count])
                    buttons_2 = telebot.types.InlineKeyboardButton(buttons[count + 1],
                                                                   callback_data=callback[count + 1])
                    buttons_3 = telebot.types.InlineKeyboardButton(buttons[count + 2],
                                                                   callback_data=callback[count + 2])
                else:
                    buttons_1 = telebot.types.InlineKeyboardButton(buttons[count])
                    buttons_2 = telebot.types.InlineKeyboardButton(buttons[count + 1])
                    buttons_3 = telebot.types.InlineKeyboardButton(buttons[count + 2])

                markup_.add(buttons_1, buttons_2, buttons_3)
                count += 3
                n -= 3
            elif n - 2 >= 0 and buttons_dest_ >= 2:
                if callback:
                    buttons_1 = telebot.types.InlineKeyboardButton(buttons[count],
                                                                   callback_data=callback[count])
                    buttons_2 = telebot.types.InlineKeyboardButton(buttons[count + 1],
                                                                   callback_data=callback[count + 1])
                else:
                    buttons_1 = telebot.types.InlineKeyboardButton(buttons[count])
                    buttons_2 = telebot.types.InlineKeyboardButton(buttons[count + 1])
                markup_.add(buttons_1, buttons_2)
                count += 2
                n -= 2
            elif n - 1 >= 0 and buttons_dest_ >= 1:
                if callback:
                    buttons_1 = telebot.types.InlineKeyboardButton(buttons[count],
                                                                   callback_data=callback[count])
                else:
                    buttons_1 = telebot.types.InlineKeyboardButton(buttons[count])
                markup_.add(buttons_1)
                count += 1
                n -= 1
            else:
                break
        return markup_

    markup = ""
    if markup_type == "Reply":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        if buttons_dest == "auto":
            for button in buttons_list:
                markup.add(button)
        elif buttons_dest == "3":
            markup = sort_buttons(markup, buttons_list, callback_list, int(buttons_dest))
    elif markup_type == "Inline":
        markup = telebot.types.InlineKeyboardMarkup()
        if buttons_dest == "auto":
            for i in range(len(buttons_list)):
                markup.add(telebot.types.InlineKeyboardButton(buttons_list[i], callback_data=callback_list[i]))
        elif int(buttons_dest) < 4:
            markup = sort_buttons(markup, buttons_list, callback_list, int(buttons_dest))

    return markup


def commands(message):
    chat_id = message["chat_id"]
    text = message["text"]
    commands_text = "Для вызова меню бота /menu\n" \
                    "Я могу предоставить топ 3 растений по параметрам.\n" \
                    "Вызови /get_info_plant_help для большей информации.\n" \
                    "/commands для вызова этого текста."
    if text == "/start":
        commands_text = "Привет, добро пожаловать в Plant Info Bot.\n" + commands_text
    if text == "/commands" or text == "/start":
        bot.send_message(chat_id, commands_text)
    return commands_text


def about_us(message):
    chat_id = message["chat_id"]
    text = message["text"]
    about_us_text = "Благодарим вас за использование нашего проекта!\n" \
                    "Проект создан командой 'Don't even try'.\n" \
                    "На хакатоне в 2023 году\n" \
                    "Подробнее о проекте\n" \
                    "                   |\n" \
                    "                   V\n" \
                    "https://github.com/Zapzatron/hackaton_solution/tree/main"
    if text == "/about_us":
        bot.send_message(chat_id, about_us_text)
    return about_us_text


def get_info_plant_help(message):
    chat_id = message["chat_id"]
    text = message["text"]
    commands_text = "Как получить топ 3 растений по параметрам?\n" \
                    "1. Вызови /info_plant\n" \
                    "2. Введите параметры, по которым будет производиться поиск (тип почвы, город)\n" \
                    "3. Подождать некоторое время\n" \
                    "/get_info_plant_help для вызова этого текста."
    if text == "/get_info_plant_help":
        bot.send_message(chat_id, commands_text)
    return commands_text


def gpt_mindsdb(prompt, model):
    sql = f"SELECT response FROM mindsdb.{model} WHERE text='{prompt}'"

    connection = pymysql.connect(host='cloud.mindsdb.com',
                                 user=config.mindsdb_login,
                                 password=config.mindsdb_password,
                                 db='mindsdb',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()
    cursor.execute(sql)
    response = cursor.fetchone()
    content = response['response']
    return content


def gpt_use(text):
    model = "gpt4"
    text_new = text.replace("'", '"')
    text_new = text_new.replace("\n", "/nl")
    text_new = text_new.replace("\\", "/")
    # print(text)
    try:
        return gpt_mindsdb(text_new, model)
    except (pymysql.err.OperationalError, pymysql.err.ProgrammingError):
        return gpt_use(text)


def get_areal(text, name=""):
    print("get_areal()")
    # text = f"Выдели из текста только ареалы: {text}"
    # text = f"Напиши из текста ареалы произрастания, если в тексте нет ответа, " \
    #        f"то дополни информацию самостоятельно. Перечисляй их через запятую: {text}"
    if name:
        text = f"Напиши из текста ареалы произрастания, если в тексте нет ответа, " \
               f"то дополни информацию самостоятельно. Если текста после знака ':' нет, " \
               f"то найди информацию об ареалах произрастания для {name} самостоятельно." \
               f" Перечисляй их через запятую: {text}"
    else:
        text = f"Напиши из текста ареалы произрастания, если в тексте нет ответа, " \
               f"то дополни информацию самостоятельно. Если текста после знака ':' нет, " \
               f"то найди информацию самостоятельно." \
               f" Перечисляй их через запятую: {text}"
    return gpt_use(text)
    # return "None"


def get_subject(text):
    print("get_subject()")
    # text = f"<promt>: {text}"
    text = f"Напиши из текста все субъекты РФ, где растет данное растение, по областям. " \
           f"Если есть какая-то часть территории, то распиши все субъекты входящие в неё. " \
           f"Больше ничего не пиши, только области!. Если оно не растет в РФ, то так и напиши. " \
           f"Если в тексте нет ответа, то дополни информацию самостоятельно. Перечисляй их через запятую: {text}"
    return gpt_use(text)
    # return "None"


def get_soil(text):
    print("get_soil()")
    text = f"Какой тип почвы необходим для {text}?"
    return gpt_use(text)
    # return "None"


def is_in_red_book(text):
    print("is_in_red_book()")
    text = f"Находится ли {text} в красной книге РФ? (Ответ да или нет)"
    return gpt_use(text)
    # return "None"


def get_plant_period(text):
    print("get_plant_period()")
    text = f"Какой период посева для растения {text}?"
    return gpt_use(text)
    # return "None"


def get_collect_period(text):
    print("get_collect_period()")
    text = f"Какой период сбора для растения {text}?"
    return gpt_use(text)
    # return "None"


def get_content_drugs(text):
    print("get_content_drugs()")
    # text = f"<promt>: {text}"
    text = rf"Ответь на следующие вопросы для растения в предоставленном формате ответа: {text}\n" \
           rf"Формат ответа: Аспирин 10%, Мукалтин 50%"
    return gpt_use(text)
    # return "None"


def count_soil(text, word_to_check):
    count = 0
    split_text = text.split()
    for word in split_text:
        if word_to_check.lower() in word.lower():
            count += 1
    return count


def get_dict_flowers(file, new_flower_token):
    # FILE = "test.txt"
    # NEW_FLOWER_TOKEN = "\\nfl"

    flower_dict = {}
    working_with_flower = False
    with open(file, encoding="utf-8") as f:
        temp_dict = {}
        for idx, line in enumerate(f):
            line = line.rstrip("\n ")

            if line == new_flower_token:
                working_with_flower = True
                if temp_dict:
                    flower_dict.update({flower_name: temp_dict.copy()})
                    temp_dict.clear()
                continue

            if working_with_flower:
                flower_name = " ".join(line.split()[:-1])
                working_with_flower = False
                continue

            k, v = line.split(".", maxsplit=1)
            temp_dict.update({k: v.strip()})
    return flower_dict


columns = ["Название культуры", "Ареалы", "Субъект", "Тип почвы", "Наличие в красной книге",
           "Период посева", "Период сбора", "Содержание в лекарствах"]

# letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# flowers_dict = {}


def csv_maker():
    flower_dict = get_dict_flowers(f"{data_dir}/db.txt", "\\nfl")
    with open(f"{data_dir}/data.csv", "w+", encoding="utf-8") as f:
        # columns = ["Название культуры", "Ареалы", "Субъект", "Тип почвы", "Наличие в красной книге",
        #            "Период посева", "Период сбора", "Содержание в лекарствах"]
        wr = csv.DictWriter(f, fieldnames=columns)
        wr.writeheader()
        for flower in flower_dict:
            print(flower)
            print(get_time())
            wr.writerow({columns[0]: flower, columns[1]: get_areal(flower_dict[flower].get("Ареал")), columns[2]: get_subject(flower_dict[flower].get("Экология")),
                         columns[3]: get_soil(flower_dict[flower].get("Экология")), columns[4]: is_in_red_book(flower), columns[5]: get_plant_period(flower),
                         columns[6]: get_collect_period(flower), columns[7]: get_content_drugs(flower)})
            print(get_time())
            print()


def get_info_plant(message):
    # print("get_info_plant()")
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text
    # print(text)
    # # print(text)
    # tokens = read_file("data/gpt-3.ini")
    # model = "gpt-3.5-turbo"
    # system_message = "Ты GPT-3, большая языковая модель созданная OpenAI, отвечающая кратко точно по теме."
    # temperature = 0.5
    # max_tokens = 2000
    #
    # if tokens[-1] == "":
    #     tokens.pop(-1)
    #
    # text = r"Найди названия лекарственных культур по следующим параметрам\n" \
    #        rf"1. Тип почвы {text}"
    # response_text = ""
    # restart = True
    # count = 0
    # while restart:
    #     if count < len(tokens):
    #         try:
    #             response_text = gpt_openai(tokens[count][:51], model, text, system_message, temperature, max_tokens)
    #             count += 1
    #             restart = False
    #         except (openai.error.AuthenticationError, openai.error.RateLimitError):
    #             tokens.pop(count)
    #     else:
    #         restart = False
    # # print(response_text)
    # bot.send_message(chat_id, response_text)
    # temp_user = f"{temp_dir}/{user_id}/info_plant"
    # print(temp_user)
    # if not os.path.exists(temp_user):
    #     os.makedirs(temp_user)
    #
    # info_file = f"{temp_user}/info_plant.txt"
    #
    # if os.path.exists(info_file):
    #     try:
    #         os.remove(info_file)
    #     except OSError:
    #         pass
    #
    # with open(info_file, "w", encoding="utf-8") as f:
    #     f.write("")
    #
    # with open("data/Атлас.txt", 'r', encoding="utf-8") as data_file:
    #     with open(info_file, "r+", encoding="utf-8") as res_file:
    #         data = data_file.readlines()
    #         # print(data)
    #         off_new = False
    #         need_info = ""
    #         for line in data:
    #             line = line.rstrip("\n")
    #             if not line:
    #                 break
    #             if line == text.split(" ")[0]:
    #                 # print(line)
    #                 need_info += line.strip()
    #                 res_file.write(line.strip().replace(r"\nt", "\n"))
    #                 off_new = True
    #             elif off_new and line == r"\nfl":
    #                 break
    #             elif off_new:
    #                 line = line.strip()
    #                 need_info += line.strip()
    #                 res_file.write(line.strip().replace(r"\nt", "\n"))
    #                 # print(line)

    # print(need_info.replace(r"\nt", "\n"))
    # bot.send_document(chat_id, open(info_file, 'rb'))

    # FILE = f"{data_dir}/db_2.txt"
    # NEW_FLOWER_TOKEN = "\\nfl"
    #
    # flower_dict = {}
    # working_with_flower = False
    # with open(FILE, encoding="utf-8") as f:
    #     temp_dict = {}
    #     for idx, line in enumerate(f):
    #         line = line.rstrip("\n ")
    #
    #         if line == NEW_FLOWER_TOKEN:
    #             working_with_flower = True
    #             if temp_dict:
    #                 flower_dict.update({flower_name: temp_dict.copy()})
    #                 temp_dict.clear()
    #             continue
    #
    #         if working_with_flower:
    #             flower_name = " ".join(line.split()[:-1])
    #             working_with_flower = False
    #             continue
    #
    #         k, v = line.split(".", maxsplit=1)
    #         temp_dict.update({k: v.strip()})

    # print(flower_dict)
    # flower_dict = get_dict_flowers()
    # with open(f"{data_dir}/data.csv", "w+", encoding="utf-8") as f:
    #     # columns = ["Название культуры", "Ареалы", "Субъект", "Тип почвы", "Наличие в красной книге",
    #     #            "Период посева", "Период сбора", "Содержание в лекарствах"]
    #     wr = csv.DictWriter(f, fieldnames=columns)
    #     wr.writeheader()
    #     for flower in flower_dict:
    #         print(flower)
    #         print(get_time())
    #         areal = ""
    #         try:
    #             areal = get_areal(flower_dict[flower]["Ареал"])
    #         except KeyError:
    #             areal = get_areal()
    #         wr.writerow({columns[0]: flower, columns[1]: get_areal(flower_dict[flower]["Ареал"]), columns[2]: get_subject(flower_dict[flower]["Экология"]),
    #                      columns[3]: get_soil(flower_dict[flower]["Экология"]), columns[4]: is_in_red_book(flower), columns[5]: get_plant_period(flower),
    #                      columns[6]: get_collect_period(flower), columns[7]: get_content_drugs(flower)})
    #         print(get_time())
    #         print()

    # flower_dict = get_dict_flowers(f"{data_dir}/Атлас.txt", "\\nfl")
    flower_dict = get_dict_flowers(f"{data_dir}/db.txt", "\\nfl")
    flowers_soil = {}
    split_text = text.split(", ")
    # mrvc = MorphVocab()
    # sgmt = Segmenter()
    # emb = NewsEmbedding()
    # nmt = NewsMorphTagger(emb)
    # doc_list = [Doc(el) for el in split_text]

    # for doc in doc_list:
    #     doc.segment(sgmt)
    #     doc.tag_morph(nmt)
    #     for token in doc.tokens:
    #         token.lemmatize(mrvc)
    split_text = [Porter.stem(el) for el in split_text]
    # print(split_text)
    for i in range(len(split_text)):
        for flower_name, value in flower_dict.items():
            if flower_name not in flowers_soil:
                flowers_soil[flower_name] = 0
            for term in value:
                # print(flowers_soil)
                flowers_soil[flower_name] = flowers_soil[flower_name] + count_soil(value[term], split_text[i])

    # print(flowers_soil)
    n = 3
    sorted_dict = {k: v for k, v in sorted(flowers_soil.items(), key=lambda item: item[1])}
    # top_text = [f"Топ {n} растений по заданным критериям."]
    top_text = f"Топ {n} растений по заданным критериям:"
    print(get_time())
    for i in range(n):
        # top_text.append(sorted_dict.popitem()[0])
        name = sorted_dict.popitem()[0]
        top_text = top_text + "\n" + f"{i + 1}." + name + "\n" + get_areal(flower_dict[name].get("Ареал"), name)

        # + "\n" + f"{i + 1}. " + sorted_dict.popitem()[0]
    print(get_time())
    # print(top_text)
    bot.send_message(chat_id, top_text)




    # with open("data/Атлас.txt", 'r', encoding="utf-8") as data_file:
    #     data = data_file.readlines()
    #     # print(data)
    #     off_new = False
    #     need_info = ""
    #     flower_name = ""
    #     for line in data:
    #         line = line.rstrip("\n")
    #         if not line:
    #             break
    #         # if line == :
    #             # print(line)
    #             # need_info += line.strip()
    #             # off_new = True
    #         if line[:9] == "Описание.":
    #             flowers_dict[flower_name]["Описание"] = line[9:]
    #         elif line[:6] == "Ареал.":
    #             flowers_dict[flower_name]["Ареал"] = line[6:]
    #         elif line[:9] == "Экология.":
    #             flowers_dict[flower_name]["Экология"] = line[9:]
    #         elif line[:8] == "Ресурсы.":
    #             flowers_dict[flower_name]["Ресурсы"] = line[8:]
    #         elif line[:17] == "Химический состав.":
    #             flowers_dict[flower_name]["Химический состав"] = line[17:]
    #         elif line[:5] == "Сырье.":
    #             flowers_dict[flower_name]["Сырье"] = line[5:]
    #         # elif line[:] == "Фармакологические свойства."
    #         elif line.isupper():
    #             flower_name = line
    #             flowers_dict[flower_name] = {}
    #         elif off_new and line == r"\nfl":
    #             break
    #         elif off_new:
    #             line = line.strip()
    #             need_info += line.strip()

    # bot.send_document(chat_id, open(f"{data_dir}/data.csv", 'rb'))
    # print()
    print()


def menu(message, first=True):
    buttons_list = ["Инфо о растении ", "Команды 🔍", "О нас ℹ︎"]
    callback_list = ["/get_info_plant_help_c", "/commands_c", "/about_us_c"]
    markup = gen_markup(buttons_list, buttons_dest="3", markup_type="Inline", callback_list=callback_list)
    button_text = "Выбери нужное"
    chat_id = message["chat_id"]
    message_id = message["message_id"]
    if first:
        bot.send_message(chat_id, button_text, reply_markup=markup)
    else:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=button_text, reply_markup=markup)


@bot.callback_query_handler(func=lambda message: True)
def callback_buttons(message):
    def button_message(message_, button_text_):
        chat_id = message_["chat_id"]
        message_id = message_["message_id"]
        bot.answer_callback_query(message_["all_message_id"])
        buttons_list = ["Назад 🔙"]
        callback_list = ["/back_с"]
        markup = gen_markup(buttons_list, markup_type="Inline", callback_list=callback_list)
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=button_text_, reply_markup=markup)

    text = message.data

    message_2 = {"chat_id": message.message.chat.id,
                 "message_id": message.message.message_id,
                 "all_message_id": message.id,
                 "user_id": message.message.chat.id,
                 "first_name": message.message.chat.first_name,
                 "last_name": message.message.chat.last_name,
                 "text": text}

    if text == "/commands_c":
        button_message(message_2, commands(message_2))
    elif text == "/about_us_c":
        button_message(message_2, about_us(message_2))
    elif text == "/get_info_plant_help_c":
        button_message(message_2, get_info_plant_help(message_2))
    elif text == "/back_с":
        bot.answer_callback_query(message.id)
        menu(message_2, first=False)


user_state = {}
actions = ["/info_plant", ]
actions_text = {
    "/info_plant": "Введите параметры, по которым будет производиться поиск (тип почвы, город)",
}


@bot.message_handler(content_types=["text"])
def get_command_text(message):
    user_id = message.from_user.id
    text = message.text

    message_2 = {"chat_id": message.chat.id,
                 "message_id": message.id,
                 "user_id": user_id,
                 "first_name": message.from_user.first_name,
                 "last_name": message.from_user.last_name,
                 "text": text}

    if message.content_type == "text" and text == "/menu":
        menu(message_2)
    elif message.content_type == "text" and text[0] == "/" and text in actions:
        user_state[user_id] = (text, None)
        if text in actions_text:
            bot.reply_to(message, actions_text[text])
    elif message.content_type == "text" and text[0] == "/" and text not in actions:
        if text == "/commands" or text == "/start":
            commands(message_2)
        elif text == "/about_us":
            about_us(message_2)
        elif text == "/get_info_plant_help":
            get_info_plant_help(message_2)
        elif text == "/csv_maker_secret":
            csv_maker()

    elif message.content_type == "text" and text[0] != "/" and user_id in user_state:
        if user_state[user_id][0] == "/info_plant":
            get_info_plant(message)


if __name__ == "__main__":
    while True:
        try:
            print("Бот запущен :)")
            apihelper.RETRY_ON_ERROR = True
            bot.polling(logger_level=None)
        except Exception:
            handle_exception()
