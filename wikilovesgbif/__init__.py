from flask import Flask
from markupsafe import escape
from flask import render_template
import re
import requests

placeholder = "check value"

app = Flask(__name__)


@app.route('/')
def hello():
    return render_template('main.html')

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
    def add_upload(self, url, extension="jpg"):
        description = '{{Information%0A  |description={{en|1=Photo of ' + self.species + ' uploaded from GBIF}}'
        description +='%0A  |date=' + self.date + '%0A  |source=https://www.gbif.org/occurrence/' + str(self.key)
        description +='%0A  |author=' + self.author +'%0A}}%0A{{gbif|' + str(self.key) + '}}'
        description += '%0A[[Category:Media from GBIF]]%0A[[Category:' + self.species + ']]'
        dest = 'https://commons.wikimedia.org/wiki/Special:Upload'
        res = dest + '?wpUploadDescription=' + description + '&wpLicense=cc-by-4.0&wpDestFile='
        target_name = self.species + " GBIF observation " + str(self.key) + " " + str(len(self.urls)) + "." + extension
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


def objectify_result(result):
    eventDate = placeholder
    eventAuthor = placeholder
    eventSpecies = placeholder
    eventKey = placeholder
    if 'eventDate' in result:
        eventDate = result['eventDate']
    if 'key' in result:
        eventKey = result['key']
    if 'species' in result:
        eventSpecies = result['species']
    if 'recordedBy' in result:
        eventAuthor = result['recordedBy']
    o = Observation (eventKey, eventSpecies, eventAuthor, eventDate)
    if result['media'] != []:
        if result['extensions'] != {}:
            # observation 1998474076 uses url1, sub_url1, format_url1
            url1 = 'http://rs.gbif.org/terms/1.0/Multimedia'
            url2 = 'http://rs.tdwg.org/ac/terms/Multimedia'
            sub_url1 = 'http://purl.org/dc/terms/identifier'
            sub_url2 = 'http://rs.tdwg.org/ac/terms/accessURI'
            format_url1 = 'http://purl.org/dc/terms/format'
            if url1 in result['extensions']:
                for med in result['extensions'][url1]:
                    o.add_url(med[sub_url1])
                    extension = med[format_url1].split("/")[-1]
                    o.add_upload(med[sub_url1], extension)
            # observation 3716074644 uses url2, sub_url2 but also format_url1
            if url2 in result['extensions']:
                for med in result['extensions'][url2]:
                    o.add_url(med[sub_url2])
                    extension = med[format_url1].split("/")[-1]
                    o.add_upload(med[sub_url2], extension)

        else:
            for med in result['media']:
                if 'identifier' in med:
                    o.add_url(med['identifier'])
                    o.add_upload(med['identifier'])
        o.zip_urls()
    return o

def get_observations(gbif_id):
    observations = []
    url='https://api.gbif.org/v1/occurrence/search?acceptedTaxonKey='+str(gbif_id)+'&license=CC_BY_4_0'
    print(url)
    response = requests.get(url).json()
    for result in response['results']:
        if result['media'] != []:
            observations.append(objectify_result(result))
    return observations


@app.route("/res/<species_id>")
def show_results(species_id):
    objects = get_observations(species_id)
    return render_template('results.html', objects=objects)

def get_observation(obs_id):
    observations = []
    url='https://api.gbif.org/v1/occurrence/'+str(obs_id)
    response = requests.get(url).json()
    observations.append(objectify_result(response))
    return observations

@app.route("/obs/<observation_id>")
def show_observation(observation_id):
    objects = get_observation(observation_id)
    return render_template('results.html', objects=objects)
