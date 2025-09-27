# -*- coding: utf-8 -*-
"""
PyInstaller 打包配置文件
使用命令: pyinstaller build_exe.spec
"""

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    [
        'main.py', 'gui/main_window.py', 'gui/file_list_window.py',
        'core/config_manager.py',
        'core/file_cache_manager.py',
        'core/file_comparator.py',
        'core/file_scanner.py',
        'core/make_win_center.py',
        'core/package_builder.py',
        'core/version_manager.py'
    ],
    pathex=[],
    binaries=[],
    datas=[
        # 如果有静态资源文件，在这里添加
       ('logo.ico', '.'),
       ('gui/*', 'gui'),
       ('core/*', 'core')
    ],
    hiddenimports=[
        'customtkinter',
        'packaging',
        'packaging.version',
        'PIL._tkinter_finder',  # customtkinter 依赖
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小文件大小
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'notebook',
        'jupyter',
        'sphinx',
        'pytest',
        'setuptools',
        'pip',
        'wheel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='996母包打包工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用 UPX 压缩（需要安装 UPX）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示命令行窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.ico'],  # 如果有图标文件，在这里指定
)
