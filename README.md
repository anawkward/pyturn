under testing. you can use for trial

# < pyturn project >
an automation tool for image click task. use baseline functions from pyautogui

# pyturn.py (recording, scripting)
1. you record pictures where you click with this
2. this makes script from images

# pyturn_factory.py (source file)
- it has functions and classes to import

# demonstration picture for macro

# description
it's like script language. easy syntax + any python external modules.
- supports multimonitors. you can specify which monitor you want to work with.
- has simple pythonic syntax.
- easy for maintenance. most detailed action can be done changing parameters
- of course, full compatability with other python syntax.


(syntax example)
if image('abc.png').exist:
  click('xyz.png', n = 3)

(actual example)
turn = 1
if turn == -10:
  proc.kill()
if turn == 1:
  try_click('start.png')
if turn == 2:
  try_click('do1-1.png', fail_then_to = 5)
if turn == 3:
  try_click('do1-2.png')
if turn == 4:
  try_click('do1-3.png')
if turn == 5:
  try_click('do2-1.png')
if turn == 6:
  goto(-10)
