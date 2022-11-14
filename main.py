import re, requests


ROOT = 'http://www.quanxue.cn/CT_NanHuaiJin'

def get_html_text(url):
    resp = requests.get(url)
    resp.encoding = 'utf-8'
    return resp.text

def get_book_dict(html_text):
    expr = re.compile(r'<li class="index_left_td">..、<a href="(.+?).html" target="_blank">(.+?)</a>')
    results = expr.findall(html_text)
    return {r[0]:r[1] for r in results}

def get_chapter_urls(html_text):
    expr = re.compile(r'<li class="index_left_td">..、<a href="(.+?).html">.+?</a>')
    results = expr.findall(html_text)
    urls = ['{}/{}.html'.format(ROOT, r) for r in results]
    return urls

def main():
    root_html_text = get_html_text('{}/index.html'.format(ROOT))
    # 书籍列表
    book_dict = get_book_dict(root_html_text)
    # 循环书籍，获得书名与网址
    for book_key in book_dict:
        # 获取章节目录
        book_url = '{}/{}.html'.format(ROOT, book_key)
        chapter_html_text = get_html_text(book_url)
        chapter_urls = get_chapter_urls(chapter_html_text)
        print(chapter_urls)
        break


if __name__ == '__main__':
    main()
