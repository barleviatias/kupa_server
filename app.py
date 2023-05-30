import re
from flask import Flask, request, jsonify
import certifi as certifi
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
# Create Flask app
app = Flask(__name__)

# global variables
SCRIPT_FILE_PATH = "kupa_rashit_script.txt"
CONTEXT_LEN = 20
MAX_MATCHES = 30
BATCH_SIZE = 300

# mongo vars
MONGO_URI = "mongodb+srv://barlevi_atias:Bb8159075@atlascluster.8h1liyd.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = 'test'
COLLECTION_NAME = 'kupa'


# def parse_file(filename):
#     # Parsing logic...
#
#
# def save_to_mongo(data, db_name, collection_name):
#     # Saving to MongoDB logic...
#
#
# def collection_exists(db_name, collection_name):
#     # Collection check logic...
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://127.0.0.1:5500'
    return response

def search_string_in_episodes(search_string, db_name, collection_name, batch_size=100, max_matches=10):
    print(search_string)
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())

    db = client[db_name]
    collection = db[collection_name]

    cursor = collection.find().batch_size(batch_size)
    pattern = search_string.split(" ")
    pattern = ",?\\s?".join(pattern) + ",?\\s?"
    matches = []
    for doc in cursor:
        local_matches = re.finditer(pattern, doc["script"])
        spans = [match.span() for match in local_matches]
        for start, end in spans:
            matches.append({
                "episode_name": doc["episode_name"],
                "episode_number": doc["episode_number"],
                "season_number": doc["season_number"],
                "url": doc["youtube_url"],
                "context": doc["script"][max(start - CONTEXT_LEN, 0):min(end + CONTEXT_LEN, len(doc["script"]))],
            })
            if len(matches) >= max_matches:
                break
        if len(matches) >= max_matches:
            break

    client.close()
    print(matches)
    return matches


@app.route('/search', methods=['GET'])
def search_episodes():
    search_string = request.args.get('q')

    if not search_string:
        return jsonify({'error': 'No search query provided.'}), 400

    results = search_string_in_episodes(search_string, DB_NAME, COLLECTION_NAME, batch_size=BATCH_SIZE,
                                        max_matches=MAX_MATCHES)

    return jsonify(results)


if __name__ == '__main__':
    # if not collection_exists(DB_NAME, COLLECTION_NAME):
    #     # read and parse file
    #     tv_show_data = parse_file(SCRIPT_FILE_PATH)
    #
    #     # Save tv_show_data to MongoDB
    #     save_to_mongo(tv_show_data, DB_NAME, COLLECTION_NAME)

    app.run()
