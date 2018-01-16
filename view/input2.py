from flask import Flask, render_template, request, session
# from flask.ext.session import Session
from flask_pymongo import PyMongo
from pymongo import MongoClient
import urllib.request
import json
from bs4 import BeautifulSoup
from bson import ObjectId
from bson.son import SON

from selenium import webdriver
import time

app = Flask(__name__)
mongo = PyMongo(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/post', methods=['POST'])
def post_request():
    import os, csv, re
    os.chdir("/Users/Atsushi/Downloads")

# 第１段階　トレインデータ
    input_file = "train_hpb.csv"
    f = open(input_file, "r", encoding="cp932")
    csv_data = csv.reader(f)
    data = [row for row in csv_data]
    data_str=str(data)
    data_str2=data_str.replace("[","")
    data_str3=data_str2.replace("]","")
    data_list=data_str3.split(",")
# 第１段階　トレインラベル
    input_label = "hpb_冒頭文_不保証_管轄.csv"
    h = open(input_label,'r', encoding="cp932")
    raw=h.read()
    import nltk
    tokens = nltk.word_tokenize(raw)
# 第１段階　テストデータ
    url = request.form["url"]
    # with urllib.request.urlopen(url) as response:
    #     html = response.read()
    # soup = BeautifulSoup(html, "html.parser")
    driver = webdriver.PhantomJS()
    driver.get(url)
    # time.sleep(3)
    # print(driver.find_element_by_id("content").text)
    pageSource = driver.page_source
    soup=BeautifulSoup(pageSource, "html.parser")
    # print(soup.find().get_text())
    # driver.save_screenshot("ss.png")
    driver.close()
    # img_urls = [img.get("src") for img in soup.select("#unique-pickup img")]
    # print(img_urls)

    soup = str(soup)
    # soup = re.sub('<a href[^>]*>','(link)',soup)
    soup = re.sub('<a href=','link',soup)
    soup = re.sub('https://','rarara',soup)
    soup = re.sub('</a>','toji',soup)
    # soup = re.sub('<[^>]*>','/',soup)
    soup = re.sub('<[^>]*>','@',soup)
    # soup = re.sub('<[^>^a href=".*"^/a]*>','/',soup)
    # <a href="https://fb.omiai-jp.com/japan/site/paidservice/">こちら</a>
    soup = re.sub('link','<a href=',soup)
    soup = re.sub('\\n','',soup)
    # soup = re.sub('\.','',soup)
    # 英語の「,」をエスケープ
    soup = re.sub(',','ー',soup)
    # soup_tokens = soup.split("/")
    soup_tokens = soup.split("@")
    # print(soup_tokens)
    sentence_tokens=[w for w in soup_tokens if re.search('a href=.*rarara|。|条|行為|内容|場合|活動|^[ぁ-ん]+こと|[^a-zA-Z]\([0-9]+\)|^[0-9]+.*[ぁ-んァ-ン-龥]$|[0-9]+[ぁ-んァ-ン龥]+|歳|年|月|日|toji', w)]
    # sentence_tokens=[w for w in soup_tokens if re.search('。|条|行為|内容|場合|活動|こと', w)]
    # 洗練されたsentence_tokensをcollection4へ格納する場合
    aaa_str= str(sentence_tokens)
    aaa_str = re.sub('rarara','https://',aaa_str)
    aaa_str = re.sub('toji','</a>',aaa_str)
    aaa_str = re.sub('[^\(^\)^\（^\）^\,^ぁ-ん^ァ-ン^一^-龥^a-zA-Z^0-9^０^１^２^３^４^５^６^７^８^９^0-9^</a>^<^>^=^\:^\.^\/^\-^ ]*','',aaa_str)
    # aaa_str= re.sub('^ぁ-ん^ァ-ン^一^-龥^a-z^A-Z^0-9^０^１^２^３^４^５^６^７^８^９^<^>^=^\:^</a>','',aaa_str)
    aaa_str= re.sub('u3000','　',aaa_str)
    aaa_str_tokens = aaa_str.split(",")
    # print(aaa_str_tokens)

    # testdata4 = cv.transform(aaa_str_tokens)

    data1 = {
    "sentences":[{"id":[],"labels":[],"sentence":[]}]
    }

    for i in range(len(aaa_str_tokens)):
       data1["sentences"].append({
                       "id":[i],
                       "labels":"ccc",
                       "sentence":aaa_str_tokens[i]
      })

    client = MongoClient("mongodb://zakishima:cUwtgzOWiY7D4Sn8FYi12aE1itKZRhg8pzRDGc5h1F36i6xyahyzjsCIpAbnhUEQNeejWNWlsAVPvjEYoHjlyQ==@zakishima.documents.azure.com:10255/?ssl=true&replicaSet=globaldb")
    db = client.testdb
    co2 = db.collection4
    co2.insert_one(data1)

    import MeCab
    from sklearn.feature_extraction.text import CountVectorizer
    class WordDividor:
         INDEX_CATEGORY = 0
         INDEX_ROOT_FORM = 6
         TARGET_CATEGORIES = ["名詞", " 動詞",  "形容詞", "副詞", "連体詞", "感動詞"]
         def __init__(self, dictionary="mecabrc"):
                 self.dictionary = dictionary
                 self.tagger = MeCab.Tagger(self.dictionary)
         def extract_words(self, text):
                 if not text:
                         return []
                 words = []
                 node = self.tagger.parseToNode(text)
                 while node:
                         features = node.feature.split(',')
                         if features[self.INDEX_CATEGORY] in self.TARGET_CATEGORIES:
                                 if features[self.INDEX_ROOT_FORM] == "*":
                                         words.append(node.surface)
                                 else:
                                         words.append(features[self.INDEX_ROOT_FORM])
                         node = node.next
                 return words

    if __name__ == '__main__':
         wd = WordDividor()
         cv = CountVectorizer(analyzer = wd.extract_words)

         # 非重要クラスーーーーーー
         bag_of_text = cv.fit_transform(data_list)
         # print(cv.vocabulary_)
         # print(bag_of_text)
         feature_names = cv.get_feature_names()
         # print("Number of features: {}".format(len(feature_names)))
         # print("First 20 features:\n{}".format(feature_names[:20]))
         from sklearn import svm
         from sklearn.svm import SVC
         # C=1だとbbb判定が少なすぎ、100だと多すぎる。
         clf=svm.SVC(C=10)
         clf.fit(bag_of_text,tokens)

         # print(clf.score(bag_of_text,tokens))
         testdata = cv.transform(sentence_tokens)
         # print(cv.vocabulary_)
         # print(X_test)
         feature_names = cv.get_feature_names()
         # print("Number of features: {}".format(len(feature_names)))
         # print("First 20 features:\n{}".format(feature_names[:20]))
         prediction = clf.predict(testdata)
         # numpy.ndarrayをlistへ
         prediction_list = prediction.tolist()

# 第１段階　Prediction結果の格納
# １　CSVへ格納する場合
# （１）　CSVへaaaもbbbも格納する場合
# （２）　CSVへaaaのみ格納する場合
         output_file = "predicted_aaa.csv"

         j = open(output_file, 'w', encoding="cp932")
         writer = csv.writer(j, delimiter='\n')
         two_list=[[]]
         # one_list=[]
         for i in range(len(sentence_tokens)):
             if prediction_list[i] == "aaa":
                 two_list[0].append([sentence_tokens[i], prediction_list[i]])
         writer.writerows(two_list)
         j.close()


# 第２段階　ラベルデータ
         input_label2 = "hpb_責任.csv"

         h2 = open(input_label2,'r',encoding="cp932")
         raw2 = h2.read()
         tokens2 = nltk.word_tokenize(raw2)

# 第２段階　トレインデータ（train_hpb.csvのbag_of_textを使う。
         clf==svm.SVC(C=10)
         clf.fit(bag_of_text,tokens2)

# 第２段階　テストデータ（aaaテストデータ）
         aaa_list=[]
         with open(output_file, "r", encoding="cp932") as f:
             csv_data = csv.reader(f)
             for row in csv_data:
                 aaa_list = list(row[0] for row in csv_data)
         testdata2 = cv.transform(aaa_list)

# 第２段階　Prediction
         prediction2 = clf.predict(testdata2)
         prediction_list2 = prediction2.tolist()

# 第２段階　Prediction結果の格納
#１　CSVへ格納する場合
#（１）　CSVへaaaもbbbも格納する場合
#（２）　CSVへaaaのみ格納する場合
         output_file2 = "predicted_aaa2.csv"

         # j2 = open(output_file2, 'w', encoding="shift_jis")
         j2 = open(output_file2, 'w', encoding="cp932")

         writer = csv.writer(j2, delimiter='\n')
         two_list2=[[]]
         for i in range(len(aaa_list)):
             if prediction_list2[i] == "aaa":
                 two_list2[0].append([aaa_list[i], prediction_list2[i]])
         writer.writerows(two_list2)
         j2.close()

# 第３段階　ラベルデータ
         input_label3 = "hpb_禁止事項_権利譲渡.csv"
         # h3 = open(input_label3,'r',encoding="shift_jis")
         h3 = open(input_label3,'r',encoding="cp932")
         raw3 = h3.read()
         tokens3 = nltk.word_tokenize(raw3)

# 第３段階　トレインデータ（train_hpb.csvのbag_of_textを使う。
         clf.fit(bag_of_text,tokens3)

# 第３段階　テストデータ（aaaテストデータ）
         aaa_list2=[]
         with open(output_file2, "r", encoding="cp932") as f:
             csv_data = csv.reader(f)
             for row in csv_data:
                 aaa_list2 = list(row[0] for row in csv_data)
         testdata3 = cv.transform(aaa_list2)

# 第３段階　Prediction
         prediction3 = clf.predict(testdata3)
         prediction_list3 = prediction3.tolist()
         # print(prediction_list3)

# 第３段階　Prediction結果の格納
#１　CSVへ格納する場合
#（１）　CSVへaaaもbbbも格納する場合
#（２）　CSVへaaaのみ格納する場合
         output_file3 = "predicted_aaa3.csv"
         # j3 = open(output_file3, 'w', encoding="shift_jis")
         j3 = open(output_file3, 'w', encoding="cp932")
         writer = csv.writer(j3, delimiter='\n')
         two_list3=[[]]
         for i in range(len(aaa_list2)):
             if prediction_list3[i] == "aaa":
                 two_list3[0].append([aaa_list2[i], prediction_list3[i]])
         writer.writerows(two_list3)
         j3.close()

# 第４段階　ラベルデータ
         input_label4 = "omiai_禁止事項.csv"
         # h4 = open(input_label4,'r',encoding="shift_jis")
         h4 = open(input_label4,'r',encoding="cp932")
         raw4 = h4.read()
         tokens4 = nltk.word_tokenize(raw4)

# 第４段階　トレインデータ
         input_file2 = "train_omiai.csv"
         f2 = open(input_file2, "r", encoding="cp932")
         csv_data2 = csv.reader(f2)
         data2 = [row for row in csv_data2]
         data2_str=str(data2)
         data2_str2=data2_str.replace("[","")
         data2_str3=data2_str2.replace("]","")
         data2_list=data2_str3.split(",")
         bag_of_text2 = cv.fit_transform(data2_list)
         # feature_names = cv.get_feature_names()
         clf=svm.SVC(C=10)
         clf.fit(bag_of_text2,tokens4)

# 第４段階　テストデータ（aaaテストデータ）
         aaa_list3=[]
         with open(output_file3, "r", encoding="cp932") as f:
             csv_data = csv.reader(f)
             for row in csv_data:
                 aaa_list3 = list(row[0] for row in csv_data)
         testdata4 = cv.transform(aaa_list3)

# 第４段階　Prediction
         prediction4 = clf.predict(testdata4)
         prediction_list4 = prediction4.tolist()
         # print(prediction_list4)

# 第４段階　Prediction結果の格納
#１　CSVへ格納する場合
#（１）　CSVへaaaもbbbも格納する場合
#（２）　CSVへaaaのみ格納する場合
         output_file4 = "predicted_aaa4.csv"
         # j4 = open(output_file4, 'w', encoding="shift_jis")
         j4 = open(output_file4, 'w', encoding="cp932")
         writer = csv.writer(j4, delimiter='\n')
         two_list4=[[]]
         for i in range(len(aaa_list3)):
             if prediction_list4[i] == "aaa":
                 two_list4[0].append([aaa_list3[i], prediction_list4[i]])
         writer.writerows(two_list4)
         j4.close()

# 第５段階　ラベルデータ
         input_label5 = "omiai_不保証_問合せ.csv"
         # h4 = open(input_label4,'r',encoding="shift_jis")
         h5 = open(input_label5,'r',encoding="cp932")
         raw5 = h5.read()
         tokens5 = nltk.word_tokenize(raw5)

# 第５段階　トレインデータ
         clf.fit(bag_of_text2,tokens5)

# 第５段階　テストデータ（aaaテストデータ）
         aaa_list4=[]
         with open(output_file4, "r", encoding="cp932") as f:
             csv_data = csv.reader(f)
             for row in csv_data:
                 aaa_list4 = list(row[0] for row in csv_data)
         testdata5 = cv.transform(aaa_list4)

# 第５段階　Prediction
         prediction5 = clf.predict(testdata5)
         prediction_list5 = prediction5.tolist()

# 第５段階　Prediction結果の格納
#１　CSVへ格納する場合
#（１）　CSVへaaaもbbbも格納する場合
#（２）　CSVへaaaのみ格納する場合
         output_file5 = "predicted_aaa5.csv"
         # j4 = open(output_file4, 'w', encoding="shift_jis")
         j5 = open(output_file5, 'w', encoding="cp932")
         writer = csv.writer(j5, delimiter='\n')
         two_list5=[[]]
         for i in range(len(aaa_list4)):
             if prediction_list5[i] == "aaa":
                 two_list5[0].append([aaa_list4[i], prediction_list5[i]])
         writer.writerows(two_list5)
         j5.close()

# 第６段階　ラベルデータ
         input_label6 = "line_同意_変更_アカウント_接続.csv"
         # h4 = open(input_label4,'r',encoding="shift_jis")
         h6 = open(input_label6,'r',encoding="cp932")
         raw6 = h6.read()
         tokens6 = nltk.word_tokenize(raw6)

# 第６段階　トレインデータ
         input_file3 = "train_line.csv"
         f3 = open(input_file3, "r", encoding="cp932")
         csv_data3 = csv.reader(f3)
         data3 = [row for row in csv_data3]
         data3_str=str(data3)
         data3_str2=data3_str.replace("[","")
         data3_str3=data3_str2.replace("]","")
         data3_list=data3_str3.split(",")
         bag_of_text3 = cv.fit_transform(data3_list)
         # feature_names = cv.get_feature_names()
         clf=svm.SVC(C=10)
         clf.fit(bag_of_text3,tokens6)

# 第６段階　テストデータ（aaaテストデータ）
         aaa_list5=[]
         with open(output_file5, "r", encoding="cp932") as f:
             csv_data = csv.reader(f)
             for row in csv_data:
                 aaa_list5 = list(row[0] for row in csv_data)
         # testdata4 = cv.transform(aaa_list3)

         # aaa_listをDB格納用に洗練する。最終段階でのみ記入。
         aaa_str5= str(aaa_list5)
         # aaa_str5= re.sub('[^\（^\）^\(^\)^\\,^ぁ-ん^ァ-ン^一^-龥^a-z^A-Z^0-9^０^１^２^３^４^５^６^７^８^９^<^>^=^\:^</a>^\"^\'^ ]*^\^-.','',aaa_str5)
         aaa_str5= re.sub('[^\(^\)^\（^\）^\,^ぁ-ん^ァ-ン^一^-龥^a-zA-Z^0-9^０^１^２^３^４^５^６^７^８^９^0-9^</a>^<^>^=^\:^\.^\/^\-^ ]*','',aaa_str5)
         # aaa_str= re.sub('[^\,^ぁ-ん^ァ-ン^一^-龥^a-zA-Z^\(^\)^0-9^</a>^<^>^=^\:]*','',aaa_str)
         aaa_str5= re.sub('u3000',' ',aaa_str5)

         # "sentences_and_label":[{"文":"ラベル"}]のときだけ以下必要
         # aaa_str = re.sub('\.','',aaa_str)
         # /でsplitするのが一番キレイ（\u3000はhtmlに表示した際には空白に変換される）
         aaa_str_tokens5 = aaa_str5.split(",")
         aaa_str_tokens6= [w for w in aaa_str_tokens5 if re.search('[ぁ-んァ-ン一-龥]', w)]
         testdata6 = cv.transform(aaa_str_tokens6)

# 第６段階　Prediction
         prediction6 = clf.predict(testdata6)
         prediction_list6 = prediction6.tolist()

# 第６段階　Prediction結果の格納
#１　CSVへ格納する場合
#（１）　CSVへaaaもbbbも格納する場合
#（２）　CSVへaaaのみ格納する場合
#（３）　DBへ格納する場合
         data2 = {
         "labels_and_sentences":[{"id":[],"labels":[],"sentences":[]}]
         }

         for i in range(len(aaa_str_tokens6)):
               data2["labels_and_sentences"].append({
                                   "id":[i],
                                   "labels":prediction_list6[i],
                                   "sentences":aaa_str_tokens6[i]
              })

         client = MongoClient("mongodb://zakishima:cUwtgzOWiY7D4Sn8FYi12aE1itKZRhg8pzRDGc5h1F36i6xyahyzjsCIpAbnhUEQNeejWNWlsAVPvjEYoHjlyQ==@zakishima.documents.azure.com:10255/?ssl=true&replicaSet=globaldb")
         db = client.testdb
         co = db.collection3
         co.insert_one(data2)




# 重要クラス(neo)ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
# 第１段階　トレインデータ
         input_file = "train_omiai.csv"
         f = open(input_file, "r", encoding="cp932")
         csv_data = csv.reader(f)
         data = [row for row in csv_data]
         data_str=str(data)
         data_str2=data_str.replace("[","")
         data_str3=data_str2.replace("]","")
         data_list=data_str3.split(",")
         # print(data_list)
# 第１段階　トレインラベル
         input_label_neo = "omiai_料金.csv"
         k = open(input_label_neo,'r', encoding="cp932")
         raw_neo=k.read()
         import nltk
         tokens_neo = nltk.word_tokenize(raw_neo)

         bag_of_text_neo = cv.fit_transform(data_list)
         feature_names = cv.get_feature_names()
         from sklearn import svm
         from sklearn.svm import SVC
         clf=svm.SVC(C=100)
         clf.fit(bag_of_text_neo,tokens_neo)

# テストデータ
         testdata_neo = cv.transform(sentence_tokens)
         feature_names = cv.get_feature_names()
         prediction_neo = clf.predict(testdata_neo)
         prediction_list_neo = prediction_neo.tolist()
         # print(len(prediction_list_neo))
         # print(len(sentence_tokens))
         # 163

# 第１段階　Prediction結果の格納
# （２）　CSVへaaaのみ格納する場合
         # output_file_neo = "predicted_neo.csv"
         # j_neo = open(output_file_neo, 'w', encoding="cp932")
         # writer = csv.writer(j_neo, delimiter='\n')
         # two_list_neo=[[]]
         # # one_list=[]
         # for i in range(len(sentence_tokens)):
         #     if prediction_list_neo[i] == "aaa":
         #         two_list_neo[0].append([sentence_tokens[i], prediction_list_neo[i]])
         # writer.writerows(two_list_neo)
         # j_neo.close()
#（３）　DBへ格納する場合
         data3 = {
         "labels_and_sentences":[{"id":[],"labels":[],"sentences":[]}]
         }

         for i in range(len(sentence_tokens)):
               data3["labels_and_sentences"].append({
                                   "id":[i],
                                   "labels":prediction_list_neo[i],
                                   "sentences":sentence_tokens[i]
              })

         client = MongoClient("mongodb://zakishima:cUwtgzOWiY7D4Sn8FYi12aE1itKZRhg8pzRDGc5h1F36i6xyahyzjsCIpAbnhUEQNeejWNWlsAVPvjEYoHjlyQ==@zakishima.documents.azure.com:10255/?ssl=true&replicaSet=globaldb")
         db = client.testdb
         co3 = db.collection5
         co3.insert_one(data3)
# ーーーーーーーーーーーーーーーーーーーーー

if __name__ == "__main__":
    app.run()
