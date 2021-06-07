# Name:Prabal Pathak

import feedparser
import string
import time
import threading
from project_util import translate_html
from tkinter import *
from datetime import datetime
import pytz


#-----------------------------------------------------------------------

#======================
# Code for retrieving and parsing
# Google and Yahoo News feeds
#======================

def process(url):
    """
    Fetches news items from the rss url and parses them.
    Returns a list of NewsStory-s.
    """
    feed = feedparser.parse(url)
    entries = feed.entries
    ret = []
    for entry in entries:
        guid = entry.guid
        title = translate_html(entry.title)
        link = entry.link
        description = translate_html(entry.description)
        pubdate = translate_html(entry.published)

        try:
            pubdate = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %Z")
            pubdate.replace(tzinfo=pytz.timezone("GMT"))
          #  pubdate = pubdate.astimezone(pytz.timezone('EST'))
          #  pubdate.replace(tzinfo=None)
        except ValueError:
            pubdate = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %z")

        newsStory = NewsStory(guid, title, description, link, pubdate)
        ret.append(newsStory)
    return ret

#======================
# Data structure design
#======================
class NewsStory(object):
    def __init__(self,guid,title,description,link,pubdate):
        self.guid = guid
        self.title = title 
        self.description = description
        self.link = link 
        self.pubdate = pubdate

    def get_guid(self):
        return self.guid

    def get_title(self):
        return self.title
    def get_description(self):
        return self.description
    def get_link(self):
        return self.link
    def get_pubdate(self):
        return self.pubdate


#======================
# Triggers
#======================
class Trigger(object):
    def evaluate(self, story):
        """
        Returns True if an alert should be generated
        for the given news item, or False otherwise.
        """
        raise NotImplementedError

def get_punc(t):
    p= string.punctuation
    for i in t:
        if i in p:
            t = t.replace(i,' ')
    spl = t.split()
    t = " ".join(spl)
    return t

class PhraseTrigger(Trigger):
    def __init__(self,phrase):
        self.phrase = phrase.lower()

class TitleTrigger(PhraseTrigger):
    def evaluate(self,story):
        text = story.get_title()
        text = text.lower()
        text = get_punc(text)
        if self.phrase in text :
            return True
        return False

    
class DescriptionTrigger(PhraseTrigger):
    def evaluate(self,story):
        text= story.get_description()
        text = text.lower()
        text = get_punc(text)
        if self.phrase in text:
            return True
        return False

# TIME TRIGGERS
class TimeTrigger(Trigger):
    def __init__(self,pubdate):
        self.pubdate = datetime.strptime(pubdate, "%d %b %Y %H:%M:%S")
        self.pubdate = self.pubdate.replace(tzinfo=pytz.timezone("UTC"))
        

class BeforeTrigger(TimeTrigger):
    def evaluate(self,story):
        publish = story.get_pubdate()
        publish = publish.replace(tzinfo=pytz.timezone("UTC"))

        if self.pubdate > publish:
            return True
        return False

class AfterTrigger(TimeTrigger):
    def evaluate(self,story):
        publish = story.get_pubdate()
        publish = publish.replace(tzinfo=pytz.timezone("UTC"))
        if self.pubdate < publish:
            return True
        return False

# COMPOSITE TRIGGERS

class NotTrigger(Trigger):
    def __init__(self,klass,*args):
        self.evaluation = klass
    def evaluate(self,story):
        if self.evaluation.evaluate(story) == True:
            return False
        return True
        
    
class AndTrigger(Trigger):
    def __init__(self,klass1,klass2):
        self.class1 = klass1
        self.class2 = klass2
    def evaluate(self,story):
        if (self.class1.evaluate(story) and self.class2.evaluate(story)) is True:
            print(True)
            return True 
        print(False)
        return False

class OrTrigger(Trigger):
    def __init__(self,klass1,klass2):
        self.class1 = klass1 
        self.class2 = klass2
    def evaluate(self,story):
        if (self.class1.evaluate(story) or self.class2.evaluate(story)) is True :
            return True 
        return False


#======================
# Filtering
#======================

def filter_stories(stories, triggerlist):
    """
    Takes in a list of NewsStory instances.

    Returns: a list of only the stories for which a trigger in triggerlist fires.
    """
    lists = []
    for i in stories:
        for triggers in triggerlist:
            if triggers.evaluate(i)==True:
                lists.append(i)
    # This is a placeholder
    return lists



#======================
# User-Specified Triggers
#======================
def read_trigger_config(filename):
    """
    filename: the name of a trigger configuration file

    Returns: a list of trigger objects specified by the trigger configuration
        file.
    """
    trigger_file = open(filename, 'r')
    lines = []
    for line in trigger_file:
        line = line.rstrip()
        if not (len(line) == 0 or line.startswith('//')):
            lines.append(line)
    hash_table ={}


    print(lines) 
    return lines



SLEEPTIME = 120 #seconds -- how often we poll

def main_thread(master):
    # to what is currently in the news
    try:
        t1 = TitleTrigger("a")
        t2 = DescriptionTrigger("a")
        t3 = DescriptionTrigger("t")
        t4 = AndTrigger(t2, t3)
        triggerlist = [t1, t2]

        # Retrieves and filters the stories from the RSS feeds
        frame = Frame(master)
        frame.pack(side=BOTTOM)
        scrollbar = Scrollbar(master)
        scrollbar.pack(side=RIGHT,fill=Y)

        t = "Google & Yahoo Top News"
        title = StringVar()
        title.set(t)
        ttl = Label(master, textvariable=title, font=("Helvetica", 18))
        ttl.pack(side=TOP)
        cont = Text(master, font=("Helvetica",14), yscrollcommand=scrollbar.set)
        cont.pack(side=BOTTOM)
        cont.tag_config("title", justify='center')
        button = Button(frame, text="Exit", command=root.destroy)
        button.pack(side=BOTTOM)
        guidShown = []
        def get_cont(newstory):
            if newstory.get_guid() not in guidShown:
                cont.insert(END, newstory.get_title()+"\n", "title")
                cont.insert(END, "\n---------------------------------------------------------------\n", "title")
                cont.insert(END, newstory.get_description())
                cont.insert(END, "\n*********************************************************************\n", "title")
                guidShown.append(newstory.get_guid())
        while True:

            print("Polling . . .", end=' ')
            # Get stories from Google's Top Stories RSS news feed
            stories = process("http://news.google.com/news?output=rss")


            list(map(get_cont,stories))
            scrollbar.config(command=cont.yview)


            print("Sleeping...")
            time.sleep(SLEEPTIME)

    except Exception as e:
        print(e)


if __name__ == '__main__':
    root = Tk()
    root.title("Some RSS parser")
    t = threading.Thread(target=main_thread, args=(root,))
    t.start()
    root.mainloop()

