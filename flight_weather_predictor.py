#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""Copy of Condensed Modeling File

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ko62CzMgRUf4RyJGyR0r9z0LayQB1aIG
"""

#Install packages 

# pip install graphviz

# !pip install pydotplus

# !pip install six

# Commented out IPython magic to ensure Python compatibility.
# Import Packages
import numpy as np
import pandas as pd
# from google.colab import drive
# import pandas as pd
# import numpy as np
import matplotlib.pyplot as plt
# %matplotlib inline
import seaborn as sns
# import os
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA 
from sklearn.neighbors import KNeighborsClassifier
from sklearn import tree, metrics
from sklearn.tree import export_graphviz
from six import StringIO  
from IPython.display import Image  
import pydotplus
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score, recall_score
import warnings
from datetime import datetime
warnings.filterwarnings("ignore")
# drive.mount('/content/drive')


# Import Data into Python 
# os.chdir("/content/drive/My Drive/6242 project/Cleaned_Data")
#flight2017  = pd.read_csv("2017.csv")
clean_2017 = pd.read_csv("cleaned_2017.csv")
clean_2012_2016 = pd.read_csv("Cleaned_Data_2012-2016.csv")

# Train and Test data: 2012-2016 & 2017 flight delay data 
delay2017 = clean_2017[clean_2017['WEATHER_DELAY'].notna()][(clean_2017["DEP_DELAY"]>0) | (clean_2017["ARR_DELAY"]>0)]
delay_train = clean_2012_2016[clean_2012_2016['WEATHER_DELAY'].notna()][(clean_2012_2016["DEP_DELAY"]>0) | (clean_2012_2016["ARR_DELAY"]>0)]

# Airport to City mapping 
airports = ["PDX", "SFO", "SEA", "LAX", "SAN", "LAS", "PHX", "ABQ", "DEN", "SAT", "DAL", "IAH", "MCI", "MSP", "STL", "ORD", "BNA", "IND", "ATL", "DTW", "JAX", "CLT", "MIA", "PIT", "PHL", "JFK", "LGA", "BOS"]
airport_mappings = {
    "time": "datetime",
    "PDX": "Portland",
    "SFO": "San Francisco",
    "SEA": "Seattle",
    "LAX": "Los Angeles",
    "SAN": "San Diego",
    "LAS": "Las Vegas", 
    "PHX": "Phoenix",
    "ABQ": "Albuquerque",
    "DEN": "Denver",
    "SAT": "San Antonio",
    "DAL": "Dallas",
    "IAH": "Houston",
    "MCI": "Kansas City",
    "MSP": "Minneapolis",
    "STL": "Saint Louis",
    "ORD": "Chicago",
    "BNA": "Nashville",
    "IND": "Indianapolis",
    "ATL": "Atlanta",
    "DTW": "Detroit",
    "JAX": "Jacksonville",
    "CLT": "Charlotte",
    "MIA": "Miami",
    "PIT": "Pittsburgh",
    "PHL": "Philadelphia",
    "JFK": "New York",
    "LGA": "New York",
    "BOS": "Boston",
}

# Import weather data 
# os.chdir("/content/drive/My Drive/6242 project/DataSet/Climate")
humidity = pd.read_csv('humidity.csv')
pressure = pd.read_csv('pressure.csv')
temperature = pd.read_csv('temperature.csv')
weather_description = pd.read_csv('weather_description.csv')
wind_direction = pd.read_csv('wind_direction.csv')
wind_speed = pd.read_csv('wind_speed.csv')

dataframes = [humidity, pressure, temperature, wind_direction, wind_speed, weather_description]
airport_mappings_rev = dict((v,k) for k,v in airport_mappings.items())


for i in range(len(dataframes)):
  dataframes[i].columns = dataframes[i].columns.map(airport_mappings_rev)
  dataframes[i]["JFK"] = dataframes[i]["LGA"]
  dataframes[i] = dataframes[i].loc[1:44460, dataframes[i].columns.notnull()]
  if i < 5:
    temp1 = dataframes[i].ffill()
    temp2 = dataframes[i].bfill()
    df_concat = pd.concat((temp1, temp2))
    by_row_index = df_concat.groupby(df_concat.index)
    df_means = by_row_index.mean()
    df_means['time'] = temp1['time']
    dataframes[i] = df_means

humidity = dataframes[0]
pressure = dataframes[1]
temperature = dataframes[2]
wind_direction = dataframes[3]
wind_speed = dataframes[4]
weather_description = dataframes[5]

humidity = humidity.loc[:, humidity.columns.notnull()]
humidity= humidity.fillna(0)
pressure = pressure.fillna(0)
temperature = temperature.fillna(0)
weather_description = weather_description.fillna(0)
wind_direction = wind_direction.fillna(0)
wind_speed = wind_speed.fillna(0)

# Subset flight data for cities with weather data 
delay2017 = delay2017[-~delay2017['ORIGIN'].isin(airports)]
delay2017 = delay2017[-~delay2017['DEST'].isin(airports)]
delay2017 = delay2017[1:(len(delay2017)-62)]
delay_train = delay_train[-~delay_train['ORIGIN'].isin(airports)]
delay_train = delay_train[-~delay_train['DEST'].isin(airports)]

# Melt weather data 
humiditydf = pd.melt(humidity, id_vars=['time'], value_vars=airports).rename(columns={"value":"humidity"})
pressuredf = pd.melt(pressure, id_vars=['time'], value_vars=airports).rename(columns={"value":"pressure"})
temperaturedf = pd.melt(temperature, id_vars=['time'], value_vars=airports).rename(columns={"value":"temperature"})
wind_directiondf = pd.melt(wind_direction, id_vars=['time'], value_vars=airports).rename(columns={"value":"wind_direction"})
wind_speeddf = pd.melt(wind_speed, id_vars=['time'], value_vars=airports).rename(columns={"value":"wind_speed"})

# Get rid of unnamed columns 
CLEAN2017 =delay2017.drop(["Unnamed: 0"], axis=1)
clean_train = delay_train.loc[:,~delay_train.columns.duplicated()]
clean_train =clean_train.drop(["Unnamed: 0", "Unnamed: 0.1"], axis=1)

"""PCA 

"""

# Weather variables
WEATHER = clean_train[['DEPHum', 'DEPPres', 'DEPTemp', 'DEPWS', 'ARRHum', 'ARRPres', 'ARRTemp', 'ARRWS']]
WEATHER_2017 = CLEAN2017[['DEPHum', 'DEPPres', 'DEPTemp', 'DEPWS', 'ARRHum', 'ARRPres', 'ARRTemp', 'ARRWS']]

# Scale weather data 
scale = StandardScaler()
WEATHER = scale.fit_transform(WEATHER)
WEATHER_2017 = scale.transform(WEATHER_2017)

#PCA 

pca = PCA(n_components = 7)

principalComponents = pca.fit_transform(WEATHER)
principalDf = pd.DataFrame(data = principalComponents
             , columns = ['PC_1','PC_2','PC_3','PC_4','PC_5','PC_6','PC_7'])

principalComponents_2017 = pca.transform(WEATHER_2017)
principalDf_2017 = pd.DataFrame(data = principalComponents_2017
             , columns = ['PC_1','PC_2','PC_3','PC_4','PC_5','PC_6','PC_7'])

# PCA data with weather_delay
finalDf = pd.concat([principalDf, clean_train[['WEATHER_DELAY']]], axis = 1)
finalDf_2017 = pd.concat([principalDf_2017, CLEAN2017[['WEATHER_DELAY']]], axis = 1)

x_train, x_test, y_train, y_test = principalDf, principalDf_2017, finalDf[['WEATHER_DELAY']], finalDf_2017[['WEATHER_DELAY']][1:]

y_train_log = np.where(y_train != 0, 1, 0)
y_test_log = np.where(y_test != 0, 1, 0)

"""KNN"""

#KNN model with PCA 
neigh = KNeighborsClassifier(n_neighbors=3)
neigh.fit(x_train, y_train_log)

#y_pred = neigh.predict(x_test)

#print(f'Accuracy Score: {accuracy_score(y_test_log,y_pred)}')
#print(f'Confusion Matrix: \n{confusion_matrix(y_test_log, y_pred)}')
#print(f'Area Under Curve: {roc_auc_score(y_test_log, y_pred)}')
#print(f'Recall score: {recall_score(y_test_log,y_pred)}')

"""DELAY """

# add new column: month 
delay_train = clean_train[clean_train['WEATHER_DELAY']>0][['FL_DATE', 'WEATHER_DELAY', 'DEPHum', 'DEPPres', 'DEPTemp', 'DEPWD', 'DEPWS', 'ARRHum', 'ARRPres', 'ARRTemp', 'ARRWD', 'ARRWS']]
delay_train['month'] = delay_train['FL_DATE'].apply([lambda x: x[5:7]])

delay_2017 = CLEAN2017[CLEAN2017['WEATHER_DELAY']>0][['FL_DATE', 'WEATHER_DELAY', 'DEPHum', 'DEPPres', 'DEPTemp', 'DEPWD', 'DEPWS', 'ARRHum', 'ARRPres', 'ARRTemp', 'ARRWD', 'ARRWS']]
delay_2017['month'] = delay_2017['FL_DATE'].apply([lambda x: x[5:7]])

delay_train['peak'] = (delay_train['month'] == 12) | (delay_train['month'] == 1) | (delay_train['month'] == 2) | (delay_train['month'] == 6) | (delay_train['month'] == 7) | (delay_train['month'] == 8)
delay_train['peak'] = delay_train['peak'].apply(int)

delay_2017['peak'] = (delay_2017['month'] == 12) | (delay_2017['month'] == 1) | (delay_2017['month'] == 2) | (delay_2017['month'] == 6) | (delay_2017['month'] == 7) | (delay_2017['month'] == 8)
delay_2017['peak'] = delay_2017['peak'].apply(int)

# Changing delay to categorical data
delay_train['delay'] = pd.cut(delay_train['WEATHER_DELAY'], bins = [0, 90, 180, 1600], labels = [0,1, 2])
delay_2017['delay'] = pd.cut(delay_2017['WEATHER_DELAY'], bins = [0, 90, 180, 1600], labels = [0,1, 2])

# Decision Tree

X = delay_train[[ 'peak', 'DEPHum', 'DEPPres', 'DEPTemp', 'DEPWS', 'ARRHum', 'ARRPres', 'ARRTemp', 'ARRWS']]
y = delay_train[['delay']]
X_2017 = delay_2017[[ 'peak', 'DEPHum', 'DEPPres', 'DEPTemp', 'DEPWS', 'ARRHum', 'ARRPres', 'ARRTemp', 'ARRWS']]
y_2017 = delay_2017[['delay']]

clf = tree.DecisionTreeClassifier(max_depth = 4)
clf = clf.fit(X, y)

#y_pred = clf.predict(X_2017)

# Model Accuracy, how often is the classifier correct?
#print("Accuracy:",metrics.accuracy_score(y_2017, y_pred))

# Visualize tree

# dot_data = StringIO()
# export_graphviz(clf, out_file=dot_data,  
#                 filled=True, rounded=True,
#                 special_characters=True,feature_names = [ 'peak', 'DEPHum', 'DEPPres', 'DEPTemp', 'DEPWS', 'ARRHum', 'ARRPres', 'ARRTemp', 'ARRWS'],class_names=['0','1', '2'])
# graph = pydotplus.graph_from_dot_data(dot_data.getvalue())  
# graph.write_png('diabetes.png')
# Image(graph.create_png())

# !apt-get install -y xvfb # Install X Virtual Frame Buffer
# import os
# os.system('Xvfb :1 -screen 0 1600x1200x16  &')    # create virtual display with size 1600x1200 and 16 bit color. Color can be changed to 24 or 8
# os.environ['DISPLAY']=':1.0'    # tell X clients to use our virtual DISPLAY :1.0

"""VISUALIZATION"""
from tkinter import *
from tkinter import messagebox
import webbrowser
import requests, json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go


class EntryDemo:
  def __init__(self, win):
      #Create a entry and button to put in the root window!
      self.mainwin = win
      frame1 = Frame(win, borderwidth=1, relief="solid")
      frame1.pack()
      frame2 = Frame(win, borderwidth=15,relief="raised")
      frame2.pack()
      
      self.label_title = Label(frame1 ,text="Input your city names")
      self.label_title.pack()

      self.entry1  = Entry(frame2)
      self.entry1.delete(0, END)
      self.entry1.insert(0, "departure city")
      self.entry1.grid(row=0, column=0, columnspan=5, pady=5, padx=5)

      self.entry2 = Entry(frame2)
      self.entry2.delete(0, END)
      self.entry2.insert(0, "arrival city")
      self.entry2.grid(row=1, column=0, columnspan=5, pady=5, padx=5)

      #self.button = Button(frame2, text="Submit", command=self.clicked_submit)
      #self.button.grid(row=2, column=0, columnspan=2, pady=10, padx=10)
      self.button_map = Button(frame2, text="Map & Info", command=self.clicked_Map)
      self.button_map.grid(row=2, column=3, columnspan=2, pady=10, padx=10)

  def createMap(self):
      codes = pd.read_csv('airports_codes.csv')

      pd.set_option("max.columns", 30)
      import geopandas as gpd
      world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
      flight  = pd.read_csv("Cleaned_Data_2012-2017.csv")
      Location = pd.merge(flight, codes, left_on = "ORIGIN", right_on = "IATA_CODE").rename(columns = {"LATITUDE": "ORI-LA", "LONGITUDE": "ORI-LO"}).drop(['IATA_CODE', 'AIRPORT', 'STATE', 'COUNTRY'], axis=1)
      Location = pd.merge(Location, codes, left_on = "DEST", right_on = "IATA_CODE").rename(columns = {"LATITUDE": "DES-LA", "LONGITUDE": "DES-LO"}).drop(['IATA_CODE', 'AIRPORT', 'STATE', 'COUNTRY'], axis=1)
      Count = Location.groupby(["ORIGIN", "DEST", "ORI-LA", "ORI-LO", "DES-LA", "DES-LO", "CITY_x", "CITY_y"])["OP_CARRIER_FL_NUM"].count().reset_index()
      with plt.style.context(("seaborn", "ggplot")):
        fig = go.Figure()
        ## Plot world
        world[world.name == "United States of America"].plot(figsize=(15,15), edgecolor="grey", color="white");
        departure_city = self.entry1.get()
        arrival_city  = self.entry2.get()
        temp = Count[(Count["CITY_x"]==departure_city) ]
        temp = temp[(temp["CITY_y"]==arrival_city)]
        temp
        self.c = str(int(temp["OP_CARRIER_FL_NUM"]))
        ## Loop through each flight plotting line depicting flight between source and destination
        ## We are also plotting scatter points depicting source and destinations
        slat = temp["ORI-LA"]
        dlat = temp['DES-LA']
        slon = temp['ORI-LO']
        dlon = temp['DES-LO']
        num_flights = 1
        plt.plot([slon , dlon], [slat, dlat], linewidth=num_flights*2, color="blue", alpha=0.5)
        plt.scatter( [slon, dlon], [slat, dlat], color="red", alpha=0.1, s=num_flights*300)

    
        plt.title("Connection Map Depicting Flights between Chosen Cities")
        #plt.show()
#    plt.savefig("connection-map-geopandas-4.png")

        fig1 = plt.gcf()
        fig1.savefig('output.png', dpi=50)
      return None

  def clicked_Map(self):
      self.createMap()
      entry1_input = self.entry1.get()
      entry2_input = self.entry2.get()
      if entry1_input == "" or entry2_input == "":
          messagebox.showwarning("Invalid input", "please input the correct cities")

      self.secondWin = Toplevel()
      frame21 = Frame(self.secondWin, borderwidth=1, relief="solid")
      frame21.pack(side=LEFT)
      frame22 = Frame(self.secondWin, borderwidth=1, relief="solid")
      frame22.pack(side=RIGHT)
      #Label(self.secondWin, text="map").pack()

      #map on left frame
      photo = PhotoImage(file="output.png")
      self.imageLabel = Label(frame21, image=photo)
      self.imageLabel.photo = photo
      self.imageLabel.pack()

      #info on right frame
      info = self.getWeatherinfo(entry1_input, entry2_input)
      info = str(entry1_input.upper() + " >>> " +
             entry2_input.upper() + "\n" + "\n" + "Total number of flights between the city pair: " + self.c + "\n" + "\n" + info)
      #print(info)
      self.info = Label(frame22 , text=info)
      self.info.pack()

      button_back_2 = Button(self.secondWin, text="Back", command=self.win1up)
      button_back_2.pack(side=BOTTOM)
      #self.secondWin.withdraw()  # Hide this window until we need it!
      #self.secondWin.protocol("WM_DELETE_WINDOW", self.endProgram)

  def win1up(self):
      print("Switching to window 1!")
      self.secondWin.withdraw()
      self.mainwin.deiconify()

  '''def win2up(self):
      print("Switching to heat map!")
      #self.mainWin.withdraw()
      self.secondWin.deiconify()'''

  '''def clicked_d3(self):
      print("Switching to heat map!")
      #self.mainWin.withdraw()
      self.thirdwin.deiconify()'''

  def clicked_submit(self):
      entry1_input = self.entry1.get()
      entry2_input = self.entry2.get()
      if entry1_input == "" or entry2_input == "":
          messagebox.showwarning("Invalid input", "please input the correct cities")
      else:
          print("information submitted")
          print("Departure City:", entry1_input)
          print("Arrival City:", entry2_input)
          print("Get Weather!")
          self.getWeatherinfo(entry1_input, entry2_input)

  def getWeatherinfo(self, dep_city, arr_city):
 
      # Enter your API key here
      api_key = "2a6781794cd4cf00d524b0755dfd8167"
       
      # base_url variable to store url
      base_url = "http://api.openweathermap.org/data/2.5/weather?"
       
      # Give city name
      dep = dep_city
      arr = arr_city
       
      # complete_url variable to store
      # complete url address
      complete_url_dep = base_url + "q=" + dep + "&appid=" + api_key
      complete_url_arr = base_url + "q=" + arr + "&appid=" + api_key
      # get method of requests module
      # return response object
      response_dep = requests.get(complete_url_dep)
      response_arr = requests.get(complete_url_arr)
      # json method of response object
      # convert json format data into
      # python format data
      x0 = response_dep.json()
      x1 = response_arr.json()
      # Now x contains list of nested dictionaries
      # Check the value of "cod" key is equal to
      # "404", means city is found otherwise,
      # city is not found
      if x0["cod"] != "404" and x1["cod"] != "404":
       
          # store the value of "main"
          # key in variable y
          y0 = x0["main"]
          y1 = x1["main"]
       
          # store the value corresponding
          # to the "temp" key of y
          current_dep_temperature = y0["temp"]
          current_arr_temperature = y1["temp"]
          # store the value corresponding
          # to the "pressure" key of y
          current_dep_pressure = y0["pressure"]
          current_arr_pressure = y1["pressure"]
          # store the value corresponding
          # to the "humidity" key of y
          current_dep_humidity = y0["humidity"]
          current_arr_humidity = y1["humidity"]



          # get wind speed
          w0 = x0["wind"]
          w1 = x1["wind"]
          current_dep_windSpeed = w0["speed"]
          current_arr_windSpeed = w1["speed"]



          # store the value of "weather"
          # key in variable z
          z0 = x0["weather"]
          z1 = x1["weather"]
          # store the value corresponding
          # to the "description" key at
          # the 0th index of z
          weather_description_dep = z0[0]["description"]
          weather_description_arr = z1[0]["description"]

          lastupdate = x0['dt']
          month = int(datetime.utcfromtimestamp(lastupdate).strftime('%m'))
          peak_months = [1,2,6,7,8,12]
          is_peak = 0
          if month in peak_months:
              is_peak = 1

          

          # print following values
          print("                              ")
          print(" Last weather update: " + datetime.utcfromtimestamp(lastupdate).strftime('%Y-%m-%d %H:%M:%S') + " (UTC)")
          print("-------" + dep_city + "'s weather information" + "-------")
          '''
          print("                              ")
          print(" Temperature (in kelvin unit) = " +
                          str(current_dep_temperature) +
                "\n atmospheric pressure (in hPa unit) = " +
                          str(current_dep_pressure) +
                "\n humidity (in percentage) = " +
                          str(current_dep_humidity) +
                "\n description = " +
                          str(weather_description_dep) +
                "\n wind speed (in meters per second) = " +
                          str(current_dep_windSpeed))
          print("                              ")
          print("-------" + arr_city + "'s weather information" + "-------")
          print("                              ")
          print(" Temperature (in kelvin unit) = " +
                          str(current_arr_temperature) +
                "\n atmospheric pressure (in hPa unit) = " +
                          str(current_arr_pressure) +
                "\n humidity (in percentage) = " +
                          str(current_arr_humidity) +
                "\n description = " +
                          str(weather_description_arr) +
                "\n wind speed (in meters per second) = " +
                          str(current_arr_windSpeed))'''
      else:
          print(" City Not Found ")

      info = str("-------" + dep_city + "'s weather information" + "-------" +
                "\n Temperature (in kelvin unit) = " +
                          str(current_dep_temperature) +
                "\n atmospheric pressure (in hPa unit) = " +
                          str(current_dep_pressure) +
                "\n humidity (in percentage) = " +
                          str(current_dep_humidity) +
                "\n description = " +
                          str(weather_description_dep) +
                "\n wind speed (in meters per second) = " +
                          str(current_dep_windSpeed) +
                "\n" +
                "\n -------" + arr_city + "'s weather information" + "-------"+
                "\n Temperature (in kelvin unit) = " +
                          str(current_arr_temperature) +
                "\n atmospheric pressure (in hPa unit) = " +
                          str(current_arr_pressure) +
                "\n humidity (in percentage) = " +
                          str(current_arr_humidity) +
                "\n description = " +
                          str(weather_description_arr) +
                "\n wind speed (in meters per second) = " +
                          str(current_arr_windSpeed))
      info = str("Last weather update: " + datetime.utcfromtimestamp(lastupdate).strftime('%Y-%m-%d %H:%M:%S') + " (UTC)") + "\n" + info
      


        ### PREDICT #####

      new_data = pd.DataFrame(data = [[current_dep_humidity, current_dep_pressure, current_dep_temperature, current_dep_windSpeed, current_arr_humidity, current_arr_pressure, current_arr_temperature, current_arr_windSpeed]] , columns = ['DEPHum', 'DEPPres', 'DEPTemp', 'DEPWS', 'ARRHum', 'ARRPres', 'ARRTemp', 'ARRWS'])
      new_data = scale.transform(new_data)
      new_data = pca.transform(new_data)
      delay_prediction = neigh.predict(new_data)
      temp_info = ""
          #print("")
          #print("------- Delay Prediction -------")
      temp_info = "------- Delay Prediction -------"
      if delay_prediction:
          temp_info = temp_info + "\n" + "We predict that there will be a delay for your flight"
          peak_data = [[is_peak, current_dep_humidity, current_dep_pressure, current_dep_temperature, current_dep_windSpeed, current_arr_humidity, current_arr_pressure, current_arr_temperature, current_arr_windSpeed]]
          delay = clf.predict(peak_data)
          if delay == 0:
              temp_info = temp_info + "\n" + "The delay should be less than 90 minutes"
                  #print("The delay should be less than 90 minutes")
          elif delay == 1:
              temp_info = temp_info + "\n" + "The delay should be between 90 and 180 minutes"
                  #print("The delay should be between 90 and 180 minutes")
          else:
              temp_info = temp_info + "\n" + "The delay should be longer than 180 minutes"
                  #print("The delay should be longer than 180 minutes")
      else:
          temp_info = temp_info + "\n" + "We predict that there will not be a delay for your flight"
              #print("We predict that there will not be a delay for your flight")
          
      #else:
          #print(" City Not Found ")
     
      return str(info + "\n" + "\n" + temp_info)



#Create the main root window, instantiate the object, and run the main loop!
rootWin = Tk()
app = EntryDemo( rootWin )
rootWin.mainloop()