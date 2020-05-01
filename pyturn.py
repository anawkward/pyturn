import pynput
from pynput.keyboard import Key
import time
from PIL import ImageGrab
import os
import re
from win32api import GetSystemMetrics
from typing import Union
import cv2
import os
import sys
from PIL import Image
import yaml
##############################################################################################
key = down_x = down_y = up_x = up_y = -1
path = 'D:/dev/pycharmproject/pyautogui/'
folders = next(os.walk(path))[1]
path = path+folders[-1]+'/'
manual = '''
1. click : 일반적인 click 지점의 이미지를 기록
2. shift+click : 드래그 기록. 드래그 시작점의 이미지를 기록. 드래그 방향을 간략하게 이름에 함께 기록.
3. caps_lock : 조건 기록. 마우스 클릭 없이 해당 위치의 그림을 Condi 로 기록
4. +- : 큰 이미지, 작은 이미지
'''

def images_resize(path:str, From:tuple, To:Union[tuple,None]=None):
    pngs = [item for item in os.listdir(path) if item[-3:] == 'png']
    full_paths = [path + f for f in pngs]

    for img in full_paths:
        src = Image.open(img) #type: Image.Image
        From = From
        scaling = (To[0] / From[0], To[1] / From[1])
        d1 = src.size[0] * scaling[0]
        d2 = src.size[1] * scaling[1]
        im_dsize = (d1.__round__(), d2.__round__())
        new = src.resize(im_dsize)  # type:Image.Image
        folder = '/'.join(img.split('/')[:-1]) + '/resize/'
        fn = img.split('/')[-1]
        os.makedirs(folder, exist_ok=True)
        new.save(folder + fn)
def images_reresolution():
    return
def pretty_dict(dic:dict):
    lines = []
    for k, v in dic.items():
        k = f'"{k}"'
        v = f'"{v}"'
        line = k + ': ' + v + ','
        lines.append(line)
    lines[-1] = lines[-1][:-1]
    ret = "{\n" + "\n".join(lines) + "\n}"
    return ret
def meta_write(path:str, fn:str, coor:tuple):
    if 'meta.txt' not in os.listdir(path):
        print(f'meta file not found, create new one')
        meta = {
            "supported_monitor_size": "",
            "home": path,
            "process_path": "",
            "window_title": ""
        }
        metafile = open(path + 'meta.txt', 'w+', encoding='UTF-8')
        metafile.write('"info": '+pretty_dict(meta)+ '\n"box": {')
        metafile.close()
    metafile = open(path + 'meta.txt', 'a', encoding = 'utf-8')
    metafile.write('\n"' + fn + '": "' + str(coor) + '",')
    metafile.close()
def do_numbering(path):
    pngs = sorted_alphanumeric([item for item in os.listdir(path) if item[-3:] == 'png'])
    if len(pngs) >= 1:
        number = str((int(pngs[-1].split('_')[0])) + 10)
    else:
        number = '9'
    return number
def on_press(k):
    global k_listener
    global m_listener
    global mouse
    global key
    global path
    numbering = do_numbering(path)
    key = k
    print(f'key "{k}" pressed')
    # Stop Recording
    if k is Key.pause:
        print('Stop Recording !')
        k_listener.stop()
        m_listener.stop()
        print("recommended file name format examples\n"
              "49_Click_n12.png : click this image 12 times\n"
              "59_drag.png : drag parameter, from and to must be filled manually in script\n"
              "229_Click_start.png : loop block starts from 'this' image\n"
              "289_Click_end.png : loop block ends to 'this' image\n"
              "379_Click_center.png : just click window center, not this image\n"
              "389_Click_ax100.png : click not this image, but ax100(right) from this image\n"
              "439_drag_left : drag from this image to left\n" 
              "Any other names than 'click', 'start', 'end', 'n', 'center/top/bottom/left/right', 'drag', 'ax', 'ay'\n"
              "are NOT recognized for scripting, feel free to use custom names for files\n"
              )

        if 'meta.txt' not in os.listdir(path):
            print(f'meta file not found, create new one')
            return
        else:
            metafile = open(path + 'meta.txt', 'rb+')
            metafile.seek(-1, os.SEEK_END)
            metafile.truncate()
            metafile.close()
            metafile = open(path + 'meta.txt', 'a', encoding = 'utf-8')
            metafile.write('}')
            metafile.close()
    # Capture image for condition
    if k is Key.caps_lock:
        print('Saved Condition Image !')
        x,y = mouse.position
        box = (x-50, y-50, x+50, y+50)
        img = ImageGrab.grab(bbox=box)
        key = -1
        fn = numbering + '_Condi' + '.png'
        img.save(path+fn)
        meta_write(path, fn, box)
def on_click(x,y,button,pressed):
    global down_x
    global down_y
    global up_x
    global up_y
    global key
    global path
    numbering = do_numbering(path)
    if pressed:
        (down_x, down_y) = (x, y)
        if key == -1:                                       # just click
            print('Saved Click Images !')
            print(manual)
            box = (down_x - 50, down_y - 50, down_x + 50, down_y + 50)
            img = ImageGrab.grab(bbox=box)
            fn = numbering + '_Click.png'
            img.save(path + fn)
            meta_write(path, fn, box)
        if key != Key.shift:
            try:
                key.char == 'any'
            except:
                print(f'captured with wrong key of "{key}"')
                key = -1
                return
            if key.char == '-':                                       # small click
                print('Saved Click Images(small) !')
                print(manual)
                key = -1
                box = (down_x - 25, down_y - 25, down_x + 25, down_y + 25)
                img = ImageGrab.grab(bbox=box)
                fn = numbering + '_Click.png'
                img.save(path + fn)
                meta_write(path, fn, box)
            elif key.char == '+':                                       # large click
                print('Saved Click Images(large) !')
                print(manual)
                key = -1
                box = (down_x - 100, down_y - 100, down_x + 100, down_y + 100)
                img = ImageGrab.grab(bbox = box)
                fn = numbering + '_Click.png'
                img.save(path + fn)
                meta_write(path, fn, box)
    else:                                                   # on_release
        (up_x, up_y) = (x, y)
        if key == Key.shift and abs(down_x - up_x) + abs(down_y - up_y) > 10: # 드래그가 아주 약간은 움직여야 shift 가 작동하도록.
            key = -1
            print("Mouse drag from", down_x, ",", down_y, "to", up_x, ",", up_y)
            # 모니터 [0,0]

            #               모니터[1920,1080]
            if abs(up_x - down_x) > abs(up_y - down_y) and up_x > down_x: # 오른쪽으로 드래그
                name = '_Drag_To_Right'
            if abs(up_x - down_x) > abs(up_y - down_y) and up_x < down_x: # 왼쪽으로 드래그
                name = '_Drag_To_Left'
            if abs(up_x - down_x) < abs(up_y - down_y) and up_y > down_y: # 아래로 드래그
                name = '_Drag_To_Bottom'
            if abs(up_x - down_x) < abs(up_y - down_y) and up_y < down_y: # 위로 드래그
                name = '_Drag_To_Top'
            box = (down_x - 50, down_y - 50, down_x + 50, down_y + 50)
            img = ImageGrab.grab(bbox=box) # 드래그 시작점 이미지. 끝은 따로 기록안하겠음.
            fn = numbering + name + '.png'
            img.save(path + fn)

def start_check(k):
    global k_listener
    global m_listener
    global key
    if k == Key.f12:
        k_listener = pynput.keyboard.Listener(on_press=on_press)  # listener 스레드를 생성한다.
        m_listener = pynput.mouse.Listener(on_click=on_click)
        print('Recording will start in 3 seconds')
        time.sleep(1)
        print('Recording will start in 2 seconds')
        time.sleep(1)
        print('Recording will start in 1 seconds')
        time.sleep(1)
        key = -1
        k_listener.start()
        m_listener.start()

def sorted_alphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(data, key=alphanum_key)

def images_to_pyauto(path):
    if not path.endswith('/'):
        path = path + '/'
    pyturn_factory_file = open('pyturn_factory.py', mode='r', encoding = 'utf-8')
    pyturn_factory_script = pyturn_factory_file.read()
    head = pyturn_factory_script
#################################### Script Body #######################################################################
    pngs = [item for item in os.listdir(path) if item[-3:] == 'png']
    files = sorted_alphanumeric(pngs)
    full_paths = [path + f for f in files]
    short_paths = [f.split('.')[0] for f in files]
    body = []

    direction = ['Center', 'center', 'Top', 'top', 'Bottom', 'bottom', 'Left', 'left', 'Right', 'right']
    manu = True

    with open(path + 'meta.txt', 'r') as f:
        meta = yaml.load(f.read())
    info = meta['info']
    boxes = meta['box']
    for i in range(len(short_paths)):
        mn = files[i]
        try:
            box = boxes[mn]
        except:
            box = None
        fname = short_paths[i].split('_')
        n = False
        aax = False
        aay = False
        t_line = False
        direc = False
        for fn in fname:
            if fn.startswith('n'):
                n = fn[1:]
            if fn.startswith('ax'):
                aax = fn[2:]
            if fn.startswith('ay'):
                aay = fn[2:]
        if 'Drag' in fname or 'drag' in fname:
            t_line = f"    if turn == {i+1}:  drag(From = image('{short_paths[i]}').location, To = "
            for item in direction:
                if item in fname:
                    t_line = t_line + item.lower()
            t_line = t_line + ')'
        elif 'start' in fname or 'Start' in fname:
            num_start = i + 1
            prev_line = body[i-1]
            prev_line.split(':')[-1].strip()
            prev_action = prev_line.split(':')[-1].strip()

            body[i-1] = f'''    if turn == {i}:
        {prev_action}
    # loop block ↘↘↘
        count = '''
            if n is not False:
                body[i-1] = body[i-1] + n
        elif 'end' in fname or 'End' in fname:
            t_line = f'''    if turn == {i+1}:
        try_click('{short_paths[i]}')
        if count > 1:
            goto({num_start})
            count -= 1
    # loop block ↗↗↗'''
            num_start = None
        if t_line is False and ('Click' in fname or 'click' in fname):
            if manu is True:
                t_line = f"    if turn == {i+1}:  try_click('{short_paths[i]}', confidence = 0.8, For = 3, n = 1, pause = 2, ax = 0, ay = 0, fail_then_to = None, verbose = True)"
                manu = False
            elif 'start' in fname or 'Start' in fname:
                t_line = f"    if turn == {i+1}:  try_click('{short_paths[i]}')"
            else:
                for item in direction:
                    if item in fname:
                        t_line = f"    if turn == {i+1}:  click({item}"
                        direc = True
                        break
                if t_line is False:
                    t_line = f"    if turn == {i+1}:  try_click('{short_paths[i]}'"
                if n is not False:
                    t_line = t_line + ', n = ' + n
                if aax is not False:
                    t_line = t_line + ', ax = ' + aax
                if aay is not False:
                    t_line = t_line + ', ay = ' + aay
                if box is not None:
                    t_line = t_line + ', region = ' + box
                t_line = t_line + ')'
                if direc is True:
                    t_line = t_line + '; turn += 1'
                    direc = False
        elif t_line is False:
            t_line = f"    if turn == {i+1}:  turn += 1"
        body.append(t_line)
#################################### Script foot #######################################################################
    foot = "; global_count -= 1"

    codes = head +'\n'.join(body) + '\n' + foot

    pyfile = open(path+'pyauto.py', 'w+', encoding = 'UTF-8')
    pyfile.write(codes)
    pyfile.close()
####################################################################################################
# initialize
mouse = pynput.mouse.Controller()

print("Baseline manual : 파이썬 스크립트가 실행 중인 상태에서, F12를 누르면 기록 시작. Pause를 누르면 기록 종료.")

start_listener = pynput.keyboard.Listener(on_press=start_check) # Always on to check record starting
start_listener.start()

images_to_pyauto('D:\Dev\PycharmProject\pyautogui/test')