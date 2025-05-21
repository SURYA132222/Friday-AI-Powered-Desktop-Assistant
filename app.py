from flask import Flask, render_template, request, jsonify
from assistant_core import reply, greet

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/greet")
def greet_route():
    return jsonify({"response": greet()})

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    bot_msg  = reply(user_msg)
    return jsonify({"response": bot_msg})

if __name__ == "__main__":
    app.run(debug=True)
