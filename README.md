# HTMLifyAPI
The HTMLify API wrapper

## Instalation:

```shell
pip install git+https://GitHub.com/AmanBabuHemant/HTMLifyAPI
```

## Usage

```python
from HTMLifyAPI import HTMLify

htmlify = HTMLify("username", "api_key", "https://HTMLify.artizote.com")

# creating a file on HTMLify by API

file = htmlify.create(
    "Hello World",
    "hello.txt"
)

# this will create a file at /your_username/hello.txt which containing "Hello World"
# and also return an HTMLify File object
# you can get file url, like this:

print(file.url) # this will print file URL

# creating shortlink from url

short = htmlify.shortlink("https://example.com/your/long/long/long/long/url")

print(short.url)

```

more functnalities will add soon.

You can get your HTMLify API key from [here](https://htmlify.artizote.com/api)

