#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
#   Viito -- an image dictionary for sign language
#
#   Copyright (C) 2013  Aki Niemi <aki.niemi@iki.fi>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# This script web scrapes the papunet.net site for sign images and
# metadata
#

from BeautifulSoup import BeautifulSoup
import urllib2
import sqlite3
import re
import pickle

root = u'http://papunet.net/materiaalia/kuvapankki/'
opener = None

# The following regexps are meant to parse the image name and author
# information from an 'a' tag such as the one below:
#
# <a href="http://papunet.net/sites/papunet.net/files/kuvapankki/anna_minulle2.jpg"
#   title="anna minulle (kuva: Elina Vanninen)"
#   rel="lightbox[kuvapankkihaku][<strong>A</strong><br><em>Kuva:</em> Kalevi Puistolinna<br><em>Lähde: </em>Papunetin kuvapankki]"
#   class="lightbox-processed nounderline">
#   <img typeof="foaf:Image"
#     src="http://papunet.net/sites/papunet.net/files/styles/thumbnail/public/kuvapankki/anna_minulle2.jpg"
#     width="100" height="100">
# </a>
word_re = re.compile('(?<=<strong>)[\w -]+', re.U)
author_re = re.compile('(?<=Kuva:</em>)[\w ]+', re.U)

def populate_database(data):
    """Write the data into an sqlite3 database. The 'images.db' file
    has to exist, and have the proper tables set up. Here is the
    required sql:

    DROP TABLE IF EXISTS Author;
    DROP TABLE IF EXISTS Topic;
    DROP TABLE IF EXISTS Word;
    DROP TABLE IF EXISTS Sign;

    CREATE TABLE Author (
       Id INTEGER PRIMARY KEY AUTOINCREMENT,
       Name TEXT UNIQUE
    );
    CREATE TABLE Topic (
       Id INTEGER PRIMARY KEY AUTOINCREMENT,
       Name TEXT UNIQUE
    );
    CREATE TABLE Word (
       Id INTEGER PRIMARY KEY AUTOINCREMENT,
       Name TEXT UNIQUE
    );
    CREATE TABLE Sign (
       Id INTEGER PRIMARY KEY AUTOINCREMENT,
       Data BLOB,
       AuthorId INTEGER REFERENCES Author,
       TopicId INTEGER REFERENCES Topic,
       WordId INTEGER REFERENCES Word
    );

    The command line for creating a database file is:

    $ sqlite3 images.db < mkimages.sql

    """

    conn = sqlite3.connect('images.db')
    cursor = conn.cursor()

    for key, values in data.iteritems():
        cursor.execute("INSERT OR IGNORE INTO Topic(Name) VALUES(?)", (key,))
        cursor.execute("SELECT Id FROM Topic WHERE Name=?", (key,))
        topic_id = cursor.fetchone()[0]

        for (word, author, url) in values:
            cursor.execute("INSERT OR IGNORE INTO Author(Name) VALUES(?)", (author,))
            cursor.execute("INSERT OR IGNORE INTO Word(Name) VALUES(?)", (word,))

            cursor.execute("SELECT Id FROM Author WHERE Name=?", (author,))
            author_id = cursor.fetchone()[0]

            cursor.execute("SELECT Id FROM Word WHERE Name=?", (word,))
            word_id = cursor.fetchone()[0]

            img = opener.open(url).read()
            cursor.execute("INSERT OR IGNORE INTO Sign(Data, AuthorId, TopicId, WordId)"
                           "VALUES(?, ?, ?, ?)",
                           (sqlite3.Binary(img), author_id, topic_id, word_id))
    conn.commit()
    conn.close()

def get_imgurl(li):
    """Get the image URL"""
    return li.a.get('href')

def get_author(li):
    """Get image author"""
    return author_re.search(li.a.get('rel')).group().strip()

def get_word(li):
    """Get the word name"""
    return word_re.search(li.a.get('rel')).group().strip()

def extract_images(link, no):
    """Extract images from the image-list <ul> element. Recurse into
    additional pages of images, if such exist."""

    if no > 0:
        url = link + u'&page=' + str(no)
    else:
        url = link

    page = BeautifulSoup(opener.open(url).read())
    root = page.find('ul', attrs = { 'class' : 'image-list' })

    if root is None:
        return []

    return [ (get_word(li), get_author(li), get_imgurl(li)) for li in root.findAll('li') ] + extract_images(link, no + 1)

def get_title(li):
    """Make sure we always use the top-level topic name"""

    if ('class', 'expanded') in li.parent.parent.attrs:
        return li.parent.parent.a.get('title')
    else:
        return li.a.get('title')

def get_url(li):
    """Helper to get the absolute URL for the topic, including form
    data that filters out all but the sign images"""

    return u'http://papunet.net' + li.a.get('href') + u'?field_stockimage_type_tid[181]=181'

def is_leaf(li):
    """Determine if this page is a leaf node"""
    return 'leaf' in li.get('class')

def scrape():
    """Find the <div> for the topics menu, and scrape each page that they link to"""

    begin = BeautifulSoup(opener.open(root).read())
    items = begin.find('div', id='block-menu-menu-kuvapankin-luokat').div.ul.findAll('li')
    pages = [ (get_title(li), get_url(li)) for li in items if is_leaf(li) ]

    data = {}

    for (title, link) in pages:
        images = extract_images(link, 0)
        if len(images) == 0:
            continue

        if title in data.keys():
            print "appending to %s" % (title,)
            data[title] += images
        else:
            data[title] = images

    return data

if __name__ == "__main__":
    opener = urllib2.build_opener()

    try:
        data = pickle.load(open('images.pickle', 'r'))
    except IOError:
        data = scrape()
        pickle.dump(data, open('images.pickle', 'w'))

    l = 0
    for v in data.values():
        l += len(v)

    print "%d topics, %d images" % (len(data.keys()),l)

    populate_database(data)
