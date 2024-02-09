import os
import time
import threading
import docker
import psutil
import requests
import telebot
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv('TOKEN'))
website_url = os.getenv('URL')
chat_ids = [int(chat_id) 
            for chat_id 
            in os.getenv('CHAT_IDS', '').split(',') 
            if chat_id]
client = docker.from_env()
last_running_containers = set()


@bot.message_handler(commands=['start'])
def start(message):
    mess = ('/docker - названия контейнеров, их статус и порт.\n'
            '/docker_sum - количество запущенных контейнеров.\n'
            '/check_website_status - status code веб-приложения.\n'
            '/ram - информация о ram сервера.\n')
    bot.send_message(message.chat.id, mess, parse_mode='html')


@bot.message_handler(commands=['docker'])
def docker_info(message):
    containers = client.containers.list()
    container_info = []

    for container in containers:
        info = (f'Image: {container.name}\n'
                f'Status: {container.status}\n'
                f'Ports: {container.ports}\n')
        container_info.append(info)

    for mess in container_info:
        bot.send_message(message.chat.id, mess, parse_mode='html')


@bot.message_handler(commands=['docker_sum'])
def docker_sums(message):
    containers = client.containers.list()
    num_containers = len(containers)
    mess = (f"Total number of containers: {num_containers}")
    bot.send_message(message.chat.id, mess, parse_mode='html')


def check_website_status(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return (f'The website {url} is up and running! '
                    f'Status code: {response.status_code}')
        else:
            return (f'The website {url} is down. '
                    f'Status code: {response.status_code}')
    except requests.exceptions.RequestException as e:
        return f'An error occurred while connecting to the website: {e}'


@bot.message_handler(commands=['check_website_status'])
def status_website(message):
    mess = check_website_status(website_url)
    bot.send_message(message.chat.id, mess, parse_mode='html')


@bot.message_handler(commands=['ram'])
def ram_server(message):
    memory = psutil.virtual_memory()

    total_mb = memory.total / (1024 * 1024)
    available_mb = memory.available / (1024 * 1024)
    used_mb = memory.used / (1024 * 1024)

    mess = (f'Total Memory: {total_mb:.2f} MB\n'
            f'Available Memory: {available_mb:.2f} MB\n'
            f'Used Memory: {used_mb:.2f} MB\n'
            f'Memory Usage Percentage: {memory.percent}%')

    bot.send_message(message.chat.id, mess, parse_mode='html')


def notify_container_failure(container_name):
    message = f"Container {container_name} has crashed!"
    for chat_id in chat_ids:
        bot.send_message(chat_id, message, parse_mode='html')


def check_container_status():
    containers = client.containers.list()
    current_running_containers = {container.name for container in containers
                                  if container.status == 'running'}

    global last_running_containers
    for container_name in last_running_containers:
        if container_name not in current_running_containers:
            notify_container_failure(container_name)

    last_running_containers = current_running_containers


def main():
    bot_thread = threading.Thread(target=bot.polling,
                                  kwargs={'none_stop': True})
    bot_thread.start()

    while True:
        try:
            check_container_status()
        except Exception as e:
            print(f"Error in container status check: {e}")
        
        time.sleep(10)


if __name__ == '__main__':
    last_running_containers = set()
    main()
