import pandas as pd
from descriptive_analysis import Descriptive_analysis
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import seaborn as sns
import json

class TangPoetryVisual:
    def __init__(self):
        # 加载数据
        self.poetry_data = pd.read_csv('data/legal.csv', encoding='utf-8')
        self.poets_df = pd.read_csv('data/poets_df.csv', encoding='utf-8')
        self.char_freq = pd.read_csv('data/char_frequency.csv', encoding='utf-8')
        self.descriptive = Descriptive_analysis()
        
    def get_period_distribution(self):
        """各时期分布图"""
        period_stats = self.poets_df['period'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=period_stats.index,
            values=period_stats.values,
            textinfo='percent+label',
            hole=0.3,
            marker=dict(
                colors=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99'],
                line=dict(color='white', width=2)
            )
        )])
        
        fig.update_layout(
            title=dict(
                text='唐诗各时期分布',
                font=dict(size=18),
                x=0.5,
                y=1,
                pad=dict(t=1)
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=20, r=20, t=80, b=60),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
        
        return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
        
    def get_poetry_types(self, threshold=0.01):
        """诗歌体裁分布图"""
        type_stats = self.poetry_data['type'].value_counts()
        total_poems = len(self.poetry_data)
        type_percentages = type_stats / total_poems
        
        major_types = type_percentages[type_percentages >= threshold]
        minor_types = type_percentages[type_percentages < threshold]
        
        if not minor_types.empty:
            labels = major_types.index.tolist() + ['其他']
            values = major_types.values.tolist() + [minor_types.sum()]
        else:
            labels = major_types.index.tolist()
            values = major_types.values.tolist()
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            textinfo='percent+label',
            hole=0.3
        )])
        
        fig.update_layout(
            title='唐诗体裁分布',
            title_font_size=16,
            margin=dict(l=50, r=50, t=50, b=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
        
    def get_top_poets(self, top_n=20):
        """诗人排名"""
        # 获取并排序数据（降序）
        poet_counts = self.poetry_data['poets'].value_counts().head(top_n)
        
        # 创建横向柱状图
        fig = go.Figure(data=[go.Bar(
            x=poet_counts.values[::-1],  # 反转数据以便从上到下显示
            y=poet_counts.index[::-1],   # 反转索引以便从上到下显示
            text=poet_counts.values[::-1],
            textposition='auto',
            orientation='h',  # 横向显示
            marker_color='#66B2FF'  # 添加统一的颜色
        )])
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=f'作品数量最多的{top_n}位诗人',
                font=dict(size=18),
                x=0.5,
                y=0.95
            ),
            xaxis_title='作品数量',
            yaxis_title='诗人',
            margin=dict(l=150, r=50, t=60, b=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=800,  # 增加高度
            xaxis=dict(showgrid=False),
            yaxis=dict(
                tickfont=dict(size=12),  # 调整y轴字体大小
                automargin=True,  # 自动调整边距以适应标签
                showgrid=False
            ),
            bargap=0.2  # 调整条形图间距
        )
        
        # 返回 JSON 格式的图表数据
        return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
        
    def get_poetry_length_distribution(self):
        """诗歌长度分布图"""
        # 计算每首诗的字数
        poetry_lengths = self.poetry_data['content'].str.len()
        
        # 设置长度区间
        bins = [0, 20, 40, 60, 80, 100, 150, 200, 300, float('inf')]
        labels = ['1-20字', '21-40字', '41-60字', '61-80字', '81-100字', 
                '101-150字', '151-200字', '201-300字', '300字以上']
        
        # 统计各区间的诗歌数量
        length_dist = pd.cut(poetry_lengths, bins=bins, labels=labels).value_counts().sort_index()
        
        # 创建柱状图
        fig = go.Figure(data=[go.Bar(
            x=length_dist.index,
            y=length_dist.values,
            text=length_dist.values,
            textposition='auto',
        )])
        
        # 更新布局
        fig.update_layout(
            title='唐诗长度分布',
            title_font_size=16,
            xaxis_title='字数区间',
            yaxis_title='诗歌数量',
            margin=dict(l=50, r=50, t=50, b=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
        
        return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    def get_poets_by_period(self):
        """各时期诗人数量图"""
        period_counts = self.poets_df['period'].value_counts()
        
        # 创建柱状图
        fig = go.Figure(data=[go.Bar(
            x=period_counts.index,
            y=period_counts.values,
            text=period_counts.values,
            textposition='auto',
            marker_color=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99']  # 添加统一的颜色方案
        )])
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text='各时期诗人数量分布',
                font=dict(size=18),
                x=0.5,
                y=0.95
            ),
            xaxis_title='时期',
            yaxis_title='诗人数量',
            margin=dict(l=50, r=50, t=60, b=60),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
        
        # 返回 JSON 格式的图表数据
        return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    
    def get_char_frequency(self, top_n=20):
        """字频统计图"""
        top_chars = self.char_freq.head(top_n)
        
        fig = go.Figure(data=[go.Bar(
            x=top_chars['char'],
            y=top_chars['frequency'],
            text=top_chars['frequency'],
            textposition='auto',
        )])
        
        fig.update_layout(
            title='唐诗字频统计（Top {}）'.format(top_n),
            title_font_size=16,
            xaxis_title='字符',
            yaxis_title='出现频率',
            margin=dict(l=50, r=50, t=50, b=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
        
        return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    
    def plot_period_distribution(self):
        """绘制唐诗各时期分布"""
        period_stats = self.poets_df['period'].value_counts()
        
        # 创建图表
        fig = go.Figure(data=[go.Pie(
            labels=period_stats.index,
            values=period_stats.values,
            textinfo='percent+label',
            insidetextorientation='radial',
            marker=dict(colors=sns.color_palette("pastel")),
        )])
        
        # 更新布局
        fig.update_layout(
            title='唐诗各时期分布',
            title_font_size=16,
            margin=dict(l=0, r=0, t=40, b=0)  # 调整边距
        )
        
        fig.show()  # 显示图表

    def get_seasons_chart(self):
        """四季词频分布图"""
        seasons_data = self.descriptive.analyze_four_seasons()
        
        # 设置季节对应的颜色
        season_colors = {
            '春': '#99FF99',  # 浅绿色
            '夏': '#FF9999',  # 浅红色
            '秋': '#FFCC99',  # 浅橙色
            '冬': '#66B2FF'   # 浅蓝色
        }
        
        # 根据季节设置颜色
        colors = [season_colors[season] for season in seasons_data['season']]
        
        fig = go.Figure(data=[go.Bar(
            x=seasons_data['season'],
            y=seasons_data['frequency'],
            text=seasons_data['frequency'],
            textposition='auto',
            marker_color=colors
        )])
        
        fig.update_layout(
            title=dict(
                text='唐诗四季词频分布',
                font=dict(size=18),
                x=0.5,
                y=0.95
            ),
            xaxis_title='季节',
            yaxis_title='出现频率',
            margin=dict(l=50, r=50, t=60, b=60),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            showlegend=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
        
        return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    def get_colors_chart(self):
        """颜色词频分布图"""
        _, color_summary = self.descriptive.analyze_color_frequency()
        
        fig = go.Figure(data=[go.Bar(
            x=color_summary['color_group'],
            y=color_summary['total_frequency'],
            text=color_summary['total_frequency'],
            textposition='auto',
            marker_color=['#FFFFFF', '#99FF99', '#CCCCCC', '#FF9999', '#FFCC99', '#333333', '#66B2FF']
        )])
        
        fig.update_layout(
            title=dict(
                text='唐诗颜色词系统分布',
                font=dict(size=18),
                x=0.5,
                y=0.95
            ),
            xaxis_title='颜色系',
            yaxis_title='出现频率',
            margin=dict(l=50, r=50, t=60, b=60),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
        
        return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    def get_all_charts(self):
        """获取所有图表数据"""
        return {
            'period_chart': self.get_period_distribution(),
            'type_chart': self.get_poetry_types(),
            'top_poets_chart': self.get_top_poets(),
            'length_chart': self.get_poetry_length_distribution(),
            'poets_period_chart': self.get_poets_by_period(),
            'char_freq_chart': self.get_char_frequency(),
            'seasons_chart': self.get_seasons_chart(),
            'colors_chart': self.get_colors_chart()
        }


