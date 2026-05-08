# 遥感样本制作工具 (Remote Sensing Sample Tool)

[![Python 2.7](https://img.shields.io/badge/python-2.7-blue.svg)](https://www.python.org/downloads/release/python-270/)
[![ArcGIS 10.4](https://img.shields.io/badge/ArcGIS-10.4-green.svg)](https://desktop.arcgis.com/en/arcmap/10.4/main/get-started/what-s-new-in-arcgis.htm)
[![Vue.js 3](https://img.shields.io/badge/Vue.js-3.0-4FC08D.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)

> 一款基于 ArcGIS 和 Web 技术的遥感影像样本自动裁剪与分类工具，支持桌面端和 Web 端双模式运行。

## 📖 项目简介

遥感样本制作工具是一款专为遥感影像数据处理设计的自动化工具，能够将大范围的遥感影像和标签数据自动裁剪成标准尺寸的样本 patch，并根据地物类别进行智能分类。该工具广泛应用于深度学习遥感影像分割、目标检测等任务的训练数据准备。

### 核心功能

- 🛰️ **自动 Patch 裁剪**：根据设定的 patch 尺寸和重叠率，自动生成规则网格
- 🏷️ **智能样本分类**：基于矢量标签自动识别正样本，支持 DLMC（地类编码）分组
- 🖼️ **多格式输出**：支持 GeoTIFF、真彩色 JPG、假彩色 JPG 三种格式同时输出
- 🌐 **双模式支持**：提供桌面端（Tkinter）和 Web 端（Vue.js + FastAPI）两种使用方式
- 📊 **实时进度显示**：处理过程可视化，支持平滑进度动画
- 🔧 **灵活参数配置**：支持自定义波段组合、输出路径、作者缩写等

## 🚀 技术栈

### 后端
- **Python 2.7** + **ArcGIS 10.4**（arcpy 地理处理）
- **FastAPI**（Web API 框架）
- **Uvicorn**（ASGI 服务器）

### 前端
- **Vue.js 3**（渐进式 JavaScript 框架）
- **Vite**（构建工具）
- **CSS3**（现代化样式设计）

### 桌面端
- **Tkinter**（Python GUI 库）
- **ttk**（主题化控件）

## 📦 安装步骤

### 环境要求

- Windows 操作系统
- Python 2.7（推荐 ArcGIS 内置 Python）
- ArcGIS Desktop 10.4 或更高版本
- Node.js 16+（Web 端开发）

### 1. 克隆仓库

```bash
git clone https://github.com/Masterq8/RemoteSensingSampleTool.git
cd RemoteSensingSampleTool
```

### 2. 后端环境配置

```bash
# 使用 ArcGIS Python 环境
C:\Python27\ArcGIS10.4\python.exe -m pip install fastapi uvicorn

# 或使用虚拟环境
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 前端环境配置

```bash
cd web_version/vue-app
npm install
```

## 🎯 使用方法

### Web 端模式

1. **启动后端服务**
   ```bash
   cd web_version
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **启动前端开发服务器**
   ```bash
   cd web_version/vue-app
   npm run dev
   ```

3. **访问应用**
   打开浏览器访问 http://localhost:5173

### 桌面端模式

```bash
python remote_sensing_sample_tool.py
```

### 处理流程

1. **上传影像**：选择遥感影像文件（支持 TIFF 格式）
2. **上传标签**：选择对应的矢量标签文件（Shapefile 或 TIFF）
3. **配置参数**：
   - Patch 尺寸：128x128、256x256、512x512 等
   - 重叠率：0%、25%、50%、75%
   - 作者缩写：用于样本命名
   - 输出格式：TIFF、真彩色 JPG、假彩色 JPG
   - 波段组合：自定义真彩色和假彩色波段
4. **开始处理**：系统自动完成 6 步处理流程
5. **下载结果**：处理完成后下载样本数据集

## 📂 项目结构

```
RemoteSensingSampleTool/
├── remote_sensing_sample_tool.py    # 桌面端主程序
├── web_version/                     # Web 端代码
│   ├── main.py                      # FastAPI 主应用
│   ├── processor.py                 # 核心处理逻辑
│   ├── vue-app/                     # Vue.js 前端
│   │   ├── src/
│   │   │   ├── App.vue              # 主组件
│   │   │   └── main.js              # 入口文件
│   │   ├── package.json
│   │   └── vite.config.js
│   ├── uploads/                     # 上传文件存储
│   └── outputs/                     # 处理结果输出
├── requirements.txt                 # Python 依赖
└── README.md                        # 项目文档
```

## 🔧 处理流程详解

工具采用 6 步流水线处理遥感数据：

| 步骤 | 功能 | 进度范围 |
|------|------|----------|
| 1 | 计算坐标并生成 Patch 网格 | 20% → 32% |
| 2 | 创建 Patch 总索引 Shapefile | 32% → 43% |
| 3 | 裁剪标签，识别正样本 | 43% → 55% |
| 4 | 裁剪正样本影像 | 55% → 67% |
| 5 | 样本分类与清洗 | 67% → 78% |
| 6 | 按 DLMC 分组并生成二值标签 | 78% → 90% |
| 完成 | 清理临时文件，生成最终数据集 | 90% → 100% |

## 📝 配置说明

### 输出格式

- **GeoTIFF**：原始影像数据，保留地理坐标信息
- **真彩色 JPG**：使用指定波段（默认 3,2,1）合成 RGB 图像
- **假彩色 JPG**：使用指定波段（默认 4,3,2）合成标准假彩色图像

### DLMC 映射

支持自定义地类编码映射，通过 `dlmc_mapping.json` 文件配置：

```json
{
  "0101": "CZCSYD",
  "0102": "CZCSYD",
  "0201": "GGYDYD"
}
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 感谢 ArcGIS 提供强大的地理处理能力
- 感谢 Vue.js 和 FastAPI 提供优秀的 Web 开发框架

## 📧 联系方式

如有问题或建议，欢迎通过 GitHub Issues 联系我们。

---

**注意**：本项目需要 ArcGIS 授权才能完整运行地理处理功能。
