from flask import Flask, render_template, request
from TangPoetryVisual import TangPoetryVisual
import pandas as pd
from utils.pagination import Pagination
#from EmotionAnalyzer import EmotionAnalyzer
from gensim.models import KeyedVectors
from word2vec import find_similar_words
from SklearnModel import EmotionAnalyzer

app = Flask(__name__)

# 加载数据
poetry_data = pd.read_csv('data/legal.csv', encoding='utf-8')
poets_info = pd.read_csv('data/poets_info.csv', encoding='utf-8')
poets_df = pd.read_csv('data/poets_df.csv', encoding='utf-8')
poet_counts = pd.read_csv('data/poet_stats_cache.csv')
vis = TangPoetryVisual()
analyzer = EmotionAnalyzer()
word2vec_model = KeyedVectors.load('models/word_vectors.model')

# 加载字频数据
char_frequency = pd.read_csv('data/char_frequency.csv')

# 初始化情感分析模型
analyzer.load()

@app.route('/')
def index():
    # 获取统计数据
    total_poems = len(poetry_data)
    total_poets = len(poets_df)
    
    # 随机推荐一首诗
    random_poem = poetry_data.sample(n=1).iloc[0]
    
    return render_template('index.html', 
                         total_poems=total_poems,
                         total_poets=total_poets,
                         random_poem=random_poem)

@app.route('/poems')
def poems():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 计算当前页的数据范围
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # 获取总数据量
    total_items = len(poetry_data)
    total_pages = (total_items + per_page - 1) // per_page
    
    # 获取当前页的数据
    current_poems = poetry_data.iloc[start_idx:end_idx]
    
    # 创建分页信息
    pagination = Pagination(page, per_page, total_items)
    
    # 将 DataFrame 转换为字典列表
    poems_list = current_poems.to_dict('records')
    
    return render_template('poems.html',
                         poems=poems_list,
                         pagination=pagination)

@app.route('/poets')
def poets():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 如果 top_chars 是字符串格式，需要转换回列表
    if isinstance(poet_counts['top_chars'].iloc[0], str):
        poet_counts['top_chars'] = poet_counts['top_chars'].apply(lambda x: x.split(','))
    
    # 计算当前页的数据范围
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # 获取总数据量和分页信息
    total_items = len(poet_counts)
    pagination = Pagination(page, per_page, total_items)
    
    # 获取当前页的数据
    current_poets = poet_counts.iloc[start_idx:end_idx]
    poets_list = current_poets.to_dict('records')
    
    # 获取一些总体统计信息
    total_poets = len(poet_counts)
    total_poems = poetry_data.shape[0]
    avg_poems_per_poet = total_poems / total_poets
    
    return render_template('poets.html',
                         poets=poets_list,
                         pagination=pagination,
                         total_poets=total_poets,
                         total_poems=total_poems,
                         avg_poems=round(avg_poems_per_poet, 1))

@app.route('/analysis')
def analysis():
    vis = TangPoetryVisual()
    
    # 计算基础统计信息
    stats = {
        'total_poets': len(vis.poets_df),
        'total_poems': len(vis.poetry_data),
        'avg_poems': round(len(vis.poetry_data) / len(vis.poets_df), 1),
        'avg_length': round(vis.poetry_data['content'].str.len().mean(), 1)
    }
    
    # 获取所有图表数据
    charts = vis.get_all_charts()
    
    return render_template('analysis.html',
                         stats=stats,
                         charts=charts)

@app.route('/search')
def search():
    keyword = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if not keyword:
        return render_template('search.html')
    
    # 根据搜索类型进行不同的查询
    if search_type == 'poet':
        results = poetry_data[poetry_data['poets'].str.contains(keyword, na=False)]
    elif search_type == 'title':
        results = poetry_data[poetry_data['title'].str.contains(keyword, na=False)]
    elif search_type == 'content':
        results = poetry_data[poetry_data['content'].str.contains(keyword, na=False)]
    else:  # 全部搜索
        results = poetry_data[
            poetry_data['title'].str.contains(keyword, na=False) |
            poetry_data['content'].str.contains(keyword, na=False) |
            poetry_data['poets'].str.contains(keyword, na=False)
        ]
    
    # 获取匹配的诗人信息
    if search_type == 'poet' or search_type == 'all':
        matching_poets = poets_df[poets_df['poets'].str.contains(keyword, na=False)]
        poet_info = matching_poets.to_dict('records') if not matching_poets.empty else []
    else:
        poet_info = []
    
    # 按诗人分组统计结果
    if not results.empty:
        poet_counts = results['poets'].value_counts().to_dict()
    else:
        poet_counts = {}
    
    # 添加分页功能
    total_items = len(results)
    pagination = Pagination(page, per_page, total_items)
    
    # 计算当前页的数据范围
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # 获取当前页的搜索结果
    current_results = results.iloc[start_idx:end_idx]
    
    return render_template('search.html', 
                         results=current_results.to_dict('records'),
                         keyword=keyword,
                         search_type=search_type,
                         poet_info=poet_info,
                         poet_counts=poet_counts,
                         total_results=total_items,
                         pagination=pagination)
@app.route('/poet/<poet>')
def poet_detail(poet):
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 查找该诗人的所有诗歌
    poet_poems = poetry_data[poetry_data['poets'] == poet]
    
    # 从poets_info.csv中查询诗人信息
    poet_info = poets_info[poets_info['name'] == poet]
    if len(poet_info) == 0:
        basic_info = {
            "name": poet,
            "dynasty": "未知",
            "life_time": "未知",
            "description": "未找到该诗人信息",
            "poem_count": len(poet_poems)
        }
    else:
        # 获取第一条匹配记录
        info = poet_info.iloc[0]
        dynasty_life = info['dynasty']
        dynasty = dynasty_life.split(']')[0].strip('[')
        life_time = dynasty_life.split(']')[1].strip() if ']' in dynasty_life else "未知"
        
        basic_info = {
            "name": info['name'],
            "dynasty": dynasty,
            "life_time": life_time,
            "description": info['description'],
            "poem_count": len(poet_poems)
        }
    
    # 计算分页
    total_items = len(poet_poems)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # 获取当前页的诗歌
    current_poems = poet_poems.iloc[start_idx:end_idx]
    
    # 创建分页信息
    pagination = Pagination(page, per_page, total_items)
    
    return render_template('poet_detail.html',
                         poet=poet,
                         basic_info=basic_info,
                         poems=current_poems.to_dict('records'),
                         pagination=pagination)

@app.route('/sentiment', methods=['GET', 'POST'])
def sentiment():
    if request.method == 'POST':
        poem_text = request.form.get('poem_text', '')
        if poem_text:
            result = analyzer.predict_sklearn(poem_text)
            return render_template('sentiment.html', 
                                poem_text=poem_text,
                                sentiment_result=result)
    
    return render_template('sentiment.html')

@app.route('/similar_chars', methods=['GET', 'POST'])
def similar_chars():
    if request.method == 'POST':
        char = request.form.get('char', '')
        if char:
            # 确保输入是单个汉字
            char = char[0] if len(char) > 0 else ''
            try:
                # 获取相似的字
                similar_results = find_similar_words(word2vec_model, char, topn=10)
                return render_template('similar_chars.html',
                                    char=char,
                                    similar_results=similar_results,
                                    error=None)
            except KeyError:
                # 处理输入字不在词向量模型中的情况
                error = f'抱歉，未能找到与"{char}"相关的字'
                return render_template('similar_chars.html',
                                    char=char,
                                    similar_results=None,
                                    error=error)
    
    return render_template('similar_chars.html')

if __name__ == '__main__':
    app.run(debug=True)
