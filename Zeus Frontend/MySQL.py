import MySQLdb

class MySql:

    def __init__(self):
        self.con = MySQLdb.connect(host="localhost", user="root", passwd="bupids")
        self.cursor = self.con.cursor(MySQLdb.cursors.DictCursor)
        self.error = None
        
        #self.RunQuery("DROP DATABASE ZeusLibrary;")
        #At first run, check to ensure the database structure is created.
        if len(self.RunQuery("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'ZeusLibrary';")) == 0:
            #Create the database since it doesn't exist.
            self.RunQuery("CREATE DATABASE ZeusLibrary;")
        self.SelectDatabase("ZeusLibrary")
        if len(self.RunQuery("SHOW TABLES LIKE 'Artists';")) == 0:
            self.RunQuery("""CREATE TABLE Artists (ArtistID INT AUTO_INCREMENT,
                                                   ArtistName VARCHAR(255),
                                                   PRIMARY KEY (ArtistID)
                                                   ) ENGINE=InnoDB""")
        if len(self.RunQuery("SHOW TABLES LIKE 'Albums';")) == 0:
            self.RunQuery("""CREATE TABLE Albums (AlbumID INT AUTO_INCREMENT,
                                                  ArtistID INT,
                                                  AlbumName VARCHAR(255),
                                                  PRIMARY KEY (AlbumID, ArtistID)
                                                  ) ENGINE=InnoDB;""")
        if len(self.RunQuery("SHOW TABLES LIKE 'Tracks';")) == 0:
            self.RunQuery("""CREATE TABLE Tracks (TrackID INT AUTO_INCREMENT,
                                                  AlbumID INT,
                                                  ArtistID INT,
                                                  Filename VARCHAR(255),
                                                  TrackTitle VARCHAR(255),
                                                  TrackNumber INT,
                                                  PlayCount INT,
                                                  PRIMARY KEY (TrackID)
                                                  ) ENGINE=InnoDB;""")
        if len(self.RunQuery("SHOW TABLES LIKE 'Playlists';")) == 0:
            self.RunQuery("""CREATE TABLE Playlists (PlaylistID INT,
                                                     TrackID INT,
                                                     ItemIndex INT,
                                                     PRIMARY KEY (PlaylistID, TrackID, ItemIndex)
                                                     ) ENGINE=InnoDB;""")
        if len(self.RunQuery("SHOW TABLES LIKE 'FailedToScan';")) == 0:
            self.RunQuery("""CREATE TABLE FailedToScan (Filename VARCHAR(255),
                                                        PRIMARY KEY (Filename)
                                                        ) ENGINE=InnoDB;""")
        if len(self.RunQuery("SHOW TABLES LIKE 'FilesToScan';")) == 0:
            self.RunQuery("""CREATE TABLE FilesToScan (Filename VARCHAR(255),
                                                       PRIMARY KEY (Filename)
                                                       ) ENGINE=InnoDB;""")
        if len(self.RunQuery("SHOW TABLES LIKE 'Config';")) == 0:
            self.RunQuery("""CREATE TABLE Config (Entry VARCHAR(255),
                                                  PRIMARY KEY (Entry),
                                                  Data VARCHAR(255)
                                                  ) ENGINE=InnoDB;""")

    def SelectDatabase(self, sDatabaseName):
        try:
            self.cursor.execute("USE " + sDatabaseName)
            return True
        except MySQLdb.Error:
            self.error = MySQLdb.Error
            return False
    
    def RunQuery(self, sSQL, aVariables=()):
        try:
            self.cursor.execute(sSQL, aVariables)
            if sSQL.startswith("SELECT") or sSQL.startswith("SHOW"):
                #Return the results of a SELECT/SHOW query.
                return self.cursor.fetchall()
            elif sSQL.startswith("INSERT") or sSQL.startswith("UPDATE"):
                #These commands require commitment.
                self.con.commit()
            return True
        except MySQLdb.Error, e:
            self.error = e[1]
            print self.error
            return False