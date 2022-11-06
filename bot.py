import json
import requests
from os import getenv
from time import sleep


def run(token_env_name: str, debug=False):
    """Run bot instance to run in debug mode
    use debug=True flag
    """

    bot_url = create_bot_url(token_env_name) 

    if debug:
        # print(bot_url)
        # print(type(get_bot_info(bot_url)))
        #print(get_bot_updates(bot_url))
        bot_set_commands(bot_url)
        print(bot_echo_polling(bot_url, 3))
    

def create_bot_url(token_env: str) -> str:
    """Create request url for bot
    Get telegram bot token and root url from ENV
    variables
    export ROOT_URL=https://api.telegram.org/bot
    export BOT_TOKEN=yourbottoken
    """

    root_url = getenv('ROOT_URL')
    token = getenv(token_env)
    
    if not token:
        raise ValueError(f"Dont have env variable with name {token_env}")

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

    if updates['result']:
        return updates
    else:
        return None


def parse_message(updates: dict) -> tuple:
    """Get message_id, chat_id and text from last bot update
    """
    last_update = updates['result'][-1]

    update_id = last_update['update_id']
    message_id = last_update['message']['message_id']
    text = last_update['message']['text']
    chat_id = last_update['message']['chat']['id']

    return update_id, message_id, chat_id, text


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
    """Check bot last update and send echo message to user 
    """

    update = get_bot_updates(bot_url)
    last_update_id, last_message_id, chat_id, text = parse_message(update)
    print(f"Last update id = {last_update_id}\nLast message id = {last_message_id}")

    while True:
        bot_updates = get_bot_updates(bot_url)
    
        try:
            update_id, message_id, chat_id, text = parse_message(bot_updates)

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
