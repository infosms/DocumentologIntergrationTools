from sirius.integrations.documentolog.models import DocumentologMail

docs = DocumentologMail.objects.filter(
    view_name='08b21639-77bd-4a2c-af7c-529049b70329',
    created_at__year=2021
)
for n_d, d in enumerate(docs):
    print(n_d)
    links = []
    documents = [v for v in list(d.body.values()) if isinstance(v, dict) and v['type'] == 'document']
    for n_doc, doc in enumerate(documents):
        if 'value' not in doc.keys():
            continue
        for n_val, val in enumerate(doc.get('value')):
            try:
                uid = val.get('uid').split(':')[1]
                documentolog_mail = DocumentologMail.objects.filter(
                    uid=uid
                ).first()
                if documentolog_mail:
                    documentolog_mail.body[f'execution_card_{n_doc}_{n_val}'] = {
                        'type': 'document',
                        'value': [
                            {
                                'title': 'Карточка исполнения',
                                'uid': val.get('uid')
                            }
                        ],
                        'verbose': ' '
                    }
                    documentolog_mail.save()
            except Exception as e:
                print(e)
                continue