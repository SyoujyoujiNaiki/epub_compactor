from ebooklib import epub
from pathlib import Path
import os
import re
import sys
import uuid


# 对于标题而已只要求有一个数字作为排序依据
def extract_title_number(title):
    numbers = re.findall(r"\d+", title)  # 提取所有数字
    return int(numbers[0]) if numbers else 0  # 取第一个数字


# 但是对于图片而言，要求以_p{d}的形式来排序
def extract_pic_number(pic):
    match = re.search(r"_p(\d+)", pic)
    return int(match.group(1)) if match else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("No path provided!")
        exit()
    # 获取工作目录
    cur_dir = sys.argv[1]

    # 获取作者列表
    authors = [
        author_name
        for author_name in os.listdir(cur_dir)
        if os.path.isdir(os.path.join(cur_dir, author_name))
    ]

    # 获取作品列表
    for a in authors:
        print(f"Packing epub for {a}")
        author_dir = os.path.join(cur_dir, a)
        books = [book_title for book_title in os.listdir(author_dir)]

        for b in books:
            print(f"Packing epub for {b}")
            book_dir = os.path.join(author_dir, b)

            ebook = epub.EpubBook()

            # Set metadata
            ebook.set_identifier(str(uuid.uuid4))
            ebook.set_title = b
            ebook.set_language("ja")
            ebook.add_author(a)

            cover_path = next(
                (
                    f
                    for f in Path(book_dir).iterdir()
                    if f.is_file() and f.stem == "cover"
                ),
                None,
            )
            if cover_path is not None:
                cover_file = cover_path.suffix
                ebook.set_cover(cover_file, open(cover_path, "rb").read())

            chapt_spine = ["nav"]

            # 获取各章节
            chapts = [
                chapt_name
                for chapt_name in os.listdir(book_dir)
                if os.path.isdir(os.path.join(book_dir, chapt_name))
            ]
            # 对章节排序（否则默认按字符排序，会导致第1话之后是第10话、第11话这样的情况）
            sorted_chapts = sorted(chapts, key=extract_title_number)

            for chapt in sorted_chapts:
                print(f"Packing chapt {chapt}")
                chapt_dir = os.path.join(book_dir, chapt)
                chapt_xhtml = epub.EpubHtml(title=chapt, file_name=(chapt + ".xhtml"))
                chapt_content = "<html><head></head><body>"
                # 获取章节图片
                pics = os.listdir(os.path.join(book_dir, chapt))
                # 对图片进行排序，否则也会出现p1之后是p10，p11的情况
                sorted_pics = sorted(pics, key=extract_pic_number)

                for p in sorted_pics:
                    img_f = open(os.path.join(chapt_dir, p), "rb").read()
                    img_uid = p[: p.find(".")]
                    _, img_type = os.path.splitext(p)
                    if img_type == "jpg":
                        img_type = "jpeg"
                    elif img_type == "svg":
                        img_type = "svg+xml"

                    img = epub.EpubImage(
                        uid=img_uid,
                        file_name=p,
                        media_type=f"image/{img_type}",
                        content=img_f,
                    )
                    ebook.add_item(img)
                    chapt_content += f"<img src={p}/>\n"
                chapt_content += "</body></html>"
                chapt_xhtml.set_content(chapt_content)
                ebook.add_item(chapt_xhtml)
                chapt_spine.append(chapt_xhtml)

            ebook.toc = chapt_spine
            ebook.spine = chapt_spine

            ebook.add_item(epub.EpubNav())

            epub.write_epub(f"{b}.epub", ebook)
