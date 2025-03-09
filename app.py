from flask import Flask, request, jsonify, render_template
from transformers import AutoTokenizer, AutoModelForCausalLM
from pymongo import MongoClient

# Initialize Flask app
app = Flask(__name__)

# Load distilgpt2 model and tokenizer
MODEL_NAME = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

# Connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client.ubayog_db
    assets_collection = db.assets
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    assets_collection = None  # Handle cases where DB connection fails

# Root Route
@app.route("/", methods=["GET"])
def home():
    return render_template('index.html')

# Chatbot Route with Unique Endpoint
@app.route("/chat", methods=["POST"], endpoint='chatbot')
def chat():
    user_input = request.json.get("message")
    
    if not user_input:
        return jsonify({"error": "No message provided"}), 400
    
    # Define a prompt style for distilgpt2
    prompt_style = f"""
    You are an AI assistant. Please respond to the user's message.

    User: {user_input}
    Assistant:
    """
    
    try:
        # Tokenize input and generate response
        inputs = tokenizer(prompt_style, return_tensors="pt", truncation=True)
        outputs = model.generate(
            input_ids=inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens=150,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        # Decode and return response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Check if the response contains the expected format
        lines = response.splitlines()
        assistant_response = ""
        for line in lines:
            if line.startswith("Assistant:"):
                assistant_response = line.replace("Assistant:", "").strip()
                break
        
        if not assistant_response:
            return jsonify({"error": "Failed to generate response"}), 500
        
        return jsonify({"response": assistant_response})
    
    except Exception as e:
        return jsonify({"error": f"Failed to process request: {e}"}), 500

# Search Assets Route with Unique Endpoint
@app.route("/search", methods=["POST"], endpoint='search_assets')
def search_assets():
    query = request.json.get("query")
    
    if not assets_collection:
        return jsonify({"error": "Database connection unavailable"}), 500
    
    try:
        # Search assets in MongoDB using regex for partial matches
        results = assets_collection.find({"name": {"$regex": query, "$options": "i"}})
        
        # Format results as JSON
        assets = [{"name": r["name"], "description": r["description"]} for r in results]
        return jsonify(assets)
    
    except Exception as e:
        return jsonify({"error": f"Failed to search assets: {e}"}), 500

# List Asset Route with Unique Endpoint
@app.route("/list", methods=["POST"], endpoint='list_asset')
def list_asset():
    asset_data = request.json  # Expecting {"name": "Asset Name", "description": "Asset Description"}
    
    if not assets_collection:
        return jsonify({"error": "Database connection unavailable"}), 500
    
    try:
        # Insert asset into MongoDB
        assets_collection.insert_one(asset_data)
        return jsonify({"message": "Asset listed successfully!"})
    
    except Exception as e:
        return jsonify({"error": f"Failed to list asset: {e}"}), 500

# Start Flask server
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
