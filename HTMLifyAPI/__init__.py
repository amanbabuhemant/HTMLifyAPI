from requests import get, post
from json import loads

class ShortLink:
    def __init__(self):
        pass
    @staticmethod
    def from_json(json: dict) -> "ShortLink":
        """Create ShortLink object from json-dict"""
        self = ShortLink()
        self.id = json["id"]
        self.url = json["url"]
        self.shortcode = json["shortcode"]
        self.hits = json["hits"]
        self.href = json["href"]
        return self

class File:
    def __init__(self):
        pass
    @staticmethod
    def from_json(json: dict) -> "File":
        """Create File object from json-dict"""
        self = File()
        self.id = json["id"]
        self.owner = json["owner"]
        self.url = json["url"]
        self.type = json["type"]
        self.text = json["content"]
        hostname = self.url[:self.url.find("/", 8)]
        raw_path = hostname + "/raw/" + self.url[len(hostname)+1:]
        self.bytes = get(raw_path).content
        self.path = self.url[len(hostname)+1:]
        return self
    def delete(self) -> None:
        if htmlify := HTMLify.get_instance():
            return htmlify.delete(self.id)
        else:
            raise Exception("Create an HTMLify instance first")
class User:
    def __init__(self, username=None):
        if username:
            self.username = username

    def __str__(self):
        return self.username

    def __eq__(self, other):
        if isinstance(other, str):
            return self.username == other
        if isinstance(other, User):
            return self.username == other.username

    def profile_url(self):
        htmlify = HTMLify.get_instance()
        if not htmlify:
            raise Exception("Create an HMTLify object first")
        return htmlify.SERVER + "/" + username


class HTMLify:

    instances = []

    def __init__(self, username, api_key, SERVER_ADDRESS="http://127.0.0.1:5000"):
        self.username = username
        self.api_key = api_key
        self.SERVER = SERVER_ADDRESS
        HTMLify.instances.append(self)

    @classmethod
    def get_instance(HTMLify):
        if HTMLify.instances:
            return HTMLify.instances[-1]

    def create(self, content="", path="", ext="", as_guest=False, mode="s", visibility="p") -> File:
        """Create a file"""
        if not ext and path:
            ext = path.split(".")[-1]
        if not content:
            raise ValueError("Content is required")
        if not as_guest and not path:
            raise ValueError("Path is required for non guest files")
        if mode and not mode in set("psr"):
            raise ValueError("Mode can only have a value from 's', 'p', 'r'")
        if visibility and not visibility in set("pho"):
            raise ValueError("Visibility can only have a value from 'p', 'h', 'o'")

        data = {
            "username": self.username,
            "api-key": self.api_key,
            "path": path,
            "content": content,
            "as-guest": as_guest,
            "ext": ext,
            "mode": mode,
            "visibility": visibility
        }
        res = loads(post(self.SERVER+"/api/create", data=data).text)
        if "error" in res.keys():
            print(res["error"])
            return False
        return self.file(res["id"])

    def file(self, id:int) -> File:
        """Return File by ID"""
        file_json = loads(get(self.SERVER+"/api/file", params={"id":id}).text)
        if "error" in file_json.keys():
            return False
        file_json["id"] = id
        return File.from_json(file_json)

    def delete(self, id:int) -> None:
        """Delete a file by it's ID"""
        data = {
            "id": id,
            "api-key": self.api_key,
            "username": self.username,
        }
        res = loads(post(self.SERVER+"/api/delete", data=data).text)
        return res

    def shortlink(self, id:int=0, url:str="", shortcode:str="") -> ShortLink:
        if id:
            shortlink_json = loads(get(self.SERVER+"/api/shortlink", params={"id":id}).text)
            try:
                return ShortLink.from_json(shortlink_json)
            except:
                return None
        if url:
            shortlink_json = loads(get(self.SERVER+"/api/shortlink", params={"url":url}).text)
            try:
                return ShortLink.from_json(shortlink_json)
            except:
                return None
        if shortcode:
            shortlink_json = loads(get(self.SERVER+"/api/shortlink", params={"shortcode":shortcode}).text)
            try:
                return ShortLink.from_json(shortlink_json)
            except:
                return None
        raise ValueError("No argument passed")

    def user(username:str) -> User:
        return User(username.lower())

    def search(self, query:str) -> list[File]:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non empty string")
        res = loads(get(self.SERVER+"/api/search", params={"q":query}).text)
        for result in res["results"]:
            yield self.file(result["id"])

