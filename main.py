import re, requests, json, time, wget


EPUBPRESS = 'https://epub.press/api/v1/books'

def get_html_text(url):
    resp = requests.get(url)
    resp.encoding = 'utf-8'
    return resp.text

def get_book_dict(html_text):
    expr = re.compile(r'<li class="index_left_td">..、<a href="(.+?).html" target="_blank">(.+?)</a>')
    results = expr.findall(html_text)
    return {r[0]:r[1] for r in results}

def get_chapter_urls(root_url, html_text):
    expr = re.compile(r'<li class="index_left_td">..、<a href="(.+?).html">.+?</a>')
    results = expr.findall(html_text)
    urls = ['{}/{}.html'.format(root_url, r) for r in results]
    return urls

def create_ebook(title, author, urls):
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
    if resp.status_code == 202:
        return resp.json().get('id')
    else:
        print('create_ebook url:{} resp.status_code:{} resp.text:{}'.format(
            url, resp.status_code, resp.text,
        ))
        return None

def check_created_ebook(book_id):
    url = '{}/{}/status'.format(EPUBPRESS, book_id)
    print('check_created_ebook url: %s' % url)
    resp = requests.get(url)
    if resp.json().get('progress') == 100:
        return True
    else:
        print(resp.status_code, resp.text)
        return False

def download_ebook(book_id, title, author):
    url = '{}/{}/download'.format(EPUBPRESS, book_id)
    resp = wget.download(url, '{}-{}.epub'.format(title, author))
    print('download_ebook url:{} book_id:{}, title:{}, author:{}\nresp:{}\n'.format( 
        url, book_id, title, author, resp,
    ))

def call_epub_press(book_name, book_author, chapter_urls):
    # 调用 epub press api 创建书籍
    book_id = create_ebook(book_name, book_author, chapter_urls)
    # 验证书籍状态
    time.sleep(3)
    if check_created_ebook(book_id):
        # 下载书籍
        time.sleep(1)
        download_ebook(book_id, book_name, book_author)
    else:
        # 休息一会
        time.sleep(60)
        if check_created_ebook(book_id):
            # 下载书籍
            time.sleep(1)
            download_ebook(book_id, book_name, book_author)
        else:
            # 休息一会
            time.sleep(60)
            if check_created_ebook(book_id):
                # 下载书籍
                time.sleep(1)
                download_ebook(book_id, book_name, book_author)
            else:
                print('download error. book_id:{} book_name:{} book_author'.format(book_id, book_name, book_author))


def main():
    book_author = '南怀瑾'
    root_url = 'http://www.quanxue.cn/CT_NanHuaiJin'
    root_html_text = get_html_text('{}/index.html'.format(root_url))
    # 书籍列表
    book_dict = get_book_dict(root_html_text)
    # 循环书籍，获得书名与网址
    i = 0
    for book_key, book_name in book_dict.items():
        print('Index: %d Book: %s' % (i, book_name, ))
        # 获取章节目录
        book_url = '{}/{}.html'.format(root_url, book_key)
        chapter_html_text = get_html_text(book_url)
        chapter_urls = get_chapter_urls(root_url, chapter_html_text)
        
        '''
        章节数量不能超过45。当超过时，对章节进行拆分
        '''
        if len(chapter_urls) > 45:
            offset = 0
            while offset < len(chapter_urls):
                next_offset = offset+45
                new_book_name = '{}.{}.{}'.format(book_name, offset, next_offset)
                call_epub_press(new_book_name, book_author, chapter_urls[offset:next_offset])
                offset = next_offset
        else:
            call_epub_press(book_name, book_author, chapter_urls)
        
        time.sleep(1)
        i+=1
        break


if __name__ == '__main__':
    main()
