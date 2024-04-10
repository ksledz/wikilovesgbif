from flask import Flask
from markupsafe import escape
from flask import render_template
import re
import requests


app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello, World!'

class Observation:
    key: int
    species: str
    author: str
    date:str
    def __init__(self, key, species, author, date):
        self.key = key
        self.species = species
        self.author = author
        self.date = date
        self.urls = []
        self.uploads = []
    def add_url(self, url):
        self.urls.append(url)
    def add_upload(self, url):
        description = '{{Information%0A  |description={{en|1=Photo of ' + self.species + ' uploaded from GBIF}}'
        description +='%0A  |date=' + self.date + '%0A  |source=https://www.gbif.org/occurrence/' + str(self.key)
        description +='%0A  |author=' + self.author +'%0A}}%0A{{gbif|' + str(self.key) + '}}'
        description += '%0A[[Category:Media from GBIF]]%0A[[Category:' + self.species + ']]'
        dest = 'https://commons.wikimedia.org/wiki/Special:Upload'
        res = dest + '?wpUploadDescription=' + description + '&wpLicense=cc-by-4.0&wpDestFile='
        target_name = self.species + " GBIF observation " + str(self.key) + " " + str(len(self.urls))
        res += target_name + '&wpSourceType=url&wpUploadFileURL=' + url
        self.uploads.append(res)
    def __str__(self):
        reply = "key: " + str(self.key) + "\n"
        reply += "author: " + self.author +'\n'
        reply += "species: " + self.species +'\n'
        reply += "date: " + self.date +'\n'
        reply += "urls: \n"
        for url in self.urls:
            reply += url + "\n"
        reply += "uploads: \n"
        for upload in self.uploads:
            reply += upload + "\n"
        return reply
    def zip_urls(self):
        self.zipped = zip(self.urls, self.uploads)

def get_observations(gbif_id):
    observations = []
    url='https://api.gbif.org/v1/occurrence/search?acceptedTaxonKey='+str(gbif_id)+'&license=CC_BY_4_0'
    print(url)
    response = requests.get(url).json()
    for result in response['results']:
        if result['media'] != []:
            o = Observation (result['key'], result['species'], result['recordedBy'], result['eventDate'])
            for med in result['media']:
                o.add_url(med['identifier'])
                o.add_upload(med['identifier'])
            o.zip_urls()
            observations.append(o)
    return observations


@app.route("/res/<question_id>")
def show_results(question_id):
    objects = get_observations(question_id)
    return render_template('results.html', objects=objects)

