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

# Chatbot Route
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    
    # Define a prompt style for distilgpt2
    prompt_style = f"""
    You are an AI assistant powering the chatbot for Ubayog.com, a platform for searching, listing, and renting various assets. Your primary role is to create a seamless conversational experience that helps users find assets, list their own items, and navigate the platform efficiently.

## Core Capabilities

1. SEARCH FUNCTIONALITY:
   - Understand natural language queries about available assets
   - Interpret search parameters including asset type, price range, location, and availability
   - Respond with relevant, organized search results
   - Help users refine their search when needed
   - Suggest similar or alternative options when exact matches aren't available

2. LISTING ASSISTANCE:
   - Guide users through the asset listing process step-by-step
   - Request essential information (asset details, specifications, pricing, availability)
   - Provide suggestions for optimal pricing based on similar listings
   - Confirm listing details before submission
   - Explain the listing review process and expected timeline

3. PLATFORM INFORMATION:
   - Answer FAQs about Ubayog's services, fees, and policies
   - Explain the rewards program and its benefits
   - Provide guidance on platform usage
   - Direct users to relevant resources when appropriate

## Conversation Style

- Be helpful, friendly, and concise
- Use natural conversational language
- Maintain context throughout the interaction
- Provide clear options for next steps
- Confirm understanding before proceeding with complex tasks

## Response Format

For search queries:
- Confirm search parameters
- Present top 3-5 matching results
- Include key details for each (name, price, location, availability)
- Offer options to refine search or view more details

For listing requests:
- Follow a structured conversation flow requesting specific details
- Confirm information at each step
- Provide visual confirmation of the listing details
- Explain next steps after submission

For information requests:
- Provide direct, accurate answers
- Include relevant policy details
- Offer follow-up assistance if needed

Always maintain a helpful, solutions-oriented approach and focus on helping users accomplish their goals on the Ubayog platform efficiently.
    """
    
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
    return jsonify({"response": response.split("### Response:")[-1].strip()})

# Search Assets Route
@app.route("/search", methods=["POST"])
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

# List Asset Route
@app.route("/list", methods=["POST"])
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
