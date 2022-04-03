# -*- coding: utf-8 -*-
import datetime
import json
import warnings
from os import listdir
from threading import Thread
import requests
from lxml import etree
import config as cfg

# DIR = '/home/khandosaly/job/DocumentologIntegrationTools/xml/026f7078-c203-4452-a072-5289f067005c'
DIR = cfg.DIR
DAYS = [
    str(a) + str(b) if a > 10 and b > 10 \
    else '0' + str(a) + str(b) if a < 10 and b > 9 \
    else str(a) + '0' + str(b) if a > 9 and b < 10 \
    else '0' + str(a) + '0' + str(b) if a < 10 and b <10 \
    else str(a) + str(b)
    for a in range(1, 13) for b in range(1, 32)
]


def get_access_hash():
    payload = json.dumps({
        'email': cfg.AUTH_EMAIL,
        'username': cfg.AUTH_USERNAME,
        'password': cfg.AUTH_PASSWORD
    })
    headers = {
        'Content-Type': 'application/json'
    }
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        response = requests.request('POST', cfg.AUTH_URL, headers=headers, data=payload, verify=False)

    if response.status_code == 200:
        return json.loads(response.text).get('access')
    else:
        print('[ERROR] Can not get access hash!')
        raise SystemExit(0)


def upload_file(access_hash, obj_name, file_id):
    files = None
    for year in range(2012, 2022):
        for dir_day in DAYS:
            try:
                files = {
                    'files':
                        (
                            obj_name.rsplit('(', 1)[0].strip() if 'Б)' in obj_name else obj_name.strip(),
                            open(cfg.FILES_LOCATION + str(year) + '/' + dir_day + '/' + file_id, 'rb')
                        )
                }
            except (FileNotFoundError, OSError):
                pass

    if not files:
        return None

    headers = {
        'Authorization': f'Bearer {access_hash}'
    }
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        response = requests.request('POST', cfg.FILE_UPLOAD_URL, headers=headers, files=files, verify=False)

    if response.status_code == 201:
        return json.loads(response.text)[0].get('id')
    else:
        print('[ERROR] Upload request failed, bad format')
        print(files, response.text)
        return None


def get_doc_dict(file_path, access_hash):
    # Basic dict
    json_document = {
        'model': 'documentolog.documentologmail',
        'fields': {
            'organization': cfg.ORGANIZATION,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S%Z'),
            'view_name': DIR.split('/')[-1],
            'files': []
        }
    }

    root = etree.parse(rf'{file_path}').getroot()

    # Get main document id
    if len(root.xpath("//document[@id]")) > 0:
        json_document['fields']['uid'] = root.xpath("//document[@id]")[0].values()[0]

    # Get attachments
    attachments = root.xpath("//itemslist[@type='file']/item")
    for f in attachments:
        uploaded_file_id = upload_file(access_hash, f.text, f.get('id'))
        if uploaded_file_id:
            json_document['fields']['files'].append(uploaded_file_id)

    body = {}

    #
    for item in root.xpath("//item[@name][@type]"):
        if item.text:
            val = None
            if item.get('type') in ['string', 'text', 'date']:
                val = item.text.strip()
            elif item.get('type') in ['timestamp']:
                # 2021-10-19 10:48:00
                # 2013-03-18T13:19:37+00:00
                val = item.text.strip().replace(' ', 'T') + '+00:00'
                if item.get('name') == 'created_at':
                    json_document['fields']['created_at'] = val
            if val:
                body[item.values()[0]] = {
                    "verbose": item.get('title'),
                    "value": val,
                    "type": item.get('type')
                }

    # enumeration, boolean, reference
    xpath_types = ' or '.join([f"@type='{x}'" for x in ['enumeration', 'boolean', 'reference']])
    for item in root.xpath(f"//itemslist[@name][{xpath_types}]"):
        list_items = item.xpath(f"./item")
        if len(list_items) > 0:
            body[item.values()[0]] = {
                "verbose": item.get('title'),
                "value": list_items[0].text,
                "type": item.get('type')
            }

    # structures
    for item in root.xpath(f"//itemslist[@name][@type='structure']"):
        list_items = item.xpath(f"./item")
        if len(list_items) > 0:
            body[item.values()[0]] = {
                "verbose": item.get('title'),
                "value": [
                    x.text for x in list_items
                ],
                "type": item.get('type')
            }

    # document links
    for item in root.xpath(f"//itemslist[@name][@type='document']"):
        list_items = item.xpath(f"./item")
        if len(list_items) > 0:
            body[item.values()[0]] = {
                "verbose": item.get('title'),
                "value": [
                    {
                        'title': x.text,
                        'uid': x.get('id')
                    } for x in list_items
                ],
                "type": item.get('type')
            }

    # Match list
    for item in root.xpath(f"//itemslist[@name][@type='table']"):
        rows = item.xpath(f"./itemslist")
        if len(rows) > 0:
            body[item.values()[0]] = {
                "verbose": item.get('title'),
                "value": [
                    {
                        'row': x.get('row'),
                        'approvers': [
                            y.text for y in x.xpath(
                                f"./itemslist[@type='structure']/item")
                        ]
                    } for x in rows
                ],
                "type": item.get('type')
            }

    # Decision List
    body['decision_list'] = []
    for decision in root.xpath(f"//decision"):
        decision_dict = {
            'verbose': decision.get('title'),
            'files': []
        }

        decision_body = {}
        # Common items
        for item in decision.xpath(f"./item"):
            if item.text:
                val = None
                if item.get('name') in ['tstamp']:
                    val = item.text.strip().replace(' ', 'T') + '+00:00'
                else:
                    val = item.text.strip()
                if val:
                    decision_body[item.get('name')] = val
        # Lists
        for itemslist in decision.xpath(f"./itemslist"):
            items = itemslist.xpath(f"./item")
            if len(items) > 0:
                decision_body[itemslist.get('name')] = [x.text for x in items]
        # Files
        attachments = decision.xpath("./itemslist[@name='files']/item")
        for f in attachments:
            uploaded_file_id = upload_file(access_hash, f.text, f.get('id'))
            if uploaded_file_id:
                decision_dict['files'].append(uploaded_file_id)

        decision_dict['body'] = decision_body

        body['decision_list'].append(decision_dict)

    json_document['fields']['body'] = body

    return json_document


def upload_month(access_hash, year, month, docs):
    doc_num = 1
    errors = 0
    for file in listdir(f'{DIR}/{year}/{month}'):
        # Stoppers
        # if doc_num >= 5:
        #     break

        file_path = f'{DIR}/{year}/{month}/{file}'

        try:
            docs.append(get_doc_dict(file_path, access_hash))
        except Exception as e:
            errors += 1

        print(f'({month}-{year}): {doc_num}/{len(listdir(f"{DIR}/{year}/{month}"))} [{errors} errors]')
        doc_num += 1


def main():
    threads = []
    docs = []
    access_hash = get_access_hash()
    try:
        for year in listdir(DIR):
            if year != "2021":
                continue
            for month in listdir(f'{DIR}/{year}'):
                th = Thread(target=upload_month, args=(access_hash, year, month, docs))
                threads.append(th)
                th.start()
    except KeyboardInterrupt:
        pass

    for th in threads:
        th.join()

    with open(f'dump.json', 'w+', encoding='utf8') as outfile:
        json.dump(docs, outfile, ensure_ascii=False)


if __name__ == '__main__':
    main()
