#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api.urlfetch import DownloadError

from library import login
from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import amazon_region
from library import zonen_liste_funktion
from library import format_error_message_green
from library import format_error_message_red
from library import loginelb

from dateutil.parser import *

from error_messages import error_messages

from boto.ec2.connection import *
from boto.ec2.elb import ELBConnection

class CreateLoadBalancer(webapp.RequestHandler):
    def get(self):
        #self.response.out.write('posted!')
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')

        sprache = aktuelle_sprache(username)
        navigations_bar = navigations_bar_funktion(sprache)
        # Nachsehen, ob eine Region/Zone ausgew�hlte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if not results:
            regionname = '---'
            zone_amazon = ""
        else:
            conn_region, regionname = login(username)
            zone_amazon = amazon_region(username)

        url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
        url_linktext = 'Logout'

        zonen_liste = zonen_liste_funktion(username,sprache)

        if sprache != "de":
            sprache = "en"

        input_error_message = error_messages.get(message, {}).get(sprache)

        # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
        if input_error_message == None:
            input_error_message = ""

        # Wenn die Nachricht gr�n formatiert werden soll...
        if message in ("8", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60"):
            # wird sie hier, in der Hilfsfunktion rot formatiert
            input_error_message = format_error_message_red(input_error_message)
        else:
            input_error_message = ""

        try:
            # Liste mit den Zonen
            liste_zonen = conn_region.get_all_zones()
        except EC2ResponseError:
            # Wenn es nicht geklappt hat...
            fehlermeldung = "10"
            self.redirect('/loadbalancer?message='+fehlermeldung)
        except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "8"
            self.redirect('/loadbalancer?message='+fehlermeldung)
        else:
            # Wenn es geklappt hat...
            # Anzahl der Elemente in der Liste
            laenge_liste_zonen = len(liste_zonen)

        elb_erzeugen_tabelle = ''
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<form action="/elb_definiv_erzeugen" method="post" accept-charset="utf-8">\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<table border="3" cellspacing="0" cellpadding="5">'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<tr>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>Name</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td><input name="elb_name" type="text" size="40" maxlength="40"></td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</tr>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<tr>\n'
        if sprache == "de":
            elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>Verf&uuml;gbarkeitszonen</td>\n'
        else:
            elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>Availability Zones</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>\n'
        for i in range(laenge_liste_zonen):
            elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<input type="checkbox" name="'+liste_zonen[i].name+'" value="'+liste_zonen[i].name+'"> '+liste_zonen[i].name+'<BR>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</tr>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<tr>\n'
        if sprache == "de":
            elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>Protokoll</td>\n'
        else:
            elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>Protocol</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<select name="elb_protokoll" size="1">\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '  <option selected="selected">TCP</option>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '  <option>HTTP</option>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</select>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</tr>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<tr>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>Load Balancer Port</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td><input name="ELBPort" type="text" size="10" maxlength="10"></td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</tr>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<tr>\n'
        if sprache == "de":
            elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>EC2 Instanz Port</td>\n'
        else:
            elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td>EC2 Instance Port</td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td><input name="InstPort" type="text" size="10" maxlength="10"></td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</tr>\n'


        elb_erzeugen_tabelle = elb_erzeugen_tabelle + ''
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<tr>\n'
        if sprache == "de":
            elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td colspan="2"><input type="submit" value="Load Balancer anlegen"></td>\n'
        else:
            elb_erzeugen_tabelle = elb_erzeugen_tabelle + '<td colspan="2"><input type="submit" value="create load balancer"></td>\n'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</table>'
        elb_erzeugen_tabelle = elb_erzeugen_tabelle + '</form>'


        template_values = {
        'navigations_bar': navigations_bar,
        'url': url,
        'url_linktext': url_linktext,
        'zone': regionname,
        'zone_amazon': zone_amazon,
        'elb_erzeugen_tabelle': elb_erzeugen_tabelle,
        'input_error_message': input_error_message,
        'zonen_liste': zonen_liste,
        }

        #if sprache == "de": naechse_seite = "elb_create_de.html"
        #else:               naechse_seite = "elb_create_en.html"
        #path = os.path.join(os.path.dirname(__file__), naechse_seite)
        path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "elb_create.html")
        self.response.out.write(template.render(path,template_values))
        