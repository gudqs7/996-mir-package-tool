#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能测试脚本
用于验证程序的各项功能是否正常工作
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试模块导入"""
    print("✨ 正在测试模块导入...")
    
    try:
        from core.file_scanner import FileScanner
        from core.version_manager import VersionManager
        from core.package_builder import PackageBuilder
        from core.file_comparator import FileComparator
        print("✓ 核心模块导入成功")
        
        import customtkinter as ctk
        import packaging
        print("✓ 外部依赖导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_file_scanner():
    """测试文件扫描器"""
    print("\n✨ 正在测试文件扫描器...")
    
    try:
        from core.file_scanner import FileScanner
        
        # 创建临时测试目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建测试文件
            test_file = temp_path / "test.txt"
            test_file.write_text("测试内容", encoding='utf-8')
            
            # 创建测试子目录
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()
            (sub_dir / "test2.py").write_text("print('hello')", encoding='utf-8')
            
            # 创建应被排除的文件
            (temp_path / "test.exe").write_bytes(b"fake exe")
            
            # 扫描文件
            scanner = FileScanner()
            result = scanner.scan_directory(temp_path)
            
            # 验证结果
            assert len(result) == 2, f"预期2个文件，实际{len(result)}个"
            assert "test.txt" in result, "缺少 test.txt"
            assert "subdir/test2.py" in result, "缺少 subdir/test2.py"
            assert "test.exe" not in result, "exe文件应该被排除"
            
            # 验证hash值
            for file_path, info in result.items():
                assert 'hash' in info, f"{file_path} 缺少hash信息"
                assert 'size' in info, f"{file_path} 缺少大小信息"
                assert len(info['hash']) == 64, f"{file_path} hash长度不正确"
        
        print("✓ 文件扫描器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 文件扫描器测试失败: {e}")
        return False

def test_version_manager():
    """测试版本管理器"""
    print("\n✨ 正在测试版本管理器...")
    
    try:
        from core.version_manager import VersionManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            
            # 初始化版本管理器
            vm = VersionManager(cache_dir)
            
            # 测试初始版本
            first_version = vm.get_next_version()
            assert first_version == "v1.0.0", f"预期 v1.0.0，实际 {first_version}"
            
            # 添加第一个版本
            file_info = {
                "test.txt": {"size": 100, "hash": "abc123", "mtime": 1234567890}
            }
            vm.add_version("v1.0.0", file_info, True, "首个版本")
            
            # 测试下一个版本
            next_version = vm.get_next_version()
            assert next_version == "v1.1.0", f"预期 v1.1.0，实际 {next_version}"
            
            # 测试全量版本
            full_version = vm.get_next_version(True)
            assert full_version == "v2.0.0", f"预期 v2.0.0，实际 {full_version}"
            
            # 测试文件比较
            new_file_info = {
                "test.txt": {"size": 200, "hash": "def456", "mtime": 1234567891},
                "new.txt": {"size": 50, "hash": "ghi789", "mtime": 1234567892}
            }
            
            added, modified, deleted = vm.compare_files(new_file_info)
            assert "new.txt" in added, "应该检测到新增文件"
            assert "test.txt" in modified, "应该检测到修改文件"
            
        print("✓ 版本管理器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 版本管理器测试失败: {e}")
        return False

def test_package_builder():
    """测试打包构建器"""
    print("\n✨ 正在测试打包构建器...")
    
    try:
        from core.package_builder import PackageBuilder
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建源文件
            source_dir = temp_path / "source"
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("测试内容1")
            (source_dir / "file2.py").write_text("print('test')")
            
            sub_dir = source_dir / "subdir"
            sub_dir.mkdir()
            (sub_dir / "file3.md").write_text("# 测试")
            
            # 创建包
            output_file = temp_path / "test.zip"
            files_to_include = ["file1.txt", "file2.py", "subdir/file3.md"]
            
            builder = PackageBuilder()
            success = builder.create_package(source_dir, output_file, files_to_include)
            
            assert success, "打包应该成功"
            assert output_file.exists(), "zip文件应该存在"
            
            # 验证包内容
            import zipfile
            with zipfile.ZipFile(output_file, 'r') as zf:
                file_list = zf.namelist()
                assert "file1.txt" in file_list, "包中应该包含 file1.txt"
                assert "file2.py" in file_list, "包中应该包含 file2.py"
                assert "subdir/file3.md" in file_list, "包中应该包含 subdir/file3.md"
            
            # 测试包信息
            info = builder.get_package_info(output_file)
            assert info is not None, "应该能获取包信息"
            assert info['file_count'] == 3, f"预期3个文件，实际{info['file_count']}个"
        
        print("✓ 打包构建器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 打包构建器测试失败: {e}")
        return False

def test_file_comparator():
    """测试文件对比器"""
    print("\n✨ 正在测试文件对比器...")
    
    try:
        from core.file_comparator import FileComparator, ChangeType
        
        # 创建测试数据
        old_files = {
            "file1.txt": {"hash": "abc123", "size": 100, "mtime": 1000},
            "file2.py": {"hash": "def456", "size": 200, "mtime": 2000},
            "deleted.txt": {"hash": "xyz999", "size": 50, "mtime": 3000}
        }
        
        new_files = {
            "file1.txt": {"hash": "abc123", "size": 100, "mtime": 1000},  # 未变化
            "file2.py": {"hash": "def789", "size": 250, "mtime": 2001},  # 已修改
            "new_file.md": {"hash": "new123", "size": 150, "mtime": 4000}  # 新增
        }
        
        comparator = FileComparator()
        changes = comparator.compare_file_lists(old_files, new_files)
        
        # 验证结果
        change_types = {change.file_path: change.change_type for change in changes}
        
        assert "new_file.md" in change_types, "应该检测到新增文件"
        assert change_types["new_file.md"] == ChangeType.ADDED, "新文件类型应该是 ADDED"
        
        assert "file2.py" in change_types, "应该检测到修改文件"
        assert change_types["file2.py"] == ChangeType.MODIFIED, "修改文件类型应该是 MODIFIED"
        
        assert "deleted.txt" in change_types, "应该检测到删除文件"
        assert change_types["deleted.txt"] == ChangeType.DELETED, "删除文件类型应该是 DELETED"
        
        assert "file1.txt" not in change_types, "未变化的文件不应该出现在变更列表中"
        
        print("✓ 文件对比器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 文件对比器测试失败: {e}")
        return False

def test_gui_imports():
    """测试GUI模块导入（不启动界面）"""
    print("\n✨ 正在测试GUI模块导入...")
    
    try:
        # 不在此处实际创建 GUI，只测试导入
        from gui.main_window import IncrementalPackerApp
        from gui.file_list_window import FileListWindow
        from gui.diff_viewer import DiffViewer
        from gui.settings_window import SettingsWindow
        
        print("✓ GUI模块导入成功")
        return True
        
    except Exception as e:
        print(f"❌ GUI模块导入失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("增量打包工具 - 功能测试")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("文件扫描器", test_file_scanner),
        ("版本管理器", test_version_manager),
        ("打包构建器", test_package_builder),
        ("文件对比器", test_file_comparator),
        ("GUI模块", test_gui_imports)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed} 个，失败 {failed} 个")
    
    if failed == 0:
        print("✨ 所有测试通过！程序已准备好可以使用。")
        return True
    else:
        print(f"⚠️  有 {failed} 个测试失败，请检查代码或依赖。")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
