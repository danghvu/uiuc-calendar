import requests as rq
import re, getpass
from HTMLParser import HTMLParser

username = raw_input('NetID: ')
password = getpass.getpass()

def connect_get_info(u,p):
    sess = rq.Session()
    get_cookie_url = 'https://my.illinois.edu/uPortal/render.userLayoutRootNode.uP'

    r = sess.get(get_cookie_url)

    login_url = 'https://my.illinois.edu/uPortal/Login'

    r = sess.post(login_url, data = {'action':'login', 'userName':u, 'password':p, 'Login':'Sign+In'},
            headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36'}
            )
    acac_url = 'https://my.illinois.edu/uPortal/render.userLayoutRootNode.uP?uP_root=root&uP_sparam=activeTabTag&activeTabTag=Academics'
    r = sess.get(acac_url)
    return r.content

data = connect_get_info(username, password)

# lazy way to get table
rex = re.compile(b'^(\<table(?!\<table).+\<\/table\>)$',re.MULTILINE|re.DOTALL)
m = re.findall(rex, data)

for g in m:
    if 'class' in str(g) and 'Monday' in str(g): #need more generic
        result = str(g.replace(b'\n',b''))

if not result:
    print "Failed to load user data"
    sys.exit(-1)

print "Data obtained, now converting.."

class ScheHTMLParser(HTMLParser):
    __start_r = False
    __start_c = False
    __data = ''
    this_table = []
    __row = []

    def handle_starttag(self, tag, attrs):
        if (tag == 'tr'):
            self.__start_r = True
        elif (tag == 'td'):
            self.__start_c = True
    def handle_endtag(self, tag):
        if (tag == 'tr'):
            self.__start_r = False
            if self.__row: self.this_table += [self.__row]
            self.__row = []
        elif (tag == 'td'):
            __start_c = False
            if self.__data: self.__row += [self.__data]
            self.__data = ''
    def handle_data(self, data):
        if (self.__start_r and self.__start_c):
            self.__data += data


def gettime(s):
    s = s.split()
    s2 = s[0].split(':')
    s2[0] = int(s2[0])
    s2[1] = int(s2[1])
    if s[1] == 'PM' and s2[0] < 12:
        s2[0] += 12
    return s2

parser = ScheHTMLParser()
parser.feed(result)

from icalendar import Calendar, Event
from datetime import date, timedelta, datetime
import pytz, time

cal = Calendar()
cal.add('prodid', '-//w00d//UIUC Calendar prod//')
cal.add('version', '2.0')

today = date.today()
daymap = ['M','T','W','R','F']
daymap_sd = ['MO','TU','WE','TH','FR']
lastmonday = today - timedelta(days=today.weekday())

for row in parser.this_table:
    print row
    day_study = row[2].split()
    date = lastmonday + timedelta(daymap.index(day_study[0]))
    time_start = gettime(row[3])
    time_end = gettime(row[4])
    byday = ([daymap_sd[daymap.index(d)] for d in day_study])
    event = Event()
    event.add('summary',row[0])
    event.add('description',row[1])
    event.add('location',row[5])
    event.add('dtstart', datetime(date.year,date.month,date.day,time_start[0],time_start[1],0,tzinfo=pytz.timezone('America/Chicago')))
    event.add('dtend', datetime(date.year,date.month,date.day,time_end[0],time_end[1],0,tzinfo=pytz.timezone('America/Chicago')))
    event.add('dtstamp', datetime.utcnow())
    event['uid'] = '%f/%s@uiuc.edu' % (time.time(), username)
    event.add('rrule', {'freq': 'weekly', 'count':4*3*len(byday), 'byday':byday}) #3 months
    cal.add_component(event)

f = open('uiuc-calendar.ics', 'w')
f.write(cal.to_ical())
f.close()

print "Done, check uiuc-calendar.ics"


