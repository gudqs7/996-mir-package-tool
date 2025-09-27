import ctypes
import os
import sys


def set_tree_font(tree):
    """设置tree字体"""
    items = tree.get_children()  # 获取所有的单元格
    for item in items:
        tree.item(item, tags='oddrow')  # 对每一个单元格命名
        tree.tag_configure('oddrow', font='Arial 10')  # 设定treeview里字体格式font=ft


def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和打包后环境"""
    try:
        # PyInstaller 创建临时文件夹存储资源
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def set_win_icon(win):
    # 检查文件是否存在（用于调试）
    icon_path = resource_path('logo.ico')
    if not os.path.exists(icon_path):
        print(f"图标文件未找到: {icon_path}")
        # 可以设置一个默认图标或跳过
    else:
        try:
            win.iconbitmap(icon_path)
            print(f"图标加载成功")
        except Exception as e:
            print(f"图标加载失败: {e}")


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
