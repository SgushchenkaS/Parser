# -*- coding: cp1251 -*-
import requests
import csv
import time

from lxml import html
from fake_headers import Headers

HEADERS = Headers(
    browser="chrome",
    os="win",
    headers=True
).generate()
URL = 'https://www.e-katalog.ru/list/187/'
DOMAIN = 'https://www.e-katalog.ru'
ALL_DATA = dict()
QUEUE_URL = set()
Rating = []

def add_to_csv_from_file(product_dict):
    with open('Motherboard.csv', 'a') as csvfile:
        fieldnames = ['Rating', 'ID','Url', 'Manufacturer', 'Name', 'Price_min', 'Price_max', 'Price', 'Status', 'Description', 'Type', 'Socket', 'Form', 'Power-phases', 'VRM', 'Heat-pipes', 'LED', 'LED-synchron',
                      'Metal-backplate', 'Hight', 'Weight', 'Embedded-processor', 'Processor-model', 'Chipset', 'South-bridge', 'BIOS', 'DualBIOS', 'UEFI',
                      'Active-cooling', 'Ram-type', 'Slots', 'Form-slots-RAM', 'Working-mode', 'Max-Ram-Frequency', 'Max-Ram-Size', 'XMP', 'ECC', 'Hybrid-Mode',
                      'Integrated-graphics', 'Model-GPU', 'DVI', 'D-Sub', 'HDMI', 'V-HDMI', 'DisplayPort', 'V-DisplayPort', 'Audio', 'Audio-chanel',
                      'S/P-DIF', 'IDE', 'SATA2', 'SATA3', 'M2', 'M2-interface', 'M2-cooling', 'RAID', 'U.2', 'SAS', 'eSATA', 'Wi-Fi', 'Bluetooth',
                      'LAN-speed', 'N-LAN', 'LAN', 'Type-LAN', 'PCI-E-1x', 'PCI-E-16x', 'N-PCI', 'V-PCI-E', 'PCI-E', 'CrossFire', 'SLI', 'PCI-E-Steel',
                      'USB-2.0', 'USB-3.2-V1', 'USB-3.2-V2', 'USB-C-3.2-V1', 'USB-C-3.2-V2', 'USB-C-3.2-V2x2', 'PS/2', 'LPT', 'COM', 'Thunderbolt', 'Alternate-Mode',
                      'TPM', 'Mother-USB-2.0', 'Mother-USB-3.2-V1', 'Mother-USB-3.2-V2', 'Mother-USB-C-3.2-V1', 'Mother-USB-C-3.2-V2', 'Mother-USB-C-3.2-V2x2', 'ARGB-LED',
                      'RGB-LED', 'Thunderbolt-AIC', 'Other', 'Main-power-connector', 'Processor-power', 'Power-connectors-coolers', 'CPU-fan', 'CPU-waterPump',
                      'Chassis-waterPump']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writerow(product_dict)


def get_data(product_link):
    print('Сбор данных с URL', product_link)
    product = dict()
    request = requests.get(product_link, headers=HEADERS)
    time.sleep(3)
    tree = html.fromstring(request.content)
    product_name = tree.xpath("//div[@class='page-title']/@data-title")
    product_manufacturer = ''.join(product_name)
    product_manufacturer = (product_manufacturer.split())[0]
    product['Name'] = product_name[0]
    product['Manufacturer'] = product_manufacturer
    product['Url'] = product_link
    product_descriptions = tree.xpath("//div[@class='desc-ai-title']/text()")
    for descriptions in product_descriptions:
        product['Description'] = descriptions
    id = tree.xpath("translate(substring(//div[@class='ib item-img-div']//div[@class='img200 h']/img/@data-default_img, 6), '.jpg', '')")
    product["ID"] = id

    #Место в списке рейтинга
    i = 0
    for url in Rating:
        i += 1
        if url == product_link:
            product['Rating'] = i

    #загрузка изображения

    photo_link = DOMAIN + "/jpg_zoom1/" + id + ".jpg"
    request = requests.get(photo_link, headers=HEADERS)
    out = open("motherboard/" + id + ".jpg", "wb")
    out.write(request.content)
    out.close()

    #Получение цены
    product_price_min = tree.xpath("translate(//div[@class='desc-short-prices'][1]//div[@class='desc-big-price ib']//span[@itemprop='lowPrice']/text(), '  ', '')")
    if len(product_price_min) == 0: product_price_min = tree.xpath("translate(//div[@class='desc-short-prices'][1]//div[@class='desc-big-price xl ib']//span[@itemprop='lowPrice']/text(), '  ', '')")
    product_price_max = tree.xpath("translate(//div[@class='desc-short-prices'][1]//div[@class='desc-big-price ib']//span[@itemprop='highPrice']/text(), '  ', '')")
    if len(product_price_max) == 0: product_price_max = tree.xpath("translate(//div[@class='desc-short-prices'][1]//div[@class='desc-big-price xl ib']//span[@itemprop='highPrice']/text(), '  ', '')")

    min = 0
    max = 0
    price = 0

    if len(product_price_min) > 0:
        min = int(product_price_min)
        if len(product_price_max) > 0:
            max = int(product_price_max)
            price = (min+max)/2
        else:
            price = min

    if min > 0: product['Price_min'] = min
    if max > 0: product['Price_max'] = max
    product['Price'] = round(price)

    old = tree.xpath("//div[@class='desc-short-prices'][1]//div[@class=' or']/text()")
    new = tree.xpath("//div[@class='desc-short-prices'][1]//div[@class='goto-price-charts']//a[1]/@title")

    if len(old) > 0:
        if old[0] == "Ожидается в продаже": product['Status'] = "old"
    if len(new) == 0: product['Status'] = "new"

    #Переход на раздел "характеристики"
    link2 = tree.xpath("//div[@class='desc-menu']//a[3]/@link[1]")
    if len(link2) > 0:
        connect = DOMAIN + link2[0]
        request = requests.get(connect, headers=HEADERS)
        time.sleep(3)
        tree = html.fromstring(request.content)

    #Получение jid параметров

    number_last_1 = round(tree.xpath("count(//div[@class='item-block ff-roboto']//td[@class='op01']//tr)"))
    i = 0
    ID = []
    while i < number_last_1:
        xpa = "//div[@class='item-block ff-roboto']//td[@class='op01']//tr[" + str(i+1) + "]//td[@class='op1']//span/@jid"
        jid = tree.xpath(xpa)
        if len(jid) > 0:
            ID.append(jid[0])
        else:
            ID.append("None")
        i += 1

    number_last_2 = round(tree.xpath("count(//div[@class='item-block ff-roboto']//td[@class='op02']//tr)"))
    i = 0
    while i < number_last_2:
        xpa = "//div[@class='item-block ff-roboto']//td[@class='op02']//tr[" + str(
            i + 1) + "]//td[@class='op1']//span/@jid"
        jid = tree.xpath(xpa)
        if len(jid) > 0:
            ID.append(jid[0])
        else:
            ID.append("None")
        i += 1

    #получение параметров характеритсик

    i = 0
    Characters = []
    while i < number_last_1:
        xpa = "//div[@class='item-block ff-roboto']//td[@class='op01']//tr[" + str(i + 1) + "]//td[@class='op3']/text()"
        jid = tree.xpath(xpa)
        if len(jid) > 0:
            Characters.append(jid[0])
        else:
            xpa = "//div[@class='item-block ff-roboto']//td[@class='op01']//tr[" + str(i + 1) + "]//td[@class='op3']//a/text()"
            jid = tree.xpath(xpa)
            if len(jid) > 0:
                Characters.append(jid[0])
            else:
                xpa = "//div[@class='item-block ff-roboto']//td[@class='op01']//tr[" + str(i + 1) + "]//td[@class='op3']//img/@width"
                jid = tree.xpath(xpa)
                if len(jid) > 0:
                    Characters.append("+")
                else:
                    Characters.append("None")
        i += 1

    i = 0
    while i < number_last_2:
        xpa = "//div[@class='item-block ff-roboto']//td[@class='op02']//tr[" + str(i + 1) + "]//td[@class='op3']/text()"
        jid = tree.xpath(xpa)
        if len(jid) > 0:
            Characters.append(jid[0])
        else:
            xpa = "//div[@class='item-block ff-roboto']//td[@class='op02']//tr[" + str(i + 1) + "]//td[@class='op3']//a/text()"
            jid = tree.xpath(xpa)
            if len(jid) > 0:
                Characters.append(jid[0])
            else:
                xpa = "//div[@class='item-block ff-roboto']//td[@class='op02']//tr[" + str(i + 1) + "]//td[@class='op3']//img/@width"
                jid = tree.xpath(xpa)
                if len(jid) > 0:
                    Characters.append("+")
                else:
                    Characters.append("None")
        i += 1

#Запись характеритсик

    i = 0
    while i < len(ID):

        # По направлению
        if ID[i] == "p7938":
             product['Type'] = Characters[i]
        # Сокет
        if ID[i] == "p7932":
            product['Socket'] = Characters[i]
        # Форма-фактор
        if ID[i] == "p7933":
            product['Form'] = Characters[i]
        # Фазы питания
        if ID[i] == "p24686":
            product['Power-phases'] = Characters[i]
        # Радиатор VRM
        if ID[i] == "p24685":
            if Characters[i] == "+":
                product['VRM'] = "+"
        # Теловые трубки
        if ID[i] == "p27532":
            if Characters[i] == "+":
                product['Heat-pipes'] = "+"
        # LED подсветка
        if ID[i] == "p21119":
            if Characters[i] == "+":
                product['LED'] = "+"
        # Синхронизация подсветки
        if ID[i] == "p24048":
            product['LED-synchron'] = Characters[i]
        # Металлический бэкплейт
        if ID[i] == "p26222":
            if Characters[i] == "+":
                product['Metal-backplate'] = "+"
        # Размеры (ВхШ)
        if ID[i] == "p7999":
            product['Hight'] = ((Characters[i].split('\xa0'))[0].split('x'))[0]
            product['Weight'] = ((Characters[i].split('\xa0'))[0].split('x'))[1]
        # Встроенный процессор
        if ID[i] == "p7935":
            if Characters[i] == "+":
                product['Embedded-processor'] = "+"
        # Модель встроенного процессора
        if ID[i] == "p7936":
            product['Processor-model'] = Characters[i]
        # Чипсет
        if ID[i] == "p7937":
            product['Chipset'] = Characters[i]
        # Южный мост
        if ID[i] == "p7941":
            product['South-bridge'] = Characters[i]
        # BIOS
        if ID[i] == "p7944":
            product['BIOS'] = Characters[i]
        # Поддержка Dual-BIOS
        if ID[i] == "p8002":
            if Characters[i] == "+":
                product['DualBIOS'] = "+"
        # UEFI BIOS
        if ID[i] == "p8667":
            if Characters[i] == "+":
                product['UEFI'] = "+"
        # Активное охлаждение
        if ID[i] == "p27531":
            if Characters[i] == "+":
                product['Active-cooling'] = "+"
        # Тип оперативной памяти DDR3 и количество слотов
        if ID[i] == "p7948":
            Slots = []
            Slots += Characters[i]
            product['Slots'] = Slots[0]
            product['Ram-type'] = 'DDR3'
        # Тип оперативной памяти DDR4 и количество слотов
        if ID[i] == "p14043":
            Slots = []
            Slots += Characters[i]
            product['Slots'] = Slots[0]
            product['Ram-type'] = 'DDR4'
        # Тип оперативной памяти DDR5 и количество слотов
        if ID[i] == "p28342":
            Slots = []
            Slots += Characters[i]
            product['Slots'] = Slots[0]
            product['Ram-type'] = 'DDR5'
        # Форм-фактор слота для памяти
        if ID[i] == "p14423":
            product['Form-slots-RAM'] = Characters[i]
        # Режим работы
        if ID[i] == "p7949":
            product['Working-mode'] = Characters[i]
        # Максимальная тактовая частота оператиной памяти
        if ID[i] == "p7950":
            Frequency = []
            Result = ""
            Frequency += Characters[i]
            n = 0
            while n < 4:
                Result += Frequency[n]
                n += 1
            product['Max-Ram-Frequency'] = Result
        # Максимальный объем оперативной памяти
        if ID[i] == "p7951":
            Memory = []
            Result = ""
            Memory += Characters[i]
            n = 0
            while n < 2:
                Result += Memory[n]
                n += 1
            if Memory[2] != " ":
                Result += Memory[2]
            product['Max-Ram-Size'] = Result
        # Поддержка XMP
        if ID[i] == "p8003":
            if Characters[i] == "+":
                product['XMP'] = "+"
        # Поддержка ECC
        if ID[i] == "p7953":
            if Characters[i] == "+":
                product['ECC'] = "+"
        # Гибридный режим
        if ID[i] == "p7960":
            if Characters[i] == "+":
                product['Hybrid-Mode'] = "+"
        # Встроенная видеокарта
        if ID[i] == "p7956":
            if Characters[i] == "+":
                product['Integrated-graphics'] = "+"
        # Модель встроенная видеокарта
        if ID[i] == "p7957":
            product['Model-GPU'] = Characters[i]
        # Выход DVI
        if ID[i] == "p7987":
            if Characters[i] == "+":
                product['DVI'] = "+"
        # Выход D-Sub (VGA)
        if ID[i] == "p7986":
            if Characters[i] == "+":
                product['D-Sub'] = "+"
        # Выход HDMI
        if ID[i] == "p7988":
            if Characters[i] == "+":
                product['HDMI'] = "+"
        # Версия HDMI
        if ID[i] == "p8006":
            product['V-HDMI'] = Characters[i]
        # Выход DisplayPort
        if ID[i] == "p8009":
            if Characters[i] == "+":
                product['DisplayPort'] = "+"
        # Версия DisplayPort
        if ID[i] == "p24407":
            product['V-DisplayPort'] = Characters[i]
        # Аудиочип
        if ID[i] == "p7966":
            product['Audio'] = Characters[i]
        # Звук (каналов)
        if ID[i] == "p7965":
            product['Audio-chanel'] = Characters[i]
        # Оптический S/P-DIF
        if ID[i] == "p7968":
            if Characters[i] == "+":
                product['S/P-DIF'] = "+"
        # IDE
        if ID[i] == "p7977":
            Number = []
            Number += Characters[i]
            product['IDE'] = Number[0]
        # Количество слото SATA 2
        if ID[i] == "p7971":
            Number = []
            Number += Characters[i]
            product['SATA2'] = Number[0]
        # Количество слото SATA 3
        if ID[i] == "p7972":
            Number = []
            Number += Characters[i]
            product['SATA3'] = Number[0]
        # Количество слото SATA M.2
        if ID[i] == "p12537":
            Number = []
            Number += Characters[i]
            product['M2'] = Number[0]
        # Интерфейс M.2
        if ID[i] == "p23803":
            product['M2-interface'] = Characters[i]
        # Охлаждение SSD M.2
        if ID[i] == "p22365":
            if Characters[i] == "+":
                product['M2-cooling'] = "+"
        # Интегрированный RAID контроллер
        if ID[i] == "p7974":
            if Characters[i] == "+":
                product['RAID'] = "+"
        # U.2 разъем
        if ID[i] == "p17641":
            product['U.2'] = Characters[i]
       # SAS разъем
        if ID[i] == "p8164":
            if Characters[i] == "+":
                product['SAS'] = "+"
        # eSATA разъем
        if ID[i] == "p7973":
            if Characters[i] == "+":
                product['eSATA'] = "+"
        # Wi-Fi
        if ID[i] == "p7979":
            product['Wi-Fi'] = Characters[i]
        # Bluetooth
        if ID[i] == "p28052":
            product['Bluetooth'] = Characters[i]
        # LAN (RJ-45)
        if ID[i] == "p7981":
            product['LAN-speed'] = Characters[i]
        # Количество LAN-портов
        if ID[i] == "p7982":
            Number = []
            Number += Characters[i]
            product['N-LAN'] = Number[0]
        # LAN контроллер
        if ID[i] == "p7983":
            product['Type-LAN'] = Characters[i]
        # Слотов PCI-E 1x
        if ID[i] == "p7955":
            Number = []
            Number += Characters[i]
            product['PCI-E-1x'] = Number[0]
        # Слотов PCI-E 16x
        if ID[i] == "p7959":
            Number = []
            Number += Characters[i]
            product['PCI-E-16x'] = Number[0]
        # PCI слотов
        if ID[i] == "p7990":
            Number = []
            Number += Characters[i]
            product['N-PCI'] = Number[0]
        # Поддержка PCI express
        if ID[i] == "p25023":
            product['V-PCI-E'] = Characters[i]
        # Режимы PCI-E
        if ID[i] == "p24584":
            product['PCI-E'] = Characters[i]
        # Поддержка CrossFire (AMD)
        if ID[i] == "p24896":
            if Characters[i] == "+":
                product['CrossFire'] = "+"
        # Поддержка SLI (Nvidia)
        if ID[i] == "p24895":
            if Characters[i] == "+":
                product['SLI'] = "+"
        # Стальные PCI-E разъемы
        if ID[i] == "p26221":
            if Characters[i] == "+":
                product['PCI-E-Steel'] = "+"
        # USB 2.0
        if ID[i] == "p7993":
            Number = []
            Number += Characters[i]
            product['USB-2.0'] = Number[0]
        # USB 3.2 gen 1
        if ID[i] == "p7992":
            Number = []
            Number += Characters[i]
            product['USB-3.2-V1'] = Number[0]
        # USB 3.2 gen 2
        if ID[i] == "p16288":
            Number = []
            Number += Characters[i]
            product['USB-3.2-V2'] = Number[0]
        # USB C 3.2 gen 1
        if ID[i] == "p24573":
            Number = []
            Number += Characters[i]
            product['USB-C-3.2-V1'] = Number[0]
        # USB C 3.2 gen 2
        if ID[i] == "p24567":
            Number = []
            Number += Characters[i]
            product['USB-C-3.2-V2'] = Number[0]
        # USB C 3.2 gen 2x2
        if ID[i] == "p24620":
            Number = []
            Number += Characters[i]
            product['USB-C-3.2-V2x2'] = Number[0]
        # PS/2
        if ID[i] == "p7989":
            Number = []
            Number += Characters[i]
            product['PS/2'] = Number[0]
        # LPT-порт
        if ID[i] == "p7994":
            if Characters[i] == "+":
                product['LPT'] = "+"
        # COM-порт
        if ID[i] == "p7995":
            if Characters[i] == "+":
                product['COM'] = "+"
        # Интерфейс Thunderbolt
        if ID[i] == "p17524":
            product['Thunderbolt'] = Characters[i]
        # Поддержка Alternate Mode
        if ID[i] == "p26271":
            if Characters[i] == "+":
                product['Alternate-Mode'] = "+"
        # TPM-коннектор
        if ID[i] == "p25650":
            if Characters[i] == "+":
                product['TPM'] = "+"
        # Коннектор на мат. плате USB 2.0
        if ID[i] == "p24568":
            Number = []
            Number += Characters[i]
            product['Mother-USB-2.0'] = Number[0]
        # Коннектор на мат. плате USB 3.2 gen 1
        if ID[i] == "p24569":
            Number = []
            Number += Characters[i]
            product['Mother-USB-3.2-V1'] = Number[0]
        # Коннектор на мат. плате USB 3.2 gen 2
        if ID[i] == "p24570":
            Number = []
            Number += Characters[i]
            product['Mother-USB-3.2-V2'] = Number[0]
        # Коннектор на мат. плате USB C 3.2 gen 1
        if ID[i] == "p24572":
            Number = []
            Number += Characters[i]
            product['Mother-USB-C-3.2-V1'] = Number[0]
        # Коннектор на мат. плате USB C 3.2 gen 2
        if ID[i] == "p24571":
            Number = []
            Number += Characters[i]
            product['Mother-USB-C-3.2-V2'] = Number[0]
        # Коннектор на мат. плате USB C 3.2 gen 2x2
        if ID[i] == "p27495":
            Number = []
            Number += Characters[i]
            product['Mother-USB-C-3.2-V2x2'] = Number[0]
        # ARGB LED strip
        if ID[i] == "p27572":
            Number = []
            Number += Characters[i]
            product['ARGB-LED'] = Number[0]
        # GRB LED strip
        if ID[i] == "p27573":
            Number = []
            Number += Characters[i]
            product['RGB-LED'] = Number[0]
        # Разъем Thunderbolt AIC
        if ID[i] == "p27542":
            product['Thunderbolt-AIC'] = Characters[i]
        # Дополнительно
        shag = 0
        other = tree.xpath("//div[@class='item-block ff-roboto']//td[@class='op02']//tr//td")
        for oth in other:
            shag += 1
            if oth == 'Дополнительно':
                product['Other'] = other[i]
        # Основной разъем питания
        if ID[i] == "p8000":
            product['Main-power-connector'] = Characters[i]
        # Питание процессора
        if ID[i] == "p8001":
            product['Processor-power'] = Characters[i]
        # Разъем питания куллеров
        if ID[i] == "p8007":
            Number = []
            Number += Characters[i]
            product['Power-connectors-coolers'] = Number[0]
        # CPU Fan 4-pin
        if ID[i] == "p27585":
            Number = []
            Number += Characters[i]
            product['CPU-fan'] = Number[0]
        # CPU/Water Pump Fan 4-pin
        if ID[i] == "p27586":
            Number = []
            Number += Characters[i]
            product['CPU-waterPump'] = Number[0]
        # Chassis/Water Pump Fan 4-pin
        if ID[i] == "p27587":
            Number = []
            Number += Characters[i]
            product['Chassis-waterPump'] = Number[0]

        i += 1

    return product

def get_links(page_url):
    pagination_pages = []
    request = requests.get(page_url, headers=HEADERS)
    tree = html.fromstring(request.content)
    pages_count = tree.xpath('//div[@class="ib page-num"]//a[last()]/text()')
    print('\nКод ответа корневого УРЛ:', request.status_code)
    print('Всего страниц пейджинации:', pages_count)

    for i in range(int(pages_count[0])):
        url = int(pages_count[0]) - 1 - i
        full_url = f"https://www.e-katalog.ru/list/187/{url}/"
        pagination_pages.append(full_url)

    while len(pagination_pages) != 0:
        current_url = pagination_pages.pop()
        print('Сбор ссылок с URL:', current_url)
        request = requests.get(current_url, headers=HEADERS)
        time.sleep(3)
        tree = html.fromstring(request.content)
        links = tree.xpath("//a[@class='model-short-title no-u']/@href")

        for link in links:
            QUEUE_URL.add(DOMAIN + link)
            Rating.append(DOMAIN + link)
    print('Ссылок на товары считано: ', len(QUEUE_URL))
    print('Должно быть ссылок: ', int(pages_count[0])*24)
    print('Разница: ', (int(pages_count[0])*24) - len(QUEUE_URL))

def main():
    with open('Motherboard.csv', 'a') as csvfile:
        fieldnames = ['Rating', 'ID','Url', 'Manufacturer', 'Name', 'Price_min', 'Price_max', 'Price', 'Status', 'Description', 'Type', 'Socket', 'Form', 'Power-phases', 'VRM', 'Heat-pipes', 'LED', 'LED-synchron',
                      'Metal-backplate', 'Hight', 'Weight', 'Embedded-processor', 'Processor-model', 'Chipset', 'South-bridge', 'BIOS', 'DualBIOS', 'UEFI',
                      'Active-cooling', 'Ram-type', 'Slots', 'Form-slots-RAM', 'Working-mode', 'Max-Ram-Frequency', 'Max-Ram-Size', 'XMP', 'ECC', 'Hybrid-Mode',
                      'Integrated-graphics', 'Model-GPU', 'DVI', 'D-Sub', 'HDMI', 'V-HDMI', 'DisplayPort', 'V-DisplayPort', 'Audio', 'Audio-chanel',
                      'S/P-DIF', 'IDE', 'SATA2', 'SATA3', 'M2', 'M2-interface', 'M2-cooling', 'RAID', 'U.2', 'SAS', 'eSATA', 'Wi-Fi', 'Bluetooth',
                      'LAN-speed', 'N-LAN', 'LAN', 'Type-LAN', 'PCI-E-1x', 'PCI-E-16x', 'N-PCI', 'V-PCI-E', 'PCI-E', 'CrossFire', 'SLI', 'PCI-E-Steel',
                      'USB-2.0', 'USB-3.2-V1', 'USB-3.2-V2', 'USB-C-3.2-V1', 'USB-C-3.2-V2', 'USB-C-3.2-V2x2', 'PS/2', 'LPT', 'COM', 'Thunderbolt', 'Alternate-Mode',
                      'TPM', 'Mother-USB-2.0', 'Mother-USB-3.2-V1', 'Mother-USB-3.2-V2', 'Mother-USB-C-3.2-V1', 'Mother-USB-C-3.2-V2', 'Mother-USB-C-3.2-V2x2', 'ARGB-LED',
                      'RGB-LED', 'Thunderbolt-AIC', 'Other', 'Main-power-connector', 'Processor-power', 'Power-connectors-coolers', 'CPU-fan', 'CPU-waterPump',
                      'Chassis-waterPump']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()

    get_links(URL)

    while len(QUEUE_URL) != 0:
        current_url = QUEUE_URL.pop()
        add_to_csv_from_file(get_data(current_url))


if __name__ == "__main__":
    main()
