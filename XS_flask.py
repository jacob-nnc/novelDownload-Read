from bookManager import BookManager
import atexit
import threading
import flask
from flask_cors import CORS
import os

savePath = "./data1"  # 假设这是你的保存路径
book_manager = BookManager(savePath)  # 创建书籍管理对象

atexit.register(lambda: book_manager.save_Msg())

app = flask.Flask(__name__)
CORS(app)


@app.get("/")
def index():
    books = book_manager.get_books()

    ret = [[j, "", f"./{i}"] for i, j in enumerate(books)]
    if book_manager.current_book:
        ret[book_manager.current_book][1] = "prev"

    imgs = [os.path.join("/toimg/data/", i) for i in book_manager.imgs]
    response = flask.make_response(
        flask.render_template("index.html", images=imgs, books=ret, title="书籍列表")
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Expires"] = "-1"
    response.headers["Pragma"] = "no-cache"
    return response


@app.get("/remove/<int:book_id>")
def remove_book(book_id):
    book_manager.removeBook(book_id)
    return flask.jsonify({"message": f"Book {book_id} removed successfully."})


@app.get("/rename/<int:book_id>/<string:name>")
def rename_book(book_id, name):
    book_manager.renameBook(book_id, name)
    return flask.jsonify({"message": f"Book {book_id} renamed to {name} successfully."})


@app.route("/<int:fileidx>/")
def content(fileidx):
    contents = book_manager.get_content(fileidx)
    ret = [
        [
            j[0] if isinstance(j, list) else j,
            "",
            f"./{i}.html",
        ]
        for i, j in enumerate(contents)
    ]
    if book_manager.current_chapter[fileidx] != None:
        try:
            ret[book_manager.current_chapter[fileidx]][1] = "prev"
        except:
            print(ret)
            print(book_manager.current_chapter[fileidx])
    return flask.render_template(
        "index.html", books=ret, title="章节列表", isContent=True
    )


@app.route("/<int:bookidx>/<int:contentidx>.html")
def chapter(bookidx, contentidx):
    book_manager.get_content(bookidx)
    chapter = book_manager.get_chapter(contentidx, bookidx)[0]
    chaptername, chaptercharset = book_manager.current_chapterList[contentidx]

    prevlink = "./" if contentidx <= 0 else f"./{contentidx-1}.html"
    nextlink = (
        "./"
        if contentidx >= len(book_manager.current_chapterList) - 1
        else f"./{contentidx+1}.html"
    )

    return flask.render_template(
        "chapter.html",
        content=chapter,
        title=chaptername,
        charset=chaptercharset,
        next_link=nextlink,
        prev_link=prevlink,
    )


@app.post("/")
def handle_post():
    print("downloading")
    # 处理 POST 请求，接收并保存 JSON 数据
    data = flask.request.get_json()

    if data is None:
        return flask.jsonify({"error": "Invalid JSON format"}), 400

    name = data.get("name")
    dir = data.get("dir")
    content = data.get("content")
    images = data.get("images", [])
    charset = data.get("charSet")

    # 启动线程保存章节
    threading.Thread(
        target=book_manager.saveChapter2Book,
        args=(dir, name, charset, content),
    ).start()

    # 定义下载图像的函数
    def download_image():
        for img in images:
            book_manager.save_image(img["base64"], img["src"])

    # 启动线程保存图像
    threading.Thread(target=download_image).start()

    return flask.jsonify({"message": "Content and images saved successfully"}), 200


@app.route("/toimg/data/<string:imgurl>")
def img(imgurl):
    response = flask.make_response(
        flask.send_from_directory(book_manager.img_path, imgurl)
    )
    response.headers["Cache-Control"] = "max-age=31536000, immutable"
    return response


# app.run()
