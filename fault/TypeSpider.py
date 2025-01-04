from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import threading
from queue import Queue, Empty
import time
import random
import pandas as pd
import os

class TypeSpider:
    def __init__(self):
        self.base_url = "https://baike.sogou.com/"
        self.thread_num = 5  # 减少线程数，避免过于频繁的请求
        self.title_queue = Queue()
        self.result_queue = Queue()
        self.output_file = "data/titles_type.csv"
        self.unfind = []
        
    def create_driver(self):
        """创建更真实的浏览器实例"""
        options = webdriver.ChromeOptions()
        # 基础反检测
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 添加更多真实浏览器特征
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-infobars')
        
        # 随机化窗口大小
        window_width = random.randint(1024, 1920)
        window_height = random.randint(768, 1080)
        options.add_argument(f'--window-size={window_width},{window_height}')
        
        # 添加随机User-Agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        driver = webdriver.Chrome(options=options)
        # 添加随机cookie
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }})
        
        return driver

    def search_title_worker(self):
        """改进的工作线程函数"""
        driver = self.create_driver()
        retry_count = 0
        max_retries = 3
        
        while True:
            try:
                title = self.title_queue.get(timeout=10)
                try:
                    # 随机化访问间隔
                    time.sleep(random.uniform(2, 4))
                    
                    # 模拟真实用户行为
                    driver.get(self.base_url)
                    
                    # 随机鼠标移动和停顿
                    search_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "searchText"))
                    )
                    
                    # 模拟人工输入
                    for char in title:
                        search_input.send_keys(char)
                        time.sleep(random.uniform(0.1, 0.3))
                    
                    time.sleep(random.uniform(0.5, 1))
                    
                    # 检查是否出现验证码
                    if "验证码" in driver.page_source:
                        print(f"遇到验证码，等待较长时间后重试...")
                        time.sleep(random.uniform(30, 60))  # 较长等待时间
                        retry_count += 1
                        if retry_count < max_retries:
                            self.title_queue.put(title)  # 重新加入队列
                            continue
                        else:
                            self.unfind.append(title)
                            retry_count = 0
                            continue
                    
                    # 搜索输入
                    search_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "searchText"))
                    )
                    search_input.clear()
                    search_input.send_keys(title)
                    
                    # 点击搜索
                    enter_button = driver.find_element(By.ID, "enterLemma")
                    enter_button.click()
                    
                    time.sleep(0.5)
                    if "fromTitle=" not in driver.current_url:
                        self.unfind.append(title)
                        continue

                    info = {"title": title}
                    
                    # 提取体裁信息
                    try:
                        # 方法1：从表格提取
                        titles = driver.find_elements(By.CSS_SELECTOR, "th.base-info-card-title")
                        for title_element in titles:
                            if title_element.text == "文学体裁":
                                value = title_element.find_element(By.XPATH, 
                                    "following-sibling::td//div[@class='base-info-card-value']/div").text
                                info["type"] = value
                                break
                        else:
                            # 方法2：从正文提取
                            try:
                                content = driver.find_element(By.CSS_SELECTOR, ".section_content .rich_text_area")
                                text = content.text
                                if "【作品体裁】" in text:
                                    lines = text.split('\n')
                                    for line in lines:
                                        if "【作品体裁】" in line:
                                            info["type"] = line.split("】")[-1].strip()
                                            break
                                else:
                                    info["type"] = '古诗'
                            except Exception as e:
                                print(f"从正文提取体裁时发生错误: {e}")
                                info["type"] = '古诗'
                    except Exception as e:
                        print(f"提取文学体裁时发生错误: {e}")
                        info["type"] = '古诗'

                    self.result_queue.put(info)
                    
                except Exception as e:
                    print(f"处理标题 {title} 时发生错误: {e}")
                    self.unfind.append(title)
                finally:
                    self.title_queue.task_done()
                    
            except Empty:
                break
                
        driver.quit()

    def process_titles(self, title_list):
        """批量处理标题"""
        # 将标题分批处理，避免同时发起太多请求
        batch_size = 20
        for i in range(0, len(title_list), batch_size):
            batch = title_list[i:i+batch_size]
            print(f"正在处理第 {i//batch_size + 1} 批，共 {len(batch)} 个标题")
            
            # 将当前批次的标题加入队列
            for title in batch:
                self.title_queue.put(title)
            
            # 创建并启动线程
            threads = []
            for _ in range(min(self.thread_num, len(batch))):
                t = threading.Thread(target=self.search_title_worker)
                t.daemon = True
                t.start()
                threads.append(t)
            
            # 等待当前批次处理完成
            self.title_queue.join()
            
            # 处理完一批后休息一段时间
            time.sleep(random.uniform(5, 10))
        
        # 收集结果
        results = []
        while not self.result_queue.empty():
            results.append(self.result_queue.get())
            
        # 保存结果到CSV（改用追加模式）
        if results:
            df = pd.DataFrame(results)
            try:
                # 如果文件存在，追加数据（不包含表头）
                df.to_csv(self.output_file, mode='a', header=not os.path.exists(self.output_file), 
                         index=False, encoding='utf-8')
                print(f"已追加 {len(results)} 条记录到 {self.output_file}")
            except Exception as e:
                print(f"保存数据时发生错误: {e}")
                # 如果追加失败，尝试创建新文件
                df.to_csv(self.output_file, index=False, encoding='utf-8')
                print(f"已创建新文件并保存 {len(results)} 条记录到 {self.output_file}")
            
        if self.unfind:
            print(f"\n未找到的标题: {self.unfind}")
            
        return results

if __name__ == "__main__":
    spider = TypeSpider()
    test_titles = ["七夕宴悬圃二首", "过温汤", "唐享昊天乐", "不存在的词条xyz123"]
    try:
        results = spider.process_titles(test_titles)
        for info in results:
            print(f"\n标题: {info['title']}")
            print(f"体裁: {info['type']}")
    except KeyboardInterrupt:
        print("\n程序被用户中断")