import os
import random
import fitz  # PyMuPDF
import zipfile
import shutil
from pathlib import Path
import tempfile
import subprocess
import numpy as np
from PIL import Image
import argparse
import rarfile
import platform


def get_default_calibre_path():
    """Get the default calibre path based on the operating system"""
    system = platform.system().lower()

    if system == "darwin":  # macOS
        return "/Applications/calibre.app/Contents/MacOS/ebook-convert"
    elif system == "windows":
        # Common Windows installation paths
        possible_paths = [
            r"C:\Program Files\Calibre2\ebook-convert.exe",
            r"C:\Program Files (x86)\Calibre2\ebook-convert.exe",
            r"C:\Program Files\Calibre\ebook-convert.exe",
            r"C:\Program Files (x86)\Calibre\ebook-convert.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return r"C:\Program Files\Calibre2\ebook-convert.exe"  # Default fallback
    else:  # Linux
        return "/usr/bin/ebook-convert"


def convert_to_pdf(input_file, output_file, calibre_path):
    """Convert ebook to PDF using calibre's ebook-convert"""
    try:
        subprocess.run(
            [calibre_path, input_file, output_file], check=True, capture_output=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error converting {input_file} to PDF: {e}")
        return False
    except FileNotFoundError:
        print(f"Error: ebook-convert not found at {calibre_path}")
        print(
            "Please install Calibre or specify the correct path using --calibre-convert-path"
        )
        return False


def crop_white_margins(image_path):
    """Crop white margins from an image using PIL"""
    img = Image.open(image_path)
    # Convert to grayscale
    gray = img.convert("L")
    # Convert to numpy array
    img_array = np.array(gray)

    # Find non-white regions
    non_white = img_array < 250  # Threshold for white

    # Find the bounding box of non-white content
    rows = np.any(non_white, axis=1)
    cols = np.any(non_white, axis=0)
    if not np.any(rows) or not np.any(cols):
        return img  # Return original if no content found

    top, bottom = np.where(rows)[0][[0, -1]]
    left, right = np.where(cols)[0][[0, -1]]

    # Add some padding
    padding = 50
    top = max(0, top - padding)
    bottom = min(img_array.shape[0], bottom + padding)
    left = max(0, left - padding)
    right = min(img_array.shape[1], right + padding)

    # Crop the image
    cropped = img.crop((left, top, right, bottom))
    return cropped


def extract_pdf_pages(pdf_path, output_dir, num_previews, existing_images):
    """Extract pages from PDF file"""
    doc = fitz.open(pdf_path)

    # 获取下一个可用的图片编号
    next_image_num = 1
    while next_image_num in existing_images:
        next_image_num += 1

    # 如果第一页还没有提取，提取它
    if 1 not in existing_images:
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        temp_path = os.path.join(output_dir, "temp.jpg")
        pix.save(temp_path)

        # Crop and save the cover
        cropped = crop_white_margins(temp_path)
        cropped.save(os.path.join(output_dir, "1.jpg"))
        os.remove(temp_path)
        next_image_num = 2
        num_previews -= 1  # 减少需要提取的预览图片数量

    # Get random pages for previews
    if doc.page_count > 1 and num_previews > 0:
        # 排除已经提取的页面
        available_pages = [
            i for i in range(1, doc.page_count) if i not in existing_images
        ]
        if available_pages:
            # 提取需要的数量，如果可用页面不够，就提取所有可用的
            pages_to_extract = min(num_previews, len(available_pages))
            random_pages = random.sample(available_pages, pages_to_extract)

            for page_num in random_pages:
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                temp_path = os.path.join(output_dir, f"temp_{next_image_num}.jpg")
                pix.save(temp_path)

                # Crop and save the page
                cropped = crop_white_margins(temp_path)
                cropped.save(os.path.join(output_dir, f"{next_image_num}.jpg"))
                os.remove(temp_path)
                next_image_num += 1

    doc.close()


def extract_cbz_pages(cbz_path, output_dir, num_previews, existing_images):
    """Extract pages from CBZ file"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(cbz_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Get all image files
        image_files = sorted(
            [
                f
                for f in os.listdir(temp_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
        )

        if not image_files:
            return

        # 获取下一个可用的图片编号
        next_image_num = 1
        while next_image_num in existing_images:
            next_image_num += 1

        # 如果第一页还没有提取，提取它
        if 1 not in existing_images:
            cropped = crop_white_margins(os.path.join(temp_dir, image_files[0]))
            cropped.save(os.path.join(output_dir, "1.jpg"))
            next_image_num = 2
            num_previews -= 1  # 减少需要提取的预览图片数量

        # Get random images for previews
        if len(image_files) > 1 and num_previews > 0:
            # 排除已经提取的图片
            available_images = [
                img
                for i, img in enumerate(image_files[1:], 1)
                if i not in existing_images
            ]
            if available_images:
                # 提取需要的数量，如果可用图片不够，就提取所有可用的
                images_to_extract = min(num_previews, len(available_images))
                random_images = random.sample(available_images, images_to_extract)

                for img in random_images:
                    cropped = crop_white_margins(os.path.join(temp_dir, img))
                    cropped.save(os.path.join(output_dir, f"{next_image_num}.jpg"))
                    next_image_num += 1


def extract_cbr_pages(cbr_path, output_dir, num_previews, existing_images):
    """Extract pages from CBR file (RAR archive)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with rarfile.RarFile(cbr_path) as rar:
            rar.extractall(temp_dir)
        # Get all image files
        image_files = sorted(
            [
                f
                for f in os.listdir(temp_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
        )
        if not image_files:
            return
        # 获取下一个可用的图片编号
        next_image_num = 1
        while next_image_num in existing_images:
            next_image_num += 1
        # 如果第一页还没有提取，提取它
        if 1 not in existing_images:
            cropped = crop_white_margins(os.path.join(temp_dir, image_files[0]))
            cropped.save(os.path.join(output_dir, "1.jpg"))
            next_image_num = 2
            num_previews -= 1  # 减少需要提取的预览图片数量
        # Get random images for previews
        if len(image_files) > 1 and num_previews > 0:
            # 排除已经提取的图片
            available_images = [
                img
                for i, img in enumerate(image_files[1:], 1)
                if i not in existing_images
            ]
            if available_images:
                # 提取需要的数量，如果可用图片不够，就提取所有可用的
                images_to_extract = min(num_previews, len(available_images))
                random_images = random.sample(available_images, images_to_extract)

                for img in random_images:
                    cropped = crop_white_margins(os.path.join(temp_dir, img))
                    cropped.save(os.path.join(output_dir, f"{next_image_num}.jpg"))
                    next_image_num += 1


def process_book_folder(folder_path, num_previews, book_meta_dir, calibre_path):
    """Process a single book folder"""
    print(f"Processing folder: {folder_path}")

    # Create output directory if it doesn't exist
    output_dir = os.path.join(book_meta_dir, os.path.basename(folder_path))
    os.makedirs(output_dir, exist_ok=True)

    # 检查现有图片数量
    existing_images = []
    for file in os.listdir(output_dir):
        if file.lower().endswith(".jpg"):
            try:
                # 尝试从文件名中提取数字
                num = int(os.path.splitext(file)[0])
                existing_images.append(num)
            except ValueError:
                # 如果文件名不是数字，跳过
                continue

    # 计算需要的总图片数量（封面 + 预览图片）
    required_images = num_previews + 1

    # 如果已经有足够的图片，跳过处理
    if len(existing_images) >= required_images:
        print(
            f"已有 {len(existing_images)} 张图片，需要 {required_images} 张，跳过处理"
        )
        return

    # 获取所有书籍文件
    book_files = []
    for ext in [".pdf", ".mobi", ".epub", ".cbz", ".cbr", ".ppt"]:
        book_files.extend(list(Path(folder_path).glob(f"*{ext}")))

    if not book_files:
        print(f"No book files found in {folder_path}")
        return

    # Select first book file
    book_file = str(book_files[0])
    print(f"Selected book: {book_file}")

    # 计算需要提取的额外图片数量
    remaining_previews = required_images - len(existing_images)
    print(f"需要提取 {remaining_previews} 张额外的图片")

    # Process based on file type
    if book_file.lower().endswith(".pdf"):
        extract_pdf_pages(book_file, output_dir, remaining_previews, existing_images)
    elif book_file.lower().endswith(".cbz"):
        extract_cbz_pages(book_file, output_dir, remaining_previews, existing_images)
    elif book_file.lower().endswith(".cbr"):
        extract_cbr_pages(book_file, output_dir, remaining_previews, existing_images)
    elif book_file.lower().endswith((".epub", ".mobi")):
        # Convert to PDF first
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_pdf = os.path.join(temp_dir, "temp.pdf")
            if convert_to_pdf(book_file, temp_pdf, calibre_path):
                extract_pdf_pages(
                    temp_pdf, output_dir, remaining_previews, existing_images
                )
    else:
        print(f"Unsupported file type: {book_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract preview images from books (PDF, EPUB, MOBI, CBZ, CBR)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default settings
  python extract_book_previews.py

  # Extract 6 preview images (1 cover + 5 random pages)
  python extract_book_previews.py --num-previews 5

  # Specify custom directories
  python extract_book_previews.py --books-dir /path/to/books --book-meta-dir /path/to/output

  # Specify custom Calibre path (Windows)
  python extract_book_previews.py --calibre-convert-path "C:\\Program Files\\Calibre2\\ebook-convert.exe"

  # Specify custom Calibre path (macOS)
  python extract_book_previews.py --calibre-convert-path "/Applications/calibre.app/Contents/MacOS/ebook-convert"

Supported formats:
  - PDF: Direct page extraction
  - EPUB/MOBI: Converted to PDF first using Calibre
  - CBZ: Comic book archive (ZIP with images)
        """,
    )

    parser.add_argument(
        "--num-previews",
        type=int,
        default=3,
        help="Number of preview images to extract (excluding cover). Default: 4 (total: 1 cover + 4 previews)",
    )

    parser.add_argument(
        "--books-dir",
        type=str,
        default="books",
        help="Directory containing book folders. Default: 'books'",
    )

    parser.add_argument(
        "--book-meta-dir",
        type=str,
        default="book_metadata",
        help="Output directory for preview images. Default: 'book_metadata'",
    )

    parser.add_argument(
        "--calibre-convert-path",
        type=str,
        default=get_default_calibre_path(),
        help=f"Path to Calibre's ebook-convert executable. Default: {get_default_calibre_path()}",
    )

    args = parser.parse_args()

    books_dir = args.books_dir
    book_meta_dir = args.book_meta_dir
    calibre_path = args.calibre_convert_path

    # Validate calibre path
    if not os.path.exists(calibre_path):
        print(f"Warning: Calibre path not found: {calibre_path}")
        print("This will prevent processing EPUB and MOBI files.")
        print(
            "Please install Calibre or specify the correct path using --calibre-convert-path"
        )
        print("\nCommon installation paths:")
        system = platform.system().lower()
        if system == "darwin":
            print("  macOS: /Applications/calibre.app/Contents/MacOS/ebook-convert")
        elif system == "windows":
            print("  Windows: C:\\Program Files\\Calibre2\\ebook-convert.exe")
        else:
            print("  Linux: /usr/bin/ebook-convert")
        print()

    if not os.path.exists(books_dir):
        print(f"Error: Directory {books_dir} does not exist")
        print(
            f"Please create the directory or specify a different path using --books-dir"
        )
        return

    print(f"Processing books from: {books_dir}")
    print(f"Output directory: {book_meta_dir}")
    print(f"Calibre path: {calibre_path}")
    print(f"Number of previews per book: {args.num_previews}")
    print("-" * 50)

    # Process each subfolder
    processed_count = 0
    for folder_name in os.listdir(books_dir):
        folder_path = os.path.join(books_dir, folder_name)
        if os.path.isdir(folder_path):
            process_book_folder(
                folder_path, args.num_previews, book_meta_dir, calibre_path
            )
            processed_count += 1

    print("-" * 50)
    print(f"Processing complete! Processed {processed_count} book folders.")


if __name__ == "__main__":
    main()
