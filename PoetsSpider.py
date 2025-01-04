from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import threading
from queue import Queue, Empty
import random
import re
from PoetsSpider_2 import PoetsSpider_2

class PoetsSpider:
    def __init__(self):
        self.base_url = "http://hkxy.xcz.im/search?q="
        self.thread_num = 10
        self.poet_queue = Queue()
        self.result_queue = Queue()
        self.output_file="data/poets_info.csv"
        self.output_file_2 = "data/poets_info2.csv"
        self.unfind = []
    def create_driver(self):
        driver = webdriver.Chrome()
        return driver
        
    def get_poet_info(self):
        driver = self.create_driver()
        while True:
            try:
                poet_name = self.poet_queue.get(timeout=30)
                try:
                    # 访问搜索页面
                    driver.get(self.base_url + poet_name)
                    time.sleep(1 + random.random())  # 随机延迟
                    
                    # 等待并点击第一个诗人链接
                    first_poet = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".author-item"))
                    )
                    first_poet.click()
                    
                    # 等待并获取诗人信息
                    name = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".author .name"))
                    ).text.strip()
                    
                    dynasty = driver.find_element(By.CSS_SELECTOR, ".author .dynasty").text.strip()
                    description = driver.find_element(By.CSS_SELECTOR, ".author .desc").text.strip()
                    
                    self.result_queue.put({
                        "name": name,
                        "dynasty": dynasty,
                        "description": description
                    })                    
                except Exception as e:
                    self.unfind.append(poet_name)
                    print(f"获取诗人 {poet_name} 信息时出错: {str(e)}")
                finally:
                    self.poet_queue.task_done()
                    
            except Empty:
                break
                
        driver.quit()
    
    def extract_years(self, info_text):
        """从诗人信息中提取生卒年
        Args:
            info_text: str, 诗人的简介信息
        Returns:
            tuple: (birth_year, death_year) 如果无法提取则返回 (None, None)
        """
        match = re.search(r'(\d{3})[年～－至].*?(\d{3})年?', info_text)
        if match:
            birth_year = match.group(1)  # 生年
            death_year = match.group(2)  # 死年
            return birth_year, death_year
        
    def save_to_csv(self, poet_list):
        # 将诗人名单加入队列
        for poet in poet_list:
            self.poet_queue.put(poet)
            
        # 创建并启动线程
        threads = []
        for _ in range(self.thread_num):
            t = threading.Thread(target=self.get_poet_info)
            t.daemon = True
            t.start()
            threads.append(t)
            
        # 等待队列处理完成
        self.poet_queue.join()
        
        # 收集结果
        results = []
        while not self.result_queue.empty():
            results.append(self.result_queue.get())
        print("处理爬取未能成功获取的诗人信息：")
        spider = PoetsSpider_2()
        results_2 = spider.run(self.unfind)
        df_2 = pd.DataFrame(list(results_2.items()), columns=['poets', 'info'])
            
        # 保存到CSV
        df = pd.DataFrame(results)
        df.to_csv(self.output_file, index=False, encoding='utf-8')
        print(f"已保存 {len(results)} 位诗人信息到 {self.output_file}")
        df_2.to_csv(self.output_file_2, index=False, encoding='utf-8')
        print(f"已保存 {len(results_2)} 位诗人信息到 {self.output_file_2}")
        return df
if __name__ == '__main__':
    spider = PoetsSpider()
    try:
        # 批量处理多个诗人
        poet_list = ["李白", "杜甫", "白居易", "王维", "齐己"]
        spider.save_to_csv(poet_list)
    except KeyboardInterrupt:
        print("程序被用户中断")