from math import floor, log10
import re
from colorthief import ColorThief
import aiohttp
from io import BytesIO

invite_re = re.compile("discord(?:app\.com|\.gg)[\/invite\/]?(?:(?!.*[Ii10OolL]).[a-zA-Z0-9]{5,6}|[a-zA-Z0-9\-]{2,32})")

anilist_query = """
query ($id: Int, $search: String) {
  Page(page: 1, perPage: 1) {
    media(id: $id, search: $search) {
      id
      idMal
      isAdult
      startDate {
        year
        month
        day
      }
      endDate {
        year
        month
        day
      }
      status
      episodes
      description
      genres
      averageScore
      coverImage {
        extraLarge
        color
      }
      title {
        romaji
        english
        native
      }
    }
  }
}"""

def millify(n):
    millnames = ["", "k", "M", " Billion", " Trillion"]
    n = float(n)
    millidx = max(0, min(len(millnames) - 1, int(floor(0 if n == 0 else log10(abs(n)) / 3))))
    return "{:.0f}{}".format(n / 10 ** (3 * millidx), millnames[millidx])

def clean_text(text: str):
    return invite_re.sub("[INVITE]", text.replace("@", "@\u200B"))

async def get_dominant_color(bot, url, key, expire: int):
    data = await bot.redis.get("color:{}".format(key))
    if data is None:
        async with aiohttp.ClientSession() as cs:
            async with cs.get(url) as res:
                image = await res.read()
                r, g, b = ColorThief(BytesIO(image)).get_color()
                color = int(format(r << 16 | g << 8 | b, "06" + "x"), 16)
        await bot.redis.set("color:{}".format(key), color, expire=expire)
        return color
    return int(data)

def to_emoji(c):
    base = 0x1f1e6
    return chr(base + c)

def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])

    # remove `foo`
    return content.strip('` \n')

def get_syntax_error(e):
    if e.text is None:
        return f'```py\n{e.__class__.__name__}: {e}\n```'
    return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'
