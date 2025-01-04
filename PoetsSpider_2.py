from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
from queue import Queue, Empty
import time
import random

class PoetsSpider_2:
    def __init__(self):
        self.base_url = 'https://www.gushiwen.cn/search.aspx'
        self.results = {}
        self.thread_num = 5
        self.poet_queue = Queue()
        self.result_queue = Queue()
        
    def create_driver(self):
        options = webdriver.ChromeOptions()
        # 添加一些反爬虫检测选项
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        driver = webdriver.Chrome(options=options)
        return driver

    def search_poet(self, driver, name):
        """
        使用Selenium搜索诗人信息
        """
        try:
            url = f"{self.base_url}?value={name}&valuej={name[0]}"
            driver.get(url)
            time.sleep(random.uniform(1, 2))  # 随机延迟
            
            # 等待简介内容加载
            intro_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p[style=' margin:0px;']"))
            )
            return intro_element.text
            
        except Exception as e:
            print(f"搜索诗人 {name} 信息时发生错误: {e}")
            return None

    def worker(self):
        """
        工作线程函数
        """
        driver = self.create_driver()
        try:
            while True:
                try:
                    poet = self.poet_queue.get_nowait()
                    intro = self.search_poet(driver, poet)
                    if intro:
                        self.result_queue.put((poet, intro))
                    self.poet_queue.task_done()
                except Empty:
                    break
        finally:
            driver.quit()

    def run(self, poets, max_workers=5):
        """
        使用多线程并发搜索多个诗人信息
        """
        self.results.clear()
        
        # 将诗人名单加入队列
        for poet in poets:
            self.poet_queue.put(poet)
        
        # 创建并启动线程
        threads = []
        for _ in range(min(max_workers, len(poets))):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            threads.append(t)
        
        # 等待所有任务完成
        self.poet_queue.join()
        
        # 收集结果
        while not self.result_queue.empty():
            poet, intro = self.result_queue.get()
            self.results[poet] = intro
            
        print("\n搜索完成！")
        return self.results
if __name__ == '__main__':
    spider = PoetsSpider_2()
    # 测试多线程搜索
    poets_list = ['李白', 'wtt']
    results = spider.run(poets_list)
    print("\n多线程搜索结果:")
    for poet, intro in results.items():
        print(f"\n{poet}:")
        print(intro)
    print(results)
