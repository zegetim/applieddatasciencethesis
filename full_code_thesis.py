**Preparing NER model**


from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import pandas as pd

tokenizer = AutoTokenizer.from_pretrained("Babelscape/wikineural-multilingual-ner")
model = AutoModelForTokenClassification.from_pretrained("Babelscape/wikineural-multilingual-ner")

nlp = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

"""**2001 Lonely Planet guide NLP**

Splitting text
"""

import re

with open("LP2004_all.txt", "r") as text:
  text = text.read().replace("$", "")
  text2 = re.split(r"\-(?=SLEEPING|EATING|DRINKING|ENTERTAINMENT|SHOPPING|Sleeping|Eating|Drinking|Entertainment|Shopping)", text)
  del text2[0]
  print(len(text2))
  print(text2[2])
  for tekst in text2:
    text4 = re.split(r"\.\s+(?=.[^.]*?.*?\(\n?[Mm][Aa][Pp])", tekst, flags=re.DOTALL)

"""**Creating dataframe**"""

import pandas as pd
import re

LP_list = ["testLP2004.txt", "testLP2013.txt", "testLP2022.txt","restaurantsLP2004.txt", "restaurantsLP2013.txt", "restaurantsLP2022.txt"]
res_list = ["restaurantsLP2004.txt", "restaurantsLP2007.txt", "restaurantsLP2010.txt", "restaurantsLP2013.txt", "restaurantsLP2016.txt", "restaurantsLP2019.txt", "restaurantsLP2022.txt"]
LP_all = ["LP2004_all.txt", "LP2007_all.txt", "LP2010_all.txt", "LP2013_all.txt", "LP2016_all.txt", "LP2019_all.txt", "LP2022_all.txt"]
results = []
types = ["Sleeping", "Eating", "Drinking", "Entertainment", "Shopping"]


# Extracting the name of the netity using a NER model
def extract_name(text):
  name = re.search(r".*?(?=\n?\(\n?[Mm][Aa][Pp])", text, flags=re.DOTALL)
  if name:
    name2 = name.group()
    ner_results1 = nlp(name2)
    nerresults1 = pd.DataFrame(ner_results1)
    if nerresults1.empty:
      return "No name"
    result = nerresults1.iloc[-1]["word"]
    return result
  else:
    return

# Extracting the price of the entity in Gulden
def extract_price_gulden(text):
  price = re.search(r"f\d+", text)
  price_wrong_format = re.search(r"fl\s*\d+", text, flags=re.DOTALL)
  price_wrong_format2 = re.search(r"£\s*\d+", text, flags=re.DOTALL)
  if price:
    return price.group()
  if price_wrong_format:
    return price_wrong_format.group()
  if price_wrong_format2:
    return price_wrong_format2.group()
  else:
    return

# Extracting the price of the entity in Euros
def extract_price_euro(text):
  price = re.findall(r"€\s*[0-9/-]+", text)
  price_gulden = re.findall(r"f\d+", text)
  price_wrong_format = re.findall(r"fl\s*\d+", text, flags=re.DOTALL)
  price_wrong_format2 = re.findall(r"£\s*\d+", text, flags=re.DOTALL)
  if price:
    return price
  if price_gulden or price_wrong_format or price_wrong_format2:
    return price_gulden + price_wrong_format + price_wrong_format2
  else:
    return

# Extracting the category of price
def extract_category(text):
  category = re.findall(r"\b(s|d|t|tr|q|f|ste|dm|breakfast|single|double|triple|suite|r|mains)\b", text)
  if category:
    return category

# Extracting addresses using REGEX
def extract_address(text):
  address = re.search(r"\, [a-zA-Z\s]+ \d+(\)|-)", text, flags=re.DOTALL)
  address_new = re.search(r"[:|;]\s*[a-zA-Z\s+\n -]+\s+\d+[:|;)-]", text, flags=re.DOTALL)
  address_new_wrong = re.search(r"\: [a-zA-Z\s+ -]+ \d+\:", text, flags=re.DOTALL)
  if address_new:
    return address_new.group()
  if address:
    return address.group()
  if address_new_wrong:
    return address_new_wrong.group()
  else:
    return

# Function to use all extraciton funtions
def get_data(text):
  name = extract_name(text)
  price = extract_price_euro(text)
  address = extract_address(text)
  category = extract_category(text)
  return name, price, address, category

# Looping through all travel guides and texts, and creating a dataframe
for LP in LP_all:
  with open(LP, "r") as text:
    text = text.read().replace("$", "")
    text2 = re.split(r"\-(?=SLEEPING|EATING|DRINKING|ENTERTAINMENT|SHOPPING|Sleeping|Eating|Drinking|Entertainment|Shopping)", text)
    del text2[0]
    for i, t in enumerate(text2):
      texts = re.split(r"\.\s+(?=.[^.]*?.*?\(\n?[Mm][Aa][Pp])", t, flags=re.DOTALL)
      entity_type = types[i]
      # print(t)

      for text in texts:
        name, price, address, category = get_data(text)
        print(name, price, address, category)
        results.append(
          {
              "name": name,
              "price": price,
              "address": address,
              "year": LP,
              "category": category,
              "text": text,
              "type": entity_type
          }
        )

df_results = pd.DataFrame(results)
df_results = df_results[df_results['name'].notna()]
df_results

df_results.to_csv("results_all1.csv", index=False, encoding = "utf-8")

"""test Extractie"""

!pip install requests

df_results = df_results[df_results['address'].notna()]
df_results

df_results.to_csv("results_all1_notna.csv", index=False, encoding = "utf-8")

import pandas as pd

# Adding 'Amsterdam' to dataframe to make it easier for the geocoding API
df_results["address2"] = df_results["address"].astype(str) + ", Amsterdam"
df_results

"""Using PDOK Api to transform the addresses into coordinates"""

import requests
import time

# Looping through all addresses and getting their coordinates, area code and district code
def get_data():
  ll_list = []
  wijk_list = []
  buurt_list = []
  for address in df_results["address2"]:
    location = None
    wijk = None
    buurt = None
    time.sleep(1)
    parameters = {'q' : address}
    response = requests.get("https://api.pdok.nl/bzk/locatieserver/search/v3_1/free", params=parameters)
    data = {}
    location = None
    if response.status_code == 200:
      data = response.json()
    print(address)
    print(data)
    if "response" in data:
      if data["response"]["numFound"] > 0 and data["response"]["docs"][0]["type"] == "adres":
        location = data["response"]["docs"][0]["centroide_ll"]
        wijk = data["response"]["docs"][0]["wijkcode"]
        buurt = data["response"]["docs"][0]["buurtnaam"]
    ll_list.append(location)
    wijk_list.append(wijk)
    buurt_list.append(buurt)
    print(ll_list)
    print(wijk_list)
    print(buurt_list)
  return ll_list, wijk_list, buurt_list
ll, wijk, buurt = get_data()
df_results["location"] = ll
df_results["wijk"] = wijk
df_results["buurt"] = buurt
print(df_results)

coordinates_list = []

# Transform coordinates in fucntional format

for item in df_results["location"]:

  if pd.isna(item):
    coordinates_list.append(None)
    continue
  item_split = item.split("(")[1]
  item_split = item_split.split(")")[0]
  lat_lon_split = item_split.split(" ")
  lon = lat_lon_split[0]
  lat = lat_lon_split[1]
  lon_lat = [float(lat), float(lon)]
  coordinates_list.append(lon_lat)

df_results["coordinates"] = coordinates_list
print(df_results)

print(len(coordinates_list))

df_results.to_csv("results_all2.csv", index=False, encoding = "utf-8")

"""# Spatial analysis"""

import folium
import json

with open('geojson_lnglat.json', 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# df_results = pd.read_csv("resultsLP13.csv")
m = folium.Map(location=(52.37311361881209, 4.892449892289996), zoom_start=14)
folium.GeoJson(
    geojson_data
).add_to(m)

a = folium.Map(location=(52.37311361881209, 4.892449892289996), zoom_start=14)
folium.GeoJson(
    geojson_data
).add_to(a)

p = folium.Map(location=(52.37311361881209, 4.892449892289996), zoom_start=14)
folium.GeoJson(
    geojson_data
).add_to(p)

map = folium.Map(location=(52.37311361881209, 4.892449892289996), zoom_start=14)
folium.GeoJson(
    geojson_data
).add_to(map)

for i, row in df_results.iterrows():
  if row['coordinates'] == None:
    continue
  if row['year'] == "LP2004_all.txt":
    folium.CircleMarker(location = row['coordinates'], color='red', fill=True, radius =5).add_to(m)
    folium.CircleMarker(location = row['coordinates'], color='red', fill=True, radius =5).add_to(map)
  elif row['year'] == "LP2013_all.txt":
    folium.CircleMarker(location = row['coordinates'], color='blue', fill=True, radius = 5).add_to(a)
    folium.CircleMarker(location = row['coordinates'], color='blue', fill=True, radius =10).add_to(map)
  else:
    folium.CircleMarker(location = row['coordinates'], color='green', fill=True, radius =5).add_to(p)
    folium.CircleMarker(location = row['coordinates'], color='green', fill=True, radius =15).add_to(map)
display(m)
display(a)
display(p)
display(map)

"""# Price analysis"""

# pip install --upgrade transformers accelerate
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import pandas as pd
import sympy
import sympy.printing
import json
import torch

quant_config = BitsAndBytesConfig(
      load_in_4bit=True,
      bnb_4bit_use_double_quant=True,
      bnb_4bit_quant_type="nf4",
      bnb_4bit_compute_dtype=torch.float16
      )

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-3B-Instruct",
    # quantization_config=quant_config,
    torch_dtype="auto",
    device_map="auto")

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")

# with open("testLP2004.txt", "r") as text2:
#   text2 = text2.read().replace("$", "")

# df = pd.read_csv("resultsLP14_utf8.csv")
df = pd.read_csv("results_all2.csv")
df = df[df['type'] == "Sleeping"].reset_index(drop=True)

input = """You are a model for data extraction. For every hotel or hostel,
return a json with name and price for single and double categories.

Rules:
1. very strict: json format should always be (for hotels/hostels):
{"name": "string", "price": {"single": number or null, "double": number}}
2. Only single (s) and double (d) categories
3. If there is an option without bathroom, choose only with bathroom
4. If there is a range: e.g. 30-40, always choose the lowest number
5. dm is not a single room, ignore dm
6. if single room is not mentioned, single: null
7. very strict: start the response with { and end with }, no conversational text, only json

Examples:
input: Hotel London, www.hotellondon.com, s/d/f €20/30/40
output: {"name": "Hotel London", "price": {"single": 20, "double": 30}}

input: Hotel Paris, www.hotelparis.com, single €30-40, double €50-60
output: {"name": "Hotel Paris", "price": {"single": 30, "double": 50}}
"""

response_list = []
for d in df["text"]:
  messages = [
      {"role": "system", "content": input},
      {"role": "user", "content": d}
  ]

  text = tokenizer.apply_chat_template(
      messages,
      tokenize=False,
      add_generation_prompt=True
  )

  model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

  generated_ids = model.generate(
      **model_inputs,
      max_new_tokens=512,
      temperature=0.2,
  )

  generated_ids = [
      output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
  ]

  response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
  print(response)
  print("----------------------------------------")
  try:
    response2 = json.loads(response)
  except:
    response2 = {"name": None, "price": {"single": None, "double": None}}
  response_list.append(response2)
for i, j in enumerate(response_list):
  if j == None:
    response_list[i] = {"name": None, "price": {"single": None, "double": None}}
df2 = pd.DataFrame(response_list)
df3 = pd.concat([df, df2], axis=1)
df3.to_csv("results_all2_prices.csv", index=False, encoding="utf-8")
print(df2)

"""# Linear mixed models"""

import pandas as pd
from geopy.distance import geodesic
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("price_list.csv")
inflatie = {
   'LP2004_all.txt': 121.43 / 83.48,
   'LP2007_all.txt': 121.43 / 87.20,
   'LP2010_all.txt': 121.43 / 91.59,
   'LP2013_all.txt': 121.43 / 98.44,
   'LP2016_all.txt': 121.43 / 100.32,
   'LP2019_all.txt': 121.43 / 106.16,
   'LP2022_all.txt': 121.43 / 121.43,
}

years = {
   'LP2004_all.txt': '2004',
   'LP2007_all.txt': '2007',
   'LP2010_all.txt': '2010',
   'LP2013_all.txt': '2013',
   'LP2016_all.txt': '2016',
   'LP2019_all.txt': '2019',
   'LP2022_all.txt': '2022',
}

df['inflatie'] = df['year'].map(inflatie)
df['year2'] = df['year'].map(years)
df['prijs_inflatie'] = (df['inflatie'] * df['price3'])

df = df.dropna(subset=['coordinates'])
df['coordinates'] = df['coordinates'].str.strip('[]')
df[['latitude', 'longitude']] = df['coordinates'].str.split(',', expand=True)


df['latitude'] = df['latitude'].astype(float)
df['longitude'] = df['longitude'].astype(float)
# station: 52.3788524896101, 4.900545928891128
# dam: 52.373186539236066, 4.892475385925442
# random locatie: 52.37223302386973, 4.9006555183596525
df["distance_dam"] = df.apply(lambda row: geodesic((row['latitude'], row['longitude']), (52.373186539236066, 4.892475385925442)).km, 
    axis=1)

# print(df.groupby("year")["distance_dam"].mean())
# df.to_csv("coordinates_list.csv", encoding="utf-8", index=False)

print(df.head())

import statsmodels.api as sm

import statsmodels.formula.api as smf

df['distance_dam_linear'] = df['distance_dam'].copy()

df['year'] = df['year2'].astype('category')
df['gebied'] = df['gebied'].astype('category')
df['buurt'] = df['buurt'].astype('category')
df['wijk'] = df['wijk'].astype('category')
df['distance_dam'] = np.log(df['distance_dam'])
md = smf.mixedlm("prijs_inflatie ~ distance_dam * year", df, groups=df["wijk"])
mdf = md.fit()
print(mdf.summary())

"""# Topic modelling"""

from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import nltk
from umap import UMAP
from nltk.corpus import stopwords


nltk.download('stopwords')

df = pd.read_csv("results_all2.csv")

df = df[(df["type"] == "Drinking") | (df["type"] == "Shopping") | (df["type"] == "Eating")]

df_2004 = df[df["year"] == "LP2004_all.txt"].copy()
df_2007 = df[df["year"] == "LP2007_all.txt"].copy()
df_2010 = df[df["year"] == "LP2010_all.txt"].copy()
df_2013 = df[df["year"] == "LP2013_all.txt"].copy()
df_2016 = df[df["year"] == "LP2016_all.txt"].copy()
df_2019 = df[df["year"] == "LP2019_all.txt"].copy()
df_2022 = df[df["year"] == "LP2022_all.txt"].copy()
df_2004.loc[:, "year"] = 2004
df_2007.loc[:, "year"] = 2007
df_2010.loc[:, "year"] = 2010
df_2013.loc[:, "year"] = 2013
df_2016.loc[:, "year"] = 2016
df_2019.loc[:, "year"] = 2019
df_2022.loc[:, "year"] = 2022

df_list = pd.concat([df_2004["text"], df_2007["text"], df_2010["text"], df_2013["text"], df_2016["text"], df_2019["text"], df_2022["text"]])

df_list = df_list.tolist()

timestamps = pd.concat([df_2004["year"], df_2007["year"], df_2010["year"], df_2013["year"], df_2016["year"], df_2019["year"], df_2022["year"]])

timestamps = timestamps.tolist()

extra_stopwords = ["google", "map", "maps", "www.lonelyplanet.com", "p74", "p54", "google", "amsterdam", "fri", "sat", "sun", "ampm", "ha" , "hampm", "mon", "hpm", "thu", "noonpm" "sunthu", "pmam", "hpmam", "hotel", "restaurant", "cafe", "bar", "café", "©from", "2m", "45035045", "4430", "p92", "j351224", "88", "p90", "p92", "p9697", "wwwlonelyplanetcom"
                   "van", "sunthu", "inci", "without", "breakfast", "monthu", "ste", "like", "main", "amam", "noonpm", "hnoonpm", "dinner", "room", "menu", "hostel", "dish", "bathroom", "lunch", "dutch", "one", "across", "place", "offer", "wa", "tuefri", "pp923", "pp889", "350", "515", "020423", "3343", "0622", "b6387307amstelstraat", "1318", "101750"]
stop_words = set(stopwords.words('english'))
stop_words.update(extra_stopwords)

vectorizer = CountVectorizer(stop_words=list(stop_words), ngram_range=(1,2))

umap = UMAP(random_state=0, min_dist=0.0, n_neighbors=10, n_components=5, metric="cosine")

topic_model = BERTopic(vectorizer_model=vectorizer, umap_model=umap, nr_topics="auto")
topics, probs = topic_model.fit_transform(df_list)

topic_model.get_topic_info()

topics_over_time = topic_model.topics_over_time(df_list, timestamps)
topics_over_time.to_csv("topics2.csv")

print(topics_over_time)

fig = topic_model.visualize_topics_over_time(topics_over_time)
print(type(fig))
print(len(fig.data))
fig.show()
