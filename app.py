<<<<<<< HEAD
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
=======
from flask import Flask
app = Flask(__name__)
@app.route("/")
def home():
 return "<h1>Employee Task Scheduler</h1>"
if __name__ == "__main__":
 app.run(debug=True)
>>>>>>> 4cb9ae6012a2fa03f81acee9d8b4d29d231ab13d
