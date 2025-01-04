import multiprocessing
from gensim.models import Word2Vec
import pandas as pd
import os
import re
from openai import OpenAI
import time
import json

def prepare_sample_data():
    print("开始加载数据并分词...")
    # 1. 增加训练数据
    with open('data/全唐诗2.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    # 2. 更好的文本预处理
    sentences = []
    for i, line in enumerate(text.split('\n')):
        # 移除标点符号
        line = re.sub(r'[^\u4e00-\u9fff]', '', line)
        if len(line) > 1:
            sentences.append(list(line))

        if i % 100 == 0:
            print(f"已处理 {i}/{len(text.split('\n'))} 条数据")
    print("分词完成！")
    return sentences

def train_word2vec(save_path='models/word_vectors.model'):
    """训练Word2Vec模型并保存"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    if os.path.exists(save_path):
        print(f"发现已有模型，正在加载 {save_path}")
        return Word2Vec.load(save_path)
    
    sentences = prepare_sample_data()
    
    print("开始训练模型...")
    model = Word2Vec(sentences,
                    vector_size=100,     # 降低维度
                    window=10,           # 扩大窗口以捕获更多上下文
                    min_count=10,        # 提高词频阈值过滤低频词
                    sg=1,                # 使用skip-gram
                    negative=10,         # 增加负采样
                    epochs=20,           # 增加训练轮数
                    workers=multiprocessing.cpu_count())
    
    # 保存模型
    print(f"保存模型到 {save_path}")
    model.save(save_path)
    
    return model

def find_similar_words(model, word, topn=20):
    try:
        similar_words = model.wv.most_similar(
            positive=[word],
            topn=topn,
            restrict_vocab=None
        )
        return similar_words
    except KeyError:
        return f"词语 '{word}' 不在词汇表中"

def analyze_words(model, threshold=0.45):
    """构建情绪字典
    Args:
        model: 训练好的word2vec模型
        threshold: 相似度阈值，只保留相似度大于此值的词
    """
    emotion_dict = {}
    results = {}
    emotions = ['悲', '喜', '怒', '乐', '忧', '思']
    for emotion in emotions:
        similar = find_similar_words(model,emotion)
        if isinstance(similar, list):
            # 只显示相似度大于0.45的结果
            emotion_dict[emotion] = [w for w, s in similar if s > threshold]
            results[emotion] = [(w, s) for w, s in similar if s > threshold]

    return results, emotion_dict


def analyze_sentiment(emotion_dicts,poem_content):
    client = OpenAI(
        api_key="sk-8U3EuqHdqzCTqbuVuTNClwygtiXwgrHwtU6A1CgijYKH4ZCr",
        base_url="https://api.chatanywhere.tech/v1"
    )
    try:
        # 添加延时避免API限制
        time.sleep(1)
        # 获取训练数据
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一个诗词分析专家。请只返回以下情感之一：悲、惧、乐、怒、思、喜、忧"},
                {
                    "role": "user",
                    "content": f"这是一个情绪字典{emotion_dicts}。分析这首诗的主要情感，返回json格式 诗句:其对应一个字的情感类别（悲、惧、乐、怒、思、喜、忧）：\n\n{poem_content}"
                }
            ]
        )
        sentiment = completion.choices[0].message.content
        return sentiment
    except Exception as e:
        print(f"分析诗句时出错: {str(e)}")
        return None
def get_openai_response(input_path, output_path,model,max_num=100):
    emotion_dict = analyze_words(model, threshold=0.45)
    # 读取CSV文件
    df = pd.read_csv(input_path)
    # 只处理前10行
    df_sample = df.head(max_num).copy()
    sentiments = []
    for idx, row in df_sample.iterrows():
        print(f"正在分析第 {idx+1} 首诗...")
        sentiment = analyze_sentiment(emotion_dict)
        sentiments.append(sentiment)
        print(f"情感分析结果: {sentiment}")
    return sentiments

def clean_json_string(json_str):
    # 移除 ```json 和 ``` 标记
    json_str = re.sub(r'```json\n|\n```', '', json_str)
    return json_str

def process_sentiments(sentiments):

    all_verses = {}
    
    for sentiment_json in sentiments:
        # 清理JSON字符串
        clean_json = clean_json_string(sentiment_json)
        
        try:
            # 解析JSON字符串并直接更新到总字典中
            verse_sentiments = json.loads(clean_json)
            all_verses.update(verse_sentiments)
            
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {str(e)}")
    return all_verses
def save_to_json(all_verses, output_path):
    # 如果文件已存在，先读取现有内容
    existing_data = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            print(f"警告：现有文件 {output_path} 不是有效的JSON格式")
    existing_data.update(all_verses)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

def main():
    # 训练模型
    print("开始处理...")
    model = train_word2vec()
    print("模型处理完成！")
    
    # 构建情绪字典，设置相似度阈值为0.45
    # results, emotion_dict = analyze_words(model, threshold=0.45)
    # if results:
    #     for emotion, similar_words in results.items():
    #         print(f"\n与'{emotion}'相关的词 (相似度 > 0.45):")
    #         for word, score in similar_words:
    #             print(f"{word}: {score:.4f}")
    #save_to_json(process_sentiments(sentiments),'data/train.json')
    print(find_similar_words(model,'人'))
if __name__ == "__main__":
    main() 