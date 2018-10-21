
# Module werden importiert
import requests  # Packet muss man vorher installieren.  c:/python -m pip install requests
from datetime import datetime, timedelta ,date ,time
import json
import sys
import argparse #zum einfuegen von Parametern. script.py -start 09.11.2018
import pprint #zeigt Dict schoener an
import mysql.connector #zum schreiben der Daten in die Datenbank



parser = argparse.ArgumentParser()
parser.add_argument("-s", "--start",help="Beginn der Ablesung Format=TT.MM.JJJJ")
parser.add_argument("-a", "--anzahl", help="Anzahl der Tage nach dem Beginn")
args=parser.parse_args()

#print(type(args.echo))
#print(args.echo)

if args.start:
    print("Ablesung ab " + args.start)
    argsStartDatum=datetime.strptime(args.start, '%d.%m.%Y') #'15.10.2018'
if args.start == None:
    print("Datum nicht angegeben - Aktuelles Datum wird verwendet")
    argsStartDatum=datetime.today()  #2018-10-17 22:18:52.614769

tage=0
if args.anzahl == None:
    print("Zeitraum 1 Tag")
else:
    tage=int(args.anzahl)-1
    print("Zeitraum " + args.anzahl + " Tage")     



Start=argsStartDatum
Startdatum = Start.strftime("%d.%m.%Y")
#Ende = Start + timedelta(days=1)
Ende = Start + timedelta(days=tage)
Enddatum = Ende.strftime("%d.%m.%Y")
ZeitLastgangintervall = Start


mydb = mysql.connector.connect(
  host="192.168.0.1",	#IP anpassen
  user="fronius",		#User anpassen
  passwd="pwfronius",	#Passwort anpassen
  database="dblogger"	#Deine Datenbank. Manuel vorab erstellt!
)



Parameter = {'Scope': 'System', 'SeriesType': 'Detail', 'StartDate': Startdatum, 'EndDate':Enddatum,
             'Channel':'900', 'Channel': 'EnergyReal_WAC_Sum_Produced'}
#print(Parameter)

#Query_PV_Erzeugung
query_pv_archive = 'http://192.168.0.2/solar_api/v1/GetArchiveData.cgi?' #IP anpassen
print("Http Anfrage gestartet - warten")
json_archive_data = requests.get(query_pv_archive, params=Parameter).json() 
#print(json_archive_data)

print("Http Anfrage beendet")
#print(query_pv_archive, Parameter)

# je nach Format des JSON antwort muss man hier den Pfad zum gewuenschten Wert anlegen 
PV_Erzeugung_Total = json_archive_data['Body']['Data']['inverter/1']['Data']['EnergyReal_WAC_Sum_Produced']['Values']
#temp=json_archive_data['Body']['Data']['inverter/1']['Start']    #"2018-10-17T00:00:00+02:00"
#temp2 = temp.strftime("%Y-%m-%d") 
#print(type(temp2))

maxKeyNr = int(max(PV_Erzeugung_Total, key=int)) #der Key ist eine Zahl im Dict. mit List werden die Keys angezeigt > max sucht den hoechsten Wert > int macht aus Unicode ein int fuer die while Schleife.


print("parsen der json Antwort")
summe=0.0
status='W'
dict_Daten = {} 
keyNr=0
#summeErzeugung=0
while keyNr <= maxKeyNr:
    summe=0.0
    status='W'
    #print(type(summe))
    #print("begin" + str(keyNr))
    for i in range(3): #Schleife ermittelt die Summe von drei Werten a 5 min
        #print(PV_Erzeugung_Total.get(str(keyNr)))
        #valueDict=round(PV_Erzeugung_Total.get(str(keyNr)), 0) #Rundet die Zahl bis zum Komma
        valueDict=PV_Erzeugung_Total.get(str(keyNr))
        if valueDict == None:
            print('Fehler. Im jeson fehlt ein Wert beim Key'+str(keyNr))
            keyNr = keyNr+300
            summe=summe+0
            status="G"
            continue
        else:
            summe=summe+round(valueDict,0)
            #summe = summe + round(PV_Erzeugung_Total.get(str(keyNr)), 0) #Rundet die Zahl bis zum Komma
            #summe = summe + int(PV_Erzeugung_Total.get(str(keyNr))) #ohne float. zu ungenau
            keyNr = keyNr+300 # Fronius legt alle 5min Werte ab. bzw 300 Sekunden
            #print (keyNr)
    #summeErzeugung=summeErzeugung + summe    
    dict_Daten[keyNr]={}
    dict_Daten[keyNr]['DatumZeit']=ZeitLastgangintervall
    dict_Daten[keyNr]['Wert']=summe*4 #Leistungswert auf eine Stunde
    dict_Daten[keyNr]['Einheit']="W"
    dict_Daten[keyNr]['Status']=status
    ZeitLastgangintervall = ZeitLastgangintervall + timedelta(minutes=15)    
    #erstellt den passenden Zeitstempel fuer die 15min Lastgangwerte
    #print(str(ZeitLastgangintervall) + " , " + str(summe)+ " , " +str(summeErzeugung))
    #print(str(ZeitLastgangintervall.strftime("%d-%m-%Y %H:%M")) + " , " + str(int(summe))) #sehr genau

#pprint.pprint(dict_Daten)

print("Schreibe Daten in SQL")
mycursor = mydb.cursor()
mycursor.execute('DELETE FROM tbfroniuslogger')
mydb.commit()
keyNr=900

while keyNr <= maxKeyNr:
    print(str(keyNr) + " von " + str(maxKeyNr))
    var_DatumZeit=dict_Daten[keyNr]['DatumZeit']
    var_Wert=dict_Daten[keyNr]['Wert']
    var_Einheit=dict_Daten[keyNr]['Einheit']
    var_Status=dict_Daten[keyNr]['Status']

    #Variable erstellen die in die Datenbank geschrieben werden sollen.
    sql="INSERT INTO tbfroniuslogger (DatumZeit, Wert, Einheit, Status) VALUES (%s, %s, %s,%s)"
    data=(var_DatumZeit, var_Wert, var_Einheit, var_Status)

    mycursor.execute(sql, data) #ausfuehren
    mydb.commit() #bestaetigen des INSERT. Ohne das wir nichts in die DB geschrieben.

    #Rueckmeldung an die Konsole das der Auftrag ausgefuehrt wurde.
    #print(mycursor.rowcount, "record inserted.")
    keyNr=keyNr + 900    

    #print(str(keyNr) + "Summe:" + str(summe))
#print(str(summeErzeugung))
       
print("Werte in SQL geschrieben")