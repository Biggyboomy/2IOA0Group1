from __future__ import print_function

from flask import Flask, render_template, request
from flask_uploads import UploadSet, configure_uploads, DATA

import jinja2
import pandas as pd
import json

from bokeh.embed import json_item
from bokeh.resources import CDN


import os
import numpy as np
import holoviews as hv
import networkx as nx
from bokeh.plotting import figure
from holoviews.element.graphs import layout_nodes
hv.extension('bokeh')

app = Flask(__name__)

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

# links to go from page to page
@app.route("/")
def index():
    return render_template("mainpage.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")


# extra stuff for uploading data-sets
datafiles = UploadSet('data', DATA)
app.config['UPLOADED_DATA_DEST'] = 'static/data'
configure_uploads(app, datafiles)

# upload path
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'any' in request.files:
        filename = datafiles.save(request.files['any'])
        return render_template('mainpage.html')
    return render_template('mainpage.html')


# generator for plot-page, also set some variables
page = jinja_env.get_template('vis.html')
holdFileName = 'nodeDummy'
file = f'static/data/{holdFileName}.csv'

# route to the page with visualizations and plot selection
@app.route("/visualization", methods=['GET', 'POST'])
def root():
    global holdFileName
    global file
    arr = os.listdir(app.config['UPLOADED_DATA_DEST'])
    if request.method == 'POST':
        holdFileName = request.form.get('set')
    file = f'static/data/{holdFileName}'
    return page.render(resources=CDN.render(), selected=holdFileName, arr=arr, holdFileName=holdFileName, file=file)

# Node-link diagram
@app.route('/plot')
def plot():
    df_data = pd.read_csv(file, sep=';', header=0, index_col=False)

    d = []
    e = []
    f = []
    hold = df_data.shape[0]

    # loop that sets values first in lists for columns
    i = 0
    while i < hold:

        b = list(df_data.columns.values)
        del b[0]
        a1 = len(b) - i
        a = list(a1 * (df_data.iloc[i, 0],))
        del a[:1]

        p = b
        del p[:(i + 1)]

        c = df_data.iloc[:, 1].tolist()
        del c[:(i + 1)]

        for ele in c:
            if ele == 1:
                c.remove(ele)

        e = list(e + a)
        d = list(d + p)
        f = list(f + c)

        i += 1

    # df from which the plot will be made
    df_plot = pd.DataFrame(columns=['from', 'to', 'weight'])

    # puts said lists in columns
    df_plot['from'] = e
    df_plot['to'] = d
    df_plot['weight'] = f

    df_plot = df_plot.loc[df_plot['weight'] != 0.0]

    graph = hv.Graph(df_plot)
    graph.opts(width=600, height=600, show_frame=False, edge_color='weight',
               xaxis=None, yaxis=None, node_size=10, edge_line_width='weight')
    layout_nodes(graph, layout=nx.layout.circular_layout)

    holder = graph
    renderer = hv.renderer('bokeh')
    k = renderer.get_plot(holder).state

    k.plot_width = 700
    k.plot_height = 700

    return json.dumps(json_item(k))

# Adjacency Matrix
@app.route('/plot2')
def plot2():

    # read csv file
    df_data = pd.read_csv(file, sep=';', header=0, index_col=False)

    x = []
    namesTo = []
    namesFrom = []
    namesWeight = []
    hold = df_data.shape[0]  # fixed number for column length

    # loop that sets values first in lists for columns
    i = 0
    while i < hold:
        namesVal = list(df_data.columns.values)
        del namesVal[0]
        namesTimes = len(namesVal)
        namesHold = list(namesTimes * (df_data.iloc[i, 0],))

        # To names
        x = namesVal

        # weights
        c = df_data.iloc[:, (i + 1)].tolist()

        namesFrom = list(namesFrom + namesHold)
        namesTo = list(namesTo + x)
        namesWeight = list(namesWeight + c)

        i += 1

    # df from which the plot will be made
    df_plot = pd.DataFrame(columns=['from', 'to', 'weight'])

    # might still need to drop rows with namesHold 0
    # puts said lists in columns
    df_plot['from'] = namesFrom
    df_plot['to'] = namesTo
    df_plot['weight'] = namesWeight

    data = dict(
        xname=namesFrom,
        yname=namesTo,
        weights=namesWeight
    )

    # plotting the figure
    p = figure(x_axis_location="above",
               x_range=list(reversed(df_plot['from'].unique())), y_range=(df_plot['from'].unique()),
               tooltips=[('names', '@yname, @xname'), ('weight', '@weights'), ])

    p.plot_width = 700
    p.plot_height = 700
    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "6pt"
    p.axis.major_label_standoff = 0
    p.xaxis.major_label_orientation = np.pi / 3

    p.rect('xname', 'yname', 0.9, 0.9, source=data, alpha='weights', line_color=None,
           hover_line_color='black', color='blue', hover_color='blue')

    # output_file("auth_sim.html", title="auth_sim.py example")

    return json.dumps(json_item(p))


if __name__ == '__main__':
    app.run(debug=True)
