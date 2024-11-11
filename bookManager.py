import os
from typing import List
import base64
import shutil
import random
from threading import Lock


class BookManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.img_path = os.path.join(base_path, "toimg/data")

        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(self.img_path, exist_ok=True)
        # 创建文件夹，如果不存在

        self.books = []
        self.lock = Lock()
        self.current_book = None
        self.current_chapterList = []
        # print(f"Downloaded and saved image: {image_file_path}")
        self.saveBookID = None
        self.current_chapter = []
        self.imgs = []
        self.chulichapter = None
        self.load_books()
        self.load_Msg()
        self.load_imgs()

        # 提取文件扩展名

    def save_Msg(self):
        with open(os.path.join(self.base_path, "msg.txt"), "w") as f:
            f.write(str({"book": self.current_book, "chapter": self.current_chapter}))

    def load_Msg(self):
        try:
            with open(os.path.join(self.base_path, "msg.txt"), "r") as f:
                txt = eval(f.read())
        except:
            return
        self.current_book = txt["book"]
        self.current_chapter = txt["chapter"]

    def save_Books(self, dir: str):
        # 保存文本内容到文件
        bookid = self.getBookId(dir)
        self.saveBookID = bookid
        xsSavePath = os.path.join(self.base_path, str(bookid))
        os.makedirs(xsSavePath, exist_ok=True)

    def saveChapter2Book(self, dir, name, charset, content):
        with self.lock:
            self.save_Books(dir)
            self.saveChapter(name, charset, content)

    def removeBook(self, bookid):
        booksList = os.path.join(self.base_path, "books.txt")
        filePath = os.path.join(self.base_path, str(bookid))
        removePath = os.path.join(self.base_path, "_")
        removeList = os.path.join(removePath, "remove.txt")

        os.makedirs(removePath, exist_ok=True)
        with self.lock:
            if os.path.exists(removeList):
                with open(removeList, "r", encoding="utf-8") as f:
                    try:
                        removeList1: dict = eval(f.read())
                    except:
                        removeList1 = {}
            else:
                removeList1 = {}
            with open(booksList, "r", encoding="utf-8") as f:
                try:
                    Contentlist = eval(f.read())
                except:
                    return None
            bookname = Contentlist.pop(bookid)
            self.current_chapter.pop(bookid)
            if self.current_book == None:
                pass
            elif self.current_book > bookid:
                self.current_book -= 1
            elif self.current_book == bookid:
                self.current_book = None
            with open(booksList, "w", encoding="utf-8") as f:
                f.write(str(Contentlist))
            bookidx = str(bookid) + str(random.random())
            removeList1[bookidx] = bookname
            with open(removeList, "w", encoding="utf-8") as f:
                f.write(str(removeList1))

        shutil.move(filePath, os.path.join(removePath, bookidx))
        N = len(Contentlist)
        try:
            for i in range(bookid + 1, N + 1):
                os.rename(
                    os.path.join(self.base_path, str(i)),
                    os.path.join(self.base_path, str(i - 1)),
                )
        except:
            pass

    def renameBook(self, bookid, newName):
        Xfile = os.path.join(self.base_path, "books.txt")
        with open(Xfile, "r", encoding="utf-8") as f:
            try:
                Contentlist = eval(f.read())  # 使用 json 加载，确保安全
            except:
                return None
        Contentlist[bookid] = newName

        with self.lock:
            with open(Xfile, "w", encoding="utf-8") as f:
                f.write(str(Contentlist))

    def saveChapter(self, name, charset, content):
        contentid = self.getContentId([name, charset])
        xsFilePath = os.path.join(
            os.path.join(self.base_path, str(self.saveBookID)), f"{contentid}.html"
        )

        if self.chulichapter is not None:
            content = self.chulichapter(content)
        with open(xsFilePath, "w", encoding=charset, errors="ignore") as output_file:
            output_file.write(content)

    def load_books(self):
        """读取 book.txt 并解析书籍列表"""
        book_file = os.path.join(self.base_path, "books.txt")
        if os.path.exists(book_file):
            with self.lock:
                with open(book_file, "r", encoding="utf-8") as f:
                    self.books = eval(f.read())
                    self.current_chapter += [None] * (
                        len(self.books) - len(self.current_chapter)
                    )
        else:
            print("books.txt not found.")

    def get_books(self):
        """返回书籍列表"""
        self.load_books()
        return self.books

    def repairContent(self, index):
        t = filter(
            lambda x: x.endswith(".html") and x[0] != "N",
            os.listdir(os.path.join(self.base_path, str(index))),
        )
        t = sorted(map(lambda x: int(x[:-5]), t))

        return [["分卷阅读" + str(i), "utf-8"] for i in t]

    def get_content(self, index):
        index = int(index)
        if index == self.current_book and self.current_chapterList != []:
            return self.current_chapterList
        content_file = os.path.join(self.base_path, str(index), "content.txt")
        self.current_book = index
        ret = None
        if os.path.exists(content_file):
            with self.lock:
                with open(content_file, "r", encoding="utf-8") as f:
                    try:
                        txt = f.read()
                    except Exception as e:
                        print("章节内容解析失败")
                        ret = self.repairContent(index)
            try:
                chapters = eval(txt)
                self.current_chapterList = list(
                    map(lambda x: x if isinstance(x, list) else [x, "gbk"], chapters)
                )
                return chapters
            except Exception as e:
                print("章节内容解析失败")
                ret = self.repairContent(index)
        else:
            print("章节内容未找到")
            ret = self.repairContent(index)

        if ret != None:
            with open(content_file, "w", encoding="utf-8") as f:
                f.write(str(ret))
        self.current_chapterList = ret
        return ret

    def get_chapter(self, index, bookid):
        index = int(index)
        self.get_content(bookid)

        self.current_book = bookid

        self.current_chapter[self.current_book] = index

        chapter_file = os.path.join(
            self.base_path,
            str(self.current_book),
            f"{self.current_chapter[self.current_book]}.html",
        )

        if os.path.exists(chapter_file):
            temp = self.current_chapterList[index]
            charset = temp[1] if isinstance(temp, list) else "gbk"
            if charset == None:
                charset = "gbk"
            with self.lock:
                with open(chapter_file, "r", encoding=charset) as f:
                    return f.read(), charset

        return None

    def __getXid(self, name: str | List[str], isbook=True) -> int:
        if isbook:
            Xfile = os.path.join(self.base_path, "books.txt")
        else:
            Xfile = os.path.join(self.base_path, str(self.saveBookID), "content.txt")
        # 读取文件，如果文件不存在则创建一个空的书列表
        if not os.path.exists(Xfile):
            Contentlist: List[str] = []
        else:
            with open(Xfile, "r", encoding="utf-8") as f:
                try:
                    Contentlist = eval(f.read())
                except:
                    return None
        # 如果书名已经存在，返回书名的索引
        nameList = [i[0] if isinstance(i, list) else i for i in Contentlist]
        name1 = name if isinstance(name, str) else name[0]
        if name1 in nameList:
            Xid = Contentlist.index(name)
        else:
            # 否则，追加新书，并返回新的索引
            Xid = len(Contentlist)
            Contentlist.append(name)

            # 将更新后的书列表保存回文件
            with open(Xfile, "w", encoding="utf-8") as f:
                f.write(str(Contentlist))

        return Xid

    def getBookId(self, name: str):
        return self.__getXid(name)

    def getContentId(self, name: str | List[str]):
        return self.__getXid(name, False)

    def save_image(self, base64_data, img_src):

        image_file_name = f"{os.path.basename(img_src)}"
        image_file_path = os.path.join(IMG_SAVE_FOLDER, image_file_name)

        # 去掉前缀 'data:image/png;base64,'
        header, encoded = base64_data.split(",", 1)
        if not os.path.exists(image_file_name):
            with open(image_file_path, "wb") as img_file:
                img_file.write(base64.b64decode(encoded))

    def get_image(self, url):
        fullurl = os.path.join(self.img_path, url)
        try:
            with open(fullurl, "rb") as f:
                return f.read()
        except:
            return None

    def load_imgs(self):
        self.imgs = os.listdir(self.img_path)
