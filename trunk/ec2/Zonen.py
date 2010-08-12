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

from dateutil.parser import *

from error_messages import error_messages

from boto.ec2.connection import *

class Zonen(webapp.RequestHandler):
    def get(self):
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')

        # Nachsehen, ob eine Region/Zone ausgew�hlte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if results:
          # Nachsehen, ob eine Sprache ausgew�hlte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache)

          try:
            # Liste mit den Zonen
            liste_zonen = conn_region.get_all_zones()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            if sprache == "de":
              zonentabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
            else:
              zonentabelle = '<font color="red">An error occured</font>'
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            if sprache == "de":
              zonentabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
            else:
              zonentabelle = '<font color="red">A timeout error occured</font>'
          else:
            # Wenn es geklappt hat...
            # Anzahl der Elemente in der Liste
            laenge_liste_zonen = len(liste_zonen)

            zonentabelle = ''
            zonentabelle = zonentabelle + '<table border="3" cellspacing="0" cellpadding="5">'
            zonentabelle = zonentabelle + '<tr>'
            zonentabelle = zonentabelle + '<th align="center">Name</th>'
            zonentabelle = zonentabelle + '<th align="center">Status</th>'
            zonentabelle = zonentabelle + '</tr>'
            for i in range(laenge_liste_zonen):
                zonentabelle = zonentabelle + '<tr>'
                zonentabelle = zonentabelle + '<td>'+str(liste_zonen[i].name)+'</td>'
                if liste_zonen[i].state == u'available':
                  zonentabelle = zonentabelle + '<td bgcolor="#c3ddc3" align="center">'
                  if sprache == "de":
                    zonentabelle = zonentabelle + 'verf&uuml;gbar'
                  else:
                    zonentabelle = zonentabelle + str(liste_zonen[i].state)
                else:
                  zonentabelle = zonentabelle + '<td align="center">'
                  zonentabelle = zonentabelle + str(liste_zonen[i].state)
                zonentabelle = zonentabelle + '</td>'
                zonentabelle = zonentabelle + '</tr>'
            zonentabelle = zonentabelle + '</table>'

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonenliste': zonentabelle,
          'zonen_liste': zonen_liste,
          }

          #if sprache == "de": naechse_seite = "zonen_de.html"
          #else:               naechse_seite = "zonen_en.html"
          #path = os.path.join(os.path.dirname(__file__), naechse_seite)
          path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "zonen.html")
          self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')
          