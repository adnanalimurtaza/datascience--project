#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import nltk
import os
import pandas as pd
import string
from PIL import Image

# nltk.download('corpora') # Uncomment this if corpora/stopwords is not found in nltk resources
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud

def make_passage(reviews):
    passage = ""
    for review in reviews:
        passage = passage + review + "\n"
    return passage

def make_corpus(reviews):
    corpus = []
    for review in reviews:
        passage = make_passage(review)
        corpus.append(passage)
    return corpus

def top_tfidf_features(row, features, top_n=25):
    ''' Get top n tfidf values in row and return them with their corresponding feature names.'''
    topn_ids = np.argsort(row)[::-1][:top_n]
    top_feats = [(features[i], row[i]) for i in topn_ids]
    df = pd.DataFrame(top_feats)
    df.columns = ['feature', 'tfidf']
    return df


def top_features_in_doc(tfidf_matrix, features, rows, top_n=25):
    ''' Top tfidf features in specific document (matrix row) '''
    for row_id in range(0,rows):
        row = np.squeeze(tfidf_matrix[row_id].toarray())
        if (row_id == 0):
            df_pos  = top_tfidf_features(row, features, top_n)
        else:
            df_neg  = top_tfidf_features(row, features, top_n)
    return df_pos, df_neg

def hotels_within_clusters(cluster_hotels):
    cluster1 = cluster2 = cluster3 = cluster4 = cluster5 = cluster6 = cluster7 = cluster8 = []
    for k, v in cluster_hotels.items():
        print(v)
        if(v == "Cluster 0"):
            cluster1.append(k)
        elif (v == "Cluster 1"):
            cluster2.append(k)
        elif (v == "Cluster 2"):
            cluster3.append(k)
        elif (v == "Cluster 3"):
            cluster4.append(k)
        elif (v == "Cluster 4"):
            cluster5.append(k)
        elif (v == "Cluster 5"):
            cluster6.append(k)
        elif (v == "Cluster 6"):
            cluster7.append(k)
        elif (v == "Cluster 7"):
            cluster8.append(k)

def save_wordcloud_hotels_with_clusters():
    # Read Cluster Model
    with open(base_path + "/models/hotels_clusters.txt") as f:
        hotels_within_clusters = f.read() # whole txt file
    hotels_within_clusters = hotels_within_clusters[:-3]
    hotels_within_clusters = hotels_within_clusters.split(",")
    
    count = 1
    for hotels_names in hotels_within_clusters:
        hotels_names = hotels_names.replace(' ', "")
        hotels_names = hotels_names.replace(':', " ")
        # Generate a word cloud image
        one_mask = np.array(Image.open(base_path + "/mask_images/"+str(count)+".png"))
        
        wordcloud1 = WordCloud(background_color="white", mask=one_mask).generate(clusters[count-1])
        wordcloud2 = WordCloud(background_color="white").generate(hotels_names)
        fig = plt.figure()
        fig.add_subplot(1, 2, 1)
        plt.imshow(wordcloud1, interpolation="bilinear")
        plt.axis("off")
        plt.title("Indicative words in cluster " + str(count), fontSize=18)
        fig.add_subplot(1, 2, 2)
        plt.imshow(wordcloud2, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout()
        plt.title("Hotels within cluster", fontSize=18)
        fig.savefig(base_path + '/wordcloud/cluster_'+str(count)+".png")
        count = count + 1

base_path =  os.path.dirname(os.path.abspath('__file__'))   

### ------------------------- Load files
hotels_data = pd.read_csv(base_path + "/datasets/Finland_Hotels_Reviews.csv")
hotels_data = hotels_data[hotels_data['review_title'].notnull()]
data = hotels_data

### ------------------------- Preprocessing on textual data (review_title, reviews and tags)

# Removing all digits, stopwords as well as punctuation
stop = stopwords.words('english') + list(string.punctuation)

hotels_data['review_title'] = hotels_data['review_title'].astype(str).str.replace('\d+', '')
hotels_data['review'] = hotels_data['review'].astype(str).str.replace('\d+', '')
hotels_data['tags'] = hotels_data['tags'].astype(str).str.replace(':', ' ')
hotels_data['tags'] = hotels_data['tags'].astype(str).str.replace('\d+', '')

hotels_data['review_title'] = hotels_data['review_title'].apply(lambda words:' '.join([word for word in words.split() if word not in (stop)]))
hotels_data['review'] = hotels_data['review'].apply(lambda words:' '.join([word for word in words.split() if word not in (stop)]))
hotels_data['tags'] = hotels_data['tags'].apply(lambda words:' '.join([word for word in words.split() if word not in (stop)]))

# Applying stemming
stemmer = nltk.stem.SnowballStemmer('english')
hotels_data['review_title'] = hotels_data['review_title'].apply(lambda words: ' '.join([stemmer.stem(word) for word in words.split()]))
hotels_data['review'] = hotels_data['review'].apply(lambda words: ' '.join([stemmer.stem(word) for word in words.split()]))
hotels_data['tags'] = hotels_data['tags'].apply(lambda words: ' '.join([stemmer.stem(word) for word in words.split()]))

###-------------------------- Read Cluster Model
with open(base_path + "/models/cluster_model.txt") as f:
    cluster_model = f.read() # whole txt file

# Remove ',\n' from end
cluster_model = cluster_model[:-3]
clusters = cluster_model.split(',')
n_clusters = len(clusters)

### ------------------------- Cluster Hotels
hotels = hotels_data['name'].unique()
print(hotels)
n = 50
cluster_hotels = {}
for hotel_name in hotels:  
    cluster_scores = {}      
    # Find Indicative words(bad and good) using review_title, review for each hotel
    hotel = hotels_data[hotels_data['name'] == hotel_name]
    hotel["combine_reviews"] = hotel['review_title'].map(str) +" "+ hotel['review'].map(str)
    pos_review = hotel[hotel['rating'] > 3]
    neg_review = hotel[hotel['rating'] < 3.5]
    
    # Make Corpus
    reviews = [pos_review['combine_reviews'], neg_review['combine_reviews']]
    corpus = make_corpus(reviews)
    
    # Create TF_IDF Matrix 2 x uniques_features
    tf = TfidfVectorizer(analyzer='word', min_df = 0, stop_words = 'english')
    print(hotel_name)
    tfidf_matrix =  tf.fit_transform(corpus)
    feature_names = tf.get_feature_names()
    rows, columns = tfidf_matrix.shape
    
    # Calculate top n tf-idf scores w.r.t features 
    if (len(feature_names) < n ):
        n = feature_names
    df_pos, df_neg = top_features_in_doc(tfidf_matrix, feature_names, rows, n)
    df_pos['name'] = hotel_name
    df_neg['name'] = hotel_name
    df_pos.label = 'postive'
    df_neg.label = 'negative'

    # Extract pos words, match them with cluster models
    pos_words = df_pos['feature'].values
    for count in range(0,n_clusters):
        cluster_words = clusters[count].split(' ')
        score = 0
        for word in pos_words:
            for cluster_word in cluster_words:
                if (word == cluster_word):
                    score = score + 1
        cluster_scores["Cluster " + str(count)] = score
        
    # Find max score and cluster hotel  
    max_key = max(cluster_scores, key=cluster_scores.get)    
    cluster_hotels[hotel_name] = max_key          
    
#print(cluster_hotels)
hotels_within_clusters(cluster_hotels)
save_wordcloud_hotels_with_clusters()