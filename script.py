import json
from os import listdir
from lxml import etree


DIR = 'xml/026f7078-c203-4452-a072-5289f067005c'
ORGANIZATION = 3

docs = []

for year in listdir(DIR):
    for month in listdir(f'{DIR}/{year}'):
        for file in listdir(f'{DIR}/{year}/{month}'):

            json_document = {
                'model': 'documentolog.commonmail',
                'fields': {
                    'organization': ORGANIZATION,
                }
            }

            root = etree.parse(rf'{DIR}/{year}/{month}/{file}').getroot()

            attachments = root.xpath("//itemslist[@type='file'][@title='Вложения']/item")
            for f in attachments:
                print(f.text)

            if len(root.xpath("//document[@id]")) > 0:
                json_document['fields']['uid'] = root.xpath("//document[@id]")[0].values()[0]

            body = {}
            for item in root.xpath("//item[@name][@type]"):
                if item.text:
                    body[item.values()[0]] = {
                        "verbose": item.get('title'),
                        "value": item.text,
                        "type": item.get('type')
                    }

            json_document['fields']['body'] = body

            docs.append(json_document)

            #break
with open(f'dump.json', 'w+', encoding='utf8') as outfile:
    json.dump(docs, outfile, ensure_ascii=False)
