import re
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')

def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    words = text.split()
    filtered_words = [w for w in words if w not in stopwords.words("english")]
    return " ".join(filtered_words)