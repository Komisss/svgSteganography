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

#saveLabels для сохранения ссылки на svg при их выводе на экран 
saveLabels = []
x = ''
tree = ''
encodedSvg = ''

#Кодирование и декодирование сообщения
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

#Преобразование линии в полигон
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

#Встраивание сообщения в координаты промежуточных узлов ломаной. Выводит элемент ломаной линии в дереве SVG с внедренным сообщением.
def embed_message(polyline, message):
    # Преобразуем сообщение в биты
    bits = text_to_bits(message)

    # Встраиваем биты сообщения в наименее значимые биты координат
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

#Кодирование сообщения
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
            line.attrib['col'] = str(len(text_to_bits(enterMessage.get("1.0", END))))
            colAdded = not colAdded
        newPolyline = embed_message(polyline, enterMessage.get("1.0", END))
        line.attrib['points'] = ' '.join(newPolyline.attrib['points'])
        # Надо в svg как-то запихнуть все polyline  0,0 -> 00000000 00110100 00100000
        # разбиваем количество символов в сообщении на количество линий. Получаем примерно одинаковые по длине подсообщения и запихиваем их в координаты полигона
    tree.write("output.svg")
    pathToOutputFile = os.path.abspath(os.curdir) + '\output.svg'
    global encodedSvg
    encodedSvg = tksvg.SvgImage(file=pathToOutputFile)
    label = tk.Label(image=encodedSvg, height=300, width=300, background="#FFCDD2")
    label.grid(row=0, column=2)
    saveLabels.append(encodedSvg)

#Раскодирование сообщения
def decodeMessage(polygons, bitsLength):
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
    label = tk.Label(image=svg_image, height=300, width=300, background="#FFCDD2", borderwidth=5, relief="groove")
    label.grid(row=0, column=0)
    saveLabels.append(svg_image)

#Скачивание закодированной svg
def downloadSvg():
    downloads_path = str(Path.home() / "Downloads")
    first_date = datetime.datetime(1970, 1, 1)
    time_since = datetime.datetime.now() - first_date
    seconds = int(time_since.total_seconds())
    tree.write(downloads_path + f'\\output{seconds}.svg')
    
#Декодирование svg
def decodeSvg():
    svg = tree.getroot()
    polygons = svg.findall("polygon")
    global decodedMessage
    decodedMessage = decodeMessage(polygons, int(polygons[0].attrib.get('col')))
    decodMessage.delete("1.0", END)
    decodMessage.insert("1.0", decodedMessage)


focusBorderImageData = '''
    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
    Ry/99NIz//oGrZpUUEAAOw==
'''

borderImageData = '''
    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
'''

# Создать окно tkinter
root = Tk()
message = StringVar()
decodedMessage = StringVar()
root.title("Стеганография")     # устанавливаем заголовок окна
root.geometry("1200x950")    # устанавливаем размеры окна
root.configure(bg='#A6CAC7')
label = Label(text="Стеганография СВГ") # создаем текстовую метку

for c in range(3): root.columnconfigure(index=c, weight=1)
for r in range(5): root.rowconfigure(index=r, weight=1)
 

#btnDownload = ttk.Button(text="Загрузить", command=click)
loadImage = tk.PhotoImage(file="images/Download.png")
btnDownload = Button(root, relief='flat', bg='#A6CAC7', image=loadImage, command=open_img)
btnDownload.grid(row=1, column=0)

uploadImage = tk.PhotoImage(file="images/Upload.png")
btnUpload = ttk.Button(relief='flat', bg='#A6CAC7', image=uploadImage, command=downloadSvg)
btnUpload.grid(row=1, column=2)

encodeImage = tk.PhotoImage(file="images/Encode.png")
btnEncode = ttk.Button(relief='flat', bg='#A6CAC7', image=encodeImage, command=encodeMessage)
btnEncode.grid(row=2, column=1)

decodeImage = tk.PhotoImage(file="images/Decode.png")
btnDecode = ttk.Button(relief='flat', bg='#A6CAC7', image=decodeImage, command=decodeSvg)
btnDecode.grid(row=3, column=1)

borderImage = tk.PhotoImage("borderImage", data=borderImageData)
focusBorderImage = tk.PhotoImage("focusBorderImage", data=focusBorderImageData)
enterMessage = ttk.Text(height=5, width=30, padx='10px', pady='10px', bg='#EEE6DD', fg='#1D5B58', font='Arial 17')
enterMessage.grid(row=4, column=0)

decodMessage = ttk.Text(height=5, width=30, padx='10px', pady='10px', bg='#EEE6DD', fg='#1D5B58', font='Arial 17')
decodMessage.grid(row=4, column=2)


# # Запустить главное окно
root.mainloop()

