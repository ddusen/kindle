import re, requests, json, time, wget

from meta import (BOOKS, EPUBPRESS, IPOINT, )


def get_html_text(url):
    time.sleep(3)
    resp = requests.get(url, timeout=600)
    resp.encoding = 'utf-8'
    return resp.text

def get_book_dict(html_text):
    expr = re.compile(r'<li class="index_left_td">..、<a href="(.+?).html" target="_blank">(.+?)</a>(.*?)</li>')
    results = expr.findall(html_text)
    f = lambda x: x.replace('（', '(').replace('）', ')')
    return {r[0]:'{}{}'.format(r[1], f(r[2])) for r in results}

def get_chapter_urls(author_key, book_key, html_text):
    book_key = book_key.replace('Index', '')
    expr = re.compile(r'<a href="{}/(.+?).html'.format(book_key))
    results = expr.findall(html_text)

    urls = []
    exists = dict()
    for r in results:
        if r in exists:
            continue

        exists[r] = True
        url = '{}/{}/{}/{}.html'.format(BOOKS, author_key, book_key, r)
        urls.append(url)
    
    return urls

def create_ebook(title, author, urls):
    time.sleep(3)
    url = EPUBPRESS
    headers = {'Content-Type': 'application/json'}
    data = {
        "title": title,
        "description": "",
        "author": author,
        "genre": "ebooks",
        "coverPath": "",
        "urls": urls
    }
    resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=600)
    print('create_ebook url:{} resp.status_code:{} resp.text:{}'.format(
        url, resp.status_code, resp.text,
    ))
    return resp.json().get('id')

def check_created_ebook(book_id):
    time.sleep(3)
    url = '{}/{}/status'.format(EPUBPRESS, book_id)
    print('check_created_ebook url: %s' % url)
    resp = requests.get(url, timeout=600)
    if resp.json().get('progress') == 100:
        return True
    else:
        print(resp.status_code, resp.text)
        return False

def _download_ebook_epub(book_id, title, author):
    time.sleep(3)
    url = '{}/{}/download'.format(EPUBPRESS, book_id)
    resp = wget.download(url, '{}-{}.epub'.format(title, author))
    print('_download_ebook_epub url:{} book_id:{}, title:{}, author:{}\nresp:{}\n'.format( 
        url, book_id, title, author, resp,
    ))

def _download_ebook_mobi(book_id, title, author):
    time.sleep(3)
    url = '{}/{}/download?filetype=mobi'.format(EPUBPRESS, book_id)
    resp = wget.download(url, '{}-{}.mobi'.format(title, author))
    print('_download_ebook_mobi url:{} book_id:{}, title:{}, author:{}\nresp:{}\n'.format( 
        url, book_id, title, author, resp,
    ))

def download_ebook(book_id, title, author):
    _download_ebook_epub(book_id, title, author)
    _download_ebook_mobi(book_id, title, author)

def call_epub_press(book_name, book_author, chapter_urls):
    # 调用 epub press api 创建书籍
    book_id = create_ebook(book_name, book_author, chapter_urls)
    # 验证书籍状态
    if check_created_ebook(book_id):
        # 下载书籍
        download_ebook(book_id, book_name, book_author)
    else:
        # 休息一会
        time.sleep(60)
        if check_created_ebook(book_id):
            # 下载书籍
            download_ebook(book_id, book_name, book_author)
        else:
            # 休息一会
            time.sleep(60)
            if check_created_ebook(book_id):
                # 下载书籍
                download_ebook(book_id, book_name, book_author)
            else:
                print('download error. book_id:{} book_name:{} book_author'.format(book_id, book_name, book_author))


def main():
    author = '南怀瑾'
    author_key = 'ct_NanHuaijin'
    root_html_text = get_html_text('{}/{}/index.html'.format(BOOKS, author_key))
    # 书籍列表
    book_dict = get_book_dict(root_html_text)

    # 循环书籍，获得书名与网址
    i = 0
    for book_key, book_name in book_dict.items():
        print('Index: %d Book: %s' % (i, book_name, ))
        # 断点续下
        if i < IPOINT:
            i += 1
            continue

        # 获取章节目录
        book_url = '{}/{}/{}.html'.format(BOOKS, author_key, book_key)
        chapter_html_text = get_html_text(book_url)
        chapter_urls = get_chapter_urls(author_key, book_key, chapter_html_text)

        # 对章节目录进行处理
        chapter_urls_len = len(chapter_urls)
        chapter_max_len = 49
        if chapter_urls_len == 0: #章节为空，直接转换成书籍
            call_epub_press(book_name, author, [book_url])
        elif chapter_urls_len <= chapter_max_len: #章节小于等于49，直接转换成书籍
            call_epub_press(book_name, author, chapter_urls)
        else: #章节大于49，分批转换成书籍
            offset = 0
            while offset < chapter_urls_len:
                next_offset = offset+chapter_max_len
                new_book_name = '{}.{}.{}'.format(
                    book_name, offset, 
                    chapter_urls_len if next_offset > chapter_urls_len else next_offset
                )
                call_epub_press(new_book_name, author, chapter_urls[offset:next_offset])
                offset = next_offset
        
        i+=1

if __name__ == '__main__':
    main()
