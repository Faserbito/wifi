from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
import smtplib
from cryptography.fernet import Fernet
from datetime import datetime
import time
import re
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

permitted_mac = ['34:F6:4B:40:01:87', 'A8:1E:84:BC:BE:CC']

def write_key_connect():
    key = Fernet.generate_key()
    with open('connect.key', 'wb') as key_file:
        key_file.write(key)

def load_key_connect():
    key = open('connect.key', 'rb').read()
    return key

def encrypt():
    f = Fernet(load_key_connect())
    with open('connect.txt', 'rb') as file:
        file_data = file.read()
    encrypted_data = f.encrypt(file_data)
    with open('connect.txt', 'wb') as file:
        file.write(encrypted_data)

def read_data_connect():
    f = Fernet(load_key_connect())
    with open('connect.txt', 'rb') as file:
        encrypted_data = file.read()
    decrypted_data = f.decrypt(encrypted_data).decode('utf8')
    return decrypted_data

def send_email(message):
    server = 'smtp.mail.ru'
    user = 'example_api@mail.ru'
    password = 'LkybB53PjruzpkPAjnFi'

    sender = 'example_api@mail.ru'
    to_address = 'ne4kin.zh@yandex.ru'
    subject = 'Вторжение в wi-fi сеть неизвестных устройств' 

    body = "\r\n".join((f"From: {user}", f"To: {to_address}", 
           f"Subject: {subject}", message))

    mail = smtplib.SMTP_SSL(server)
    mail.login(user, password)
    mail.sendmail(sender, to_address, body.encode('utf8'))
    mail.quit()

options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_argument("--log-level=3")

browser = webdriver.Chrome(chrome_options=options)
browser.get("http://192.168.0.1")
connect_data = read_data_connect().split("|")
login = browser.find_element_by_id("A1").send_keys(f"{connect_data[0]}")
password = browser.find_element_by_id("A2").send_keys(f"{connect_data[1]}")
action = ActionChains(browser)
action.send_keys(Keys.ENTER)
action.perform()
while True:
    minute_now = datetime.now().strftime('%M')
    seconds_now = datetime.now().second
    time.sleep(1)
    if seconds_now == 0 and (int(minute_now[-1]) == 0 or int(minute_now[-1]) == 5): 
        browser.get("http://192.168.0.1/index.cgi#status/clients")
        time.sleep(3)
        clients = browser.find_element_by_class_name("grid")
        clients_mac = re.findall(r'\S{2}:\S{2}:\S{2}:\S{2}:\S{2}:\S{2}', clients.get_attribute("innerHTML"))
        current_mac = list(map(str.upper, clients_mac))
        list_permitted_mac = "\n\t".join(permitted_mac)
        print(f'Список разрешенных mac-адресов:\n\t{list_permitted_mac}')
        list_current_mac = "\n\t".join(current_mac)
        print(f'Список подключенных mac-адресов:\n\t{list_current_mac}')
        new_blocked_mac = []
        for mac in current_mac:
            if mac not in permitted_mac:
                new_blocked_mac.append(mac)        
        if len(new_blocked_mac) != 0:
            list_new_blocked_mac = "\n\t".join(new_blocked_mac)
            print(f'Список неизвестных mac-адресов:\n\t{list_new_blocked_mac}')
            browser.get("http://192.168.0.1/index.cgi#wifi/mac")
            time.sleep(3)
            browser.find_element_by_link_text('MAC-адреса').click()
            time.sleep(3)            
            current_blocked_mac = [mac.text for mac in browser.find_elements_by_css_selector('td.editable.mandatory')]
            list_current_blocked_mac = "\n\t".join(current_blocked_mac)
            print(f'Список заблокированных mac-адресов:\n\t{list_current_blocked_mac}')
            blocked_mac = []
            for mac in new_blocked_mac:
                if mac not in current_blocked_mac:
                    blocked_mac.append(mac)
            if len(blocked_mac) != 0:
                list_blocked_mac = "\n\t".join(blocked_mac)
                print(f'В список запретов будут добавлены следующие mac-адреса:\n\t{list_blocked_mac}')
                buttons = browser.find_elements_by_css_selector('div.button.normal.unselectable')
                add_button = buttons[0]
                for mac in blocked_mac:            
                    action.drag_and_drop(add_button, add_button)
                    action.perform()
                    new_entry = browser.find_elements_by_css_selector('td.editable.mandatory')
                    action.move_to_element(new_entry[-1])
                    action.perform()
                    action.click(new_entry[-1])
                    action.perform()
                    new_entry_text = browser.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[5]/div[2]/div[1]/div[3]/div[1]/div/div/div[3]/div[1]/div[1]/div/input')               
                    new_entry_text.send_keys(mac)
                save_button = buttons[1]
                action.drag_and_drop(save_button, save_button)
                action.perform()
                time.sleep(100)
                first_fastmenu = browser.find_element_by_css_selector('li.first.fastmenu.notifier')
                action.move_to_element(first_fastmenu)
                action.perform()            
                save_all_button = browser.find_element_by_css_selector('li.notifierItem')
                action.drag_and_drop(save_all_button, save_all_button)
                action.perform()
                time.sleep(5)
                browser.switch_to.alert.accept()
                unknown_mac_address = "\n".join(blocked_mac)
                message = f'При проведении анализа wi-fi сети были выявлены подключения следующих неизвестных устройств:\n{unknown_mac_address}\nДанные устройства были добавлены в список запретов на подключения.'
                send_email(message)
                print('Неизвестные устройства были добавлены в список запретов. Письмо с данной информацией отправлено на почту')
                print('--------------------------------------------------------------------------------------------------------\n')
            else:
                print('Все неизвестные устройства уже находятся в списке запретов')
                print('--------------------------------------------------------------------------------------------------------\n')

        else:
            print('Все подключенные устройства находятся в белом списке.')

