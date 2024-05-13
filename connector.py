import mysql.connector

class DataBase:
    def __init__(self, host,user,password,databases):
        self.connect = mysql.connector.connect(host=host, port='3306', user=user, password=password)
        self.cur = self.connect.cursor()

        self.cur.execute("show databases")

        if ('users',) not in self.cur.fetchall():
            self.cur.execute("CREATE DATABASE users")
            self.connect.commit()

        self.connect.cmd_change_user(username=user, password=password, database=databases)

        self.cur.execute("show tables")
        tables = self.cur.fetchall()

        if ('users',) not in tables:
            self.cur.execute("CREATE TABLE users(id INT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(64) NOT NULL ,email VARCHAR(64) NOT NULL,password VARCHAR(64) NOT NULL,photo VARCHAR(64) NOT NULL DEFAULT 'avatar.png',admin VARCHAR(1) NOT NULL DEFAULT 'n')")
            self.connect.commit()
        if ('images',) not in tables:
            self.cur.execute("CREATE TABLE images(id INT AUTO_INCREMENT PRIMARY KEY,idUsers INT NOT NULL DEFAULT 0,path VARCHAR(128) NOT NULL,positive VARCHAR(128) DEFAULT '',negative VARCHAR(128) DEFAULT '')")
            self.connect.commit()

        if ('reports',) not in tables:
            self.cur.execute("CREATE TABLE reports(id INT AUTO_INCREMENT PRIMARY KEY,idUsers INT NOT NULL ,error VARCHAR(64) NOT NULL,text VARCHAR(2000) NOT NULL)")
            self.connect.commit()
 
    def get_all_user(self):
        self.cur.execute("SELECT * FROM users")
        return self.cur.fetchall()
    
    def registor(self,name,email,password):
        self.cur.execute("INSERT INTO users(name, email, password) VALUES (%s,%s,%s)", (name, email, password))
        self.connect.commit()

    def get_user_by_id(self,id):
        self.cur.execute("SELECT * FROM users WHERE id = (%s)",(id,))
        return self.cur.fetchone()
    
    def get_user_by_email(self,email):
        self.cur.execute("SELECT * FROM users WHERE email = (%s)",(email,))
        return self.cur.fetchone()
    
    def get_user_by_email(self,email):
        self.cur.execute("SELECT * FROM users WHERE email = (%s)",(email,))
        return self.cur.fetchone()
    
    def is_exists_user(self,email):
        self.cur.execute("SELECT * FROM users WHERE email = (%s)",(email,))
        return self.cur.fetchone() != None

    def update_user_by_id(self,id,username,email,password):
        self.cur.execute("UPDATE users SET name = (%s),email = (%s),password = (%s) WHERE id = (%s)",(username,email,password,id))
        self.connect.commit()

    def update_photo_by_id(self,id,photo):
        self.cur.execute("UPDATE users SET photo = (%s) WHERE id = (%s)",(photo,id))
        self.connect.commit()

    def add_report(self,idUsers,error,text):
        self.cur.execute("INSERT INTO reports(idUsers,error,text) VALUES (%s,%s,%s)", (idUsers, error, text))
        self.connect.commit()

    def add_image(self,idUsers,path,positive,negative):
        self.cur.execute("INSERT INTO images(idUsers,path,positive,negative) VALUES (%s,%s,%s,%s)", (idUsers,path, positive, negative))
        self.connect.commit()
