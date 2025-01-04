import time
from openai import OpenAI
import re
import json
import os
import pandas as pd

def analyze_type(contents):
    # 将内容列表转换为更简洁的格式
    simplified_contents = []
    for _, row in contents.iterrows():
        simplified_contents.append({
            "title": row['title'],
            "content": row['content']
        })
    # 初始化 OpenAI 客户端
    client = OpenAI(
        api_key="sk-5e329eb2ca954936bc587878b2bef459",
        base_url="https://api.deepseek.com/v1"
    )
    
    try:
        time.sleep(1)
        completion = client.chat.completions.create(
            model='deepseek-chat',
            messages=[
                {"role": "system", "content": "你是一个诗词分析专家。请按照固定格式返回诗词的体裁分析结果。"},
                {
                    "role": "user",
                    "content": f"""必须按照以下JSON格式返回：
[
    {{"诗词题目": "题目1", "体裁": "体裁1"}},
    {{"诗词题目": "题目2", "体裁": "体裁2"}}
]
这是诗文内容{simplified_contents}
"""
                }
            ]
        )
        content = completion.choices[0].message.content
        return content
        
    except Exception as e:
        print(f"分析诗句时出错: {str(e)}")
        return None
def update_df_with_types(content, batch_df):
    # 清理JSON字符串
    clean_json = re.sub(r'```json\n|\n```', '', content)
    
    try:
        # 解析JSON字符串为Python对象
        poems_info = json.loads(clean_json)
        print(poems_info)
        # 创建type列（如果不存在）
        if 'type' not in batch_df.columns:
            batch_df['type'] = '古诗'
            
        # 更新每首诗的体裁
        for poem in poems_info:
            title = poem['诗词题目']
            poem_type = poem['体裁']
            # 只在当前批次中查找并更新
            mask = batch_df['title'] == title
            if mask.any():
                batch_df.loc[mask, 'type'] = poem_type
            
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {str(e)}")
        print(f"问题JSON字符串: {clean_json}")
    except Exception as e:
        print(f"其他错误: {str(e)}")
    
    return batch_df

def batch_process_types(df, batch_size=5):
    """
    分批处理数据，每批处理batch_size条记录
    """
    processed_df = pd.DataFrame()
    total_batches = len(df) // batch_size + (1 if len(df) % batch_size != 0 else 0)
    
    for i in range(total_batches):
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, len(df))
        print(f"处理批次 {i+1}/{total_batches} (记录 {start_idx+1}-{end_idx})")
        
        # 获取当前批次的数据
        batch_df = df.iloc[start_idx:end_idx].copy()
        
        # 处理当前批次
        content = analyze_type(batch_df)
        if content:
            processed_batch = update_df_with_types(content, batch_df)
            processed_df = pd.concat([processed_df, processed_batch])
        else:
            print(f"批次 {i+1} 处理失败，跳过")
            
        print(f"完成批次 {i+1}")
    
    return processed_df
df = pd.read_csv('data/legal.csv',encoding='utf-8')
df = df.drop(df[df['title'] == '句'].index)
df_processed = batch_process_types(df, batch_size=10)
df_processed.to_csv('data/legal_processed.csv',index=False,encoding='utf-8')
