
from flask import Flask, render_template, request, session
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

if __name__ == "__main__":
    app.run()
