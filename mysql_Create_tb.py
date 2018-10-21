import requests  #wird fuer die HTTP Anfrage benoetigt
import mysql.connector #zum schreiben der Daten in die Datenbank
from datetime import datetime, timedelta ,date ,time



#Verbindung zur Datenbank. Ist auf meinem zweiten NAS zum Test erstellt worden. Stichwort MiranderDB und phpMyAdmin
mydb = mysql.connector.connect(
  host="192.168.0.1",	#IP anpassen
  user="fronius",		#User anpassen
  passwd="pwfronius",	#Passwort anpassen
  database="dblogger"	#Deine Datenbank. Manuel vorab erstellt!
)

#Python Modul zum verbinden zur Datenbank
mycursor = mydb.cursor()


#Erstell eine Tabele fuer die Daten aus Fronius Wechselrichter
mycursor.execute("CREATE TABLE `dblogger`.`tbfroniuslogger` ( `i` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT , `DatumZeit` DATETIME NOT NULL , `Wert` INT NOT NULL , `Einheit` TEXT NOT NULL , `Status` TEXT NOT NULL , PRIMARY KEY (`i`)) ENGINE = InnoDB")

exit()

