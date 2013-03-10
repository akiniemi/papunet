papunet
=======

Web scraper for papunet.net. Scrapes all of the sign language images from the site, and stores them into an sqlite database.

Here's the SQL for the database:

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

The script also pickles the data prior to fetching the images themselves, so that you don't have to scrape the site all the time if you want to experiment.
