import json
import requests
from datetime import datetime
from os import getenv
from time import sleep
from sentences import load_sentences_local
from sentences import load_sentences_remote


class User:
    def __init__(self, uId: int, uName: str, uLevel: int) -> None:
        self.id = uId
        self.name = uName
        self.level = uLevel
        print("Object User was created")

    def __str__(self) -> str:
        return f"User chat id = {self.id}\
            User level = {self.level}"


def run(token_env_name: str, debug=False):
    """Run bot instance to run in debug mode
    use debug=True flag
    """

    bot_url = create_bot_url(token_env_name)

    if debug:
        print(bot_url)
        print(type(get_bot_info(bot_url)))
        print(get_bot_updates(bot_url))
        bot_set_commands(bot_url)
        print(bot_echo_polling(bot_url, 3))

    if not debug:
        bot_set_commands(bot_url)
        bot_send_sentences(bot_url, 2, True)


def create_bot_url(token_env: str) -> str:
    """Concatenate request url for bot
    export BOT_TOKEN=yourbottoken
    """
    root_url= 'https://api.telegram.org/bot'
    token = getenv(token_env)

    if not token:
        raise ValueError(f"Dont have value for env variable with name {token_env}")

    bot_url = f"{root_url}{token}"

    return bot_url


def get_bot_info(bot_url: str) -> dict:
    """Get basic info about bot"""
    url = f"{bot_url}/getMe"
    response = requests.get(url, timeout=5)
    return response.json()


def get_bot_updates(bot_url: str) -> dict:
    """Get bot updates return None if no updates available
    """
    url = f"{bot_url}/getUpdates"
    response = requests.get(url, timeout=5)
    updates = response.json()

    # Set offset if updates greater then 100

    if len(updates['result']) == 100:
        offset = updates['result'][-1]['update_id']
        url = f"{bot_url}/getUpdates?offset={offset}"
        response = requests.get(url, timeout=5)
        url = f"{bot_url}/getUpdates"
        response = requests.get(url, timeout=5)
        updates = response.json()

    if updates['result']:
        return updates
    if len(updates) == 0:
        return None
    else:
        return None


def parse_message(updates: dict) -> tuple:
    """Get message_id, chat_id and text from last bot update
    """
    last_update = updates['result'][-1]
    is_command = False

    update_id = last_update['update_id']
    message_id = last_update['message']['message_id']
    text = last_update['message']['text']
    chat_id = last_update['message']['chat']['id']
    entity = last_update['message'].get('entities')

    if entity:
        type_of_entity = entity[-1].get('type')
        if type_of_entity == 'bot_command':
            is_command = True

    return is_command, update_id, message_id, chat_id, text


def send_message(bot_url: str, chat_id: int, message: str):
    """Send message to user with chat id
    returns status code 200 if ok
    """

    url = f"{bot_url}/sendMessage"
    response = requests.post(
        url, json={'chat_id': chat_id, 'text': message}, timeout=5
    )

    return response.status_code


def bot_echo_polling(bot_url: str, polling_interval=1):
    """Check bot last update and send echo message to user"""

    update = get_bot_updates(bot_url)
    
    is_command, last_update_id, last_message_id, chat_id, text = parse_message(
        update)
    
    print(
        f"Last update id = {last_update_id}\nLast message id = {last_message_id}")

    while True:
        bot_updates = get_bot_updates(bot_url)

        try:
            is_command, update_id, message_id, chat_id, text = parse_message(
                bot_updates)

            if message_id > last_message_id and update_id > last_update_id:
                last_message_id = message_id
                last_update_id = update_id
                print(f"New message from {chat_id}\nText = {text}")
                send_message(bot_url, chat_id, text)
                print(f"Send echo {text} to user {chat_id}")
            else:
                print("Polling...")
                sleep(polling_interval)
        except Exception as e:
            sleep(5)
            print(e)
            print("Dont have updates, send something to bot!")


def bot_set_commands(bot_url: str):
    """ Set menu with avaliable comands for bot """
    url = f"{bot_url}/setMyCommands?commands="
    commands = [
        {
            "command": "start",
            "description": "get started with the bot"
        },
        {
            "command": "time",
            "description": "send current time"
        },
        {
            "command": "help",
            "description": "print help message to user"
        },
        {
            "command": "getlvl",
            "description": "get current level of user"
        },
        {
            "command": "setlvl",
            "description": "set level to user"
        }
    ]
    commands = json.dumps(commands)
    url = url + str(commands)
    response = requests.post(url, timeout=5)

    return response.status_code


def command_handler(users: list, bot_url: str, command: str, chat_id: int):
    """Processing bot commands received from chat"""

    if command == '/start':
        start_msg = "Hello from English bot!\n"\
        + "With me you can learn new words in context"
        send_message(bot_url, chat_id, start_msg)

    if command == '/help':
        help_msg = "1. Use menu to interact with the "\
        + "bot.\n\n2. To get sentences you need to send "\
        + "any word in chat.\n\n3. Your default level "\
        + "is elementary you can change this."
        send_message(bot_url, chat_id, help_msg)

    if command == '/time':
        c_time = datetime.now().strftime('%H:%M:%S')
        time_msg = f'Hello 👋 Current time is {c_time}'
        send_message(bot_url, chat_id, time_msg)

    if command == '/getlvl':
        current_lvl = [u.level for u in users if u.id == chat_id][0]
        send_message(bot_url, chat_id, current_lvl)

    if command == '/setlvl':
        msg = "1 -> Elementary -> A1 -> A2\n\n"\
            + "2 -> Intermediate -> B1 -> B2\n\n"\
            + "3 -> Advanced -> C1 -> C2\n\n"

        send_message(bot_url, chat_id, msg)
        is_correct_lvl = False
        while (not is_correct_lvl):
            update = get_bot_updates(bot_url)
            try:
                lvl, lvl_name = parse_level_from_message(update)
                if lvl:
                    msg = f"Level changed to {lvl_name}"
                    for u in users:
                        if u.id == chat_id:
                            u.level = lvl
                    send_message(bot_url, chat_id, msg)
                    is_correct_lvl = True
                    print(f"User: {chat_id}\n{msg}")
                else:
                    print("Wait for correct input from user")
                    sleep(2)
            except Exception as e:
                print(f"Error {e} for set level command")

    return f"Command {command} done!"


def parse_level_from_message(update: dict) -> int:
    """Handling level number from last update message text"""
    level = None
    level_name = ''
    text = update['result'][-1]['message'].get('text')

    correct_lvls = [x + 1 for x in range(3)]
    levels_dict = {
        1: ['1', 'elementary', 'a1', 'a2'],
        2: ['2', 'intermediate', 'b1', 'b2'],
        3: ['3', 'advanced', 'c1', 'c2']
    }

    for lvl in correct_lvls:
        if text.lower() in levels_dict[lvl]:
            level = lvl
            level_name = levels_dict.get(lvl)[1].capitalize()

    return level, level_name


def get_sentences_from_local(word: str, level: int) -> str:
    """Get sentences from local sentences.py file
    return string with matched sentences with user word
    """
    list_sentences = []
    matched_sentences = []
    result_msg = ''

    list_sentences = load_sentences_local()
    for sentence in list_sentences:
        text_from_sentence = sentence['text']
        level_from_sentence = sentence['level']
        if word.lower() in text_from_sentence.lower() and level_from_sentence == level:
            matched_sentences.append(text_from_sentence)

    if len(matched_sentences) == 0:
        result_msg += "No matches"
    if len(matched_sentences) == 1:
        result_msg += matched_sentences[0]
    if len(matched_sentences) > 1:
        for match in matched_sentences:
            result_msg += match + "\n\n"

    return result_msg


def get_sentences_from_remote(word: str, level: int, amount=10) -> str:
    """Get sentences from web site
    https://sentence.yourdictionary.com/{word}
    Optionally you can specify the number of examples
    in "amount" input argument default 10

    return string with matched sentences with user word
    """

    list_sentences = []
    matched_sentences = []
    result_msg = ''

    list_sentences = load_sentences_remote(word)[:amount]

    for sentence in list_sentences:
        text_from_sentence = sentence['text']
        level_from_sentence = sentence['level']
        if level_from_sentence == level:
            matched_sentences.append(text_from_sentence)

    if len(matched_sentences) == 0:
        result_msg += "No matches"
    if len(matched_sentences) == 1:
        result_msg += matched_sentences[0]
    if len(matched_sentences) > 1:
        for match in matched_sentences:
            result_msg += match + "\n\n"

    return result_msg


def bot_send_sentences(bot_url: str, polling_interval=1, remote=False):
    """
    Launching the bot in the mode of sending a sentence with the user's word 
    """
    users = []
    update = get_bot_updates(bot_url)
    try:
        is_command, last_update_id, last_message_id, chat_id, last_message_text = parse_message(
        update)
        print(
        f"Last update id = {last_update_id}\nLast message id = {last_message_id}")
    except Exception as e:
        sleep(5)
        print(e)
        print("Dont have updates, send something to bot!")

    while True:
        bot_updates = get_bot_updates(bot_url)
        last_message_id = 0
        try:
            is_command, update_id, message_id, chat_id, text = parse_message(
                bot_updates)
            level, level_name = parse_level_from_message(bot_updates)
            # Add new user to list if not exist
            if not users or chat_id not in [u.id for u in users]:
                users.append(User(chat_id, '', 1))
                print(f"Add new user {chat_id} to list")

            if message_id > last_message_id and update_id > last_update_id:
                last_message_id = message_id
                last_update_id = update_id
                print(f"New message from {chat_id} Text = {text}")

                if is_command:
                    if last_message_text != text:
                        last_message_text = text
                        res = command_handler(users, bot_url, text, chat_id)
                        send_message(bot_url, chat_id, res)
                else:
                    if not level:
                        if not remote and last_message_text != text:
                            last_message_text = text
                            user_lvl = [
                                u.level for u in users if u.id == chat_id][0]
                            result_msg = get_sentences_from_local(
                                text, user_lvl)
                            print(f"User level is {user_lvl}")
                            send_message(bot_url, chat_id, result_msg)
                        if remote and last_message_text != text:
                            last_message_text = text
                            user_lvl = [
                                u.level for u in users if u.id == chat_id][0]
                            result_msg = get_sentences_from_remote(
                                text, user_lvl, 10)
                            print(f"User level is {user_lvl}")
                            send_message(bot_url, chat_id, result_msg)

            else:
                print("Polling...")
                sleep(polling_interval)
        except Exception as e:
            sleep(5)
            print(e)
            print("Dont have updates, send something to bot!")
