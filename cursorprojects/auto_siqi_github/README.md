# 思齐PT自动脚本合集

## 1. 书籍预览图片提取器

一个Python脚本，可以从各种书籍格式（PDF、EPUB、MOBI、CBZ）中提取预览图片，用于创建书籍预览图。

### 功能特点

- **多格式支持**：支持PDF、EPUB、MOBI、CBZ文件
- **智能图片提取**：自动提取封面页和随机预览页
- **白边裁剪**：自动裁剪提取图片的白边
- **增量处理**：跳过已处理的书籍，只提取缺失的图片
- **跨平台**：支持Windows、macOS和Linux
- **灵活配置**：可自定义预览数量和目录路径

### 功能说明

该脚本处理包含书籍文件夹的目录，并从每本书中提取预览图片：

1. **封面页**：始终提取第一页/封面作为`1.jpg`
2. **预览页**：从书籍中提取随机页面作为`2.jpg`、`3.jpg`等
3. **智能裁剪**：自动移除所有提取图片的白边
4. **格式处理**：
   - PDF：直接页面提取
   - EPUB/MOBI：使用Calibre先转换为PDF
   - CBZ：从ZIP压缩包中提取图片

### 系统要求

#### 1. Python依赖

安装所需的Python包：

```bash
pip install -r requirements.txt
```

#### 2. Calibre（用于EPUB/MOBI支持）

**macOS：**
```bash
# 从 https://calibre-ebook.com/download_osx 下载
# 或通过Homebrew安装
brew install --cask calibre
```

**Windows：**
```bash
# 从 https://calibre-ebook.com/download_windows 下载
# 安装到默认位置 (C:\Program Files\Calibre2\)
```

**Linux：**
```bash
# Ubuntu/Debian
sudo apt-get install calibre

# 或从 https://calibre-ebook.com/download_linux 下载
```

### 安装步骤

1. **克隆或下载脚本：**
   ```bash
   git clone <repository-url>
   cd auto_siqi_github
   ```

2. **安装Python依赖：**
   ```bash
   pip install -r requirements.txt
   ```

3. **准备书籍目录结构：**
   ```
   books/
   ├── 书籍合集文件夹/
   │   ├── book1.pdf
   │   └── book2.pdf
   ├── 书籍单本文件夹/
   │   ├── book.epub
   └── 漫画书合集文件夹/
       └── comic1.cbz
       └── comic2.pdf
   ```
   ##### ⚠️注意，不管是单本还是合集请都放到一个文件夹（到时候制种就是在这个文件夹上）里面。对于合集，脚本会随机选择一个书籍文件去截图。

### 使用教程

#### 基本用法

使用脚本的最简单方式：

```bash
python extract_book_previews.py
```

这将：
- 在`books/`目录中查找书籍
- 每本书提取1张封面+3张预览图片
- 将图片保存到`book_metadata/`目录
- 使用您操作系统的默认Calibre路径

#### 自定义预览数量

提取更多或更少的预览图片：

```bash
# 提取1张封面+6张预览图片（总共：7张图片）
python extract_book_previews.py --num-previews 6

# 提取1张封面+2张预览图片（总共：3张图片）
python extract_book_previews.py --num-previews 2
```

#### 自定义目录路径

指定自定义输入和输出目录：

```bash
# 使用自定义目录
python extract_book_previews.py --books-dir /path/to/my/books --book-meta-dir /path/to/output
```

#### 指定Calibre路径

如果Calibre安装在非标准位置：

**Windows：**
```bash
python extract_book_previews.py --calibre-convert-path "C:\Program Files\Calibre2\ebook-convert.exe"
```

**macOS：**
```bash
python extract_book_previews.py --calibre-convert-path "/Applications/calibre.app/Contents/MacOS/ebook-convert"
```

**Linux：**
```bash
python extract_book_previews.py --calibre-convert-path "/usr/bin/ebook-convert"
```

#### 完整示例

这是一个显示所有选项的完整示例：

```bash
python extract_book_previews.py \
  --num-previews 5 \
  --books-dir /Users/username/Documents/MyBooks \
  --book-meta-dir /Users/username/Documents/BookPreviews \
  --calibre-convert-path "/Applications/calibre.app/Contents/MacOS/ebook-convert"
```

### 输出结构

运行脚本后，您将得到如下结构：

```
book_metadata/
├── 书籍标题1/
│   ├── 1.jpg          # 封面页
│   ├── 2.jpg          # 随机预览页
│   ├── 3.jpg          # 随机预览页
│   └── 4.jpg          # 随机预览页
├── 书籍标题2/
│   ├── 1.jpg          # 封面页
│   ├── 2.jpg          # 随机预览页
│   └── 3.jpg          # 随机预览页
└── 漫画书/
    ├── 1.jpg          # 封面页
    ├── 2.jpg          # 随机预览页
    └── 3.jpg          # 随机预览页
```

### 命令行选项

| 选项 | 描述 | 默认值 |
|------|------|--------|
| `--num-previews` | 预览图片数量（不包括封面） | 4 |
| `--books-dir` | 包含书籍文件夹的目录 | `books` |
| `--book-meta-dir` | 预览图片的输出目录 | `book_metadata` |
| `--calibre-convert-path` | Calibre的ebook-convert可执行文件路径 | 自动检测 |

### 故障排除

#### "Calibre路径未找到"警告

如果您看到此警告，脚本找不到Calibre。解决方案：

1. **安装Calibre**（如果尚未安装）
2. **指定正确路径**使用`--calibre-convert-path`
3. **忽略警告**如果您只处理PDF/CBZ文件

#### "未找到书籍文件"错误

这意味着脚本在文件夹中找不到支持的书籍文件。检查：

1. **文件扩展名**：仅支持`.pdf`、`.epub`、`.mobi`、`.cbz`、`.ppt`
2. **文件位置**：确保书籍文件直接在书籍文件夹中
3. **文件权限**：确保脚本可以读取文件

#### 图片质量问题

如果提取的图片质量较差：

1. **检查源文件**：确保原始书籍文件质量良好
2. **文件格式**：某些格式（特别是扫描的PDF）可能质量较低
3. **处理**：脚本对PDF页面使用2倍缩放 - 这通常足够了

### 支持的文件格式

| 格式 | 描述 | 处理方法 |
|------|------|----------|
| PDF | 便携式文档格式 | 直接页面提取 |
| EPUB | 电子出版物 | 通过Calibre转换为PDF |
| MOBI | Mobipocket格式 | 通过Calibre转换为PDF |
| CBZ | 漫画书ZIP | 从ZIP中提取图片 |

### 注意事项

- 脚本增量处理书籍 - 不会重新提取已存在的图片
- 每个书籍文件夹应包含恰好一个书籍文件
- 图片会自动裁剪以移除白边
- 脚本使用随机页面选择进行预览，避免总是提取相同的页面
- 所有提取的图片都保存为JPG格式以保持一致性

### 许可证

此脚本按原样提供，仅供教育和个人使用。 