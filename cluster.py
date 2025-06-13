from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

def cluster_other_comments(comments, num_clusters=3):
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(comments)
    kmeans = KMeans(n_clusters=num_clusters)
    labels = kmeans.fit_predict(X)
    return labels