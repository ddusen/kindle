import re, requests, json, time, wget


BOOKS = 'http://www.quanxue.cn'
EPUBPRESS = 'https://epub.press/api/v1/books'

def get_html_text(url):
    time.sleep(3)
    resp = requests.get(url)
    resp.encoding = 'utf-8'
    return resp.text

def get_book_dict(html_text):
    expr = re.compile(r'<li class="index_left_td">..、<a href="(.+?).html" target="_blank">(.+?)</a>(.*?)</li>')
    results = expr.findall(html_text)
    return {r[0]:'{}{}'.format(r[1], r[2]) for r in results}

def get_chapter_urls(author_key, book_key, html_text):
    book_key = book_key.rstrip('Index')
    expr = re.compile(r'<a href="{}/(.+?).html"'.format(book_key))
    results = expr.findall(html_text)
    urls = ['{}/{}/{}/{}.html'.format(BOOKS, author_key, book_key, r) for r in results]
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
    resp = requests.post(url, headers=headers, data=json.dumps(data))
    print('create_ebook url:{} resp.status_code:{} resp.text:{}'.format(
        url, resp.status_code, resp.text,
    ))
    return resp.json().get('id')

def check_created_ebook(book_id):
    time.sleep(3)
    url = '{}/{}/status'.format(EPUBPRESS, book_id)
    print('check_created_ebook url: %s' % url)
    resp = requests.get(url)
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
        # 获取章节目录
        book_url = '{}/{}/{}.html'.format(BOOKS, author_key, book_key)
        chapter_html_text = get_html_text(book_url)
        chapter_urls = get_chapter_urls(author_key, book_key, chapter_html_text)

        '''
        章节数量不能超过45。当超过时，对章节进行拆分
        '''
        if len(chapter_urls) > 45:
            offset = 0
            while offset < len(chapter_urls):
                next_offset = offset+45
                new_book_name = '{}.{}.{}'.format(book_name, offset, next_offset)
                call_epub_press(new_book_name, author, chapter_urls[offset:next_offset])
                offset = next_offset
        else:
            call_epub_press(book_name, author, chapter_urls)
        
        i+=1

if __name__ == '__main__':
    main()
