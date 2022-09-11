import telebot
from config import tele_token
import os
import csv
import json

bot = telebot.TeleBot(tele_token)

column_str = []
column_json = []
json_exceptions = []
encoding = 'utf-8'


@bot.message_handler(commands=['start', 'старт'])
def start(message):
    print('/start')
    bot.send_message(message.from_user.id, 'Вы запустили бота для обезличивания данных.\n'
                                           'Вам необходимо указать следующие параметры:\n'
                                           '/column_str: в этой команде нужно указать столбцы для '
                                           'обезличивания (Вводить через ";")\n'
                                           '/column_json: в этой команде нужно указать столбцы '
                                           'содержащие json (Вводить через ";")\n'
                                           '/json_exceptions: в этой команде нужно указать параметры json, которые не '
                                           'нужно обезличивать (Вводить через ";")\n'
                                           '/encoding: кодировка, по умолчанию utf-8\n\n'
                                           'После настройки необходимо загрузить csv файл и ввести /deperson')


@bot.message_handler(commands=['column_str'])
def config_column_str(message):
    global column_str
    column_str = message.text[12:].replace(' ', '').split(';')
    bot.send_message(message.from_user.id, f'Вы выбрали: {column_str}')
    print('/config')


@bot.message_handler(commands=['column_json'])
def config_column_json(message):
    global column_json
    column_json = message.text[13:].replace(' ', '').split(';')
    bot.send_message(message.from_user.id, f'Вы выбрали: {column_json}')
    print('/config')


@bot.message_handler(commands=['json_exceptions'])
def config_json_exceptions(message):
    global json_exceptions
    json_exceptions = message.text[16:].replace(' ', '').split(';')
    bot.send_message(message.from_user.id, f'Вы выбрали: {json_exceptions}')
    print('/config')


@bot.message_handler(commands=['encoding'])
def config_encoding(message):
    global encoding
    encoding = message.text[10:].replace(' ', '')
    bot.send_message(message.from_user.id, f'Вы выбрали: {encoding}')
    print('/config')


@bot.message_handler(content_types=['document'])
def handle_docs(message):
    global encoding
    bot.reply_to(message, "Сохраняю файл...")
    try:
        file_type = str(message.document.file_name).split('.')[-1]
        if file_type != 'csv':
            bot.send_message(message.from_user.id, 'Неверный тип файла, должен быть csv!')
            error = 1 / 0
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = 'C:/Python progs/DepersonTelebot/' + message.document.file_name
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
    except:
        bot.send_message(message.from_user.id, 'Файл не сохранен, проверьте файл и повторите попытку позже')
    else:
        bot.send_message(message.from_user.id, 'Файл успешно сохранен')


@bot.message_handler(commands=['deperson'])
def start_deperson(message):
    global column_str, column_json, json_exceptions, encoding
    cur_dir = os.getcwd()
    bot.send_message(message.from_user.id, 'Начинаю обезличивание, скоро загружу файл...')
    # Берем первый файл в директории с расширением .csv
    file_name = [i for i in os.listdir(cur_dir) if '.csv' and 'query' in i and 'new' not in i][0]
    try:
        with open(file_name, 'r', encoding=encoding) as csv_read:
            data = csv.reader(csv_read)
            data = list(data)
            column_str = [data[0].index(item) for item in column_str]
            column_json = [data[0].index(item) for item in column_json]
            data = main(data)
        with open('new_query_result.csv', 'w', newline='', encoding=encoding) as csv_write:
            csv.writer(csv_write).writerows(data)
    except:
        bot.send_message(message.from_user.id,
                         'Произошла ошибка при обезличивании файла, проверьте файл и повторите попытку позже')
    else:
        bot.send_message(message.from_user.id, 'Файл успешно обезличен')
        bot.send_message(message.from_user.id, 'Загружаю файл...')
        file = open('new_query_result.csv', 'rb')
        bot.send_document(message.chat.id, file)
        try:
            os.remove(cur_dir + '\\' + 'new_query_result.csv')
            os.remove(cur_dir + '\\' + 'file_name')
        except:
            bot.send_message(message.from_user.id, 'Произошла ошибка при удалении файлов на сервере бота')
        else:
            bot.send_message(message.from_user.id, '.csv файлы успешно удалены с сервера бота')


bot.infinity_polling()


# -------------------------------------------------------------------

def json_deperson(buf):
    '''
    Функция обезличивания json
    :param buf: json в виде строки
    :return: Обезличенный json
    '''
    json_object = json.loads(buf)
    for obj in json_object:
        if obj not in json_exceptions:
            if type(json_object[str(obj)]) == str:
                json_object[str(obj)] = str_deperson(json_object[str(obj)])
            elif type(json_object[str(obj)]) == list:

                # Обезличиваем список
                for key, item in enumerate(json_object[str(obj)]):
                    json_object[str(obj)][key] = str_deperson(str(item))
    try:
        del json_object['serial_number']
    except KeyError:
        pass
    result = json.dumps(json_object)
    return result


def str_deperson(buf):
    '''
    Функция обезличивания строки
    :param buf: строка
    :return: обезличенная строка
    '''
    result = ''
    for k, symbol in enumerate(buf):
        num = ord(symbol)
        if 0 <= num <= 47 or 58 <= num <= 64 or 91 <= num <= 96 or 123 <= num <= 127:
            result += symbol
        elif num == 122:
            result += chr(97)
        elif num == 90:
            result += chr(65)
        elif num == 57:
            result += chr(48)
        else:
            result += chr(num + 1)
    return result


def main(data):
    for i, row in enumerate(data):
        if i != 0:
            for j, item in enumerate(row):
                # j - номер столба таблицы
                if j in column_str:
                    row[j] = str_deperson(item)
                if j in column_json:
                    row[j] = json_deperson(item)
        data[i] = row
    return data
