# 🌍 Minecraft World Converter (存档转换器)

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11-yellow)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

这是一个基于 Python 和 Tkinter 构建的现代化桌面工具，旨在简化 **Minecraft
Java版** 与 **基岩版 (Bedrock)** 之间的存档转换流程。核心基于强大的
[Amulet Core](https://github.com/Amulet-Team/Amulet-Core) 库开发。

---

## ✨ 主要功能 (Features)

| 功能            | 说明                                              |
| :-------------- | :------------------------------------------------ |
| 🔄 **双向转换** | 支持 **Java ↔ Bedrock** 跨平台无缝转换            |
| 🔀 **版本切换** | 支持同平台版本升降级 (如 Java 1.20 → Java 1.16)   |
| 📦 **批量处理** | 一键导入多个存档，自动化批量转换                  |
| 🛠️ **存档修复** | 包含“强制修复”模式，通过重新保存区块修复损坏数据  |
| 🎯 **版本选择** | 可指定具体的目标游戏版本 (如 `1.20.1`, `1.19` 等) |
| 🖥️ **图形界面** | 简洁易用的 GUI，无需命令行操作，实时日志显示      |

## 🚀 快速开始 (Quick Start)

### 直接使用 (Windows)

1. 下载最新发布的 `mcconvert.exe`。
2. 双击运行程序。
3. **选择转换模式**：
   - **单存档模式**：转换单个世界文件夹。
   - **批量模式**：添加多个世界文件夹，统一输出到指定目录。
4. **设置参数**：
   - 选择输入/输出路径。
   - 选择目标版本（默认“最新”）。
   - (可选) 勾选“强制修复”以整理区块数据。
5. 点击 **"开始转换"**。

## 🛠️ 开发环境搭建 (Development)

如果您想参与开发或从源码运行：

### 前置要求

- Python 3.10 或 3.11 (推荐)
- Windows 环境 (建议)

### 安装步骤

1. **克隆仓库**

   ```bash
   git clone https://github.com/chewthaocc/minecraft_convert.git
   cd minecraft_convert
   ```

2. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

3. **运行代码**
   ```bash
   python main.py
   ```

## 📦 打包发布 (Build)

本项目使用 `PyInstaller` 打包为单文件可执行程序。

```bash
pyinstaller --noconsole --onefile --name mcconvert --paths src --collect-all amulet main.py
```

> 打包后的文件位于 `dist/mcconvert.exe`。

## ⚠️ 注意事项 (Notes)

- **备份**：转换操作属于高风险行为，**请务必在转换前备份您的原始存档！**
- **版本支持**：目标版本列表依赖于 Amulet 库的更新。如果选择的版本不受支持，工具将尝试使用最接近的兼容版本。
- **运行库**：如果在其他电脑上运行报错（缺少 DLL），请安装
  [Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)。

## 📝 开源协议

MIT License. 本工具基于 Amulet-Core 开发，使用请遵循其开源协议。
