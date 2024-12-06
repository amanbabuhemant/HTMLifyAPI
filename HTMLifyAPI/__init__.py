from requests import get, post
from json import loads

class ShortLink:
    def __init__(self):
        pass
    def __repr__(self):
        return "<ShortLink to '" + str(self) + "' >"
    def __str__(self):
        if self.href.startswith("http://") or self.href.startswith("https://"):
            return self.href
        htmlify = HTMLify.get_instance()
        if self.href.startswith("/"):
            return htmlify.SERVER + self.href
        return htmlify.SERVER + "/r/" + self.href
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
        self.path = self.url[len(hostname):]
        return self

    def delete(self) -> None:
        """Delete self content"""
        if htmlify := HTMLify.get_instance():
            return htmlify.delete(self.id)
        else:
            raise Exception("Create an HTMLify instance first")

    def update_content(self, content: str):
        """Update self content"""
        if self.type != "text":
            raise Exception("Can't edit non-text file")
        if htmlify := HTMLify.get_instance():
            if htmlify.edit(self.id, content):
                self.text = str(content)
                self.bytes = self.text.encode()
                return True
        raise Exception("Create an HTMLify instance first")

    def shortlink(self) -> ShortLink:
        """Return self shorten url of self"""
        htmlify = HTMLify.get_instance()
        return htmlify.shortlink(url=self.path)

    def size(self) -> int:
        """Return file size in bytes"""
        return len(self.bytes)

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
        return htmlify.SERVER + "/" + self.username

class Notification:
    def __init__(self):
        pass
    @staticmethod
    def from_json(json):
        self = Notification()
        self.id = json["id"]
        self.user = json["user"]
        self.content = json["content"]
        self.href = json["href"]
        self.seen = json["seen"]
        return self

    def mark_seen(self):
        htmlify = HTMLify.get_instance()
        data = {
            "username": htmlify.username,
            "api-key": htmlify.api_key,
            "markseen": self.id,
        }
        res = loads(post(htmlify.SERVER+"/api/notifications", data=data).text)
        return not res["error"]

class Comment:
    def __init__(self):
        pass
    @staticmethod
    def from_json(json):
        self = Comment()
        self.id = json["id"]
        self.file = json["file"]
        self.content = json["content"]
        self.author = json["author"]
        return self

class Process:
    def __init__(self, pid):
        self.pid = pid
        self.full_stdout = ""
        self.full_stderr = ""
        self.full_stdin = ""

    def communicate(self, input=""):
        htmlify = HTMLify.get_instance()
        data = {
            "input": input
        }
        res = htmlify.proc_communicate(self.pid, input)
        if "pid" in res:
            self.full_stdout += res["stdout"]
            self.full_stderr += res["stderr"]
        self.full_stdin += input
        return res


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
        raise Exception("Create an HTMLify instance first")

    def create(self, path="", content="", ext="", as_guest=False, mode="s", visibility="p") -> File:
        """Create a new file"""
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

    def edit(self, id: int, content: str):
        """Update a file's content"""
        try:
            id = int(id)
            content = str(content)
        except:
            raise ValueError("Please provide valid arguments")

        data = {
            "id": id,
            "username": self.username,
            "api-key": self.api_key,
            "content": content
        }
        res = loads(post(self.SERVER+"/api/edit", data=data).text)
        if "success" in res.keys():
            return True
        return False

    def update(self, *args, **kargs):
        return self.edit(*args, **kargs)

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

    def notification(self, id=0) -> Notification | list[Notification]:
        """Return Notifications"""
        data = {
            "username": self.username,
            "api-key": self.api_key,
            "id": id,
        }
        res = loads(post(self.SERVER+"/api/notifications", data=data).text)
        if "notifications" in res.keys():
            for n in res["notifications"]:
                print(n)
                yield Notification.from_json(n)
        else:
            return Notification.from_json(res)

    def get_comment(self, id: int) -> "Comment":
        """Get comment by ID"""
        data = {
            "username": self.username,
            "api-key": self.api_key,
            "id": id,
        }
        res = post(self.SERVER+"/api/comment", data=data).json()
        print(res)
        if res["error"]:
            return None
        return Comment.from_json(res)

    def post_comment(self, file, content):
        """
        Post a comment on a file
        Args:
            file (int, File): File's id or File object
            content (str): Content
        """
        if isinstance(file, File):
            id = file.id
        elif isinstance(file, int):
            id = file
        else:
            raise ValueError("argument file can only be int or File type not " + str(type(file)))
        content = str(content)
        if not content:
            raise ValueError("Comment content can't be empty")
        if len(content) > 1024:
            raise ValueError("Conett length should be under 1024 charecters")
        data = {
            "username": self.username,
            "api-key": self.api_key,
            "file": id,
            "content": content,
        }
        res = loads(post(self.SERVER + "/api/comment", data=data).text)
        return not res["error"]

    def execute(self, code, executor) -> Process:
        data = {
            "code": code,
            "executor": executor
        }
        res = post(self.SERVER + "/api/exec", data=data).json()
        if res["error"]:
            raise res["message"]

        proc = Process(res["pid"])
        return proc

    def proc_communicate(self, pid, input="") -> dict:
        data = {
            "input": input
        }
        res = post(self.SERVER + f"/proc/{pid}/communicate", data=data).json()
        return res


