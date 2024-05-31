import datetime
import os
import xml.etree.ElementTree as ET
from tkinter import filedialog
from tkinter import *
import tkinter as tk
import tkinter as ttk
import svgwrite
from svgwrite import Drawing
from PIL import Image, ImageTk
import numpy as np
import binascii
from svglib.svglib import svg2rlg
import tksvg
from pathlib import Path
saveLabels = []
x = ''
tree = ''
encodedSvg = ''

class SvgCanvas(tk.Canvas):
    def __init__(self, master, *kwargs):
        super().__init__(master, *kwargs)
        self.svg_image = None

    def load_svg(self, svg_path):
        # Загрузить SVG-изображение из файла
        image = Image.open(svg_path)
        self.svg_image = ImageTk.PhotoImage(image)

        # Отобразить SVG-изображение в виджете
        self.create_image(0, 0, image=self.svg_image, anchor=tk.NW)

def text_to_bits(text, encoding='utf-8', errors='surrogatepass'):
    bits = bin(int(binascii.hexlify(text.encode(encoding, errors)), 16))[2:]
    return bits.zfill(8 * ((len(bits) + 7) // 8))

def text_from_bits(bits, encoding='utf-8', errors='surrogatepass'):
    n = int(bits, 2)
    return int2bytes(n).decode(encoding, errors)

def int2bytes(i):
    hex_string = '%x' % i
    n = len(hex_string)
    return binascii.unhexlify(hex_string.zfill(n + (n & 1)))

def create_polyline(line):
    """Создает ломаную линию из прямой линии.

    Args:
        line: элемент прямой линии в дереве SVG.

    Returns:
        Элемент ломаной линии в дереве SVG.
    """

    x1, y1, x2, y2 = line.attrib["x1"], line.attrib["y1"], line.attrib["x2"], line.attrib["y2"]
    num_segments = max([int(x1), int(y1), int(x2), int(y2)]) * 35  # Количество сегментов ломаной линии

    polyline = ET.Element("polyline")

    for i in range(num_segments + 1):
        if "points" not in polyline.attrib:
            polyline.attrib["points"] = f"{(int(int(x1) + (i / num_segments) * (int(x2) - int(x1))))}," +  f"{(int(int(y1) + (i / num_segments) * (int(y2) - int(y1))))} "
    
        else:
            polyline.attrib["points"] += f"{(int(int(x1) + (i / num_segments) * (int(x2) - int(x1))))}," + f"{(int(int(y1) + (i / num_segments) * (int(y2) - int(y1))))} "

    polyline.attrib["points"] = polyline.attrib["points"].strip()

    return polyline


def embed_message(polyline, message):
    """Встраивает сообщение в координаты промежуточных узлов ломаной.

    Args:
        polyline: элемент ломаной линии в дереве SVG.
        message: сообщение для встраивания.

    Returns:
        Элемент ломаной линии в дереве SVG с внедренным сообщением.
    """

    # Преобразуем сообщение в биты
    bits = text_to_bits(message)

    # Встраиваем биты в наименее значимые биты координат
    points = polyline.attrib["points"].split()
    newPoints = ''
    for i, bit in enumerate(bits):
        point = points[i].split(",")
        byte = text_to_bits(point[0])
        newByte = byte[:-1] + bit
        point[0] = text_from_bits(newByte)
        points[i] = f'{point[0]},{point[1]}'
    polyline.attrib["points"] = points
    return polyline

def decodeMessage(polygons, bitsLength):
    """Встраивает сообщение в координаты промежуточных узлов ломаной.

    Args:
        svg: SVG.

    Returns:
        Раскодированное сообщение.
    """
    lsbMessage = ''
    bitsCount = 0
    for polygon in polygons:
        points = polygon.attrib["points"].split()
        for point in points:
            pointSplited = point.split(',')
            byte = text_to_bits(pointSplited[0])
            lsb = byte[len(byte) - 1]
            lsbMessage += str(lsb)
            bitsCount += 1
            if(bitsCount == bitsLength):
                break
        if(bitsCount == bitsLength):
                break
    global decodedMessage
    decodedMessage = text_from_bits(lsbMessage)
    return decodedMessage

#Открытие и запись svg
def openfn():
    filename = filedialog.askopenfilename(title='open')
    return filename
def open_img():
    global tree
    x = openfn()
    tree = ET.parse(x)
    svg_image = tksvg.SvgImage(file=x)
    label = tk.Label(image=svg_image)
    label.grid(row=0, column=0)
    saveLabels.append(svg_image)

def encodeMessage():
    # Загружаем SVG-файл
    svg = tree.getroot()

    # Находим все прямые линии в SVG 
    lines = svg.findall("line")
    # Преобразуем прямые линии в ломаные и внедряем сообщение
    colAdded = False
    for line in lines:
        polyline = create_polyline(line)
        line.attrib.pop('x1')
        line.attrib.pop('y1')
        line.attrib.pop('x2')
        line.attrib.pop('y2')
        line.tag = 'polygon'
        if (not colAdded):
            line.attrib['col'] = str(len(text_to_bits(message.get())))
            colAdded = not colAdded
        newPolyline = embed_message(polyline, message.get())
        line.attrib['points'] = ' '.join(newPolyline.attrib['points'])
        # Надо в svg как-то запихнуть все polyline  0,0 -> 00000000 00110100 00100000
        # разбиваем количество символов в сообщении на количество линий. Получаем примерно одинаковые по длине подсообщения и запихиваем их в координаты полигона
    tree.write("output.svg")
    pathToOutputFile = os.path.abspath(os.curdir) + '\output.svg'
    global encodedSvg
    encodedSvg = tksvg.SvgImage(file=pathToOutputFile)
    label = tk.Label(image=encodedSvg)
    label.grid(row=0, column=2)
    saveLabels.append(encodedSvg)

def downloadSvg():
    downloads_path = str(Path.home() / "Downloads")
    first_date = datetime.datetime(1970, 1, 1)
    time_since = datetime.datetime.now() - first_date
    seconds = int(time_since.total_seconds())
    tree.write(downloads_path + f'\\output{seconds}.svg')
    
def decodeSvg():
    svg = tree.getroot()
    polygons = svg.findall("polygon")
    # + 1, потому что иначе декодирование не работает (хз почему) УДАЛИТЬ ОБЯЗАТЕЛЬНО!!!
    global decodedMessage
    decodedMessage = decodeMessage(polygons, int(polygons[0].attrib.get('col')))
    decodMessage.insert(0, decodedMessage)


# Создать окно tkinter
root = Tk()
message = StringVar()
decodedMessage = StringVar()
root.title("Приложение на Tkinter")     # устанавливаем заголовок окна
root.geometry("1200x950")    # устанавливаем размеры окна
label = Label(text="Стеганография СВГ") # создаем текстовую метку

for c in range(3): root.columnconfigure(index=c, weight=1)
for r in range(5): root.rowconfigure(index=r, weight=1)
 

#btnDownload = ttk.Button(text="Загрузить", command=click)
btnDownload = Button(root, text='open image', command=open_img)
btnDownload.grid(row=1, column=0)

btnUpload = ttk.Button(text="Выгрузить", command=downloadSvg)
btnUpload.grid(row=1, column=2)

btnEncode = ttk.Button(text="Кодировать", command=encodeMessage)
btnEncode.grid(row=2, column=1)

btnDecode = ttk.Button(text="Декодировать", command=decodeSvg)
btnDecode.grid(row=3, column=1)

enterMessage = ttk.Entry(textvariable=message)
enterMessage.grid(row=4, column=0)

decodMessage = ttk.Entry()
decodMessage.grid(row=4, column=2)


# # Запустить главное окно
root.mainloop()

