import os
import requests

import telebot
import docker
import psutil
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv('TOKEN'))
website_url = os.getenv('URL')
chat_id = os.getenv('CHAT_ID')
client = docker.from_env()


@bot.message_handler(commands=['start'])
def strat(message):
    mess = (f'/docker - названия контейнеров, их статус и порт.\n'
            f'/docker_sum - количество запущенных контейнеров.\n'
            f'/check_website_status - status code веб-приложения.\n'
            f'/ram - информация о ram сервера.\n')
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



def main():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()