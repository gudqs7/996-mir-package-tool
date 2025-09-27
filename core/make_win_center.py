
def center_on_screen(win):
    """窗口显示后自动居中"""
    win.update_idletasks()  # 更新窗口信息

    width = win.winfo_width()
    height = win.winfo_height()

    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    print(f'screen_width={screen_width} screen_height={screen_height} width={width} height={height}')
    x = 0
    y = 0

    win.geometry(f"+{x}+{y}")