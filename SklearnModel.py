import numpy as np
from sklearn.preprocessing import LabelEncoder
from gensim.models import Word2Vec
import json
from sklearn.neural_network import MLPClassifier  # 导入神经网络分类器
from sklearn.model_selection import train_test_split  # 导入训练集和测试集划分工具
import pickle  # 在文件开头添加

class EmotionAnalyzer:
    def __init__(self, vector_size=100):
        self.vector_size = vector_size
        self.model = None
        self.label_encoder = LabelEncoder()
        self.word2vec_model = None
        self.X = None
        self.y = None
        self.sklearn_model = None  # 用于存储神经网络模型
    
    def load_word2vec(self, model_path='models/word_vectors.model'):
        """加载Word2Vec模型"""
        self.word2vec_model = Word2Vec.load(model_path)
    
    def load_training_data(self, data_path='data/train.json'):
        """加载训练数据"""
        with open(data_path, 'r', encoding='utf-8') as f:
            self.train_data = json.load(f)
    
    def text_to_vec(self, text):
        """将文本转换为向量表示"""
        if self.word2vec_model is None:
            raise ValueError("Word2Vec model not loaded. Call load_word2vec first.")
            
        words = list(text)  # 将文本分成单个字
        vectors = []
        for word in words:
            if word in self.word2vec_model.wv:
                vectors.append(self.word2vec_model.wv[word])
        if vectors:
            return np.mean(vectors, axis=0)
        return np.zeros(self.vector_size)
    
    def prepare_data(self):
        """准备训练数据"""
        if self.word2vec_model is None:
            raise ValueError("Word2Vec model not loaded. Call load_word2vec first.")
        if not hasattr(self, 'train_data'):
            raise ValueError("Training data not loaded. Call load_training_data first.")
            
        X = []  # 特征向量
        y = []  # 标签
        
        for text, emotion in self.train_data.items():
            vec = self.text_to_vec(text)
            X.append(vec)
            y.append(emotion)
        
        self.X = np.array(X)
        self.y = np.array(y)
        return self.X, self.y
    
    def fit_sklearn(self):
        """使用神经网络模型进行训练"""
        if self.X is None or self.y is None:
            raise ValueError("Training data not prepared. Call prepare_data first.")
        
        # 编码标签
        y_encoded = self.label_encoder.fit_transform(self.y)
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(self.X, y_encoded, test_size=0.2, random_state=42)
        
        # 训练神经网络模型
        self.sklearn_model = MLPClassifier(
            hidden_layer_sizes=(100, 50),  # 两个隐藏层，分别有100和50个神经元
            activation='relu',              # ReLU激活函数
            max_iter=1000,                 # 最大迭代次数
            random_state=42
        )
        self.sklearn_model.fit(X_train, y_train)

    def predict_sklearn(self, text):
        """使用sklearn模型进行预测"""
        if self.sklearn_model is None:
            raise ValueError("Sklearn model not trained. Call fit_sklearn first.")
        
        vec = self.text_to_vec(text).reshape(1, -1)
        pred = self.sklearn_model.predict(vec)
        pred_proba = self.sklearn_model.predict_proba(vec)
        confidence = np.max(pred_proba)
        
        emotion = self.label_encoder.inverse_transform(pred)[0]
        
        return {
            'label': emotion,
            'score': confidence
        }

    def save(self, model_path='models/emotion_sklearn_model.pkl', encoder_path='models/label_sklean_encoder.pkl'):
        """保存sklearn模型和标签编码器"""
        if self.sklearn_model is None:
            raise ValueError("没有可保存的模型。请先训练模型。")
            
        # 保存sklearn模型
        with open(model_path, 'wb') as f:
            pickle.dump(self.sklearn_model, f)
            
        # 保存标签编码器
        with open(encoder_path, 'wb') as f:
            pickle.dump(self.label_encoder, f)
    
    def load(self, model_path='models/emotion_sklearn_model.pkl', 
            encoder_path='models/label_sklean_encoder.pkl',
            word2vec_path='models/word_vectors.model'):
        """加载预训练的sklearn模型、标签编码器和Word2Vec模型"""
        # 加载sklearn模型
        with open(model_path, 'rb') as f:
            self.sklearn_model = pickle.load(f)
        
        # 加载标签编码器
        with open(encoder_path, 'rb') as f:
            self.label_encoder = pickle.load(f)
            
        # 加载Word2Vec模型
        self.word2vec_model = Word2Vec.load(word2vec_path)

if __name__ == "__main__":
    # 使用示例：
    
    # 初始化分析器
    analyzer = EmotionAnalyzer()
    

    # 训练新模型
    analyzer.load_word2vec()
    analyzer.load_training_data()
    analyzer.prepare_data()
    analyzer.fit_sklearn()
    analyzer.save()  # 保存训练好的模型

    
    # 加载已训练的模型
    analyzer.load()
    
    # 预测
    text = "生计尚如蓬"
    sklearn_result = analyzer.predict_sklearn(text)
    
    print(f"Sklearn预测情感: 'sentiment': {sklearn_result['label']}, 'confidence': {sklearn_result['score']}") 