import ctypes

import customtkinter as ctk


def get_windows_scaling_simple():
    """简化的Windows缩放检测"""
    try:
        # 设置DPI感知
        ctypes.windll.user32.SetProcessDPIAware()

        # 获取系统DPI
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, hdc)

        return dpi / 96.0
    except:
        return 1.0


def center_on_screen(win):
    """窗口显示后自动居中"""
    win.update_idletasks()  # 更新窗口信息

    scaling = get_windows_scaling_simple()
    width = win._current_width * scaling
    height = win._current_height * scaling

    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    x = int((screen_width - width) // 2)
    y = int((screen_height - height) // 2)

    # print(f'screen_width={screen_width} screen_height={screen_height} width={width} height={height}')
    # print(f'+{x}+{y}')

    win.geometry(f"+{x}+{y}")
