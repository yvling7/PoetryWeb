import multiprocessing
from gensim.models import KeyedVectors
import pandas as pd
import os
import re
import time
import json
word2vec_model = KeyedVectors.load("/home/xiaomi1/PoetryWeb/models/word_vectors.model", mmap='r')

def find_similar_words(word, model=word2vec_model, topn=20):
    try:
        # 查找相似词
        similar_words = model.most_similar(
            positive=[word],
            topn=topn,
            restrict_vocab=None
        )
        return similar_words
    except KeyError:
        return f"词语 '{word}' 不在词汇表中"

