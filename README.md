
# 996三端母包和更新包打包工具


## 安装和使用

### 方式一：直接运行 exe 文件（推荐）

1. 从release下载
2. 双击运行，无需安装 Python 环境

### 方式二：从源码运行

#### 环境要求
- Python 3.7+
- Windows / macOS / Linux

#### 安装步骤

1. **克隆或下载项目**
   ```bash
   # 如果使用 Git
   git clone <repository-url>
   cd incremental_packer
   
   # 或直接下载并解压源码
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行程序**
   ```bash
   python main.py
   ```

#### 打包成 exe

如果您想自己打包成 exe 文件：

```bash
# 一键构建（推荐）
python build.py

# 或手动构建
pip install pyinstaller
pyinstaller build_exe.spec

```

构建完成后，exe 文件将位于 `dist/IncrementalPacker.exe`。

## 使用指南

### 基本操作流程

1. **设置目录**
   - 选择输入目录（需要打包的文件夹）
   - 选择输出目录（zip 文件的保存位置）

2. **扫描文件**
   - 点击“扫描文件”按钮
   - 程序会扫描所有文件并计算 hash 值

3. **查看变化**
   - 如果不是首次扫描，可点击“查看变更”
   - 查看新增、修改、删除的文件列表
   - 双击文件可查看详细差异

4. **执行打包**
   - **首次打包或重置后为全量打包, 后续为增量打包**
   - **全量打包**：打包所有文件
   - **增量打包**：只打包有变化的文件

## 文件结构

```
incremental_packer/
├── main.py                 # 主程序入口
├── requirements.txt        # Python 依赖列表
├── build.py               # 一键构建脚本
├── build_exe.spec         # PyInstaller 配置文件
├── README.md              # 项目说明文档
│
├── core/                  # 核心功能模块
│   ├── __init__.py
│   ├── file_scanner.py       # 文件扫描器
│   ├── version_manager.py     # 版本管理器
│   ├── package_builder.py     # 打包构建器
│   └── file_comparator.py     # 文件对比器
│
└── gui/                   # 用户界面模块
    ├── __init__.py
    ├── main_window.py        # 主窗口
    ├── file_list_window.py   # 文件列表窗口
    ├── diff_viewer.py        # 文件差异查看器
    └── settings_window.py    # 设置窗口
```

## 输出文件结构

在您指定的输出目录中，程序会创建以下结构：

```
output_directory/
├── v1.0.0.zip             # 首个全量包
├── v1.1.0.zip             # 第一个增量包
├── v1.2.0.zip             # 第二个增量包
└── cache/                 # 缓存目录（内部使用）
    ├── versions.json        # 版本信息
    └── latest_scan.json     # 最新扫描结果
```

## 技术特性

### 性能优化
- **多线程并行**：文件扫描和 hash 计算采用线程池并行处理
- **内存优化**：流式读取大文件，避免内存溢出
- **缓存机制**：本地缓存文件状态，减少重复计算

### 安全特性
- **数据完整性**：使用 SHA-256 hash 算法确保文件完整性
- **异常处理**：完善的错误处理和用户提示
- **操作可逆**：所有操作都不会修改原始文件

### 兼容性
- **跨平台**：支持 Windows、macOS、Linux
- **文件系统**：兼容各种文件系统和编码
- **Python 版本**：支持 Python 3.7+

## 常见问题

### Q: 为什么首次运行 exe 文件较慢？
A: 这是正常现象。PyInstaller 打包的程序首次运行需要解压并加载所有组件，后续运行会明显加快。

### Q: 杀毒软件误报怎么办？
A: 这是 PyInstaller 打包程序的常见问题。请将 exe 文件或整个目录添加到杀毒软件的白名单中。

### Q: 可以打包非常大的文件夹吗？
A: 可以。程序采用流式处理和多线程优化，能够处理包含数万个文件的大型项目。建议在设置中调整线程数以获得最佳性能。

### Q: 增量包和全量包有什么区别？
A: 
- **全量包**：包含所有文件，通常用于首次发布或重大版本更新
- **增量包**：只包含新增和修改的文件，体积更小，适合日常更新

### Q: 支持哪些文件类型的差异对比？
A: 程序支持所有文本文件的内容对比（如 .txt、.py、.js、.html 等），二进制文件则显示大小、修改时间等元数据信息。

## 贡献和反馈

如果您在使用过程中遇到问题或有改进建议，欢迎通过以下方式反馈：

- 提交 Issue 报告 Bug 或功能需求
- 参与代码贡献和优化
- 完善文档和使用指南

## 许可证

本项目采用 MIT 许可证，详情请查看 LICENSE 文件。

