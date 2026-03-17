from flask import Flask, render_template, request, redirect
import os
import pandas as pd
import time
import modl

df = None

app = Flask(__name__)

os.makedirs("uploads", exist_ok=True)

msg = []

def add_m(txt, msg_type):
    msg.append({
        "text": txt,
        "type": msg_type
    })

@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")

@app.route("/chat", methods=["GET", "POST"])
def index():
    global df
    if len(msg) == 0:
        add_m("Hi! I am here to help generate fully functional, interactive data dashboards using only natural language prompts! Upload a file to get started!",1)
    if request.method == "POST":
        #file
        file = request.files.get("file")
        if file and file.filename != "":
            filepath = os.path.join("uploads", file.filename)
            try:
                file.save(filepath)
                df = None
                if file.filename.endswith(".csv"):
                    df = pd.read_csv(filepath)
                elif file.filename.endswith(".xlsx"):
                    df = pd.read_excel(filepath)
                else:
                    add_m("Please upload a valid .csv or .xlsx file!", 1)
                if df is not None:
                    add_m(f'''{file.filename} uploaded successfully! Here is a summary of the dataset:\n                          
Rows: {df.shape[0]}
Columns: {df.shape[1]}\n
Column Names and Datatypes:
{df.dtypes.to_string()}''', 1)
            except Exception as e:
                df = None
                add_m(f"Sorry! There was an error while uploading the file: {str(e)}", 1)

        #text
        txt = request.form.get("message")
        if txt:
            add_m(txt, 0)
            add_m("Processing your prompt to generate output. Please wait!", 1)
            time.sleep(0.1)
            try:
                if df is not None:
                    #r = modl.sql(df,txt[1::],int(txt[0]))
                    r = modl.tosql(txt,df)
                else:
                    msg.pop()
                    r = modl.abc("Please upload a file!")
                msg.pop()
                add_m(r, 1)
            except Exception as e:
                msg.pop()
                add_m(f"Sorry! There was an error: {str(e)}", 1)
        return redirect("/chat")
    return render_template("chat.html", msg=msg)


if __name__ == "__main__":
    app.run(debug=True)