import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

def search_faces_by_id(collection, face_id):
    logging.info(f"Searching for images with face ID: {face_id}")
    result = collection.find_one({"face_id": int(face_id)})
    if result:
        logging.info(f"Found entry for face ID: {face_id}")
        return result
    else:
        logging.info(f"No entry found for face ID: {face_id}")
        return None

def get_all_face_ids(collection):
    logging.info("Retrieving all face IDs from the database.")
    return [doc['face_id'] for doc in collection.find({}, {"face_id": 1})]