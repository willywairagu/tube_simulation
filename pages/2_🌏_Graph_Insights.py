import streamlit as st
import pandas as pd
import base64
import networkx as nx
from bokeh.plotting import figure, from_networkx
from bokeh.models import Range1d, Circle, ColumnDataSource, MultiLine
from bokeh.transform import linear_cmap
from bokeh.palettes import Blues8, Reds8, Purples8, Oranges8, Viridis8, Spectral8

st.set_page_config(page_title="Graph Insights", page_icon="🌍")

# # background image
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"jpg"};base64,{encoded_string.decode()});
        background-size: cover;
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

add_bg_from_local('faint_bg.jpg')


st.markdown("# The London Tube Map & Graph")
st.markdown("## Network Analysis.")
# st.sidebar.header("Mapping Demo")
st.write(
    """The below simulations aid in analysing the network to show insights on centrality metrics...
    """
)

st.markdown("### 1. Degree Centrality plot....")

# Reading our Datasets
lu_stations = pd.read_csv("Graph_Data/london.stations.csv")
lu_conns = pd.read_csv("Graph_Data/london.connections.csv")
crowding_df = pd.read_csv("Graph_Data/station_counts_grouped_per_station.csv")

# function to merge stations and counts datasets
def stations_crowding_df(stations_df, crowding_df, year, month):
    """
      creates a dataframe with station details with their respective crowding information to be simulated from the graph network

      parameters: stations_df - dataframe of London Underground station details
                  crowding_df - dataframe with monthly crowding information of stations
                  year - year of interest
                  month - month of interest
    """
    # filter crowding data based on year and month of interest
    df = crowding_df[crowding_df['Calendar Year (Travel Date)'] == int(year)]
    df2 = df[df['Month Name (Travel Date)'] == str(month)]
    df3 = df2[['NLC', 'Count of Taps']]
    df3['NLC'] = df3['NLC'].astype('float64')

    # merged dataframe
    df4 = pd.merge(stations_df, df3, how='outer', on="NLC")
    # dropping nulls ni coordinates column
    final_df = df4.dropna(subset=['latitude', 'longitude'], axis=0)

    return final_df

# creating df to visualize
final_df = stations_crowding_df(lu_stations, crowding_df, 2021, "January")

# creating a graph object
G = nx.Graph()
G.add_nodes_from(final_df['id'])
G.add_edges_from(list(zip(lu_conns['station1'], lu_conns['station2'])))

# getting geographical coordinates
cordinates = list(zip(lu_stations['longitude'], lu_stations['latitude']))
positions = dict(zip(lu_stations['id'], cordinates))

# setting node attributes
mapping_dict = dict(zip(final_df.id, final_df.name))
zones_dict = dict(zip(final_df.id, final_df.zone))
counts_dict = dict(zip(final_df['id'], final_df['Count of Taps']))

nx.set_node_attributes(G, name="Name", values=mapping_dict)
nx.set_node_attributes(G, name="Zone", values=zones_dict)
nx.set_node_attributes(G, name="Passenger_Count", values=counts_dict)

# Graph title
Title = "Graph Simulation With Passenger Counts Demonstration"

# calculating degree centrality values for each station
degrees = dict(nx.degree(G))
nx.set_node_attributes(G, name='degree', values=degrees)

#Pick a color palette — Blues8, Reds8, Purples8, Oranges8, Viridis8
color_palette = Spectral8

# Slightly adjust degree so that the nodes with very small degrees are still visible
number_to_adjust_by = 5
adjusted_node_size = dict([(node, degree+number_to_adjust_by) for node, degree in nx.degree(G)])
nx.set_node_attributes(G, name='adjusted_node_size', values=adjusted_node_size)

#Choose attributes from G network to size and color by — setting manual size (e.g. 10) or color (e.g. 'skyblue') also allowed
size_by_this_attribute = 'adjusted_node_size'
color_by_this_attribute = 'adjusted_node_size'


# visualizing stations based on zones
SAME_ZONE_COLOR, DIFFERENT_ZONE_COLOR = "green", "red"
edge_attrs = {}

for start_node, end_node, _ in G.edges(data=True):
    edge_color = SAME_ZONE_COLOR if G.nodes[start_node]["Zone"] == G.nodes[end_node]["Zone"] else DIFFERENT_ZONE_COLOR
    edge_attrs[(start_node, end_node)] = edge_color

# setting edge attributes
nx.set_edge_attributes(G, edge_attrs, "edge_color")

# Establish which categories will appear when hovering over each node
HOVER_TOOLTIPS = [("Station", "@Name"),
                  ("Zone", "@Zone"),
                  ("Passenger Count", "@Passenger_Count"),
                  ("Degree Centrality", "@degree")]

# Create a plot — set dimensions, toolbar, and title
degree_plot = figure(tooltips=HOVER_TOOLTIPS, width=700, height=500, tools="pan,wheel_zoom,save,reset",
              active_scroll='wheel_zoom')

# Create a network graph object
degree_graph = from_networkx(G, positions, scale=1, center=(0, 0))

#Set node sizes and colors according to node degree (color as spectrum of color palette)
minimum_value_color = min(degree_graph.node_renderer.data_source.data[color_by_this_attribute])
maximum_value_color = max(degree_graph.node_renderer.data_source.data[color_by_this_attribute])
degree_graph.node_renderer.glyph = Circle(size=size_by_this_attribute, fill_color=linear_cmap(color_by_this_attribute, color_palette, minimum_value_color, maximum_value_color))

degree_graph.edge_renderer.glyph = MultiLine(line_color="edge_color", line_alpha=0.8, line_width=1)

# Add network graph to the plot
degree_plot.renderers.append(degree_graph)
st.bokeh_chart(degree_plot, use_container_width=True)


st.markdown("### 2. Betweenness Centrality plot....")

# Graph title
Title = "Graph Simulation With Passenger Counts Demonstration"

# calculating betweenness centrality values for each station
betweenness = dict(nx.betweenness_centrality(G))
nx.set_node_attributes(G, name='Betweenness', values=betweenness)

#Pick a color palette — Blues8, Reds8, Purples8, Oranges8, Viridis8
color_palette2 = Purples8

# Slightly adjust degree so that the nodes with very small degrees are still visible
number_to_adjust_by2 = 7
adjusted_node_size2 = dict([(node, betweenness+number_to_adjust_by2) for node, betweenness in betweenness.items()])
nx.set_node_attributes(G, name='adjusted_node_size2', values=adjusted_node_size2)

#Choose attributes from G network to size and color by — setting manual size (e.g. 10) or color (e.g. 'skyblue') also allowed
size_by_this_attribute2 = 'adjusted_node_size2'
color_by_this_attribute2 = 'adjusted_node_size2'

# Establish which categories will appear when hovering over each node
HOVER_TOOLTIPS = [("Station", "@Name"),
                  ("Zone", "@Zone"),
                  ("Passenger Count", "@Passenger_Count"),
                  ("Degree Centrality", "@degree"),
                  ("Betweenness Centrality", "@Betweenness")]

# Create a plot — set dimensions, toolbar, and title
degree_plot2 = figure(tooltips=HOVER_TOOLTIPS, width=700, height=500, tools="pan,wheel_zoom,save,reset",
              active_scroll='wheel_zoom')

# Create a network graph object
degree_graph2 = from_networkx(G, positions, scale=1, center=(0, 0))

#Set node sizes and colors according to node degree (color as spectrum of color palette)
minimum_value_color2 = min(degree_graph2.node_renderer.data_source.data[color_by_this_attribute2])
maximum_value_color2 = max(degree_graph2.node_renderer.data_source.data[color_by_this_attribute2])
degree_graph2.node_renderer.glyph = Circle(size=size_by_this_attribute2, fill_color=linear_cmap(color_by_this_attribute2, color_palette2, minimum_value_color2, maximum_value_color2))

degree_graph2.edge_renderer.glyph = MultiLine(line_color="edge_color", line_alpha=0.8, line_width=1)

# Add network graph to the plot
degree_plot2.renderers.append(degree_graph2)

st.bokeh_chart(degree_plot2, use_container_width=True)