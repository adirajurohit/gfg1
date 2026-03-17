import pandas as pd
import sqlite3
import tabulate
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
import time
import io
import base64
from google import genai

qs=[]

def table(d):
    return tabulate.tabulate(d, headers=d.columns, tablefmt="psql")

def graph(d, n):
    if len(d.columns)<2 or n==0:
        return None, None
    try:
        x = d.iloc[:,0]
        y = d.iloc[:,1]
        if not pd.api.types.is_numeric_dtype(y):
            return None,None
        filename = f"graph_{int(time.time())}.png"
        path = os.path.join("uploads", filename)
        plt.rcParams["font.family"] = "Consolas"
        f, a = plt.subplots()
        f.patch.set_alpha(0)
        a.set_facecolor("none")
        f.patch.set_facecolor("white")
        a.set_xlabel(d.columns[0],color="white")
        a.set_ylabel(d.columns[1],color="white")
        a.xaxis.label.set_color("white")
        a.yaxis.label.set_color("white")
        a.title.set_color("white")
        a.tick_params(axis='both', colors='white')
        a.tick_params(axis='x', labelcolor='white') 
        a.tick_params(axis='y', labelcolor='white')
        for spine in a.spines.values():
            spine.set_visible(False)
        c = "#bf80ff"
        bc = mcolors.to_rgb(c)
        clr = []
        for i in range(len(y)):  
            nc = tuple(max(0,c*(1-(i/(len(y)+1)))) for c in bc)
            clr.append(nc)
        if n==1:
            a.plot(x, y,marker="o",color=c)
            a.set_xticklabels(a.get_xticklabels(), rotation=90)
        elif n==2:
            a.pie(y, labels=x,autopct='%1.1f%%',colors=clr,textprops={'color': 'white'})
        elif n==3:
            a.bar(x, y,color=clr)
            a.set_xticklabels(a.get_xticklabels(), rotation=90)
        elif n==4:
            a.hist(y,bins=10,color=c)
        else:
            return None, None
        a.set_xlabel(d.columns[0])
        a.set_ylabel(d.columns[1])

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        plt.close()
        buf.seek(0)
        img64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()

        return filename, img64

    except Exception as e:
        print(e)

    return None, None


def sql(d,q,n=0):
    try:
        with sqlite3.connect("test.db") as c:
            d.to_sql("data", c, if_exists="replace", index=False)
            r = pd.read_sql_query(q, c)
        tbl = table(r)
        grph,img64 = graph(r,n)
        if grph:
            return "Here is the requested table along with a graph to visualise the data:\n" + tbl + f"<br><img src='data:image/png;base64,{img64}' width='700'>"
        return "Here is the requested table:\n" + tbl
    except Exception as e:
        return f"SQL Error: {e}"
    
def tosql(i,d):
    global qs
    client = genai.Client(api_key="key")
    model = "gemini-2.5-flash"
    ni=f'''convert the following into an sql query and return in the form of plaintext.
    if it requires making a graph like line plot(1) or piechart(2) or bar graph(3) or histogram(4), return the respective integer before the sql query:\n
    {i}\n
    here is the table whose name is "data": {sql(d,"select * from data")}\n
    for example, if it says "create bar graph for sales of products" then return only "3 select product as name of product,sales as no of sales from data\n"
    refer to the previous list of queries {qs} to build upon them if applicable'''
    r = client.models.generate_content(model=model,contents=ni)
    r=r.text
    n=int(r[0])
    q=r.strip("`sql")
    q=q[1::].strip()
    qs.append(q)
    return sql(d,q,n)