from PoetsSpider import PoetsSpider
import pandas as pd
import re

class Descriptive_analysis:
    def __init__(self):
        self.data_path = 'data/全唐诗2.txt'
        self.poets_info_path = 'data/poets_df.csv'
        self.poets_df = pd.DataFrame()
        self.freq_df = pd.DataFrame()
        self.data_df = pd.DataFrame()

    def clean_to_df(self, txt):
        all_list = re.split(r'卷\d+_?\d*', txt)
        volume_nums = [int(num) for num in re.findall(r'卷(\d+)_?\d*', txt)]
        cleaned_parts = [re.sub(r'\s+', ' ', part.strip()) for part in all_list if part.strip()]
        # 正则表达式：提取题目、诗人和诗文内容
        pattern = r"【(.*?)】([\u4e00-\u9fa5]+)?\s*(.*)"

        # 用于存储提取结果
        poetry_list = []
        for text,volume in zip(cleaned_parts,volume_nums):
            match = re.match(pattern, text)
            if match:
                title = match.group(1)
                poet = match.group(2) if match.group(2) else '佚名'
                content = match.group(3)
                poetry_list.append({"title": title, "poets": poet, "content": content,'volumes':volume})
        df = pd.DataFrame(poetry_list)
        return df
    def read_file(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content

    def extract_years(self,info_text):
        """从诗人信息中提取生卒年
        Args:
            info_text: str, 诗人的简介信息
        Returns:
            tuple: (birth_year, death_year) 如果无法提取则返回 (-1, -1)
        """
        if not isinstance(info_text, str):  # 添加类型检查
            return -1, -1
            
        patterns = [
            r"(\d{3})年\s*~\s*(\d{3})年",          # 完整的生卒年：803年 ~ 852年
            r"(\d{3})\?\s*~\s*(\d{3})后年",        # 864? ~ 943后年
            r"(\d{3})\?\s*~\s*(\d{3})年",          # 864? ~ 943年
            r"\?\s*~\s*(\d{3})年",                  # 只有卒年：? ~ 881年
            r"\?\s*~\s*(\d{3})后年",                # ? ~ 881后年
        ]
        
        for pattern in patterns:
            match = re.search(pattern, info_text)
            if match:
                if pattern == patterns[0]:  # 完整的生卒年
                    return int(match.group(1)), int(match.group(2))
                elif pattern in [patterns[1], patterns[2]]:  # 生年不确定
                    return int(match.group(1)), int(match.group(2))
                elif pattern in [patterns[3], patterns[4]]:  # 只有卒年
                    return -1, int(match.group(1))
                else:  # 都不确定
                    return -1, -1
                    
        return -1, -1  # 如果没有匹配到任何模式
    def poem_period(self):
        """根据诗人生卒年份划分时期
        Returns:
            DataFrame: 添加时期列的诗人数据框
        """
        def determine_period(row):
            birth_year = int(row['birth_year'])
            death_year = int(row['death_year'])
            
            # 如果没有任何年份信息
            if birth_year == -1 and death_year == -1:
                return '唐'
            
            # 如果只有出生年
            if death_year == -1:
                if birth_year <= 712:
                    return '初唐'
                elif birth_year <= 765:
                    return '盛唐'
                elif birth_year <= 835:
                    return '中唐'
                else:
                    return '晚唐'
            if birth_year == -1:
                if death_year <= 712:
                    return '初唐'
                elif death_year <= 765:
                    return '盛唐'
                elif death_year <= 835:
                    return '中唐'
                else:
                    return '晚唐'
            
            # 如果有完整的生卒年，取中间年份判断
            mid_year = (birth_year + death_year) // 2
            if mid_year <= 712:
                return '初唐'
            elif mid_year <= 765:
                return '盛唐'
            elif mid_year <= 835:
                return '中唐'
            else:
                return '晚唐'
        
        # 添加时期列
        self.poets_df['period'] = self.poets_df.apply(determine_period, axis=1)
        self.poets_df.to_csv(self.poets_info_path, encoding='utf-8')
        # 统计各时期诗人数量
        period_stats = self.poets_df['period'].value_counts().to_frame()
        period_stats.columns = ['count']
        period_stats['percentage'] = period_stats['count'] / len(self.poets_df) * 100
        
        return period_stats
    def legal_data(self):
        with open(self.data_path,'r',encoding='utf-8') as f:
            txt = f.read()
        df = self.clean_to_df(txt)
        self.data_df = df
        return df
    def analyze_poets(self):
        df = self.legal_data()
        poets_df = df['poets'].value_counts().to_frame()
        poets_df.reset_index(inplace=True)
        poets_df.columns = ['poets', 'count']
        poets_df['percentage'] = poets_df['count']/poets_df['count'].sum() * 100
        spider = PoetsSpider()
        #results = spider.save_to_csv(poets_df['poets'])
        results = pd.read_csv('data/poets_info.csv', encoding='utf-8')
        poets_df['birth_year'] = -1
        poets_df['death_year'] = -1

        for i, poet in enumerate(poets_df['poets']):
            period_info = results[results['name'] == poet]['dynasty'].values[0] if len(results[results['name'] == poet]) > 0 else ''
            birth_year, death_year = self.extract_years(period_info)
            poets_df.loc[i, 'birth_year'] = birth_year
            poets_df.loc[i, 'death_year'] = death_year
        
        self.poets_df = poets_df
        poets_df.to_csv(self.poets_info_path, encoding='utf-8')
        print('成功保存诗人信息')
        return poets_df
    def char_frequency_stat(self):
        """字频统计
        Args:
            path: 文本路径
        Returns:
            DataFrame: 字频统计结果，包含字符和出现次数
        """
        text = self.read_file(self.data_path)
        stopwords = set('而何乎乃其且若所为漹以因于与也则者之不自得一来去无可是已此的上中兮三矣焉兮欤乎哉耳夫')
        char_freq = {}
        for char in text:
            if not re.match(r'[\u4e00-\u9fff]', char):
                continue
            if char in stopwords:
                continue
            char_freq[char] = char_freq.get(char, 0) + 1
        
        freq_df = pd.DataFrame({
            'char': list(char_freq.keys()),
            'frequency': list(char_freq.values())
        })
        
        freq_df = freq_df.sort_values('frequency', ascending=False)
        freq_df = freq_df.reset_index(drop=True)
        
        self.freq_df = freq_df
        return freq_df
    def generate_poet_stats_cache(self):
        """生成诗人统计信息的缓存文件"""
        # 计算诗人作品数量
        poet_counts = self.data_df['poets'].value_counts().reset_index()
        poet_counts.columns = ['name', 'poem_count']
        
        # 定义虚词集合
        stopwords = set('而何乎乃其且若所为漹以因于与也则者之不自得一来去无可是已此的上中兮三矣焉兮欤乎哉耳夫')
        
        # 计算每个诗人最常用的字
        poet_top_chars = {}
        for poet in poet_counts['name']:
            poet_poems = self.data_df[self.data_df['poets'] == poet]['content'].str.cat()
            filtered_chars = [char for char in poet_poems 
                            if '\u4e00' <= char <= '\u9fff' and char not in stopwords]
            char_counts = pd.Series(filtered_chars).value_counts().head(5)
            poet_top_chars[poet] = ','.join(char_counts.index.tolist())
        
        # 添加最常用字信息到 poet_counts
        poet_counts['top_chars'] = poet_counts['name'].map(poet_top_chars)
        
        # 保存计算结果到缓存文件
        cache_path = 'data/poet_stats_cache.csv'
        poet_counts.to_csv(cache_path, index=False, encoding='utf-8')
        print(f'成功生成诗人统计缓存文件：{cache_path}')
        
        return poet_counts
    def analyze_char_frequency(self):
        """分析字频统计结果
        Args:
            df: 字频统计DataFrame
        """
        df = self.freq_df.copy()
        total_chars = df['frequency'].sum()
        
        df['percentage'] = df['frequency'] / total_chars * 100
        
        print(f"\n总字数: {total_chars}")
        print("\n出现频率最高的前20个字:")
        print(df.head(20).to_string(index=False))
        self.freq_df = df
        #self.freq_df.to_csv('char_frequency.csv', index=False, encoding='utf-8')
    def analyze_four_seasons(self):
        """分析四季词频
        Returns:
            DataFrame: 包含四季词频统计的数据框
        """
        # 读取字频数据
        df = pd.read_csv('data/char_frequency.csv', encoding='utf-8')
        
        # 统计四季词频
        seasons_data = {
            '春': df.loc[df['char'] == '春', 'frequency'].values[0] if not df.loc[df['char'] == '春'].empty else 0,
            '夏': df.loc[df['char'] == '夏', 'frequency'].values[0] if not df.loc[df['char'] == '夏'].empty else 0,
            '秋': df.loc[df['char'] == '秋', 'frequency'].values[0] if not df.loc[df['char'] == '秋'].empty else 0,
            '冬': df.loc[df['char'] == '冬', 'frequency'].values[0] if not df.loc[df['char'] == '冬'].empty else 0
        }
        
        # 转换为DataFrame
        seasons = pd.DataFrame({
            'season': list(seasons_data.keys()),
            'frequency': list(seasons_data.values())
        })
        
        # 计算百分比
        total_freq = seasons['frequency'].sum()
        seasons['percentage'] = seasons['frequency'] / total_freq * 100
        
        # 按频率排序
        seasons = seasons.sort_values('frequency', ascending=False)
        seasons = seasons.reset_index(drop=True)
        
        return seasons
    def analyze_color_frequency(self):
        """分析颜色字频
        Args:
            path: 字频统计路径
        Returns:
            dict: 包含各色系统计结果的字典
        """
        df = pd.read_csv('data/char_frequency.csv',encoding='utf-8')
        
        # 定义各色系字符
        color_groups = {
            '红色系': ['红', '丹', '朱', '赤', '绛', '膛', '彭', '绯', '紫', '猩','胭'],
            '黑色系': ['黑', '玄', '乌', '暗', '冥', '墨', '黯', '黝'],
            '绿色系': ['绿', '碧', '翠', '苍', '青', '兰', '芳', '萝', '葱'],
            '白色系': ['白', '素', '皎', '皓', '雪', '银', '霜', '粲'],
            '黄色系':['黄','金','橙','琥珀','萤','葭','禾'],
            '蓝色系':['蓝','碧','湛'],
            '其他':['紫','黛','瑶','灰','烟','尘','霏','粉','桃','霞','膏','铸','辉','曜','银']
        }
        
        color_stats = {}
        all_colors_total = 0
        
        # 计算总频率
        for colors in color_groups.values():
            group_freq = df.loc[df['char'].isin(colors)]
            if not group_freq.empty:
                all_colors_total += group_freq['frequency'].sum()
        
        # 分析各色系
        for color_group, colors in color_groups.items():
            group_freq = df.loc[df['char'].isin(colors)].copy()
            
            if not group_freq.empty:
                group_total = group_freq['frequency'].sum()
                
                group_freq.loc[:, 'part_percentage'] = group_freq['frequency'] / group_total * 100
                group_freq.loc[:, 'all_percentage'] = group_freq['frequency'] / all_colors_total * 100
                
                group_freq = group_freq[['char', 'part_percentage', 'all_percentage']]
                
                group_freq = group_freq.sort_values('part_percentage', ascending=False)
                
                color_stats[color_group] = {
                    'total_frequency': group_total,
                    'details': group_freq
                }
        
        color_summary = pd.DataFrame({
            'color_group': list(color_stats.keys()),
            'total_frequency': [stats['total_frequency'] for stats in color_stats.values()]
        })
        
        color_summary['percentage'] = color_summary['total_frequency'] / all_colors_total * 100
        color_summary = color_summary.sort_values('total_frequency', ascending=False)
        color_summary = color_summary.reset_index(drop=True)
        
        return color_stats, color_summary
    def add_type(self):
        """添加诗歌体裁类型"""
        df = self.data_df.copy()
        
        # 批量获取所有标题的体裁
        title_list = df['title'].tolist()
        
        # 将标题分批处理，每批100个
        batch_size = 100
        all_results = {}
        
        for i in range(0, len(title_list), batch_size):
            batch_titles = title_list[i:i + batch_size]
            print(f"正在处理第 {i//batch_size + 1} 批，共 {len(batch_titles)} 个标题")
            batch_results = self.classify_poetry_genre(batch_titles)
            all_results.update(batch_results)
        
        # 使用映射添加类型
        df['type'] = df['title'].map(all_results)
        
        self.data_df = df
        df.to_csv('legal.csv', encoding='utf-8', index=False)
        print("体裁分类完成并保存到文件")

if __name__ == "__main__":
    des = Descriptive_analysis()
    # 诗人分析
    poets_df = des.analyze_poets()
    print("诗人统计结果：")
    print(poets_df[['poets', 'birth_year', 'death_year']])
    
    # 时期分析
    period_stats = des.poem_period()
    print("\n各时期诗人统计：")
    print(period_stats)
    df = des.legal_data()
    des.add_type()
    print('成功')

    