import numpy as np
from tensorflow.keras.models import Sequential, load_model, save_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder
from gensim.models import Word2Vec
import pickle
import json

class EmotionAnalyzer:
    def __init__(self, vector_size=100):
        self.vector_size = vector_size
        self.model = None
        self.label_encoder = LabelEncoder()
        self.word2vec_model = None
        self.X = None
        self.y = None
    
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
    
    def build_model(self, num_classes):
        """构建LSTM模型"""
        self.model = Sequential([
            LSTM(128, input_shape=(1, self.vector_size), return_sequences=True),
            Dropout(0.3),
            LSTM(64),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(num_classes, activation='softmax')
        ])
        
        self.model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
    
    def fit(self, epochs=10, batch_size=64, validation_split=0.2):
        """训练模型（仅在没有加载预训练模型时使用）"""
        if self.model is not None:
            print("模型已加载，无需训练。如需重新训练，请创建新的EmotionAnalyzer实例。")
            return None
            
        if self.X is None or self.y is None:
            raise ValueError("Training data not prepared. Call prepare_data first.")
            
        # 编码标签
        y_encoded = self.label_encoder.fit_transform(self.y)
        y_onehot = to_categorical(y_encoded)
        
        # 构建模型
        self.build_model(len(self.label_encoder.classes_))
        
        # 训练模型
        history = self.model.fit(
            self.X, y_onehot,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            shuffle=True
        )
        return history
    
    def predict(self, text):
        """预测文本情感"""
        if self.model is None:
            raise ValueError("Model not trained. Call fit first.")
            
        vec = self.text_to_vec(text)
        vec = vec.reshape(1, 1, self.vector_size)
        pred_probs = self.model.predict(vec)[0]  # 获取预测概率
        emotion = self.label_encoder.inverse_transform([np.argmax(pred_probs)])[0]
        confidence = float(np.max(pred_probs))  # 获取最高概率作为置信度
        
        return {
            'label': emotion,
            'score': confidence
        }
    
    def save(self, model_path='models/emotion_lstm_model.keras', encoder_path='models/label_encoder.pkl'):
        """保存模型和标签编码器"""
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")
            
        self.model.save(model_path)
        with open(encoder_path, 'wb') as f:
            pickle.dump(self.label_encoder, f)
    
    def load(self, model_path='models/emotion_lstm_model.keras', 
            encoder_path='models/label_encoder.pkl',
            word2vec_path='models/word_vectors.model'):
        """加载预训练模型、标签编码器和Word2Vec模型"""
        # 加载LSTM模型
        self.model = load_model(model_path)
        
        # 加载标签编码器
        with open(encoder_path, 'rb') as f:
            self.label_encoder = pickle.load(f)
            
        # 加载Word2Vec模型
        self.word2vec_model = Word2Vec.load(word2vec_path)

if __name__ == "__main__":
    # 使用示例：
    
    # 初始化分析器
    analyzer = EmotionAnalyzer()
    
    """
    # 加载数据和模型
    analyzer.load_word2vec()
    analyzer.load_training_data()

    # 准备数据
    analyzer.prepare_data()

    # 训练模型
    analyzer.fit()

    # 保存模型
    analyzer.save()
    """
    # 加载已训练的模型
    analyzer.load()

    # 预测
    text = "生计尚如蓬"
    result = analyzer.predict(text)
    print(f"预测情感:'sentiment': { result['label']},'confidence':{ result['score']}")
    
