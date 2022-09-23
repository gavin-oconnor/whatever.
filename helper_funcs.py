import difflib


class User_Obj:
	def __init__(self,id,username,followers):
		self.id = id
		self.username = username
		self.followers = followers

def similarity(word, pattern):
    return difflib.SequenceMatcher(a=word.lower(), b=pattern.lower()).ratio()