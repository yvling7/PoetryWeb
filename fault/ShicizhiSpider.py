import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
import threading
from queue import Queue, Empty

class ShicizhiSpider:
    def __init__(self):
        self.base_url = "https://shicizhi.com/Poetry/ListFilter/tangshi_{}_1/Search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://shicizhi.com/Poetry/List/tangshi_1'
        }
        self._results = {}
        self._results_lock = threading.Lock()
        self._rate_lock = threading.Lock()
        
    def search_poems(self, keywords_dict, max_workers=3):
        """使用多线程搜索诗词"""
        url_queue = Queue()
        self._results.clear()
        
        # 将URL放入队列
        for item in keywords_dict:
            index = list(item.keys())[0]
            keyword = list(item.values())[0]
            encoded_keyword = urllib.parse.quote(keyword)
            url = self.base_url.format(encoded_keyword)
            url_queue.put((index, url, keyword))
        
        def worker():
            session = requests.Session()
            while True:
                try:
                    # 从队列获取任务，设置超时防止死锁
                    index, url, keyword = url_queue.get(timeout=3)
                    
                    try:
                        with self._rate_lock:  # 控制请求频率
                            time.sleep(random.uniform(1, 2))
                            response = session.get(url, headers=self.headers, timeout=10)
                            response.raise_for_status()
                        
                        # 解析结果
                        poems = self._parse_response(response.text)
                        
                        # 安全地更新结果
                        with self._results_lock:
                            self._results[index] = poems
                            print(f"成功获取关键词 '{keyword}' 的搜索结果")
                    
                    except Exception as e:
                        print(f"处理 {keyword} 时发生错误: {str(e)}")
                        with self._results_lock:
                            self._results[index] = []
                    
                    finally:
                        url_queue.task_done()
                        
                except Empty:
                    break
                except Exception as e:
                    print(f"工作线程发生错误: {str(e)}")
                    break
        
        # 创建并启动工作线程
        threads = []
        for _ in range(max_workers):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
            threads.append(t)
        
        # 等待所有任务完成
        url_queue.join()
        
        # 等待所有线程结束
        for t in threads:
            t.join(timeout=1)
        
        return self._results

    def _select_best_poem(self, poems):
        """
        从多个诗词版本中选择最合适的一个
        目前简单返回第一个，后续可以添加更复杂的匹配算法
        """
        if not poems:
            return []
        
        # 目前简单返回第一个结果
        # TODO: 后续可以添加更复杂的匹配算法，如：
        # 1. 根据内容长度选择最完整的版本
        # 2. 根据标题完全匹配度选择
        # 3. 根据第一句相似度选择
        # 4. 根据来源可靠度选择
        return [poems[0]] if poems else []

    def _parse_response(self, html_text):
        """解析诗词志网站的响应内容"""
        soup = BeautifulSoup(html_text, 'html.parser')
        # 查找 explist 类下的所有 li 元素
        poems = soup.find('ul', class_='explist')
        if not poems:
            return []
        
        poems = poems.find_all('li')
        results = []
        
        for poem in poems:
            poem_data = {}
            
            # 提取标题和链接
            title_elem = poem.find('p').find('a', class_='link')
            if title_elem:
                # 移除标题中的 highlightKeyword span
                highlight_spans = title_elem.find_all('span', class_='highlightKeyword')
                for span in highlight_spans:
                    span.unwrap()
                poem_data['title'] = title_elem.get_text(strip=True)
                poem_data['url'] = 'https://shicizhi.com' + title_elem.get('href', '')
            
            # 提取作者
            author_elem = poem.find('p').find_all('a', class_='link')
            if len(author_elem) > 1:  # 第二个 link 是作者链接
                poem_data['author'] = author_elem[1].get_text(strip=True)
            else:
                poem_data['author'] = "佚名"
            
            # 提取内容
            content_elem = poem.find('div', class_='content-limit')
            if content_elem:
                # 获取所有文本，包括 <br/> 标签
                content = ''
                for element in content_elem.children:
                    if element.name == 'br':
                        content += '\n'
                    else:
                        text = element.string if element.string else str(element)
                        content += text.strip()
                
                # 清理内容
                content = content.strip()
                # 处理连续的换行符
                content = '\n'.join(line for line in content.split('\n') if line.strip())
                poem_data['content'] = content
            
            if poem_data.get('title') and poem_data.get('content'):
                results.append(poem_data)
        
        # 提取总数信息
        total_div = soup.find('div', class_='page-total')
        if total_div:
            total_text = total_div.get_text(strip=True)
            try:
                total_count = int(''.join(filter(str.isdigit, total_text)))
                for poem in results:
                    poem['total_count'] = total_count
            except ValueError:
                pass
        
        # 选择最佳匹配的诗词
        return self._select_best_poem(results)

    def run(self, keywords_dict, max_workers=3):
        """运行爬虫"""
        return self.search_poems(keywords_dict, max_workers)

def main():
    spider = ShicizhiSpider()
    # 测试多个关键词
    test_keywords = [
        {0: "春江花月夜"},
        {1: "将进酒"},
        {2: "登高"},
        {3: "静夜思"},
        {4: "望岳"}
    ]
    results = spider.run(test_keywords, max_workers=3)
    
    # 打印结果
    for index, poems in results.items():
        print(f"\n关键词索引 {index} 的搜索结果:")
        for poem in poems:
            print(f"标题: {poem['title']}")
            print(f"作者: {poem['author']}")
            print(f"内容: {poem['content']}")
            print(f"链接: {poem.get('url', '无链接')}")
            print("-" * 50)

if __name__ == "__main__":
    main()