from datetime import datetime
from bson import ObjectId

def convert_id(doc):
    if not doc:
        return doc
    if not isinstance(doc, dict):
        return doc
    
    doc_copy = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            if k == '_id':
                doc_copy['id'] = str(v)
            else:
                doc_copy[k] = str(v)
        elif isinstance(v, datetime):
            doc_copy[k] = v.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(v, list):
            new_list = []
            for item in v:
                if isinstance(item, dict):
                    new_list.append(convert_id(item))
                elif isinstance(item, ObjectId):
                    new_list.append(str(item))
                elif isinstance(item, datetime):
                    new_list.append(item.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    new_list.append(item)
            doc_copy[k] = new_list
        elif isinstance(v, dict):
            doc_copy[k] = convert_id(v)
        else:
            doc_copy[k] = v
            
    return doc_copy

test_doc = {
    "_id": ObjectId(),
    "client_name": "Test",
    "timestamp": datetime.now(),
    "history": [
        {"msg": "hi", "timestamp": datetime.now()},
        ObjectId()
    ]
}

res = convert_id(test_doc)
import json
print(json.dumps(res, indent=2))
