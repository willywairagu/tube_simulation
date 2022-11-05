import streamlit as st
import pandas as pd
import folium
import base64
from streamlit_folium import st_folium
import networkx as nx
from bokeh.plotting import figure, from_networkx
from bokeh.models import Range1d, Circle, ColumnDataSource, MultiLine

st.set_page_config(page_title="Graph Representation", page_icon="🌍")

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
st.markdown("## Stations Map...")
# st.sidebar.header("Mapping Demo")
st.write(
    """The below Map, shows the locations of london underground stations"""
)

# Reading our Datasets
lu_stations = pd.read_csv("Graph_Data/london.stations.csv")
lu_conns = pd.read_csv("Graph_Data/london.connections.csv")
crowding_df = pd.read_csv("Graph_Data/station_counts_grouped_per_station.csv")

# creating a folium map using London Coordinates
london_map = folium.Map(zoom_start=12, width=1200, height=700, location=[51.529865, -0.128092])

# looping through stations rows
for i, r in lu_stations.iterrows():
    # setting for the popup
    popup = folium.Popup(r['name'], max_width=1000)
    # Plotting the Marker for each stationsト
    folium.map.Marker(
        location=[r['latitude'], r['longitude']],
        popup=popup,
        icon=folium.Icon(color="green", icon="train", prefix='fa')
    ).add_to(london_map)
    folium.vector_layers.CircleMarker(
        location=[r['latitude'], r['longitude']],
        # radius=r['count']/10000,
        color='#3186cc',
        fill_color='#3186cc'
    ).add_to(london_map)

# # lets view the london map
st_folium(london_map, width=725)

st.markdown("## Graph Network simulation...")
st.write(
    """The simulation below shows a graph representation of the network, each node represents a station while the edges
    represent the links of different lines and how this stations interconnect.

    - Hoover onto a particular Node to view its details, i.e Station artributes
    - The Red edges represent interconnection of stations in different zones
    - The Green edges show station links not in the same zone
    """
)


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
# Graph title

Title = "Graph Interaction Demonstration"

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
                  ("Passenger Count", "@Passenger_Count")]

# Create a plot — set dimensions, toolbar, and title
plot = figure(tooltips=HOVER_TOOLTIPS, width=700, height=500, tools="pan,wheel_zoom,save,reset",
              active_scroll='wheel_zoom')

# Create a network graph object
network_graph = from_networkx(G, positions, scale=1, center=(0, 0))

network_graph.node_renderer.glyph = Circle(size=7, fill_color="grey")
network_graph.edge_renderer.glyph = MultiLine(line_color="edge_color", line_alpha=0.8, line_width=1)

# Add network graph to the plot
plot.renderers.append(network_graph)

st.bokeh_chart(plot, use_container_width=True)
