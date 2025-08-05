from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def Welcome_Bandalgom_Caffee():
    return render_template("bandalgom.html")

@app.route("/menu")
def menu():
    return render_template("menu.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)