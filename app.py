from datetime import datetime
import re
from flask import Flask, request, jsonify
import certifi as certifi
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask_cors import CORS
# Create Flask app
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:5500", "https://barleviatias.github.io/"]}}, allow_headers=["Content-Type", "X-Search-IP"])
# global variables
SCRIPT_FILE_PATH = "kupa_rashit_script.txt"
CONTEXT_LEN = 20
MAX_MATCHES = 30
BATCH_SIZE = 300

# mongo vars
MONGO_URI = "mongodb+srv://barlevi_atias:Bb8159075@atlascluster.8h1liyd.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = 'test'
COLLECTION_NAME = 'kupa'

# Counter variable
call_counter = 0


# @app.after_request
# def add_cors_headers(response):
#     # response.headers['Access-Control-Allow-Origin'] = 'https://barleviatias.github.io'
#     response.headers['Access-Control-Allow-Origin'] = 'http://127.0.0.1:5500'
#     return response



CONTEXT_LEN = 50

def search_string_in_episodes(search_string, db_name, collection_name, batch_size=100, max_matches=10):
    print(search_string)
    global call_counter
    call_counter += 1
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())

    db = client[db_name]
    collection = db[collection_name]

    cursor = collection.find().batch_size(batch_size)
    pattern = search_string.split(" ")
    pattern = ",?\\s?".join(pattern) + ",?\\s?"
    matches = []
    episode_names = set()  # Track episode names to remove duplicates
    for doc in cursor:
        local_matches = re.finditer(pattern, doc["script"])
        for match in local_matches:
            start, end = match.span()
            episode_name = doc["episode_name"]
            if episode_name not in episode_names:  # Check for duplicate episode names
                episode_names.add(episode_name)
                context_start = start
                while context_start > 0 and doc["script"][context_start - 1] != '\n':
                    context_start -= 1
                context_end = min(end + CONTEXT_LEN, len(doc["script"]))
                context = doc["script"][context_start:context_end].strip()
                matches.append({
                    "episode_name": episode_name,
                    "episode_number": doc["episode_number"],
                    "season_number": doc["season_number"],
                    "url": doc["youtube_url"],
                    "context": context,
                })
                if len(matches) >= max_matches:
                    break
        if len(matches) >= max_matches:
            break

    # client.close()
    print(len(matches))
    return matches

@app.route('/search', methods=['GET'])
def search_episodes():
    search_string = request.args.get('q')
    ip_address = request.headers.get('X-Search-IP')
    user_agent = request.user_agent.string
    # request_url = request.url
    # request_method = request.method
    timestamp = datetime.now()

    if not search_string:
        return jsonify({'error': 'No search query provided.'}), 400

    results = search_string_in_episodes(search_string, DB_NAME, COLLECTION_NAME, batch_size=BATCH_SIZE,
                                        max_matches=MAX_MATCHES)
    search_data = {
        "search_term": search_string,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "timestamp": timestamp,
        "num_of_results":len(results)
    }
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
    db = client[DB_NAME]
    collection = db["log"]
    collection.insert_one(search_data)
    client.close()
    return jsonify(results)
@app.route('/counter', methods=['GET'])
def get_call_counter():
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
    db = client[DB_NAME]
    collection = db["log"]
    # Get the count of documents in the collection
    document_count = collection.count_documents({})


    return jsonify({'counter': document_count})


if __name__ == '__main__':
    # if not collection_exists(DB_NAME, COLLECTION_NAME):
    #     # read and parse file
    #     tv_show_data = parse_file(SCRIPT_FILE_PATH)
    #
    #     # Save tv_show_data to MongoDB
    #     save_to_mongo(tv_show_data, DB_NAME, COLLECTION_NAME)

    app.run()
