import re
import pandas as pd
import threading
from queue import Queue, Empty
from ShicizhiSpider import ShicizhiSpider
from PoetsSpider import PoetsSpider 
class PoemProcessor:
    """唐诗处理类"""
    def __init__(self, file_path):
        self.file_path = file_path
        # 定义正则表达式模式
        self.title_pattern1 = r'【(.+?)】([^\s]+)(?:\s+)(.+)?'  # 有作者模式
        self.title_pattern2 = r'【(.+?)】\s*(.+)?'  # 无作者模式
        self.chinese_pattern = r'[\u4e00-\u9fff]+'
        self.legal_pattern = r'[^\u4e00-\u9fff\【\】\。\，\（\）\-\、\！\？\"\"\：\·\；\《\》\s]'
        self.result = []
        self.df = None
        self.output_path_csv = 'output.csv'
        self.output_path_txt = 'output.txt'
        self.chinese_chars = []
    def clean_special_chars(self, text):
        """清理特殊字符"""
        return re.sub(self.legal_pattern, '', text.strip())
    
    def extract_chinese(self, text):
        """提取中文字符"""
        chinese_chars = re.findall(self.chinese_pattern, text)
        return ''.join(chinese_chars)
    
    def has_special_chars(self, text):
        """检查是否包含特殊字符"""
        special_chars = re.findall(self.legal_pattern, text)
        return bool(special_chars), ''.join(set(special_chars))
    
    def save_chinese_chars(self):
        """保存中文内容"""
        with open('chinese_chars.txt', 'w', encoding='utf-8') as f:
            for char in self.chinese_chars:
                f.write(char + '\n')

    def extract_poem_info(self, text, volume_num):
        """从文本中提取诗歌信息"""
        # 首先清理文本中的乱码字符
        text = self.clean_special_chars(text)
        pattern_status = 0
        
        # 处理标题没有结束符号的情况
        if '【' in text and '】' not in text:
            parts = text.split(maxsplit=1)
            if len(parts) >= 2:
                title = parts[0].replace('【', '').strip()
                content = parts[1].strip()
                return 0, {
                    'title': title,
                    'poets': '佚名',
                    'content': content if content else '无内容',
                    'volume': volume_num
                }
        
        # 原有的匹配逻辑保持不变
        match = re.match(self.title_pattern1, text)
        if match:
            title = match.group(1).strip()
            poets = match.group(2).strip() if match.group(2) else "佚名"
            content = ''.join(match.group(3).split()) if match.group(3) else "无内容"
            pattern_status = 1
        else:
            match = re.match(self.title_pattern2, text)
            if match:
                title = match.group(1).strip()
                poets = "佚名"
                content = ''.join(match.group(2).split()) if match.group(2) else "无内容"
            else:
                # 当无法匹配时，将整个文本作为诗文内容
                title = "无题"
                poets = "佚名"
                content = text.strip()
        
        return pattern_status, {
            'title': title,
            'poets': poets,
            'content': content,
            'volume': volume_num
        }

    def illegal_to_legal(self, text_info):
        """将非法文本转换为合法文本"""
        spider = ShicizhiSpider()
        pattern_status = text_info.get('pattern_status', 0)
        
        # 如果标题正确（pattern_status=1），先用标题搜索
        if pattern_status == 1:
            keywords = [{0: text_info['title']}]
            results = spider.run(keywords)
            if results and results.get(0) and len(results[0]) > 0:
                best_match = results[0][0]  # 获取第一个匹配结果
                return {
                    'title': best_match['title'],
                    'poets': best_match['author'],  # ShicizhiSpider 返回的是 author 字段
                    'content': best_match['content'],
                    'volume': text_info['volume']
                }
        
        # 如果标题搜索失败或标题不正确，使用诗文内容搜索
        content = text_info.get('content', '')
        if not content or len(content) < 4:
            return text_info
        
        # 将内容按四字一组切分
        content_parts = [content[i:i+4] for i in range(0, len(content)-3, 4)]
        
        for part in content_parts:
            keywords = [{0: part}]
            results = spider.run(keywords)
            if results and results.get(0) and len(results[0]) > 0:
                best_match = results[0][0]
                return {
                    'title': best_match['title'],
                    'poets': best_match['author'],  # ShicizhiSpider 返回的是 author 字段
                    'content': best_match['content'],
                    'volume': text_info['volume']
                }
        
        # 如果所有尝试都失败，返回原始数据
        return text_info

    def process_illegal_poems_mt(self, illegal_poems, max_workers=5):
        """多线程处理非法诗词
        Args:
            illegal_poems (list): 需要处理的非法诗词列表
            max_workers (int): 最大工作线程数
        Returns:
            list: 处理后的合法诗词列表
        """
        legal_poems = []
        results_lock = threading.Lock()
        poem_queue = Queue()
        
        # 将诗词放入队列
        for poem in illegal_poems:
            poem_queue.put(poem)
        
        def worker():
            while True:
                try:
                    # 从队列获取诗词，设置超时防止死锁
                    poem = poem_queue.get(timeout=3)
                    try:
                        legal_poem = self.illegal_to_legal(poem)
                        if legal_poem:
                            with results_lock:
                                legal_poems.append(legal_poem)
                    except Exception as e:
                        print(f"处理诗词时出错: {str(e)}")
                    finally:
                        poem_queue.task_done()
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
        poem_queue.join()
        
        # 等待所有线程结束
        for t in threads:
            t.join(timeout=1)
        
        return legal_poems

    def process_file(self):
        """处理文件"""
        # 读取文件
        with open(self.file_path, 'r', encoding='utf-8') as f:
            file = f.read()
        
        # 提取卷号和内容
        volume_pattern = r'卷(\d+)_?\d*'
        data = re.split(r'卷\d+_?\d*', file)
        volume_nums = [int(num) for num in re.findall(volume_pattern, file)]
        
        # 清理数据
        cleaned_parts = [re.sub(r'\s+', ' ', part.strip()) for part in data if part.strip()]

        # 提取中文内容
        chinese_chars = []
        for text in cleaned_parts:
            chinese = ''.join(re.findall(r'[\u4e00-\u9fff]', text))
            if chinese:  # 只有当提取出中文时才添加
                chinese_chars.append(chinese)
        self.chinese_chars = chinese_chars
        
        legal_parts = []
        illegal_parts_0 = []
        illegal_parts_1 = []
        pure_poems = []       # 纯诗句（无标题作者）
        for part, vol_num in zip(cleaned_parts, volume_nums):
            has_special, special_chars = self.has_special_chars(part)
            result = self.extract_poem_info(part, vol_num)
            
            if result is None:
                continue
                
            pattern_status, poem_info = result
            
            if has_special:  # 包含特殊字符
                if pattern_status:
                    illegal_parts_1.append(poem_info)
                else:
                    illegal_parts_0.append(poem_info)
            else:  # 格式完整
                legal_parts.append(poem_info)
        
        # 使用多线程处理非法部分
        # legal_parts.extend(self.process_illegal_poems_mt(
        #     [dict(poem, pattern_status=1) for poem in illegal_parts_1]
        # ))
        
        # legal_parts.extend(self.process_illegal_poems_mt(
        #     [dict(poem, pattern_status=0) for poem in illegal_parts_0]
        # ))
        
        #self.result = legal_parts
        return legal_parts,illegal_parts_0,illegal_parts_1
    def poets_info(self, path, poets=None):
        """获取诗人信息"""
        df = pd.read_csv(path, encoding='utf-8')
        if poets is None:
            poets_list  = df['poets'].unique()
        
        spider = PoetsSpider()
        results = spider.run(poets_list)
        
        # 创建诗人信息DataFrame
        poets_info = pd.DataFrame({
            'poets': list(results.keys()),
            'info': list(results.values())
        })
        
        return poets_info
        

    def transform_to_df(self):
        """将部分转换为DataFrame"""
        self.df = pd.DataFrame(self.result)
        return self.df
    def save_to_csv(self):
        self.df.to_csv(self.output_path_csv, index=False, encoding='utf-8')
    def save_to_txt(self):
        with open(self.output_path_txt, 'w', encoding='utf-8') as f:
            for part in self.result:
                f.write(part + '\n')
if __name__ == "__main__":
    # 使用示例
    processor = PoemProcessor('全唐诗.txt')
    # legal_parts,illegal_parts_0,illegal_parts_1 = processor.process_file()
    # pd.DataFrame(legal_parts).to_csv('legal_parts.csv',index=False,encoding='utf-8')
    # pd.DataFrame(illegal_parts_0).to_csv('illegal_parts_0.csv',index=False,encoding='utf-8')
    # pd.DataFrame(illegal_parts_1).to_csv('illegal_parts_1.csv',index=False,encoding='utf-8')
    # poets_info = processor.poets_info('legal_parts.csv')
    # poets_info.to_csv('poets_info.csv')
    legal_parts,illegal_parts_0,illegal_parts_1 = processor.process_file()
    processor.save_chinese_chars()
