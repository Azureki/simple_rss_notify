import tomllib
import time
import xml.etree.ElementTree as ET

import httpx


processed_entries = set()
FIRST = True


class Sub:
    tg_token = ""
    tg_chat_id = ""
    interval = 300

    def __init__(self, data):
        self.name = data["name"]
        self.url = data["url"]
        # self.interval = 300

    def fetch_rss(self):
        resp = httpx.get(self.url)
        resp.raise_for_status()
        return resp.content

    def parse_rss(self, xml_content):
        fields = ["guid", "title", "link"]
        root = ET.fromstring(xml_content)
        entries = []
        for item in root.findall(".//item"):
            entries.append({field: item.find(field).text for field in fields})
        return entries

    def process_entries(self, entries):
        global FIRST
        for entry in entries:
            if (guid := f'{self.name}-{entry["guid"]}') not in processed_entries:
                processed_entries.add(guid)
                msg = f'{entry["title"]}\n{entry["link"]}'
                print(msg)
                if not FIRST:
                    self.notify(msg)

    def notify(self, data):
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        message = f"{self.name}\n{data}"
        response = httpx.post(
            url, data={"chat_id": self.tg_chat_id, "text": message}
        )

    def run(self):
        try:
            xml_content = self.fetch_rss()
        except Exception as e:
            print(e)
        else:
            entries = self.parse_rss(xml_content)
            self.process_entries(entries)
            time.sleep(self.interval)

def main():
    with open("rss_sub_info.toml", "rb") as f:
        config = tomllib.load(f)
        Sub.tg_chat_id = config["tg_chat_id"]
        Sub.tg_token = config["tg_token"]
    for subdict in config["subs"]:
        sub = Sub(subdict)
        sub.run()


if __name__ == "__main__":
    while True:
        main()
        if FIRST:
            FIRST = False
