import datetime
import os
import xml.etree.ElementTree as ET
from tkinter import filedialog
from tkinter import *
import tkinter as tk
import tkinter as ttk
import binascii
import tksvg
from pathlib import Path

#saveLabels для сохранения ссылки на svg при их выводе на экран 
saveLabels = []
x = ''
tree = ''
encodedSvg = ''
svg_image = ''

#Кодирование и декодирование сообщения
def textToBits(text, encoding='utf-8', errors='surrogatepass'):
    bits = bin(int(binascii.hexlify(text.encode(encoding, errors)), 16))[2:]
    return bits.zfill(8 * ((len(bits) + 7) // 8))

def textFromBits(bits, encoding='utf-8', errors='surrogatepass'):
    n = int(bits, 2)
    return intToBytes(n).decode(encoding, errors)

def intToBytes(i):
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
    bits = textToBits(message)

    # Встраиваем биты сообщения в наименее значимые биты координат
    points = polyline.attrib["points"].split()
    for i, bit in enumerate(bits):
        point = points[i].split(",")
        byte = textToBits(point[0])
        newByte = byte[:-1] + bit
        point[0] = textFromBits(newByte)
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
            line.attrib['col'] = str(len(textToBits(enterMessage.get("1.0", END))))
            colAdded = not colAdded
        newPolyline = embed_message(polyline, enterMessage.get("1.0", END))
        line.attrib['points'] = ' '.join(newPolyline.attrib['points'])
        # 
    tree.write("output.svg")
    pathToOutputFile = os.path.abspath(os.curdir) + '\output.svg'
    global encodedSvg
    encodedSvg = tksvg.SvgImage(file=pathToOutputFile)
    label = tk.Label(image=encodedSvg, height=300, width=300, background="#FFCDD2")
    label.grid(row=0, column=2)
    saveLabels.append(encodedSvg)
    global btnUploadState
    btnUpload['state'] = 'normal'

#Раскодирование сообщения
def decodeMessage(polygons, bitsLength):
    lsbMessage = ''
    bitsCount = 0
    for polygon in polygons:
        points = polygon.attrib["points"].split()
        for point in points:
            pointSplited = point.split(',')
            byte = textToBits(pointSplited[0])
            lsb = byte[len(byte) - 1]
            lsbMessage += str(lsb)
            bitsCount += 1
            if(bitsCount == bitsLength):
                break
        if(bitsCount == bitsLength):
                break
    global decodedMessage
    decodedMessage = textFromBits(lsbMessage)
    return decodedMessage

#Открытие и запись svg
def openfn():
    filename = filedialog.askopenfilename(title='open')
    return filename
def open_img():
    global tree
    x = openfn()
    tree = ET.parse(x)
    global svg_image
    svg_image = tksvg.SvgImage(file=x)
    label = tk.Label(image=svg_image, height=300, width=300, background="#FFCDD2", borderwidth=5, relief="groove")
    label.grid(row=0, column=0)
    saveLabels.append(svg_image)
    btnDecode['state'] = 'normal'
    btnEncode['state'] = 'normal'

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

def on_modified(event):
    if (enterMessage.get("1.0", END) == '' or enterMessage.get("1.0", END) == '\n'):
        btnEncode['state'] = 'disabled'
    elif (svg_image == ''):
        btnEncode['state'] = 'disabled'
    else:
        btnEncode['state'] = 'normal'

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
btnUpload = ttk.Button(relief='flat', bg='#A6CAC7', image=uploadImage, command=downloadSvg, state='disabled')
btnUpload.grid(row=1, column=2)

encodeImage = tk.PhotoImage(file="images/Encode.png")
btnEncode = ttk.Button(relief='flat', bg='#A6CAC7', image=encodeImage, command=encodeMessage, state='disabled')
btnEncode.grid(row=2, column=1)

decodeImage = tk.PhotoImage(file="images/Decode.png")
btnDecode = ttk.Button(relief='flat', bg='#A6CAC7', image=decodeImage, command=decodeSvg, state='disabled')
btnDecode.grid(row=3, column=1)
enterMessage = ttk.Text(height=5, width=30, padx='10px', pady='10px', bg='#EEE6DD', fg='#1D5B58', font='Arial 17')
enterMessage.grid(row=4, column=0)
enterMessage.bind("<KeyRelease>", on_modified)

decodMessage = ttk.Text(height=5, width=30, padx='10px', pady='10px', bg='#EEE6DD', fg='#1D5B58', font='Arial 17')
decodMessage.grid(row=4, column=2)


# Запустить главное окно
root.mainloop()

