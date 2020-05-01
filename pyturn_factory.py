import pyautogui
import time
import subprocess
import matplotlib.pyplot as plt
from typing import Union
import functools
import pyscreeze
import os
import mss
from PIL import Image
import pywinauto
import pygetwindow as gw
import datetime
import re
import pygetwindow._pygetwindow_win

######################################## Baseline functions ################################################################
def detect_monitor(my_operating_monitor = 0, verbose = True):
    sct = mss.mss()
    combined_resolution = sct.monitors[0]
    each_resolution = sct.monitors[1:]
    if verbose is True:
        msg = ''
        for i in range(len(each_resolution)):
            msg += f"\nmonitor {i}| position: ({each_resolution[i]['left']}, {each_resolution[i]['top']})| size: ({each_resolution[i]['width']}x{each_resolution[i]['height']})"
        print(f'detected {len(each_resolution)} monitors.'+msg)

        print(f'selected monitor is monitor "{my_operating_monitor}"')
    res = []
    for k, v in each_resolution[my_operating_monitor].items():
        res.append(v)
    return tuple(res)

def locate(*images, For=0.0, region=None, grayscale=None, confidence: Union[float,list]=0.8, verbose = False):
    imglist = list(images)
    retVal = [None] * len(imglist)
    if region is None:
        region = detect_monitor(-1, verbose = False) # default monitor is the last(rightmost) one.
    start = time.time()
    if not isinstance(confidence, list):
        confidence = [confidence]
    while True:
        with mss.mss() as sct:
            ltrb = (region[0], region[1], region[0] + region[2], region[1] + region[3])
            x = sct.grab(monitor=ltrb)
        screenshotIm = Image.frombytes("RGB", x.size, x.bgra, "raw", "BGRX")
        for i in range(len(imglist)):
            for conf in confidence:
                try:
                    imglist[i] = pyscreeze._load_cv2(imglist[i], grayscale = grayscale)
                    bbox = pyscreeze.locate(imglist[i], screenshotIm, grayscale = grayscale, confidence = conf)
                    retVal[i] = (int(bbox[0] + bbox[2]/2 + region[0]), int(bbox[1] + bbox[3]/2) + region[1])
                    del imglist[i]
                    if verbose is True:
                        print(f'{i}th image found on confidence {conf}')
                except OSError as e:
                    raise e
                except Exception:
                    pass
        if any(retVal) or time.time() - start > For:
            if len(retVal) == 1:
                return retVal[0], screenshotIm
            else:
                return retVal, screenshotIm

def click(x=None, y=None, n=1, interval=0.0, button=pyautogui.PRIMARY, duration=0.0, tween=pyautogui.linear, pause=0.0, logScreenshot=False, ori = True):
    if isinstance(x, tuple) and y is None:
        x, y = x
    for _ in range(n):
        ori_x, ori_y = pyautogui.position()
        pyautogui.click(x = x, y = y, button = button, duration = duration,tween = tween,logScreenshot = logScreenshot, _pause = False)
        if ori is True:
            pyautogui.moveTo(ori_x, ori_y)
        time.sleep(interval)
    time.sleep(pause)

class image():
    def __init__(self, *paths, confidence: Union[float, list] = 0.8, region = None, grayscale = None, verbose = False, home = '', extension = ''):
        # Variable initialization
        if not home and not extension:
            self.paths = paths
        else:
            self.paths = tuple(home + path + extension for path in paths)
        if not isinstance(confidence, list):
            self.confidence = [confidence]
        self.clicked = False
        self.region = region
        self.grayscale = grayscale
        self.scr, self.location, self.exist = self.locate_images()
        if verbose is True:
            self.verbose(verbose)
    def locate_images(self):
        # for plural *paths: "any(image(*paths).exist)" and "all(image(*paths).exist)" are allowed
        # for singular path: "image(path).exist" is allowed
        res, scr = locate(*self.paths, confidence = self.confidence, region = self.region, grayscale = self.grayscale, verbose = False)
        if not isinstance(res, list):
            res = [res]
        if len(res) == 1:
            return scr, res[0], bool(res[0])
        else:
            return scr, res, [bool(item) for item in res]
    def click(self, n = 1, ax = 0, ay = 0, interval=0.0, duration=0.0, tween=pyautogui.linear, pause=0.0, button=pyautogui.PRIMARY, ori = False):
        if not isinstance(self.exist, list):
            exist = [self.exist]
        else:
            exist = self.exist
        if any(exist) is False:
            return
        else:
            for i in range(len(exist)):
                if exist[i] is True:
                    if len(self.paths) == 1:
                        x, y = self.location
                    else:
                        x, y = self.location[i]
                    click(x + ax, y + ay, n, interval, button, duration, tween, pause, ori = ori)
                    self.clicked = True
                    return

    def verbose(self, v):
        # display images
        n_img = len(self.paths)
        if v is True:
            if n_img == 1:
                plt.imshow(plt.imread(self.paths[0]))
                plt.show()
            else:
                fig = plt.figure()
                for i in range(n_img):
                    fig.add_subplot(1, n_img, i + 1)
                    plt.imshow(plt.imread(self.paths[i]))
                plt.show()

def exception(exc):  # if exception met, abandon all turn progress. And goto specific turn.
    for item in exc:
        if image(item[0], verbose=False).exist:
            return True, item[1]

def debug_process(scr, turn, done):
    if scr is None:
        return
    now = datetime.datetime.today()
    name = now.strftime('%Y-%m-%d_%H')
    if name not in os.listdir():
        os.mkdir(name)
        with open(f'./{name}/{name}.txt', 'w', encoding = 'utf-8') as f:
            f.write('')
    scr.save(f'./{name}/{turn}.png')
    with open(f'./{name}/{name}.txt', 'a') as f:
        f.write(f"{turn}/{'fail'*(not done)}+{'success'*done}")
    return

def focus_to_window(window_title=None):
    window = gw.getWindowsWithTitle(window_title)[0]
    if window.isActive == False:
        pywinauto.application.Application().connect(handle=window._hWnd).top_window().set_focus()
def change_turns(below, n):
    matches = re.finditer(f'(if turn ?== ?(\d+))|(goto\((\d+)\))', below, re.MULTILINE)
    k = 0
    for matchNum, match in enumerate(matches):
        if match.groups()[1]:
            number_part = 1
        elif match.groups()[3]:
            number_part = 3
        ind = match.span(number_part + 1)
        old_num = match.groups()[number_part]
        new_num = int(old_num) + n
        below = below[:ind[0] + k] + str(new_num) + below[ind[1] + k:]
        if len(str(new_num)) > len(old_num):
            k += 1
    return below
def getWindowForever(title):
    window = []
    while not window:
        window = pyautogui.getWindowsWithTitle(title)
    window = window[0]
    return window # type: pygetwindow._pygetwindow_win.Win32Window

# attach "turn_controller" to any action. action return should contain boolean
def turn_controller(action, debug_env = True):
    def wrapper_function(*args, fail_then_to = None, For = 3.0, pause = 2.0, exc = (), **kwargs):
        # init
        global turn; turn_before = turn
        global again
        if again is False:
            For = 0
        timeout = time.time() + For
        # keep doing the action until {timeout}
        while True:
            # action_return will be either (done:bool, scr:Image) or (done:bool,)
            action_return = action(*args, **kwargs)
            if isinstance(action_return, bool):
                done = action_return
            else: # in case action_return is (True, Image) or (True,)
                done = action_return[0]
                if len(action_return) == 2:
                    scr = action_return[1] # type:PIL.Image.Image
                else:
                    scr = None
            if done:
                turn += 1
                again = True
                after_done = time.time()
                break
            # after timeout, 3 cases
            if time.time() > timeout:
                # 1. exception check : when exception -> goto specified turn
                exc_res = exception(exc)
                if exc_res is not False:
                    turn = exc_res[1]
                    break
                # 2. again is True: go back in default
                elif again is True:
                    if fail_then_to:
                        turn = fail_then_to
                        break
                    else:
                        turn -= 1
                        break
                # 3. again is False: move on to next turn
                else:
                    turn += 1
                    break

        print(f"turn {turn_before} : {'fail'*(not done)}+{'success'*done} --> {turn}")
        if debug_env is True:
            debug_process(scr, turn_before, done)
        while time.time() - after_done < pause:
            time.sleep(0.1) # 디버그 등등 이후에도 pause 가 더 남았으면, 그냥 기다림
        return
    return wrapper_function

@turn_controller
def try_click(*img_paths, region = None, confidence = 0.8, n = 1, nSearch = False, interval = 2.0, ax = 0, ay = 0, verbose = True):
    img = image(*img_paths, confidence = confidence, verbose = verbose, region = region)
    if nSearch is False:
        if interval == 2.0:
            interval = 0.3
        img.click(n = n, interval = interval, ax=ax, ay=ay)
    if nSearch is True:
        while True:
            img.click(n = 1, ax = ax, ay = ay)
            if img.clicked is True:
                n -= 1
                img.clicked = False
                time.sleep(interval)
            if n < 1:
                break
    return True, img.scr

def goto(to: Union[int,float]):
    global turn
    print(f'turn has been redirected: {turn} --> {to}')
    turn = to

@turn_controller
def drag(From:tuple, To:tuple, duration=0.3):
    from_x, from_y = From
    To_x, To_y = To
    ori_x, ori_y = pyautogui.position()
    pyautogui.moveTo(from_x, from_y)
    pyautogui.dragTo(To_x, To_y, duration=duration)
    pyautogui.moveTo(ori_x, ori_y)
    return True
######################################## Utility functions ############################################################

def spacing(turn, n, script_name = None):
    if script_name is None:
        script_name = __file__
        if script_name is '<input>':
            script_name = 'pyauto.py'
            if script_name not in os.listdir():
                print("if you are using interactive interpreter like pycharm's console and changed script name from pyauto.py,"
                      f" you should specify current script name. || detected default script_name : {script_name}")
    with open(script_name, mode='r') as f:
        script = f.read()

    pattern = re.compile(f'if turn ?== ?{turn}')
    until = pattern.search(script).span()[0]
    above = script[:until]
    below = script[until:]
    below = change_turns(below, n)

    script = above + below

    with open(script_name, mode = 'w') as f:
        f.write(script)
#################################################################### What you are likely to do #####################
### Basic actions
# image('image1').exist
# image('image1').location
# image('image1').click()
# image('image1').clicked
# x, y = locate('image1','image2', confidence = 0.8)
# click(x, y, n = 12)
# drag(from = window.bottom, to = image('image2').location)
# goto(10)

### check window status and switch around
# window.activate()
# window.maximize() # pyautogui is scale dependent, so never ever try to detect an image at different scales
# window.center
# window.box
# window.moveTo() # pyautogui only works on main monitor. So, move it to main monitor.

### Mouse Drag templete
# pyautogui.moveTo(window.center) # pyautogui.moveTo(image('an_image.png').location)

### modify default parameters: you can change source function, or below
# try_click = functools.partial(try_click, For = 10) # change default parameters. applied to all try_click actions
# try_click = functools.partial(try_click, ) # change default parameters. applied to all try_click actions

### miscellaneous
# pyautogui.typewrite() # keyboard typing
# proc.kill()

### Syntax example
# if image('image1').exist:
#     image('image2').click(n = 2)
######################################## User Configuration ############################################################
if __name__ == "__main__":
    class image(image):  # inherit image class and modify it. without it, image class gets absolute path.
        def __init__(self, *paths, confidence: Union[float, list] = 0.8, region = None, grayscale = None, verbose = False, home = '', extension = ''):
            if not home: # No specific parameter for home. then,
                home = './'  # give default parameters
            elif not home.endswith('/'): # in case you missed out slash
                home = home + '/'
            if not extension:
                extension = '.png'
            if not region: # No specific parametor for which monitor. then,
                region = detect_monitor(-1, verbose = False) # the rightmost monitor is where image locate works.
                # or you can specify small region where locate_image works, like region = tuple(left, top, width, height)
                # specifying small region increases locating speed dramatically, because taking a screenshot itself takes long time.
            super().__init__(*paths, confidence = confidence, region = region, grayscale = grayscale, verbose = verbose, home = home, extension = extension)
        def click(self, n = 1, ax = 0, ay = 0, interval=0.0, duration=0.0, tween=pyautogui.linear, pause=0.0, logScreenshot=False, button=pyautogui.PRIMARY):
            super().click(n = n, ax = ax, ay = ay, interval=interval, duration=duration, tween=tween, pause=pause, button=button)

        exc = (('0_exception', -10),) # check everytime if this image exists. then, go to the specified turn.
        exc = ()  # disable exception checking
        exception = functools.partial(exception, exc = exc)

        proc = subprocess.Popen('Program_path_you_want_to_run');time.sleep(3)

        window = getWindowForever("window_title")
        x,y,w,h = detect_monitor(-1)
        window.moveTo(x,y)
        window.resizeTo(w,h)

        x_qua = window.size[0]/3
        y_qua = window.size[1]/3
        center = window.center
        top = (window.center[0], window.center[1] - y_qua) # 1/4 from top
        bottom = (window.center[0], window.center[1] + y_qua) # 3/4 from bottom
        left = (window.center[0] - x_qua, window.center[1])
        right = (window.center[0] + x_qua, window.center[1])

        global_count = 1
        turn = 1
        checkpoint = 0
        turn_history = []
        loop_count = 0
        count = 1
        while global_count >= 1:
            if turn == -10: # when there is critical exception, you can restart from exceptional turn -10
                proc.kill()
                time.sleep(3)
                subprocess.Popen('your_program')
                time.sleep(20)
                goto(1)

        ################################################ BODY BORDER ###########################################################
            if turn == 999:
                proc.kill()

            turn_history.append(turn)
            loop_count += 1
            if loop_count > 100:
                loop_count = 0
                if len(set(turn_history[-50:])) < 3 and count == 1:
                    break