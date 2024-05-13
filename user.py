from connector import DataBase

class UserLogin:
    def fromDB(self, user_id, db : DataBase):
        self.user = db.get_user_by_id(user_id)
        return self
 
    def create(self, user):
        self.user = user
        return self
 
    def is_authenticated(self):
        return True
 
    def is_active(self):
        return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        if self.user == None:
            return None
        return str(self.user[0])
