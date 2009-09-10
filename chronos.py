import os
import urllib2
import string
import re
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from HTMLParser import HTMLParser
from datetime import datetime, timedelta

class infoParser(HTMLParser):
  def __init__(self):
    self.result = []
    self.nbrow = 0
    self.active = 0
    self.finished = 0
    self.skipping=0
    self.current_row = []
    self.current_data = []
    HTMLParser.__init__(self)
    
  def start_table(self, attributes):
    # print "begin table"
    if not self.finished:
      self.active=1
  def end_table(self):
    # print "end table"
    self.active=0
    self.finished=1
    
  def start_tr(self,attributes):
    # print "  begin tr"
    if self.active and not self.skipping:
      self.current_row = []
      
  def end_tr(self):
    # print "  end tr"
    if self.active and not self.skipping:
      self.result.append(self.current_row)
      
  def start_td(self,attributes):
    # print "    begin td"
    if self.active and not self.skipping:
      self.current_data = []
      
  def end_td(self):
    # print "    end td"
    if self.active and not self.skipping:
      self.current_row.append(
        string.join(self.current_data))
        
  def handle_data(self, data):
    if self.active and not self.skipping:
      # print "      datafound:"
      # print data
      # print "      end of data"
      self.current_data.append(data)
    
  def handle_starttag(self, tag, attrs):
    # print "Encountered the beginning of a %s tag" % tag
    if tag == "table":
      self.start_table(attrs)
    elif tag == "tr":
      self.start_tr(attrs)
    elif tag == "td":
      self.start_td(attrs)

  def handle_endtag(self, tag):
    # print "Encountered the end of a %s tag" % tag
    if tag == "table":
      self.end_table()
    elif tag == "tr":
      self.end_tr()
    elif tag == "td":
      self.end_td()




def dateICal(date):
  return date.strftime("%Y%m%dT%H%M%S")
  
def make_event_list(parsed):
  events = []
  for i in parsed:
    if len(i) < 7:
      continue
    start = datetime.strptime("%s %s" % (i[0], i[1]), "%d/%m/%Y %Hh%M")
    if re.match("^\d{1,2}h$", i[2]):
      delta = datetime.strptime(i[2], "%Hh")
    else: # /2h30min/
      delta = datetime.strptime(i[2], "%Hh%Mmin")
    end = start + timedelta(hours = delta.hour, minutes = delta.minute)

    event = {"groups": i[4],
      "prof": i[5],
      "room": i[6],
      "name": i[3],
      "start": dateICal(start),
      "end": dateICal(end)
      }
      
    event_condensed_name = "%s-%s" % (event["name"], event["prof"])
    event_condensed_name = re.sub('[^\w]','_', event_condensed_name)
    event["uid"] = "%s-%s-%s" % (event["groups"], event["start"], event_condensed_name)
    
    events.append(event)

    # print ""
    # print "UID:chronos-%s-%s-%s" % (event["groups"], dateICal(event["start"]), event_condensed_name)
    # print "DTSTAMP:%s" % dateICal(datetime.now())
    # print "SUMMARY:%s - %s %s" % (event["name"], event["prof"], event["room"])
    # print "DESCRIPTION:Cours: %s\\nProf: %s\\nSalle: %s\\nGroupes: %s" % (event["name"], event["prof"], event["room"], event["groups"])
    # print "DTSTART:%s" % dateICal(event["start"])
    # print "DTEND:%s" % dateICal(event["end"])
    # print "LOCATION:%s" % event["room"]
  return events
    
    
class getICS(webapp.RequestHandler):
  def get(self):  
    url = "http://chronos.epita.net/"
	
    session_id = ""
    result = urlfetch.fetch(url)
    if result.status_code == 200:
      session_id = result.headers['set-cookie']
      
    url = "http://chronos.epita.net/ade/standard/direct_planning.jsp?projectId=3&login=student&password="
    result = urlfetch.fetch(url, headers = { 'Cookie': session_id })
    DisplaySav51 = result.headers['set-cookie']
    
    tree = "http://chronos.epita.net/ade/standard/gui/tree.jsp"
    cookie = "%s; %s" % (DisplaySav51, session_id)
    
    # Find the leaf following the given path
    categorie = "category=%s" % "trainee"
    url = "%s?%s&expand=false&forceLoad=false&reload=false" % (tree, categorie)
    result = urlfetch.fetch(url, headers = { 'cookie': cookie })
    
    index_epita = 1
    branch = "branchId=%i" % index_epita
    url = "%s?%s&expand=false&forceLoad=false&reload=false" % (tree, branch)
    result = urlfetch.fetch(url, headers = { 'cookie': cookie })

    branch = "branchId=%i" % 13
    url = "%s?%s&expand=false&forceLoad=false&reload=false" % (tree, branch)
    result = urlfetch.fetch(url, headers = { 'cookie': cookie })
    
    branch = "branchId=%i" % 15
    url = "%s?%s&expand=false&forceLoad=false&reload=false" % (tree, branch)
    result = urlfetch.fetch(url, headers = { 'cookie': cookie })
    
    # Access the leaf
    select = "selectId=%i" % 18
    url = "%s?%s&forceLoad=false&scroll=0" % (tree, select)
    result = urlfetch.fetch(url, headers = { 'cookie': cookie })
    
    # Get the time bar
    url = "http://chronos.educplanet.com/ade/custom/modules/plannings/pianoWeeks.jsp"
    result = urlfetch.fetch(url, headers = { 'cookie': cookie })
    
    # Set the weeks
    bounds = "http://chronos.educplanet.com/ade/custom/modules/plannings/bounds.jsp"
    week = "week=%i" % 1
    url = "%s?%s&reset=true" % (bounds, week)
    result = urlfetch.fetch(url, headers = { 'cookie': cookie })
    # week 2
    week = "week=%i" % 2
    url = "%s?%s&reset=false" % (bounds, week)
    result = urlfetch.fetch(url, headers = { 'cookie': cookie })
    # week 3
    week = "week=%i" % 3
    url = "%s?%s&reset=false" % (bounds, week)
    result = urlfetch.fetch(url, headers = { 'cookie': cookie })
    # week 4
    week = "week=%i" % 4
    url = "%s?%s&reset=false" % (bounds, week)
    result = urlfetch.fetch(url, headers = { 'cookie': cookie })
    
    # Retrieve the content and parse it
    info = "http://chronos.educplanet.com/ade/custom/modules/plannings/info.jsp"
    url = info
    result = urlfetch.fetch(url, headers = { 'cookie': cookie })
    
    parser = infoParser()
    parser.feed(result.content)
    parser.close()
    
    # result:
    # parser.result[*][0]: start date
    # after: start hour, length, cours, groups, professor, room
    
    events = make_event_list(parser.result)
    
    template_values = {
      'status': result.status_code,
      'header': result.headers,
      'content': string.replace(result.content,'<','_'),
      'parseres': parser.result,
      'events': events,
      'stamp': dateICal(datetime.now()),
      'id': "%s;\n%s" % (DisplaySav51, session_id)
    }

    path = os.path.join(os.path.dirname(__file__), 'calendar.ics')
    self.response.out.write(template.render(path, template_values))
    
class MainPage(webapp.RequestHandler):
  def get(self):
    template_values = {
      'status' : "no status"}

    path = os.path.join(os.path.dirname(__file__), 'view.html')
    self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/gistr.ics', getICS)
                                      ],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
  