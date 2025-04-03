import win32gui
import re
from win32gui import GetWindowText, GetForegroundWindow

# https://danieldusek.com/feeding-key-presses-to-reluctant-games-in-python.html
# https://gist.github.com/dusekdan/47346537bc25962b4b5a627f996a8fdf
class WindowMgr:
    """Encapsulates some calls to the winapi for window management"""

    def __init__ (self):
        """Constructor"""
        self._handle = None
        
    def __about__(self):
      """This is not my implementation. I found it somewhere on the
      internet, presumably on StackOverflow.com and extended it by
      the last method that returns the hwnd handle."""
      pass

    def find_window(self, class_name, window_name=None):
        """find a window by its class_name"""
        self._handle = win32gui.FindWindow(class_name, window_name)

    def _window_enum_callback(self, hwnd, wildcard):
        """Pass to win32gui.EnumWindows() to check all the opened windows"""
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) is not None:
            self._handle = hwnd

    def find_window_wildcard(self, wildcard):
        """find a window whose title matches the wildcard regex"""
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)

    def set_foreground(self):
        """put the window in the foreground"""
        win32gui.SetForegroundWindow(self._handle)

    def get_hwnd(self):
        """return hwnd for further use"""
        return self._handle

    def get_window_region(self):
        rect = win32gui.GetWindowRect(self.get_hwnd())
        # x = rect[0]
        # y = rect[1]
        # w = rect[2] - x
        # h = rect[3] - y
        return (rect[0],rect[1],rect[2],rect[3])
        # print("Window %s:" % win32gui.GetWindowText(self.get_hwnd()))
        # print("\tLocation: (%d, %d)" % (x, y))
        # print("\t    Size: (%d, %d)" % (w, h))

def correctWindowIsFocused(windowWildcard):
    windowName = GetWindowText(GetForegroundWindow())
    return windowWildcard in windowName