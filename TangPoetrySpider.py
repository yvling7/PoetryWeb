import requests
from bs4 import BeautifulSoup
import time
import threading
from queue import Queue, Empty
import random

class TangPoetrySpider:
    def __init__(self):
        self.base_url = "http://www.guoxue123.com/jijijibu/0201/00qts/"
        self.output_file = "data/全唐诗t.txt"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.url_queue = Queue()
        self.html_queue = Queue()
        self.content_queue = Queue()
        self.start_volume = 1
        self.end_volume = 10
        self.thread_num = 3
        self.session = requests.Session()
        self.session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
        self.session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))

    def get_url_queue(self):
        for volume in range(self.start_volume, self.end_volume + 1):
            self.url_queue.put(f"{self.base_url}{str(volume).zfill(3)}.htm") 

    def get_html_queue(self):
        while True:
            try:
                url = self.url_queue.get(timeout=30)
                time.sleep(1 + random.random())
                
                response = self.session.get(
                    url, 
                    headers=self.headers, 
                    timeout=(15, 30)
                )
                response.encoding = 'gbk'
                response.raise_for_status()
                html_source_page = response.text
                self.html_queue.put(html_source_page)
                self.url_queue.task_done()
            except Empty:
                break
            except requests.exceptions.RequestException as e:
                print(f"请求失败 {url}: {str(e)}")
                self.url_queue.put(url)
                time.sleep(5)
                continue

    def parse_html(self):
        while True:
            try:
                html = self.html_queue.get(timeout=30)
                soup = BeautifulSoup(html, "html.parser")
                p_tag = soup.find_all('p')[5]
                content_list = []
                for text in p_tag.stripped_strings:
                    text = text.strip()
                    if text:
                        try:
                            text = text.encode('utf-8').decode('utf-8')
                            content_list.append(text)
                        except UnicodeError:
                            print(f"编码错误，跳过文本: {text}")
                self.content_queue.put(content_list)
                self.html_queue.task_done()
            except Empty:
                break
            except Exception as e:
                print(f"解析错误: {str(e)}")
                continue

    def save_data(self):
        while True:
            try:
                content_list = self.content_queue.get(timeout=30)
                with open(self.output_file, "a+", encoding='utf-8') as f:
                    for i, line in enumerate(content_list):
                        if line:
                            # 移除全角空格和其他可能的特殊字符
                            line = line.replace('　　', '').strip()
                            f.write(f"{line}\n")
                    print(f"第 {i+1} 卷已成功下载")
                self.content_queue.task_done()
            except Empty:
                break
            except Exception as e:
                print(f"保存错误: {str(e)}")
                continue
            
    def run(self):
        thread_list = []
        
        t_url = threading.Thread(target=self.get_url_queue)
        thread_list.append(t_url)
        
        for _ in range(self.thread_num):
            t_content = threading.Thread(target=self.get_html_queue)
            thread_list.append(t_content)
        
        for _ in range(self.thread_num):
            t_parse = threading.Thread(target=self.parse_html)
            thread_list.append(t_parse)
        t_save = threading.Thread(target=self.save_data)
        thread_list.append(t_save)
        for t in thread_list:
            t.setDaemon(True)
            t.start()
        for q in [self.url_queue, self.html_queue, self.content_queue]:
            q.join()

if __name__ == "__main__":
    spider = TangPoetrySpider()
    spider.run()